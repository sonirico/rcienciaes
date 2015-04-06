"""
Django settings for podcastmanager project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Django Celery settings
import djcelery
djcelery.setup_loader()

#BROKER_URL = "django://"
BROKER_URL = "amqp://guest:guest@localhost:5672/"
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'dd8#o#d-^oq%dfon@6fhboc60h+8j91)$&o)q3cumc7^s)7pc3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = True

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

DOMAIN = 'vps84666.ovh.net'
PORT = '8080'
ALLOWED_HOSTS = [str('.' + DOMAIN), '127.0.0.1', '81.21.67.10', '37.59.103.142',]

SAVE_SESSION_EVERY_REQUEST = True
# Application definition

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mpc',
    'player',
    'djcelery',
    'playlist',
    'podget',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'podcastmanager.urls'

WSGI_APPLICATION = 'podcastmanager.wsgi.application'


#opciones de configuracion de grappelli
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

#end grappelli

GRAPPELLI_ADMIN_TITLE = "Podcast Manager"


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'podcastmanager.db'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
# Playlist settings
CURRENT_PLAYLIST = 'current.m3u'
TMP_PLAYLIST = 'tmp.m3u'

# Se alamacenan aqui las imagenes subidas por lis usuarios del directo.
LIVE_COVERS_FOLDER = 'images/live_covers/'

# Twitter settings
TWITTER_OAUTH = {}
TWITTER_OAUTH['ACCESS_TOKEN'] = '2594779706-Q7PJSr99AUILfwiGOaT3Rjvmycnx8pxl1xfoI9s'
TWITTER_OAUTH['ACCESS_TOKEN_SECRET'] = '4t53MZ7UZeqmJP7nSsxEiOjxv3NBY62ASzwD5slyaK8s6'
TWITTER_OAUTH['CONSUMER_KEY'] = '1ciuvSM3ZvEmygyunNEsnvVs7'
TWITTER_OAUTH['CONSUMER_KEY_SECRET'] = '9ZhbhOtf26nrJUVKat7uUiiZNQZTU36tbm4EPwL5WCEaNhyEZ6'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'django_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose'
        },
        'podget_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/podget.log',
            'formatter': 'verbose'
        },
        'playlist_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/playlist.log',
            'formatter': 'verbose'
        },
        'tweets_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/tweets.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['django_file'],
            'propagate': False,
            'level': 'INFO',
        },
        'podget': {
            'handlers': ['podget_file'],
            'level': 'INFO',
        },
        'playlist': {
            'handlers': ['playlist_file'],
            'level': 'INFO',
        }
    }
}


