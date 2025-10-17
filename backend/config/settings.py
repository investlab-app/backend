import os
from pathlib import Path

from celery.schedules import crontab

from config.utils import str_to_bool, str_to_list

# from django.templatetags.static import static
# from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = str_to_bool(os.environ["DEBUG"])

ALLOWED_HOSTS = str_to_list(os.environ["ALLOWED_HOSTS"])

CORS_ALLOWED_ORIGINS = str_to_list(os.environ["CORS_ALLOWED_ORIGINS"])

CSRF_TRUSTED_ORIGINS = str_to_list(os.environ.get("CSRF_TRUSTED_ORIGINS", ""))

# Application definition

INSTALLED_APPS = [
    "unfold",  # Django admin theme
    # "unfold.contrib.filters",  # optional, for special filters
    # "unfold.contrib.forms",  # optional, for special form elements
    # "unfold.contrib.inlines",  # optional, for special inlines
    # "unfold.contrib.import_export"  # optional, for django-import-export
    # "unfold.contrib.guardian",  # optional, for django-guardian
    # "unfold.contrib.simple_history",  # optional, for django-simple-history
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
    # Local modules
    "modules.authentication",
    "modules.core",
    "modules.instruments",
    "modules.investors",
    "modules.markets",
    "modules.news",
    "modules.notifications",
    "modules.orders",
    "modules.prices",
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

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

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

# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
# }

UNFOLD = {
    "SITE_TITLE": "Stocks",
    "SITE_HEADER": "Stocks Admin Panel",
    # "SITE_SUBHEADER": "Appears under SITE_HEADER",
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
    # "SITE_URL": "/",
    # # "SITE_ICON": (
    #   lambda request: static("icon.svg"),  # both modes, optimise for 32px height
    #  )
    # "SITE_ICON": {
    #     "light": lambda request: static("icon-light.svg"),  # light mode
    #     "dark": lambda request: static("icon-dark.svg"),  # dark mode
    # },
    # # "SITE_LOGO": (
    #   lambda request: static("logo.svg"),  # both modes, optimise for 32px height
    # )
    # "SITE_LOGO": {
    #     "light": lambda request: static("logo-light.svg"),  # light mode
    #     "dark": lambda request: static("logo-dark.svg"),  # dark mode
    # },
    # "SITE_SYMBOL": "speed",  # symbol from icon set
    # "SITE_FAVICONS": [
    #     {
    #         "rel": "icon",
    #         "sizes": "32x32",
    #         "type": "image/svg+xml",
    #         "href": lambda request: static("favicon.svg"),
    #     },
    # ],
    # "SHOW_HISTORY": True,  # show/hide "History" button, default: True
    # "SHOW_VIEW_ON_SITE": True,  # show/hide "View on site" button, default: True
    # "SHOW_BACK_BUTTON": (
    #    False,  # show/hide "Back" button on changeform in header, default: False
    # )
    # "ENVIRONMENT": "sample_app.environment_callback",  # environment name in header
    # # environment name prefix in title tag
    # "ENVIRONMENT_TITLE_PREFIX": "sample_app.environment_title_prefix_callback",
    # "DASHBOARD_CALLBACK": "sample_app.dashboard_callback",
    # "LOGIN": {
    #     "image": lambda request: static("sample/login-bg.jpg"),
    #     "redirect_after": lambda request: reverse_lazy("admin:APP_MODEL_changelist"),
    # },
    # "COLORS": {
    #     "base": {
    #         "50": "249, 250, 251",
    #         "100": "243, 244, 246",
    #         "200": "229, 231, 235",
    #         "300": "209, 213, 219",
    #         "400": "156, 163, 175",
    #         "500": "107, 114, 128",
    #         "600": "75, 85, 99",
    #         "700": "55, 65, 81",
    #         "800": "31, 41, 55",
    #         "900": "17, 24, 39",
    #         "950": "3, 7, 18",
    #     },
    #     "primary": {
    #         "50": "250, 245, 255",
    #         "100": "243, 232, 255",
    #         "200": "233, 213, 255",
    #         "300": "216, 180, 254",
    #         "400": "192, 132, 252",
    #         "500": "168, 85, 247",
    #         "600": "147, 51, 234",
    #         "700": "126, 34, 206",
    #         "800": "107, 33, 168",
    #         "900": "88, 28, 135",
    #         "950": "59, 7, 100",
    #     },
    #     "font": {
    #         "subtle-light": "var(--color-base-500)",  # text-base-500
    #         "subtle-dark": "var(--color-base-400)",  # text-base-400
    #         "default-light": "var(--color-base-600)",  # text-base-600
    #         "default-dark": "var(--color-base-300)",  # text-base-300
    #         "important-light": "var(--color-base-900)",  # text-base-900
    #         "important-dark": "var(--color-base-100)",  # text-base-100
    #     },
    # },
    # "EXTENSIONS": {
    #     "modeltranslation": {
    #         "flags": {
    #             "en": "🇬🇧",
    #             "fr": "🇫🇷",
    #             "nl": "🇧🇪",
    #         },
    #     },
    # },
    "SIDEBAR": {
        "show_search": True,  # Search in applications and models names
        "show_all_applications": False,  # Dropdown with all applications and models
        # "navigation": [
        #     {
        #         "title": _("Navigation"),
        #         "separator": True,  # Top border
        #         "collapsible": True,  # Collapsible group of links
        #         "items": [
        #             {
        #                 "title": _("Dashboard"),
        #                 "icon": "dashboard",  # Supported icon set: https://fonts.google.com/icons
        #                 "link": reverse_lazy("admin:index"),
        #                 "badge": "sample_app.badge_callback",
        #                 "permission": lambda request: request.user.is_superuser,
        #             },
        #             {
        #                 "title": _("Users"),
        #                 "icon": "people",
        #                 "link": reverse_lazy("admin:auth_user_changelist"),
        #             },
        #         ],
        #     },
        # ],
    },
    # "TABS": [
    #     {
    #         "models": [
    #             "app_label.model_name_in_lowercase",
    #         ],
    #         "items": [
    #             {
    #                 "title": _("Your custom title"),
    #                 "link": reverse_lazy("admin:app_label_model_name_changelist"),
    #                 "permission": "sample_app.permission_callback",
    #             },
    #         ],
    #     },
    # ],
}

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
            "schedule": crontab(day_of_week=3, hour=0),  # Every Wednesday at midnight
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

# Datetime formats
ACCEPTABLE_DATETIME_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d_%H:%M:%S"]

# Email
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
EMAIL_BACKEND = os.environ["EMAIL_BACKEND"]
EMAIL_FILE_PATH = os.environ.get("EMAIL_FILE_PATH")

# Web Push
VAPID_PRIVATE_KEY = os.environ["VAPID_PRIVATE_KEY"]
VAPID_PUBLIC_KEY = os.environ["VAPID_PUBLIC_KEY"]
VAPID_CLAIMS = {
    "sub": f"mailto:{ADMIN_EMAIL}",
}