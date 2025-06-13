import os
from pathlib import Path

from config import str_to_bool, str_to_list

# from django.templatetags.static import static
# from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = str_to_bool(os.environ["DEBUG"])

ALLOWED_HOSTS = str_to_list(os.environ["ALLOWED_HOSTS"])

# Other constants
FRONTEND_URL = os.environ.get("FRONTEND_URL")

# Application definition

INSTALLED_APPS = [
    "unfold",  # Django admin theme
    # "unfold.contrib.filters",  # optional, if special filters are needed
    # "unfold.contrib.forms",  # optional, if special form elements are needed
    # "unfold.contrib.inlines",  # optional, if special inlines are needed
    # "unfold.contrib.import_export"  # optional, for django-import-export
    # "unfold.contrib.guardian",  # optional, if django-guardian package is used
    # "unfold.contrib.simple_history",  # optional, if django-simple-history is used
    # Django modules
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # External modules
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "channels",
    "corsheaders",
    # Local modules
    "modules.authentication",
    "modules.core",
    "modules.users",
    "modules.prices",
]

if DEBUG:
    INSTALLED_APPS.insert(0, "daphne")

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "config.asgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": os.environ["POSTGRES_PORT"],
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.MinimumLengthValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.CommonPasswordValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.NumericPasswordValidator"),
    },
]

CORS_ALLOWED_ORIGINS = [
    FRONTEND_URL,
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Warsaw"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST framework settings

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "modules.authentication.clerk_auth.ClerkAuthentication",
        # "rest_framework_simplejwt.authentication.JWTAuthentication",
        # 'rest_framework.authentication.BearerAuthentication',
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SPECTACULAR_SETTINGS = {
    "TITLE": "Stocks API",
    "DESCRIPTION": "",
    "VERSION": "0.0.1",
    "SERVE_INCLUDE_SCHEMA": False,
    "SECURITY": [
        {"BearerAuth": []},
    ],
}

AUTH_USER_MODEL = "users.User"

# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
# }

UNFOLD = {
    "SITE_TITLE": "Stocks",
    "SITE_HEADER": "Stocks Admin Panel",
    "SITE_DROPDOWN": [
        {
            "icon": "folder",
            "title": "Github",
            "link": "https://github.com/wall-street-stocks/stocks-backend",
        },
        {
            "icon": "dashboard",
            "title": "Frontend",
            "link": "https://example.com",
        },
    ],
}

# Clerk settings
CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY")
CLERK_ISSUER = os.environ.get("CLERK_ISSUER")
CLERK_JWKS_URL = os.environ.get("CLERK_JWKS_URL")
