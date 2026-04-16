from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import UserCreateForm, UserUpdateForm
from .mixins import AdminRequiredMixin

User = get_user_model()


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "usuarios"
    queryset = User.objects.all().order_by("name")


class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nuevo usuario"
        return ctx


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar usuario"
        return ctx
