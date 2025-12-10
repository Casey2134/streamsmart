"""
Django settings for streamsmart project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

# Security
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-dr03dup4rrf9uy^-3lq@gz3t028m)=(7_y-5nv6qk$(rfuusrv"
)

# Hosts
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,backend,127.0.0.1").split(",")
# Always allow Railway and custom domains
ALLOWED_HOSTS += [
    "healthcheck.railway.app",
    ".railway.app",
    "streamsmart.ai",
    "www.streamsmart.ai",
]
CSRF_TRUSTED_ORIGINS = [
    "https://streamsmart.ai",
    "https://www.streamsmart.ai",
    "https://*.railway.app",
]

# Application definition
INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "summarizer",
    "watchparty",
    "rest_framework",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Serve static files in production
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "streamsmart.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

ASGI_APPLICATION = "streamsmart.asgi.application"
WSGI_APPLICATION = "streamsmart.wsgi.application"


# Database - Use DATABASE_URL if provided (Railway), otherwise SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Use WhiteNoise for static files in production
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

# Django Channels / Redis
REDIS_URL = os.environ.get("REDIS_URL")

if REDIS_URL:
    # Production: Parse Redis URL
    from urllib.parse import urlparse
    redis_parsed = urlparse(REDIS_URL)
    redis_host = redis_parsed.hostname or "localhost"
    redis_port = redis_parsed.port or 6379
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        },
    }
else:
    # Local dev with Docker
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [("redis", 6379)],
            },
        },
    }

# Tailscale Transcription Service URL
# Set this to your local machine's Tailscale IP, e.g., "http://100.x.x.x:8080"
TRANSCRIPTION_SERVICE_URL = os.environ.get("TRANSCRIPTION_SERVICE_URL", "http://localhost:8080")
