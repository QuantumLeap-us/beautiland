import os
from decouple import config

# env = environ.Env(
#     # set casting, default valuewq
#     DEBUG=(bool, True)
# )

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Take environment variables from .env file
# environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'wa_sfw+(76%th-p(&u3*#-4ls$9og^cvc+5+e$)fb12-fnjgom'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG')

# Assets Management
#ASSETS_ROOT = config('ASSETS_ROOT') 
ASSETS_ROOT = config('ASSETS_ROOT', default='/static/assets')

# load production server from .env
ALLOWED_HOSTS = ["*"]
# CSRF_TRUSTED_ORIGINS = ['http://localhost:85', 'http://127.0.0.1', 'https://' + env('SERVER', default='127.0.0.1') ]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'celery',
    'wkhtmltopdf',

    'apps.home',  # Enable the inner home (home)
    'apps.authentication'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'apps.home.crud.custom_middleware.CustomProductStatusMiddleware',

]

ROOT_URLCONF = 'core.urls'
LOGIN_REDIRECT_URL = "home"  # Route defined in home/urls.py
LOGOUT_REDIRECT_URL = "home"  # Route defined in home/urls.py
TEMPLATE_DIR = os.path.join(CORE_DIR, "apps/templates")  # ROOT dir for templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.context_processors.cfg_assets_root',
                'django.template.context_processors.i18n'
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases


DATABASES = { 
    'default': {
    'ENGINE'  : 'django.db.backends.mysql', 
    'NAME'    : config('DB_NAME'),
    'USER'    : config('DB_USERNAME'),
    'PASSWORD': config('DB_PASS'),
    'HOST'    : config('DB_HOST'),
    'PORT'    : config('DB_PORT'),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/
from django.utils.translation import gettext_lazy as _


#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-hk'
LANGUAGES=[
    ('en-us', _('English')),
    ('zh-hk', _('hong kong Chinese')),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

#############################################################
# SRC: https://devcenter.heroku.com/articles/django-assets

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
#STATIC_ROOT = '/home/ubuntu/dev/staticfiles'
STATIC_ROOT = os.path.join(CORE_DIR, 'staticfiles')
STATIC_URL = '/static/'
AUTH_USER_MODEL='authentication.User'
# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(CORE_DIR, 'apps/static'),
    os.path.join(CORE_DIR, 'staticfiles'),
)


#############################################################
#############################################################

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_HEADERS = [
'accept',
'accept-encoding',
'authorization',
'content-type',
'dnt',
'origin',
'user-agent',
'x-csrftoken',
'x-requested-with',
]


# set the celery broker url 
CELERY_BROKER_URL = 'redis://localhost:6379/'
  
# set the celery result backend 
CELERY_RESULT_BACKEND = 'redis://localhost:6379/'
  
# set the celery timezone 
CELERY_TIMEZONE = 'UTC'

#session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db' 
SESSION_COOKIE_AGE = 1209600

# if config('DEBUG', cast=bool):
#     # SRC: https://devcenter.heroku.com/articles/django-assets

#     # Static files (CSS, JavaScript, Images)
#     # https://docs.djangoproject.com/en/1.9/howto/static-files/

#     STATIC_ROOT = os.path.join(CORE_DIR, 'staticfiles')
#     STATIC_URL = '/static/'

#     # Extra places for collectstatic to find static files.
#     STATICFILES_DIRS = (
#         os.path.join(CORE_DIR, 'apps/static'),
#     )

MEDIA_ROOT = os.path.join(CORE_DIR, 'media/')
MEDIA_URL = '/media/'

# else:
    #working s3 settings #comment above code for s3
#AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
#AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')

# Bucket for static files
#STATIC_BUCKET_NAME = config('AWS_STATIC_STORAGE_BUCKET_NAME')

# Bucket for media files
#MEDIA_BUCKET_NAME = config('AWS_MEDIA_STORAGE_BUCKET_NAME')

#AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')
#AWS_S3_SIGNATURE_VERSION = config('AWS_S3_SIGNATURE_VERSION')
#AWS_S3_VERIFY = True
#AWS_DEFAULT_ACL = None

STATICFILES_DIRS = (
    os.path.join(CORE_DIR, 'apps/static'),
)

# if STATIC_BUCKET_NAME:
#     STATIC_LOCATION = 'static'
#     AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
#     STATIC_CLOUDFRONT_DOMAIN = config('AWS_STATIC_S3_CUSTOM_DOMAIN')
#     # Static files settings
#     STATIC_URL = f"https://{STATIC_CLOUDFRONT_DOMAIN}/"
#     STATICFILES_STORAGE = 'utils.storage_backends.StaticStorage' 

# if MEDIA_BUCKET_NAME:
#     PUBLIC_MEDIA_LOCATION = 'media'
#     AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
#     MEDIA_CLOUDFRONT_DOMAIN = config('AWS_MEDIA_S3_CUSTOM_DOMAIN')
#     # Media files settings
#     MEDIA_URL = f"https://{MEDIA_CLOUDFRONT_DOMAIN}/"
#     DEFAULT_FILE_STORAGE = 'utils.storage_backends.MediaStorage'
