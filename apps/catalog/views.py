from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.accounts.mixins import AdminRequiredMixin
from apps.audit.models import AuditLog
from apps.audit.services import record_vitrina

from .forms import TipoForm, VitrinaForm
from .models import Tipo, Vitrina

# ── Tipos ──────────────────────────────────────────────────────────────────


class TipoListView(AdminRequiredMixin, ListView):
    model = Tipo
    template_name = "catalog/tipo_list.html"
    context_object_name = "tipos"


class TipoCreateView(AdminRequiredMixin, CreateView):
    model = Tipo
    form_class = TipoForm
    template_name = "catalog/tipo_form.html"
    success_url = reverse_lazy("catalog:tipo_list")

    def form_valid(self, form):
        messages.success(self.request, "Tipo creado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nuevo tipo"
        return ctx


class TipoUpdateView(AdminRequiredMixin, UpdateView):
    model = Tipo
    form_class = TipoForm
    template_name = "catalog/tipo_form.html"
    success_url = reverse_lazy("catalog:tipo_list")

    def form_valid(self, form):
        messages.success(self.request, "Tipo actualizado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar tipo"
        return ctx


class TipoDeleteView(AdminRequiredMixin, DeleteView):
    model = Tipo
    template_name = "catalog/confirm_delete.html"
    success_url = reverse_lazy("catalog:tipo_list")

    def form_valid(self, form):
        messages.success(self.request, "Tipo eliminado.")
        return super().form_valid(form)


# ── Vitrinas ───────────────────────────────────────────────────────────────


class VitrinaListView(AdminRequiredMixin, ListView):
    model = Vitrina
    template_name = "catalog/vitrina_list.html"
    context_object_name = "vitrinas"


class VitrinaCreateView(AdminRequiredMixin, CreateView):
    model = Vitrina
    form_class = VitrinaForm
    template_name = "catalog/vitrina_form.html"
    success_url = reverse_lazy("catalog:vitrina_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        record_vitrina(AuditLog.ACTION_VITRINA_CREATED, self.object, self.request.user)
        messages.success(self.request, "Vitrina creada correctamente.")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva vitrina"
        return ctx


class VitrinaUpdateView(AdminRequiredMixin, UpdateView):
    model = Vitrina
    form_class = VitrinaForm
    template_name = "catalog/vitrina_form.html"
    success_url = reverse_lazy("catalog:vitrina_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        record_vitrina(AuditLog.ACTION_VITRINA_UPDATED, self.object, self.request.user)
        messages.success(self.request, "Vitrina actualizada.")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar vitrina"
        return ctx


class VitrinaDeleteView(AdminRequiredMixin, DeleteView):
    model = Vitrina
    template_name = "catalog/confirm_delete.html"
    success_url = reverse_lazy("catalog:vitrina_list")

    def form_valid(self, form):
        record_vitrina(
            AuditLog.ACTION_VITRINA_DELETED,
            self.object,
            self.request.user,
            payload={"nombre": self.object.nombre, "pk": self.object.pk},
        )
        messages.success(self.request, "Vitrina eliminada.")
        return super().form_valid(form)
