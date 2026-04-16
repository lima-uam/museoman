# Museoman

Sistema de gestión de documentación de piezas del museo de la EPS UAM, mantenido por LIMA (Laboratorio de Informática y Matemáticas).

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker + Docker Compose (para la base de datos PostgreSQL en desarrollo)

## Instalación rápida

```bash
# 1. Instalar dependencias
uv sync --all-groups

# 2. Copiar y editar configuración
cp .env.example .env
# Editar .env con tus valores

# 3. Arrancar PostgreSQL (desarrollo)
docker compose up -d

# 4. Crear tablas
uv run python manage.py migrate

# 5. Crear administrador
uv run python manage.py createadmin

# 6. (Opcional) Cargar datos de demostración
uv run python manage.py seed_demo

# 7. Arrancar servidor
uv run python manage.py runserver
```

Accede en: http://127.0.0.1:8000

## Variables de entorno

Copia `.env.example` a `.env` y configura:

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `SECRET_KEY` | Clave secreta Django — **cambiar en producción** | valor de desarrollo |
| `DEBUG` | Modo debug (`True`/`False`) | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por comas | `localhost,127.0.0.1` |
| `DATABASE_URL` | URL de conexión a la BD | SQLite local |
| `DISCORD_WEBHOOK_URL` | URL del webhook de Discord para el registro de auditoría (opcional) | vacío |
| `MEDIA_ROOT` | Directorio para subidas de fotos | `media/` |
| `STATIC_ROOT` | Directorio para ficheros estáticos en producción | `staticfiles/` |

## Comandos frecuentes

```bash
make install      # instalar dependencias
make dev          # arrancar servidor de desarrollo
make test         # ejecutar tests con cobertura
make test-fast    # tests sin cobertura (más rápido)
make lint         # comprobar código con ruff
make fmt          # formatear código
make migrate      # makemigrations + migrate
make seed         # cargar datos de demostración
make db-up        # arrancar PostgreSQL vía Docker
make db-down      # parar PostgreSQL
```

## Tests

```bash
uv run pytest                         # todos los tests
uv run pytest apps/items/tests/       # sólo tests de piezas
uv run pytest -k test_state           # por nombre
uv run pytest --no-cov -q             # rápido, sin cobertura
```

Los tests usan SQLite en memoria y no necesitan PostgreSQL.

## Arquitectura

```
config/          ← configuración Django (settings, urls, wsgi)
apps/
  accounts/      ← modelo User con autenticación por email
  catalog/       ← Tipo y Vitrina
  items/         ← Item, ItemPhoto, máquina de estados
  audit/         ← AuditLog + webhook Discord
  dashboard/     ← métricas y página de información
templates/       ← plantillas HTML (base.html + por app)
static/          ← CSS, HTMX
media/           ← fotos subidas (no versionado)
```

## Flujo de estados de las piezas

```
Libre ──► Asignado ──► En revisión ──► Documentado
  ◄──────────◄────────────◄────────────
```

- `Libre → Asignado`: cualquier usuario (a sí mismo) o administrador (a cualquiera)
- `Asignado → En revisión`: usuario asignado o administrador
- `En revisión → Documentado`: sólo administrador
- Revertir cualquier transición: usuario asignado o administrador

## Producción

Para producción:
1. Establecer `DEBUG=False` y `SECRET_KEY` segura
2. Configurar `ALLOWED_HOSTS`
3. Apuntar `DATABASE_URL` a PostgreSQL de producción
4. Ejecutar `uv run python manage.py collectstatic`
5. Servir `staticfiles/` y `media/` vía nginx
6. Usar gunicorn o uvicorn como servidor WSGI/ASGI

## LIMA — EPS UAM

Laboratorio de Informática y Matemáticas  
Escuela Politécnica Superior — Universidad Autónoma de Madrid
