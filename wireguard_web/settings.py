"""
Django settings for wireguard_web project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
from pathlib import Path
from urllib.parse import urlparse


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_URL = os.environ.get("WIREGUARD_WEB_BASE_URL", "http://localhost:8000")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-n#e@966oe0^ij3*m$g#6(8aqk#7i!3hy&1q34w10^^#y=6-hbj"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("WIREGUARD_WEB_DEBUG", "0") == "1"

parsed_url = urlparse(BASE_URL)

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    f"http://{parsed_url.hostname}",
    f"https://{parsed_url.hostname}",
    "http://localhost",
    "http://127.0.0.1",
]

# Application definition

INSTALLED_APPS = [
    "wireguard",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "wireguard.middleware.VersionMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "wireguard_web.urls"

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

WSGI_APPLICATION = "wireguard_web.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
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

# User model
AUTH_USER_MODEL = "wireguard.User"

LOGIN_URL = "login"

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# E-Mail config

EMAIL_BACKEND = os.environ.get("WIREGUARD_WEB_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("WIREGUARD_WEB_EMAIL_HOST", "localhost")
EMAIL_HOST_PASSWORD = os.environ.get("WIREGUARD_WEB_EMAIL_PASSWORD", "")
EMAIL_HOST_USER = os.environ.get("WIREGUARD_WEB_EMAIL_USER", "")
EMAIL_PORT = int(os.environ.get("WIREGUARD_WEB_EMAIL_PORT", "25"))
EMAIL_USE_TLS = os.environ.get("WIREGUARD_WEB_EMAIL_TLS", "0") == "1"
DEFAULT_FROM_EMAIL = os.environ.get("WIREGUARD_WEB_EMAIL_FROM", "root@localhost")

# Local config for wireguard

CONFIG_DIRECTORY = os.environ.get("WIREGUARD_STAGING_CONFIG_DIRECTORY", "/tmp/wireguard-staging")
