from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.views.generic import TemplateView

from apps.items.models import Item
from apps.items.state import State

User = get_user_model()


def get_stats_context():
    state_counts = {s.value: 0 for s in State}
    for row in Item.objects.values("estado").annotate(n=Count("id")):
        state_counts[row["estado"]] = row["n"]
    total = sum(state_counts.values())
    documentado = state_counts[State.DOCUMENTADO]
    progress = round(documentado / total * 100) if total else 0
    return {"state_counts": state_counts, "total_items": total, "progress": progress, "State": State}


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_stats_context())

        users_items = (
            User.objects.filter(is_active=True)
            .annotate(
                total=Count("assigned_items", filter=Q(assigned_items__activo=True)),
                documentados=Count(
                    "assigned_items",
                    filter=Q(assigned_items__activo=True, assigned_items__estado=State.DOCUMENTADO),
                ),
            )
            .filter(total__gt=0)
            .order_by("-total")
        )
        ctx["users_items"] = users_items
        return ctx


class AboutView(TemplateView):
    template_name = "dashboard/about.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_stats_context())
        return ctx
