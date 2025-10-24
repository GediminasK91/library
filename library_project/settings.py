from pathlib import Path
import environ
import os

# --------------------------------------------------------------------------------------
# Paths & environment
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
)
# Load .env next to manage.py (do not commit this file)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# --------------------------------------------------------------------------------------
# Security
# --------------------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", default="unsafe-dev-key")
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "lalibrary-hjchh0d3ckdte9hz.northeurope-01.azurewebsites.net",
        "localhost",
        "127.0.0.1",
    ],
)

# For Azure (HTTPS) — trust your public domain for CSRF
CSRF_TRUSTED_ORIGINS = [
    "https://lalibrary-hjchh0d3ckdte9hz.northeurope-01.azurewebsites.net",
]

# Tell Django to trust Azure's proxy for https scheme
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# --------------------------------------------------------------------------------------
# Apps
# --------------------------------------------------------------------------------------
INSTALLED_APPS = [
    "jazzmin",  # optional admin skin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "books",
]

# --------------------------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Whitenoise must be directly after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --------------------------------------------------------------------------------------
# URLs / WSGI
# --------------------------------------------------------------------------------------
ROOT_URLCONF = "library_project.urls"
WSGI_APPLICATION = "library_project.wsgi.application"

# --------------------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # add template dirs here if needed
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------------------------------------------
# Database (Azure PostgreSQL recommended; SQLite for local dev)
# --------------------------------------------------------------------------------------
# Switch to Postgres by setting DB_* env vars; otherwise falls back to SQLite
if env("DB_HOST", default=""):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", default="postgres"),
            "USER": env("DB_USER", default=""),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT", default="5432"),
            "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60),
            "OPTIONS": {"sslmode": "require"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --------------------------------------------------------------------------------------
# Password validation
# --------------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------------------
# I18N / TZ
# --------------------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Vilnius"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------------------
# Static & Media (Whitenoise + Django 5 STORAGES)
# --------------------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# Add extra static dirs here if you have any project-level /static folder
STATICFILES_DIRS = []

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Use Whitenoise's compressed+hashed storage for static files
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------------------
# MSAL / Entra ID
# --------------------------------------------------------------------------------------
MSAL_CLIENT_ID = env("MSAL_CLIENT_ID", default="fb026e5b-995c-4b80-ba78-d0d02cba7366")
MSAL_CLIENT_SECRET = env("MSAL_CLIENT_SECRET", default="")   # keep in Azure App Settings
MSAL_TENANT_ID = env("MSAL_TENANT_ID", default="")          # tenant GUID or 'organizations'

MSAL_REDIRECT_URI = env(
    "MSAL_REDIRECT_URI",
    default="https://lalibrary-hjchh0d3ckdte9hz.northeurope-01.azurewebsites.net/callback/",
)

# Public site base (used for QR code URLs)
SITE_BASE_URL = env(
    "SITE_BASE_URL",
    default="https://lalibrary-hjchh0d3ckdte9hz.northeurope-01.azurewebsites.net",
)

# --------------------------------------------------------------------------------------
# Auth flow redirects
# --------------------------------------------------------------------------------------
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"
