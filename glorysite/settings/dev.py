from .base import *  # noqa

DEBUG = True
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-insecure-key-do-not-use-in-production")
ALLOWED_HOSTS = ["*"]
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")

try:
    from .local import *  # noqa
except ImportError:
    pass
