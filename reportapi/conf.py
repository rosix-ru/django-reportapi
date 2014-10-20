# -*- coding: utf-8 -*-
#
#  reportapi/conf.py
#  
#  Copyright 2014 Grigoriy Kramarenko <root@rosix.ru>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
from __future__ import unicode_literals, print_function, division
from django.utils.encoding import smart_text, python_2_unicode_compatible
from django.utils import six

from django.conf import settings
from django import VERSION as django_version
from reportapi import __version__ as reportapi_version
from quickapi import __version__ as quickapi_version

SITE_ID = settings.SITE_ID
DEBUG   = settings.DEBUG

DJANGO_VERSION          = '.'.join([str(x) for x in django_version[:2]])
REPORTAPI_VERSION       = reportapi_version
QUICKAPI_VERSION        = quickapi_version
REPORTAPI_DEBUG = getattr(settings, 'REPORTAPI_DEBUG', settings.DEBUG)
REPORTAPI_ROOT = getattr(settings, 'REPORTAPI_ROOT', '%s/reports/' % settings.MEDIA_ROOT.rstrip('/'))
REPORTAPI_URL  = getattr(settings, 'REPORTAPI_URL',  '%s/reports/' % settings.MEDIA_URL.rstrip('/'))
REPORTAPI_ENABLE_THREADS = getattr(settings, 'REPORTAPI_ENABLE_THREADS', False)
REPORTAPI_CODE_HASHLIB = getattr(settings, 'REPORTAPI_CODE_HASHLIB', 'md5')
REPORTAPI_UPLOAD_HASHLIB = getattr(settings, 'REPORTAPI_UPLOAD_HASHLIB', 'md5')
REPORTAPI_FILES_UNIDECODE = getattr(settings, 'REPORTAPI_FILES_UNIDECODE', False)
REPORTAPI_PDFCONVERT_ARGS1 = getattr(settings, 'REPORTAPI_PDFCONVERT_ARGS1',
            ['unoconv', '-f', 'pdf'])
REPORTAPI_PDFCONVERT_ARGS2 = getattr(settings, 'REPORTAPI_PDFCONVERT_ARGS2', [])
REPORTAPI_CONVERTOR_BACKEND = getattr(settings, 'REPORTAPI_CONVERTOR_BACKEND', None)


REPORTAPI_DEFAULT_FORMAT = getattr(settings, 'REPORTAPI_DEFAULT_FORMAT', None)
if not REPORTAPI_DEFAULT_FORMAT:
    import subprocess

    REPORTAPI_DEFAULT_FORMAT = 'odt'
    try:
        if subprocess.check_output(["which", "unoconv"]):
            REPORTAPI_DEFAULT_FORMAT = 'pdf'
    except:
        pass

AUTH_USER_MODEL  = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
#~ REPORTAPI_EXTERNAL_SUPPORT = getattr(settings, 'REPORTAPI_EXTERNAL_SUPPORT',  False)
#~ REPORTAPI_DEFAULT_TIMEOUT = getattr(settings, 'REPORTAPI_DEFAULT_TIMEOUT', 2)
