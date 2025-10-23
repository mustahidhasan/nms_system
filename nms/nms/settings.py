from pathlib import Path
import os
from decouple import config

# -------------------------------
# BASE DIRECTORY
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------
# SECURITY
# -------------------------------
SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS").split(",")

# -------------------------------
# INSTALLED APPS
# -------------------------------
INSTALLED_APPS = [
    "corsheaders",
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "USER",
    "DASHBOARD",
]

# -------------------------------
# MIDDLEWARE
# -------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -------------------------------
# URLS AND TEMPLATES
# -------------------------------
ROOT_URLCONF = "nms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "nms.wsgi.application"

# -------------------------------
# DATABASE
# -------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # Replace with PostgreSQL/MySQL in real prod
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------------------
# PASSWORD VALIDATION
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------------
# INTERNATIONALIZATION
# -------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------------------
# STATIC FILES
# -------------------------------
STATIC_URL = '/static-django/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -------------------------------
# DEFAULT AUTO FIELD
# -------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------
# FRONTEND URLS (CORS & CSRF)
# -------------------------------
HOST_URL = config("HOST_URL")
FRONTEND_URL = HOST_URL  # No port needed in production

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default=FRONTEND_URL).split(",")
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default=FRONTEND_URL).split(",")
CORS_ALLOW_CREDENTIALS = True

# -------------------------------
# AZURE AD OAUTH2 CONFIG
# -------------------------------
AZURE_TENANT_ID = config("AZURE_TENANT_ID")
AZURE_CLIENT_ID = config("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = config("AZURE_CLIENT_SECRET")
AZURE_REDIRECT_URI = config("AZURE_REDIRECT_URI")
POST_LOGOUT_REDIRECT_URI = config("POST_LOGOUT_REDIRECT_URI", default=HOST_URL)

AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
AZURE_AUTHORIZE_ENDPOINT = f"{AZURE_AUTHORITY}/oauth2/v2.0/authorize"
AZURE_TOKEN_ENDPOINT = f"{AZURE_AUTHORITY}/oauth2/v2.0/token"
AZURE_SCOPES = config("REACT_APP_SCOPES", default="openid profile email offline_access User.Read")

# -------------------------------
# SSL SETTINGS
# -------------------------------
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
