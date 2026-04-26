import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.audit.models import AuditLog
from apps.audit.services import record, record_field_changes
from apps.catalog.models import Tipo, Vitrina
from apps.items.models import Item
from apps.items.state import State, TransitionError, apply_transition

URL_BASE = "https://museo.lima.uam.es/piezas"

ITEM_NAMES = [
    "IBM PC XT 5160",
    "IBM PC AT 5170",
    "Commodore 64",
    "Commodore Amiga 500",
    "Sinclair ZX Spectrum 48K",
    "Apple II Plus",
    "Apple Macintosh 128K",
    "Disco duro IBM 20MB",
    "Disco duro Seagate ST-506",
    'Monitor VGA 14" IBM',
    'Monitor CGA 12" Amdek',
    "Teclado PS/2 IBM",
    "Teclado Model M",
    "Raton Microsoft IntelliMouse",
    "Raton Logitech TrackMan",
    "Impresora Epson FX-80",
    "Impresora HP LaserJet II",
    "Disquetera 5.25 Tandon",
    "Disquetera 3.5 Sony",
    "Tarjeta grafica Hercules",
    "Tarjeta grafica EGA Paradise",
    "Tarjeta de red 3Com EtherLink",
    "Modem US Robotics 14400",
    "Fuente de alimentacion AT IBM",
    "Placa base XT Compaq",
]

OBSERVATIONS_POOL = [
    "Buen estado general, funciona correctamente.",
    "Falta la tapa trasera.",
    "Cable de alimentacion incluido.",
    "Necesita limpieza interna.",
    "Sin caja original.",
    "Donado por la Facultad de Ciencias.",
    "Adquirido en subasta interna.",
    "Teclas desgastadas pero funcional.",
    "Pantalla con rayaduras leves.",
    "Documentacion original incluida.",
]


class Command(BaseCommand):
    help = "Poblar la base de datos con datos de demostración"

    def handle(self, *args, **options):
        User = get_user_model()
        rng = random.Random(42)

        # ── Tipos ──────────────────────────────────────────────────────────
        tipo_names = [
            "Ordenador",
            "Disco duro",
            "Monitor",
            "Teclado",
            "Raton",
            "Impresora",
            "Disquetera",
            "Tarjeta",
            "Modem",
            "Otro",
        ]
        tipos = []
        for nombre in tipo_names:
            t, _ = Tipo.objects.get_or_create(nombre=nombre)
            tipos.append(t)
        self.stdout.write(f"Tipos: {len(tipos)}")

        # ── Vitrinas ───────────────────────────────────────────────────────
        vitrina_names = ["Sala A", "Sala B", "Sala C", "Almacen"]
        vitrinas = []
        for nombre in vitrina_names:
            v, _ = Vitrina.objects.get_or_create(nombre=nombre)
            vitrinas.append(v)
        self.stdout.write(f"Vitrinas: {len(vitrinas)}")

        # ── Users ──────────────────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            email="admin@lima.uam.es",
            defaults={"name": "Administrador LIMA", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password("admin1234")
            admin.save()
            self.stdout.write("Admin creado: admin@lima.uam.es / admin1234")

        volunteer_data = [
            ("ana@lima.uam.es", "Ana Garcia"),
            ("pedro@lima.uam.es", "Pedro Lopez"),
            ("sara@lima.uam.es", "Sara Martinez"),
        ]
        volunteers = []
        for email, name in volunteer_data:
            u, created = User.objects.get_or_create(email=email, defaults={"name": name})
            if created:
                u.set_password("usuario1234")
                u.save()
                self.stdout.write(f"Usuario creado: {email} / usuario1234")
            volunteers.append(u)

        # ── Items ──────────────────────────────────────────────────────────
        items = []
        for nombre in ITEM_NAMES:
            item, created = Item.all_objects.get_or_create(
                nombre=nombre,
                defaults={
                    "created_by": admin,
                    "vitrina": rng.choice(vitrinas + [None, None]),
                    "observaciones": rng.choice(OBSERVATIONS_POOL),
                },
            )
            if created:
                t1 = rng.choice(tipos)
                t2 = rng.choice(tipos)
                item.tipos.set([t1] if t1 == t2 else [t1, t2])
                record(AuditLog.ACTION_CREATED, item, admin)
            items.append(item)
        self.stdout.write(f"Piezas: {len(items)}")

        # ── Activity simulation ────────────────────────────────────────────
        # Each item gets a randomised lifecycle. Some reach documentado, some
        # stay mid-flow, some get reverted, a few get deactivated.
        for item in items:
            if item.estado != State.LIBRE:
                continue  # already has history from a previous seed run

            fate = rng.choice(
                ["documentado", "documentado", "en_revision", "asignado", "revert", "deactivated", "libre"]
            )
            volunteer = rng.choice(volunteers)

            # ── edits before assignment ────────────────────────────────────
            if rng.random() < 0.6:
                old = {
                    "nombre": item.nombre,
                    "observaciones": item.observaciones or "",
                    "url": str(item.url or ""),
                    "vitrina_slot": item.vitrina_slot or "",
                    "vitrina": item.vitrina.nombre if item.vitrina else "",
                    "tipos": ", ".join(sorted(item.tipos.values_list("nombre", flat=True))),
                }
                new_obs = rng.choice(OBSERVATIONS_POOL)
                item.observaciones = new_obs
                item.save(update_fields=["observaciones"])
                new = dict(old, observaciones=new_obs)
                record_field_changes(item, admin, old, new)

            if fate == "libre":
                continue

            # ── assign ────────────────────────────────────────────────────
            try:
                apply_transition(item, State.ASIGNADO, admin, assign_to=volunteer)
            except TransitionError:
                continue

            if fate == "asignado":
                continue

            if fate == "revert":
                apply_transition(item, State.LIBRE, volunteer)
                # re-assign to someone else
                other = rng.choice([v for v in volunteers if v != volunteer])
                try:
                    apply_transition(item, State.ASIGNADO, admin, assign_to=other)
                except TransitionError:
                    pass
                continue

            # ── edit nombre while assigned ─────────────────────────────────
            if rng.random() < 0.4:
                old_nombre = item.nombre
                new_nombre = item.nombre + " (revisado)"
                old = {
                    "nombre": old_nombre,
                    "observaciones": item.observaciones or "",
                    "url": str(item.url or ""),
                    "vitrina_slot": item.vitrina_slot or "",
                    "vitrina": item.vitrina.nombre if item.vitrina else "",
                    "tipos": ", ".join(sorted(item.tipos.values_list("nombre", flat=True))),
                }
                item.nombre = new_nombre
                item.save(update_fields=["nombre"])
                new = dict(old, nombre=new_nombre)
                record_field_changes(item, volunteer, old, new)

            # ── advance to en_revision ─────────────────────────────────────
            item_url = f"{URL_BASE}/{item.pk}"
            try:
                apply_transition(item, State.EN_REVISION, volunteer, url=item_url)
            except TransitionError:
                continue

            if fate == "en_revision":
                continue

            # ── documentado ───────────────────────────────────────────────
            try:
                apply_transition(item, State.DOCUMENTADO, admin)
            except TransitionError:
                continue

            if fate == "deactivated":
                item.activo = False
                item.save(update_fields=["activo"])
                record(AuditLog.ACTION_DEACTIVATED, item, admin)

        # ── High-churn item for pagination testing ─────────────────────────
        churn, created = Item.all_objects.get_or_create(
            nombre="Unidad de cinta IBM 3420 (alta actividad)",
            defaults={"created_by": admin, "observaciones": "Pieza con historial extenso.", "vitrina": vitrinas[0]},
        )
        if created:
            churn.tipos.add(tipos[0])
            record(AuditLog.ACTION_CREATED, churn, admin)
            obs_cycle = [
                "Pendiente de revision.",
                "Cables comprobados.",
                "Mecanismo de carga verificado.",
                "Limpieza completada.",
                "Etiquetado actualizado.",
                "Ubicacion cambiada a Sala B.",
                "Documentacion fotografica pendiente.",
                "Referencia cruzada con catalogo IBM.",
            ]
            for i, obs in enumerate(obs_cycle * 5):
                volunteer = volunteers[i % len(volunteers)]
                old = {
                    "nombre": churn.nombre,
                    "observaciones": churn.observaciones or "",
                    "url": str(churn.url or ""),
                    "vitrina_slot": churn.vitrina_slot or "",
                    "vitrina": churn.vitrina.nombre if churn.vitrina else "",
                    "tipos": ", ".join(sorted(churn.tipos.values_list("nombre", flat=True))),
                }
                churn.observaciones = obs
                churn.save(update_fields=["observaciones"])
                record_field_changes(churn, volunteer, old, dict(old, observaciones=obs))
            self.stdout.write(f"Pieza de alta actividad creada: pk={churn.pk}")

        # ── Ensure at least a few items stay libre and some are inactive ──
        # (covered by the fate distribution above)

        libre = Item.all_objects.filter(estado=State.LIBRE, activo=True).count()
        asignado = Item.all_objects.filter(estado=State.ASIGNADO).count()
        en_revision = Item.all_objects.filter(estado=State.EN_REVISION).count()
        documentado = Item.all_objects.filter(estado=State.DOCUMENTADO).count()
        inactivo = Item.all_objects.filter(activo=False).count()
        audit_count = AuditLog.objects.count()

        self.stdout.write(
            f"Estados: libre={libre}, asignado={asignado}, "
            f"en_revision={en_revision}, documentado={documentado}, inactivo={inactivo}"
        )
        self.stdout.write(f"Entradas de auditoria: {audit_count}")
        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados correctamente."))
