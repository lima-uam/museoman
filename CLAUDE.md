# CLAUDE.md — Museoman

Documentation management system for the EPS UAM museum, maintained by the LIMA student association (Laboratorio de Informática y Matemáticas, Universidad Autónoma de Madrid).

---

## Project overview

Django 5.2 app to manage museum item assignment and documentation. Items move through a state workflow (libre → asignado → en_revision → documentado). All UI is in Spanish. Frontend uses HTMX for partial page updates; no JS framework.

**Stack:** Python 3.12, Django 5.2, PostgreSQL (sqlite for local dev), HTMX, WhiteNoise, Gunicorn, uv (package manager).

---

## App structure

```
apps/
  accounts/   — custom User model (USERNAME_FIELD = email), user management views
  catalog/    — Tipo (item classification) and Vitrina (display case) models
  items/      — Item, ItemPhoto, state machine, views, forms
  audit/      — AuditLog model, Discord webhook notifications
  dashboard/  — stats overview, public about page
config/       — settings, urls, wsgi
templates/    — all HTML (no app-level templates dirs)
scripts/      — standalone CLI tools
static/       — CSS, JS
```

---

## Key models

### User (`apps/accounts`)
- `email` (USERNAME_FIELD), `name`, `is_staff`, `is_active`
- No public registration; staff-only creation

### Item (`apps/items`)
- `nombre`, `url` (URLField, required before asignado→en_revision), `estado`, `assigned_user` (FK nullable), `observaciones`, `tipos` (M2M → Tipo), `vitrina` (FK nullable), `activo`, `created_by`, `created_at`, `updated_at`
- Two managers: `Item.objects` (active only), `Item.all_objects` (all)
- `ItemPhoto`: FK to Item, `image` (ImageField → `items/<item_id>/<filename>`), `uploaded_by`

### Vitrina (`apps/catalog`)
- `nombre`, `url` (URLField optional). Uses Django pk as identifier (no separate numero field).

### AuditLog (`apps/audit`)
- `item` (FK nullable), `vitrina` (FK nullable), `actor`, `action`, `from_state`, `to_state`, `payload` (JSON)
- Actions: `state_change`, `assigned`, `deactivated`, `activated`, `photo_added`, `photo_deleted`, `created`, `updated`, `vitrina_created`, `vitrina_updated`, `vitrina_deleted`
- Discord webhook fired in background daemon thread (`threading.Thread(..., daemon=True)`) to avoid blocking response

---

## State machine (`apps/items/state.py`)

```
libre → asignado → en_revision → documentado
```

- `libre → asignado`: any authenticated user (self-assign) or staff (assign to anyone)
- `asignado → en_revision`: assigned user or staff. **Requires `item.url` to be set.**
- `en_revision → documentado`: staff only
- Revert `asignado → libre`: assigned user or staff
- Revert `en_revision → asignado`: staff only
- Revert `documentado → en_revision`: staff only
- `apply_transition()` uses `select_for_update()` to prevent race conditions

---

## HTMX patterns

State card (`templates/items/partials/item_state_card.html`) is swapped via `hx-target="#state-card" hx-swap="outerHTML"`. After a state change, it also pushes OOB updates for `#item-header` and `#item-info` to reflect new state without full reload:

```html
{% if request.htmx %}
{% include "items/partials/item_header.html" with oob=True %}
{% include "items/partials/item_info.html" with oob=True %}
{% endif %}
```

The `oob=True` flag adds `hx-swap-oob="true"` to the partial's root element. Guard with `{% if request.htmx %}` to prevent duplication on full-page loads.

---

## Permissions

| Action | Staff | Regular user |
|---|---|---|
| Create / edit items | ✓ | own assigned item when `estado=asignado` |
| Create / manage tipos and vitrinas | ✓ | — |
| Create users, modify any user | ✓ | own password only |
| Add / delete photos | ✓ | — |
| Assign item to self | ✓ | ✓ |
| Assign item to others | ✓ | — |
| Advance to `en_revision` | ✓ | ✓ (if assigned) |
| Advance to `documentado` | ✓ | — |
| Revert `asignado → libre` | ✓ | ✓ (if assigned) |
| Revert `en_revision` or `documentado` | ✓ | — |
| Deactivate items | ✓ | — |

---

## Tom Select (multi-select tipo picker)

Used on item form and item list filter. The Bootstrap5 theme sets `.ts-wrapper.multi .ts-control { background-color: transparent }` which overrides naive `.ts-control` rules. Override with higher specificity: `.ts-wrapper .ts-control { background-color: var(--clr-surface); }`. Also set `background-color` on `.ts-dropdown` and `z-index: 100` to prevent elements below bleeding through.

---

## Dashboard (`apps/dashboard`)

Shows: item count per state, items per user (all active users, even with zero items), overall progress bar. Public about page with project stats and Discord widget (no login required).

## Filters (item list)

- Text search, estado, assigned_user, tipo (multi-select, **AND logic** — chained `.filter(tipos=t)` per tag, not `filter(tipos__in=...)`), vitrina, activo
- Pagination (20/page), sortable
- Note: spec listed an "unread comments" filter — not implemented (no comments feature)

---

## Audit / Discord

`apps/audit/services.py`:
- `record(action, item, actor, ...)` — creates AuditLog + fires webhook
- `record_vitrina(action, vitrina, actor, ...)` — for vitrina operations
- Webhook POSTs to `settings.DISCORD_WEBHOOK_URL` in a daemon thread
- In tests: mock `threading.Thread` with `_SyncThread` (runs target immediately) to avoid race conditions

---

## Docker

- `Dockerfile`: single stage, `python:3.12-slim`, installs `uv`, runs `uv sync --no-dev`, entrypoint runs migrations + collectstatic then gunicorn
- `docker-compose.yml`: `db` (postgres:16) + `web` with hardcoded env vars, `museoman_net` network, `media_data` volume, healthcheck on db
- `docker-compose.example.yml`: template with placeholder values
- `.dockerignore`: excludes `.env`, `.git`, caches, venv, media, staticfiles

Env vars in `docker-compose.yml` are set directly (not via env_file). `docker-compose.yml` is gitignored; `docker-compose.example.yml` is committed.

---

## Subpath deployment

App supports deployment at a URL subpath via `URL_PATH` env var (e.g. `URL_PATH=/museoman`). This sets `FORCE_SCRIPT_NAME` and prefixes `LOGIN_URL`, `STATIC_URL`, `MEDIA_URL`, etc. `CSRF_TRUSTED_ORIGINS` is also configurable via env.

---

## scripts/

`scripts/local_import.py` — standalone executable for bulk item import:
- Takes a directory; each subdirectory → one Item, image files → photos
- Authenticates via session login against existing Django views (no separate API)
- CSRF handled via `csrftoken` cookie (`requests.Session`)
- Usage: `uv run scripts/local_import.py PATH --email admin@example.com [--password PASS] [--url http://localhost:8000]`
- Requires staff account. Image formats: `.jpg .jpeg .png .gif .webp` (max 5 MB, enforced server-side)

---

## Development

```bash
uv sync --all-groups       # install deps
make dev                   # runserver
make test                  # pytest with coverage
make test-fast             # pytest --no-cov -q
make lint                  # ruff check
make fmt                   # ruff format + fix
make migrate               # makemigrations + migrate
make seed                  # load demo data
make createadmin           # create admin user interactively
```

Test settings: `config/test_settings.py`. Fixtures in `conftest.py` (root): `admin_user`, `regular_user`, `tipo`, `vitrina`, `item`.

---

## Non-functional requirements

Low concurrency expected. Prioritise data consistency (hence `select_for_update()` on state transitions) and simplicity over performance. Lightweight — no heavy JS, no caching layer needed.

---

## Known pre-existing lint issues (not to fix)

Two `I001` (unsorted imports) in `apps/audit/tests/test_services.py` and `apps/items/forms.py`. These predate the current session and are not blocking.

---

## Spec deviations / decisions made

| Spec | Actual |
|---|---|
| `identificador` field on Item | Removed — Django pk used instead |
| `numero` field on Vitrina | Removed — Django pk used instead |
| Single `tipo` FK on Item | Replaced with `tipos` M2M |
| Any user can revert states | Revert from `en_revision` and `documentado` is staff-only |
| URL field not in spec | Added — required to advance to `en_revision` |
| Audit log only for state changes | Extended to item create/update and all vitrina operations |
| "Unread comments" filter | Not implemented — no comments feature |
