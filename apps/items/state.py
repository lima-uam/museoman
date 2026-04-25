from django.conf import settings
from django.db import models


class State(models.TextChoices):
    LIBRE = "libre", "Libre"
    ASIGNADO = "asignado", "Asignado"
    EN_REVISION = "en_revision", "En revisión"
    DOCUMENTADO = "documentado", "Documentado"


# Forward transitions
FORWARD: dict[str, str] = {
    State.LIBRE: State.ASIGNADO,
    State.ASIGNADO: State.EN_REVISION,
    State.EN_REVISION: State.DOCUMENTADO,
}

# Reverse transitions (derived)
BACKWARD: dict[str, str] = {v: k for k, v in FORWARD.items()}


class TransitionError(Exception):
    pass


def can_advance(item, user) -> bool:
    """Check whether user can advance item to the next state."""
    current = item.estado
    if current not in FORWARD:
        return False
    target = FORWARD[current]
    return _check_permission(current, target, item, user)


def can_revert(item, user) -> bool:
    """Check whether user can revert item to the previous state."""
    current = item.estado
    if current not in BACKWARD:
        return False
    if current == State.DOCUMENTADO:
        return user.is_staff
    return item.assigned_user == user or user.is_staff


def can_transition(item, target: str, user) -> bool:
    """Check whether user can transition item to target state."""
    current = item.estado
    if FORWARD.get(current) == target:
        return _check_permission(current, target, item, user)
    if BACKWARD.get(current) == target:
        if current == State.DOCUMENTADO:
            return user.is_staff
        return item.assigned_user == user or user.is_staff
    return False


def _check_permission(current: str, target: str, item, user) -> bool:
    if current == State.LIBRE and target == State.ASIGNADO:
        # Any authenticated user can assign themselves; admin can assign anyone
        return True
    if current == State.ASIGNADO and target == State.EN_REVISION:
        return item.assigned_user == user or user.is_staff
    if current == State.EN_REVISION and target == State.DOCUMENTADO:
        return user.is_staff
    return False


def get_active_assignment_count(user) -> int:
    """Count active items assigned to user that are not documentado."""
    from apps.items.models import Item

    return Item.objects.filter(assigned_user=user, activo=True).exclude(estado=State.DOCUMENTADO).count()


def is_at_assignment_limit(user) -> bool:
    """Return True if user has reached the assignment limit. Staff always return False."""
    if user.is_staff:
        return False
    limit = getattr(settings, "ITEM_ASSIGNMENT_LIMIT", 5)
    if limit == 0:
        return False
    return get_active_assignment_count(user) >= limit


def apply_transition(item, target: str, actor, assign_to=None, url: str = ""):
    """
    Apply a state transition atomically.

    For libre → asignado, assign_to specifies the user to assign.
    If assign_to is None and actor is not admin, assigns to actor.

    For asignado → en_revision, url may be provided to set item.url
    as part of the transition. If url is not provided and item.url is
    blank, raises TransitionError.
    """
    from django.db import transaction

    from apps.audit.models import AuditLog
    from apps.audit.services import record

    with transaction.atomic():
        # Re-fetch with lock to prevent races
        locked = item.__class__.all_objects.select_for_update().get(pk=item.pk)

        if not can_transition(locked, target, actor):
            raise TransitionError(f"Transición {locked.estado!r} → {target!r} no permitida para este usuario")

        if target == State.ASIGNADO:
            effective_assign_to = assign_to if assign_to is not None else actor
            if is_at_assignment_limit(effective_assign_to):
                limit = getattr(settings, "ITEM_ASSIGNMENT_LIMIT", 5)
                raise TransitionError(
                    f"{effective_assign_to.name} ya tiene {limit} piezas activas sin documentar "
                    f"(límite máximo). Documenta alguna antes de asumir más."
                )

        old_state = locked.estado

        if target == State.EN_REVISION:
            effective_url = url or locked.url
            if not effective_url:
                raise TransitionError("Debes establecer la URL antes de pasar a revisión.")
            locked.url = effective_url

        locked.estado = target

        if target == State.ASIGNADO:
            if assign_to is not None:
                locked.assigned_user = assign_to
            elif locked.assigned_user is None:
                locked.assigned_user = actor

        if target == State.LIBRE:
            locked.assigned_user = None

        update_fields = ["estado", "assigned_user", "url", "updated_at"]
        locked.save(update_fields=update_fields)

        record(
            AuditLog.ACTION_STATE_CHANGE,
            locked,
            actor,
            from_state=old_state,
            to_state=target,
        )

    # Refresh original object so caller sees new state
    item.refresh_from_db()
