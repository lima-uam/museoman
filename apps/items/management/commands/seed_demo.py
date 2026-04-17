from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.catalog.models import Tipo, Vitrina
from apps.items.models import Item


class Command(BaseCommand):
    help = "Poblar la base de datos con datos de demostración"

    def handle(self, *args, **options):
        User = get_user_model()

        # Tipos
        tipos = []
        for nombre in ["Ordenador", "Disco duro", "Monitor", "Teclado", "Ratón"]:
            t, _ = Tipo.objects.get_or_create(nombre=nombre)
            tipos.append(t)
        self.stdout.write(f"Tipos: {len(tipos)}")

        # Vitrinas
        vitrinas = []
        for nombre in ["Sala A", "Sala B", "Sala C"]:
            v, _ = Vitrina.objects.get_or_create(nombre=nombre)
            vitrinas.append(v)
        self.stdout.write(f"Vitrinas: {len(vitrinas)}")

        # Admin user
        admin, created = User.objects.get_or_create(
            email="admin@lima.uam.es",
            defaults={"name": "Administrador LIMA", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password("admin1234")
            admin.save()
            self.stdout.write("Admin creado: admin@lima.uam.es / admin1234")

        # Regular user
        user, created = User.objects.get_or_create(
            email="usuario@lima.uam.es",
            defaults={"name": "Usuario de prueba"},
        )
        if created:
            user.set_password("usuario1234")
            user.save()
            self.stdout.write("Usuario creado: usuario@lima.uam.es / usuario1234")

        # Items
        demo_items = [
            ("IBM PC XT 5160", tipos[0], vitrinas[0]),
            ("Disco duro IBM 20MB", tipos[1], vitrinas[0]),
            ("Monitor VGA 14\"", tipos[2], vitrinas[1]),
            ("Teclado PS/2 IBM", tipos[3], None),
            ("Commodore 64", tipos[0], vitrinas[2]),
        ]
        for nombre, tipo, vitrina in demo_items:
            Item.all_objects.get_or_create(
                nombre=nombre,
                defaults={"tipo": tipo, "vitrina": vitrina, "created_by": admin},
            )
        self.stdout.write(f"Piezas: {len(demo_items)}")

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados correctamente."))
