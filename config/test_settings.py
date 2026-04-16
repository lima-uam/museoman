from .settings import *  # noqa: F401, F403

# Always use in-memory SQLite for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
