"""Development settings."""
from .base import *  # noqa: F401,F403

INTERNAL_IPS = ["127.0.0.1"]

# Plain (non-manifest) static storage in dev so missing assets don't crash collectstatic.
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}
