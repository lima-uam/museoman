import pytest

from apps.items.state import (
    BACKWARD,
    FORWARD,
    State,
    TransitionError,
    apply_transition,
    can_revert,
    can_transition,
)

TEST_URL = "https://example.com/pieza"


@pytest.mark.django_db
class TestStateMachine:
    # ── Forward transitions ──────────────────────────────────────────────

    def test_admin_can_advance_libre_to_asignado(self, item, admin_user):
        assert can_transition(item, State.ASIGNADO, admin_user)

    def test_regular_user_can_advance_libre_to_asignado(self, item, regular_user):
        assert can_transition(item, State.ASIGNADO, regular_user)

    def test_only_assigned_user_can_advance_to_en_revision(self, item, regular_user, admin_user):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        assert can_transition(item, State.EN_REVISION, regular_user)
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other = User.objects.create_user(email="other@test.com", name="Other", password="pass")
        assert not can_transition(item, State.EN_REVISION, other)

    def test_admin_can_always_advance_to_en_revision(self, item, regular_user, admin_user):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        assert can_transition(item, State.EN_REVISION, admin_user)

    def test_only_admin_can_mark_documentado(self, item, regular_user, admin_user):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        apply_transition(item, State.EN_REVISION, regular_user, url=TEST_URL)
        assert not can_transition(item, State.DOCUMENTADO, regular_user)
        assert can_transition(item, State.DOCUMENTADO, admin_user)

    def test_documentado_has_no_forward(self, item, regular_user, admin_user):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        apply_transition(item, State.EN_REVISION, regular_user, url=TEST_URL)
        apply_transition(item, State.DOCUMENTADO, admin_user)
        assert item.estado == State.DOCUMENTADO
        assert State.DOCUMENTADO not in FORWARD

    # ── Reverse transitions ──────────────────────────────────────────────

    def test_assigned_user_can_revert(self, item, regular_user):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        assert can_revert(item, regular_user)

    def test_admin_can_always_revert(self, item, regular_user, admin_user):
        apply_transition(item, State.ASIGNADO, admin_user, assign_to=regular_user)
        assert can_revert(item, admin_user)

    def test_unrelated_user_cannot_revert(self, item, regular_user, admin_user):
        apply_transition(item, State.ASIGNADO, admin_user, assign_to=admin_user)
        assert not can_revert(item, regular_user)

    def test_libre_has_no_backward(self, item, regular_user):
        assert State.LIBRE not in BACKWARD
        assert not can_revert(item, regular_user)

    # ── apply_transition side effects ────────────────────────────────────

    def test_transition_creates_audit_log(self, item, regular_user):
        from apps.audit.models import AuditLog

        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        log = AuditLog.objects.filter(item=item, action=AuditLog.ACTION_STATE_CHANGE).first()
        assert log is not None
        assert log.from_state == State.LIBRE
        assert log.to_state == State.ASIGNADO

    def test_invalid_transition_raises(self, item, regular_user):
        with pytest.raises(TransitionError):
            apply_transition(item, State.DOCUMENTADO, regular_user)

    def test_assign_sets_user(self, item, regular_user):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        item.refresh_from_db()
        assert item.assigned_user == regular_user

    def test_revert_to_libre_clears_assigned_user(self, item, regular_user, admin_user):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        apply_transition(item, State.LIBRE, regular_user)
        item.refresh_from_db()
        assert item.assigned_user is None
        assert item.estado == State.LIBRE

    # ── URL enforcement ──────────────────────────────────────────────────

    def test_en_revision_requires_url(self, item, regular_user):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        with pytest.raises(TransitionError, match="URL"):
            apply_transition(item, State.EN_REVISION, regular_user)

    def test_en_revision_with_existing_url_succeeds(self, item, regular_user):
        item.url = TEST_URL
        item.save(update_fields=["url"])
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        apply_transition(item, State.EN_REVISION, regular_user)
        item.refresh_from_db()
        assert item.estado == State.EN_REVISION

    def test_en_revision_url_set_inline(self, item, regular_user):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        apply_transition(item, State.EN_REVISION, regular_user, url=TEST_URL)
        item.refresh_from_db()
        assert item.estado == State.EN_REVISION
        assert item.url == TEST_URL
