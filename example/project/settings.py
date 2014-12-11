# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2013 Grigoriy Kramarenko.
###############################################################################
# This file is part of ReportAPI.
#
#    ReportAPI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    ReportAPI is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with ReportAPI.  If not, see <http://www.gnu.org/licenses/>.
#
# Этот файл — часть ReportAPI.
#
#   ReportAPI - свободная программа: вы можете перераспространять ее и/или
#   изменять ее на условиях Стандартной общественной лицензии GNU в том виде,
#   в каком она была опубликована Фондом свободного программного обеспечения;
#   либо версии 3 лицензии, либо (по вашему выбору) любой более поздней
#   версии.
#
#   ReportAPI распространяется в надежде, что она будет полезной,
#   но БЕЗО ВСЯКИХ ГАРАНТИЙ; даже без неявной гарантии ТОВАРНОГО ВИДА
#   или ПРИГОДНОСТИ ДЛЯ ОПРЕДЕЛЕННЫХ ЦЕЛЕЙ. Подробнее см. в Стандартной
#   общественной лицензии GNU.
#
#   Вы должны были получить копию Стандартной общественной лицензии GNU
#   вместе с этой программой. Если это не так, см.
#   <http://www.gnu.org/licenses/>.
###############################################################################
"""
# Django settings for this project.

from django.utils.translation import ugettext_lazy as _
import os

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
def abspath(*paths):
    return os.path.abspath(os.path.join(PROJECT_PATH, *paths)).replace('\\','/')

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Webmaster Name', 'example@example.com'),
)
MANAGERS = ADMINS

try:
    f = open(abspath('AUTHORS'), 'rb')
    AUTHORS = f.readlines()
    f.close()
except:
    AUTHORS = (u'Webmaster Name', u'Manager Name')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': abspath('example.sqlite'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.4/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Vladivostok' #'Europe/Moscow'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru-ru'


LANGUAGES = (
    ('ru', _('Russian')),
    ('en', _('English')),
)

"""
LANGUAGES = (
    ('af',      _('Afrikaans')),
    ('ar',      _('Arabic')),
    ('az',      _('Azerbaijani')),
    ('bg',      _('Bulgarian')),
    ('be',      _('Belarusian')),
    ('bn',      _('Bengali')),
    ('br',      _('Breton')),
    ('bs',      _('Bosnian')),
    ('ca',      _('Catalan')),
    ('cs',      _('Czech')),
    ('cy',      _('Welsh')),
    ('da',      _('Danish')),
    ('de',      _('German')),
    ('el',      _('Greek')),
    ('en',      _('English')),
    ('en-gb',   _('British English')),
    ('eo',      _('Esperanto')),
    ('es',      _('Spanish')),
    ('es-ar',   _('Argentinian Spanish')),
    ('es-mx',   _('Mexican Spanish')),
    ('es-ni',   _('Nicaraguan Spanish')),
    ('es-ve',   _('Venezuelan Spanish')),
    ('et',      _('Estonian')),
    ('eu',      _('Basque')),
    ('fa',      _('Persian')),
    ('fi',      _('Finnish')),
    ('fr',      _('French')),
    ('fy-nl',   _('Frisian')),
    ('ga',      _('Irish')),
    ('gl',      _('Galician')),
    ('he',      _('Hebrew')),
    ('hi',      _('Hindi')),
    ('hr',      _('Croatian')),
    ('hu',      _('Hungarian')),
    ('ia',      _('Interlingua')),
    ('id',      _('Indonesian')),
    ('is',      _('Icelandic')),
    ('it',      _('Italian')),
    ('ja',      _('Japanese')),
    ('ka',      _('Georgian')),
    ('kk',      _('Kazakh')),
    ('km',      _('Khmer')),
    ('kn',      _('Kannada')),
    ('ko',      _('Korean')),
    ('lb',      _('Luxembourgish')),
    ('lt',      _('Lithuanian')),
    ('lv',      _('Latvian')),
    ('mk',      _('Macedonian')),
    ('ml',      _('Malayalam')),
    ('mn',      _('Mongolian')),
    ('nb',      _('Norwegian Bokmal')),
    ('ne',      _('Nepali')),
    ('nl',      _('Dutch')),
    ('nn',      _('Norwegian Nynorsk')),
    ('pa',      _('Punjabi')),
    ('pl',      _('Polish')),
    ('pt',      _('Portuguese')),
    ('pt-br',   _('Brazilian Portuguese')),
    ('ro',      _('Romanian')),
    ('ru',      _('Russian')),
    ('sk',      _('Slovak')),
    ('sl',      _('Slovenian')),
    ('sq',      _('Albanian')),
    ('sr',      _('Serbian')),
    ('sr-latn', _('Serbian Latin')),
    ('sv',      _('Swedish')),
    ('sw',      _('Swahili')),
    ('ta',      _('Tamil')),
    ('te',      _('Telugu')),
    ('th',      _('Thai')),
    ('tr',      _('Turkish')),
    ('tt',      _('Tatar')),
    ('udm',     _('Udmurt')),
    ('uk',      _('Ukrainian')),
    ('ur',      _('Urdu')),
    ('vi',      _('Vietnamese')),
    ('zh-cn',   _('Simplified Chinese')),
    ('zh-tw',   _('Traditional Chinese')),
)
"""

LOCALE_PATHS = (
    abspath('locale'),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = abspath('..', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = abspath('..', 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'generate-this-unique-key!!!'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'project.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'project.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    abspath("templates"),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    # append:
    'django.core.context_processors.request'
)

INSTALLED_APPS = (
    ### Обязательные
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'reportapi',
    'quickapi',
    'project.test',
)


########################################################################
#                     SETTINGS FOR APPLICATIONS                        #
########################################################################
SESSION_COOKIE_NAME = 'reportapisessionid'
LOGIN_URL = '/admin/'

########################################################################
#                   END SETTINGS FOR APPLICATIONS                      #
########################################################################

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

CACHES = {
    'default': {
        #'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'KEY_PREFIX': '_%s_' % 'ReportAPI',
        #'LOCATION': [ '127.0.0.1:11211' ]
    }
}

# This import re-definition current top settings, 
# e.g. DATABASES, SECRET_KEY, etc.
# Default path: ../securesettings.py
# outer from project paths and unavailable in Mercurial repository. 
try:
    from securesettings import *
except:
    pass
