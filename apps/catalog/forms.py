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
        fields = ["nombre", "url"]
        labels = {"nombre": "Nombre", "url": "URL"}
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
        }
