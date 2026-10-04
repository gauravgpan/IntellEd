"""
Django settings for the ThinkTurf MVP backend.

Stack: Linux / Apache (mod_wsgi, see backend/apache/) / MySQL / Python (Django + DRF).
This is a thin skeleton — see README.md at the repo root for the module map and
the list of open design decisions, several of which are encoded below as plain
settings flags so they're easy to find and flip once answered.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "corsheaders",
    "apps.users",
    "apps.schools",
    "apps.students",
    "apps.curriculum",
    "apps.scheduling",
    "apps.submissions",
    "apps.assessments",
    "apps.reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database ---------------------------------------------------------------
# MySQL by default (the "M" in LAMP). Set USE_SQLITE=1 for a zero-setup local
# run (e.g. a laptop without MySQL installed) — schema and migrations are the
# same either way, this only swaps the engine.
if os.environ.get("USE_SQLITE") == "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "thinkturf"),
            "USER": os.environ.get("DB_USER", "thinkturf"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "thinkturf"),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ---------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

# --- CORS (for the Vite dev server) ------------------------------------------
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
).split(",")

# --- OTP -----------------------------------------------------------------
# No SMS/email provider wired up yet: OTP codes are logged to the console
# (see apps/users/services.py). Swap send_otp() for a real provider when
# one is chosen.
OTP_CODE_LENGTH = 6
OTP_TTL_SECONDS = 10 * 60

# --- Feature flags for open design decisions ---------------------------------
# Each references the numbered "Open decisions" section of the technical
# design doc. Flip these once the team decides; nothing else needs to change.
#
# 1. Approval authority — doc assumed Admin or Founder can both approve a
#    tutor to Active. Enforced in apps/users/permissions.py (IsFounderOrAdmin).
#
# 7. Lesson sequence owner — doc assumed only Admin/Founder set a class's
#    lesson plan, tutors cannot reorder it.
CLASS_PLAN_EDITABLE_BY_TUTOR = False
#
# 8. What counts as "submitted" — doc assumed only Confirmed (and now Waived)
#    submissions count toward a handout being Done; NeedsReview does not.
SUBMISSION_STATUSES_COUNTED_AS_DONE = ["confirmed", "waived"]
#
# 10. Waive authority — doc assumed any tutor assigned to the class can waive
#    a student on a handout (not just a lead tutor).
ANY_ASSIGNED_TUTOR_CAN_WAIVE = True
