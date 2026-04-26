from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView

from apps.accounts.mixins import AdminRequiredMixin
from apps.audit.models import AuditLog
from apps.audit.services import record

from .forms import ItemFilterForm, ItemForm, PhotoUploadForm
from .models import Item, ItemPhoto
from .state import BACKWARD, FORWARD, State, TransitionError, apply_transition, can_revert, can_transition

User = get_user_model()


class ItemListView(LoginRequiredMixin, View):
    template_name = "items/item_list.html"
    paginate_by = 20

    def get(self, request):
        form = ItemFilterForm(request.GET)
        qs = Item.all_objects.select_related("assigned_user", "vitrina").prefetch_related("tipos", "photos")

        if form.is_valid():
            q = form.cleaned_data.get("q")
            estado = form.cleaned_data.get("estado")
            assigned_user_id = form.cleaned_data.get("assigned_user")
            tipo = form.cleaned_data.get("tipo")
            vitrina = form.cleaned_data.get("vitrina")
            activo = form.cleaned_data.get("activo")
            sort = form.cleaned_data.get("sort")

            if q:
                qs = qs.filter(Q(nombre__icontains=q))
            if estado:
                qs = qs.filter(estado=estado)
            if assigned_user_id:
                qs = qs.filter(assigned_user=assigned_user_id)
            if tipo:
                for t in tipo:
                    qs = qs.filter(tipos=t)
                qs = qs.distinct()
            if vitrina:
                qs = qs.filter(vitrina=vitrina)
            if activo == "1":
                qs = qs.filter(activo=True)
            elif activo == "0":
                qs = qs.filter(activo=False)
            # activo == "" → no filter (all)
            if not activo:
                pass  # already unfiltered

            if sort and sort in [f.name for f in Item._meta.get_fields() if hasattr(f, "name")]:
                qs = qs.order_by(sort)
            elif sort and sort.lstrip("-") in [f.name for f in Item._meta.get_fields() if hasattr(f, "name")]:
                qs = qs.order_by(sort)
        else:
            qs = qs.filter(activo=True)

        paginator = Paginator(qs, self.paginate_by)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        users = User.objects.filter(is_active=True).order_by("name")

        ctx = {
            "form": form,
            "page_obj": page_obj,
            "users": users,
            "State": State,
        }
        if request.htmx:
            return render(request, "items/partials/item_table.html", ctx)
        return render(request, self.template_name, ctx)


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = "items/item_detail.html"
    context_object_name = "item"

    def get_object(self, queryset=None):
        return get_object_or_404(Item.all_objects, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        item = self.object
        user = self.request.user

        next_s = FORWARD.get(item.estado, "")
        ctx["can_advance"] = can_transition(item, next_s, user) if item.estado in FORWARD else False
        ctx["can_revert"] = can_revert(item, user)
        ctx["next_state"] = FORWARD.get(item.estado)
        ctx["prev_state"] = BACKWARD.get(item.estado)
        ctx["audit_logs"] = item.audit_logs.select_related("actor").order_by("-created_at")[:20]
        ctx["photos"] = item.photos.all()
        ctx["photo_urls"] = [p.image.url for p in ctx["photos"]]
        ctx["photo_form"] = PhotoUploadForm()
        ctx["State"] = State
        ctx["users"] = User.objects.filter(is_active=True).order_by("name") if user.is_staff else None
        return ctx


class ItemCreateView(AdminRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "items/item_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        record(AuditLog.ACTION_CREATED, self.object, self.request.user)
        messages.success(self.request, "Pieza creada correctamente.")
        return response

    def get_success_url(self):
        return reverse_lazy("items:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva pieza"
        return ctx


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "items/item_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        item = get_object_or_404(Item.all_objects, pk=kwargs["pk"])
        if not request.user.is_staff:
            from django.core.exceptions import PermissionDenied

            if not (item.estado == State.ASIGNADO and item.assigned_user == request.user):
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Item.all_objects, pk=self.kwargs["pk"])

    def form_valid(self, form):
        response = super().form_valid(form)
        record(AuditLog.ACTION_UPDATED, self.object, self.request.user)
        messages.success(self.request, "Pieza actualizada.")
        return response

    def get_success_url(self):
        return reverse_lazy("items:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar pieza"
        return ctx


class ItemTransitionView(LoginRequiredMixin, View):
    """POST: apply a state transition."""

    def post(self, request, pk):
        item = get_object_or_404(Item.all_objects, pk=pk)
        target = request.POST.get("target")
        assign_to_id = request.POST.get("assign_to")

        assign_to = None
        if assign_to_id:
            assign_to = get_object_or_404(User, pk=assign_to_id)

        url = request.POST.get("url", "").strip()

        try:
            apply_transition(item, target, request.user, assign_to=assign_to, url=url)
            messages.success(request, f"Estado actualizado a «{State(target).label}».")
        except (TransitionError, ValueError) as e:
            messages.error(request, str(e))

        if request.htmx:
            _next = FORWARD.get(item.estado, "")
            ctx = {
                "item": item,
                "State": State,
                "can_advance": can_transition(item, _next, request.user) if item.estado in FORWARD else False,
                "can_revert": can_revert(item, request.user),
                "next_state": FORWARD.get(item.estado),
                "prev_state": BACKWARD.get(item.estado),
                "users": User.objects.filter(is_active=True).order_by("name") if request.user.is_staff else None,
            }
            return render(request, "items/partials/item_state_card.html", ctx)
        return redirect("items:detail", pk=pk)


class ItemAssignView(LoginRequiredMixin, View):
    """POST: assign item to self (or to a user if admin)."""

    def post(self, request, pk):
        item = get_object_or_404(Item.all_objects, pk=pk)
        assign_to_id = request.POST.get("assign_to")

        if assign_to_id and request.user.is_staff:
            assign_to = get_object_or_404(User, pk=assign_to_id)
        else:
            assign_to = request.user

        try:
            apply_transition(item, State.ASIGNADO, request.user, assign_to=assign_to)
            messages.success(request, f"Pieza asignada a {assign_to.name}.")
        except (TransitionError, ValueError) as e:
            messages.error(request, str(e))

        if request.htmx:
            _next = FORWARD.get(item.estado, "")
            ctx = {
                "item": item,
                "State": State,
                "can_advance": can_transition(item, _next, request.user) if item.estado in FORWARD else False,
                "can_revert": can_revert(item, request.user),
                "next_state": FORWARD.get(item.estado),
                "prev_state": BACKWARD.get(item.estado),
                "users": User.objects.filter(is_active=True).order_by("name") if request.user.is_staff else None,
            }
            return render(request, "items/partials/item_state_card.html", ctx)
        return redirect("items:detail", pk=pk)


class ItemDeactivateView(AdminRequiredMixin, View):
    """POST: toggle activo flag."""

    def post(self, request, pk):
        item = get_object_or_404(Item.all_objects, pk=pk)
        item.activo = not item.activo
        item.save(update_fields=["activo"])
        action = AuditLog.ACTION_ACTIVATED if item.activo else AuditLog.ACTION_DEACTIVATED
        record(action, item, request.user)
        state = "activada" if item.activo else "desactivada"
        messages.success(request, f"Pieza {state}.")
        return redirect("items:detail", pk=pk)


class PhotoUploadView(AdminRequiredMixin, View):
    """POST: upload a photo for an item."""

    def post(self, request, pk):
        item = get_object_or_404(Item.all_objects, pk=pk)
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.item = item
            photo.uploaded_by = request.user
            photo.save()
            record(AuditLog.ACTION_PHOTO_ADDED, item, request.user)
            messages.success(request, "Foto añadida.")
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())
        return redirect("items:detail", pk=pk)


class PhotoDeleteView(AdminRequiredMixin, View):
    """POST: delete a specific photo."""

    def post(self, request, pk, photo_pk):
        item = get_object_or_404(Item.all_objects, pk=pk)
        photo = get_object_or_404(ItemPhoto, pk=photo_pk, item=item)
        photo.delete()
        record(AuditLog.ACTION_PHOTO_DELETED, item, request.user)
        messages.success(request, "Foto eliminada.")
        return redirect("items:detail", pk=pk)
