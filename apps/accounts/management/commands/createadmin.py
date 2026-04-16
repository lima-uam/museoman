from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea un usuario administrador interactivamente"

    def handle(self, *args, **options):
        User = get_user_model()
        self.stdout.write("Crear administrador para Museoman")
        email = input("Email: ").strip()
        name = input("Nombre: ").strip()
        import getpass

        password = getpass.getpass("Contraseña: ")
        password2 = getpass.getpass("Confirmar contraseña: ")

        if password != password2:
            self.stderr.write("Las contraseñas no coinciden.")
            return

        if User.objects.filter(email=email).exists():
            self.stderr.write(f"Ya existe un usuario con el email {email}.")
            return

        User.objects.create_superuser(email=email, name=name, password=password)
        self.stdout.write(self.style.SUCCESS(f"Administrador {email} creado."))
