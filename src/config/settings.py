import os
from pathlib import Path

from celery.schedules import crontab

from config.utils import str_to_bool, str_to_list

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = str_to_bool(os.environ["DEBUG"])

ALLOWED_HOSTS = str_to_list(os.environ["ALLOWED_HOSTS"])

CORS_ALLOWED_ORIGINS = str_to_list(os.environ["CORS_ALLOWED_ORIGINS"])

CSRF_TRUSTED_ORIGINS = str_to_list(os.environ.get("CSRF_TRUSTED_ORIGINS", ""))

# Application definition

INSTALLED_APPS = [
    "unfold",  # Django admin theme, should be first
    # Django modules
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_results",
    "django_celery_beat",
    "django_filters",
    # External modules
    "django_extensions",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "corsheaders",
    "storages",
    # Local modules
    "modules.authentication",
    "modules.chats",
    "modules.core",
    "modules.graph_lang",
    "modules.instruments",
    "modules.investors",
    "modules.markets",
    "modules.news",
    "modules.notifications",
    "modules.orders",
    "modules.prices",
    "modules.statistics",
    "modules.transactions",
]

if DEBUG:
    INSTALLED_APPS.insert(0, "daphne")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Warsaw"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_ROOT = BASE_DIR / "staticfiles"

if str_to_bool(os.environ.get("USE_MINIO", "false")):
    AWS_S3_ENDPOINT_URL = (
        f"http://{os.environ['MINIO_ENDPOINT']}:{os.environ['MINIO_PORT']}"
    )
    AWS_ACCESS_KEY_ID = os.environ["MINIO_ACCESS_KEY"]
    AWS_SECRET_ACCESS_KEY = os.environ["MINIO_SECRET_KEY"]
    AWS_S3_REGION_NAME = os.environ.get("MINIO_REGION_NAME", "us-east-1")
    AWS_S3_SIGNATURE_VERSION = "s3v4"

    STORAGES = {
        "default": {
            "BACKEND": "config.storages.S3MediaStorage",
        },
        "staticfiles": {
            "BACKEND": "config.storages.S3StaticStorage",
        },
    }

    minio_use_ssl = str_to_bool(os.environ.get("MINIO_USE_SSL", "false"))
    protocol = "https" if minio_use_ssl else "http"
    minio_public_domain = os.environ.get(
        "MINIO_PUBLIC_DOMAIN",
        f"{os.environ['MINIO_ENDPOINT']}:{os.environ['MINIO_PORT']}",
    )
    STATIC_URL = (
        f"{protocol}://{minio_public_domain}/{os.environ['MINIO_STATIC_BUCKET_NAME']}/"
    )
    MEDIA_URL = (
        f"{protocol}://{minio_public_domain}/{os.environ['MINIO_MEDIA_BUCKET_NAME']}/"
    )
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

    STATIC_URL = "static/"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

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
    ),
    "DEFAULT_PAGINATION_CLASS": "modules.core.pagination.DynamicPageSizePagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SPECTACULAR_SETTINGS = {
    "TITLE": "Stocks API",
    "DESCRIPTION": "API for stock market data and trading operations",
    "VERSION": "0.0.1",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/",
    "SECURITY": [
        {"ClerkAuth": []},
    ],
    "COMPONENT_SECURITY_SCHEMES": {
        "ClerkAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Clerk JWT authentication. Use format: 'Bearer <token>'",
        }
    },
    "PREPROCESSING_HOOKS": [
        "drf_spectacular.hooks.preprocess_exclude_path_format",
    ],
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayOperationId": False,
    },
}

UNFOLD = {
    "SITE_TITLE": "Stocks",
    "SITE_HEADER": "Stocks Admin Panel",
    "SITE_DROPDOWN": [
        {
            "icon": "folder",
            "title": "Github",
            "link": "https://github.com/investlab-app/backend/",
        },
    ],
    # "SITE_ICON": {
    #     "light": lambda request: static("icon-light.svg"),  # light mode
    #     "dark": lambda request: static("icon-dark.svg"),  # dark mode
    # },
    # "SITE_LOGO": {
    #     "light": lambda request: static("logo-light.svg"),  # light mode
    #     "dark": lambda request: static("logo-dark.svg"),  # dark mode
    # },
    # "SITE_FAVICONS": [
    #     {
    #         "rel": "icon",
    #         "sizes": "32x32",
    #         "type": "image/svg+xml",
    #         "href": lambda request: static("favicon.svg"),
    #     },
    # ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SIDEBAR": {
        "show_search": True,  # Search in applications and models names
        "show_all_applications": False,  # Dropdown with all applications and models
    },
}

# Redis
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}


# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}


# Celery settings
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", f"{REDIS_URL}/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXTENDED = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

if not DEBUG:
    CELERY_BEAT_SCHEDULE = {
        "modules.instruments.tasks.sync_instruments_base_info": {
            "task": "modules.instruments.tasks.sync_instruments_base_info",
            "schedule": crontab(hour=4, minute=0),  # Every day at 4:00 AM
        },
        "modules.instruments.tasks.sync_instruments_detail_info": {
            "task": "modules.instruments.tasks.sync_instruments_detail_info",
            "schedule": crontab(hour=5, minute=0),  # Every day at 5:00 AM
        },
        "modules.instruments.tasks.sync_instruments_images": {
            "task": "modules.instruments.tasks.sync_instruments_images",
            "schedule": crontab(
                day_of_week=3,
                hour=0,
                minute=0,
            ),  # Every Wednesday at midnight
        },
        "modules.investors.tasks.save_accounts_value_snapshot": {
            "task": "modules.investors.tasks.save_accounts_value_snapshot",
            "schedule": crontab(hour=1, minute=0),  # Every Wednesday at 1:00 AM
        },
    }


# Clerk settings
CLERK_SECRET_KEY = os.environ["CLERK_SECRET_KEY"]
CLERK_ISSUER = os.environ["CLERK_ISSUER"]
CLERK_JWT_KEY = os.environ["CLERK_JWT_KEY"]

# Polygon
POLYGON_SECRET_KEY = os.environ["POLYGON_SECRET_KEY"]
POLYGON_EXCHANGE = "XNAS"
POLYGON_ASSET_TYPE = "stocks"

# Alpaca
ALPACA_PUBLIC_KEY = os.environ["ALPACA_PUBLIC_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

# Email
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
EMAIL_BACKEND = os.environ["EMAIL_BACKEND"]
EMAIL_FILE_PATH = os.environ.get("EMAIL_FILE_PATH")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = str_to_bool(os.environ.get("EMAIL_USE_TLS", "True"))
EMAIL_USE_SSL = str_to_bool(os.environ.get("EMAIL_USE_SSL", "False"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# Web Push
VAPID_PRIVATE_KEY = os.environ["VAPID_PRIVATE_KEY"]
VAPID_PUBLIC_KEY = os.environ["VAPID_PUBLIC_KEY"]
VAPID_CLAIMS = {
    "sub": f"mailto:{ADMIN_EMAIL}",
}

# OpenAI
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_API_URL = os.environ["OPENAI_API_URL"]
OPENAI_TRANSLATING_MODEL = os.environ.get(
    "OPENAI_TRANSLATING_MODEL", "llama-3.1-8b-instant"
)
OPENAI_TITLE_MODEL = os.environ.get("OPENAI_TITLE_MODEL", "llama-3.1-8b-instant")

# LLM Translation Settings
TRANSLATE_INSTRUMENT_DESCRIPTION = str_to_bool(
    os.environ.get("TRANSLATE_INSTRUMENT_DESCRIPTION", "false")
)

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
MCP_MASSIVE_URL = os.environ.get("MCP_MASSIVE_URL", "http://mcp-massive:8000/mcp")
MCP_ECHARTS_URL = os.environ.get("MCP_ECHARTS_URL", "http://mcp-echarts:8000/mcp")

# Datadog APM Configuration
DD_TRACE_ENABLED = str_to_bool(os.environ.get("DD_TRACE_ENABLED", "false"))
DD_SERVICE = os.environ.get("DD_SERVICE", "investlab-backend")
DD_ENV = os.environ.get("DD_ENV", "development")
DD_VERSION = os.environ.get("DD_VERSION", "0.1.0")
DD_AGENT_HOST = os.environ.get("DD_AGENT_HOST", "datadog-agent")
DD_TRACE_AGENT_PORT = os.environ.get("DD_TRACE_AGENT_PORT", "8126")
DD_LOGS_INJECTION = str_to_bool(os.environ.get("DD_LOGS_INJECTION", "true"))
DD_DJANGO_INSTRUMENT_MIDDLEWARE = str_to_bool(
    os.environ.get("DD_DJANGO_INSTRUMENT_MIDDLEWARE", "true")
)
DD_DJANGO_INSTRUMENT_DATABASES = str_to_bool(
    os.environ.get("DD_DJANGO_INSTRUMENT_DATABASES", "true")
)
DD_DJANGO_INSTRUMENT_CACHES = str_to_bool(
    os.environ.get("DD_DJANGO_INSTRUMENT_CACHES", "true")
)
DD_TRACE_SAMPLE_RATE = float(os.environ.get("DD_TRACE_SAMPLE_RATE", "1.0"))
DD_PROFILING_ENABLED = str_to_bool(os.environ.get("DD_PROFILING_ENABLED", "false"))
