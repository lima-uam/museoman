import os

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.catalog.models import Tipo, Vitrina

from .models import Item, ItemPhoto

_WIDGET_ATTRS = {"class": "form-control"}


def _add_attrs(form):
    for field in form.fields.values():
        w = field.widget
        if not isinstance(w, (forms.CheckboxInput, forms.HiddenInput, forms.FileInput)):
            w.attrs.setdefault("class", "form-control")
    return form


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["nombre", "tipos", "vitrina", "url", "observaciones"]
        labels = {
            "nombre": "Nombre",
            "tipos": "Tipos",
            "vitrina": "Vitrina",
            "url": "URL",
            "observaciones": "Observaciones",
        }
        widgets = {
            "tipos": forms.SelectMultiple(attrs={"class": "form-control", "id": "id_tipos"}),
            "url": forms.URLInput(attrs={"placeholder": "https://...", **_WIDGET_ATTRS}),
            "observaciones": forms.Textarea(attrs={"rows": 3, **_WIDGET_ATTRS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vitrina"].required = False
        self.fields["vitrina"].empty_label = "— Sin vitrina —"
        self.fields["tipos"].queryset = Tipo.objects.all()
        self.fields["vitrina"].queryset = Vitrina.objects.all()
        _add_attrs(self)


class ItemFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(attrs={"placeholder": "Buscar por nombre…"}),
    )
    estado = forms.ChoiceField(required=False, label="Estado", choices=[])
    assigned_user = forms.ModelChoiceField(
        required=False,
        label="Asignado a",
        queryset=None,
        empty_label="Todos los usuarios",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    tipo = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Tipo.objects.all(),
        label="Tipos",
        widget=forms.SelectMultiple(attrs={"class": "form-control", "id": "id_filter_tipo"}),
    )
    vitrina = forms.ModelChoiceField(
        required=False,
        queryset=Vitrina.objects.all(),
        label="Vitrina",
        empty_label="Todas las vitrinas",
    )
    activo = forms.ChoiceField(
        required=False,
        label="Estado de activación",
        choices=[("1", "Solo activos"), ("0", "Solo inactivos"), ("", "Todos")],
        initial="1",
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Por defecto"),
            ("nombre", "Nombre A-Z"),
            ("-nombre", "Nombre Z-A"),
            ("estado", "Estado"),
            ("-created_at", "Más recientes"),
            ("created_at", "Más antiguos"),
        ],
    )

    def __init__(self, *args, **kwargs):
        from apps.items.state import State

        super().__init__(*args, **kwargs)
        self.fields["estado"].choices = [("", "Todos los estados")] + list(State.choices)
        User = get_user_model()
        self.fields["assigned_user"].queryset = User.objects.filter(is_active=True).order_by("name")


class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = ItemPhoto
        fields = ["image"]
        labels = {"image": "Imagen"}

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
                allowed = ", ".join(settings.ALLOWED_IMAGE_EXTENSIONS)
                raise forms.ValidationError(f"Formato no permitido. Usa: {allowed}")
            if image.size > settings.MAX_UPLOAD_SIZE:
                max_mb = settings.MAX_UPLOAD_SIZE // 1024 // 1024
                raise forms.ValidationError(f"El archivo excede el tamaño máximo de {max_mb} MB.")
        return image
