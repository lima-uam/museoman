from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm

User = get_user_model()

_FC = {"class": "form-control"}


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "name", "is_staff"]
        labels = {
            "email": "Correo electrónico",
            "name": "Nombre",
            "is_staff": "Administrador",
        }
        widgets = {
            "email": forms.EmailInput(attrs=_FC),
            "name": forms.TextInput(attrs=_FC),
        }


class PasswordChangeFormStyled(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "name", "is_staff", "is_active"]
        labels = {
            "email": "Correo electrónico",
            "name": "Nombre",
            "is_staff": "Administrador",
            "is_active": "Activo",
        }
        widgets = {
            "email": forms.EmailInput(attrs=_FC),
            "name": forms.TextInput(attrs=_FC),
        }
