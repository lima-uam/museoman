from django import forms

from .models import Tipo, Vitrina


class TipoForm(forms.ModelForm):
    class Meta:
        model = Tipo
        fields = ["nombre"]
        labels = {"nombre": "Nombre"}


class VitrinaForm(forms.ModelForm):
    class Meta:
        model = Vitrina
        fields = ["numero"]
        labels = {"numero": "Número"}
