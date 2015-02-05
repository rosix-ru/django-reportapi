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
from __future__ import unicode_literals, division
from datetime import datetime

from django import get_version as django_version
from django.conf import settings
from django.utils.timezone import get_default_timezone

from quickapi import get_version as quickapi_version

from reportapi import get_version as reportapi_version

SITE_ID = settings.SITE_ID
DEBUG   = settings.DEBUG

DJANGO_VERSION    = django_version()
REPORTAPI_VERSION = reportapi_version()
QUICKAPI_VERSION  = quickapi_version()

PROJECT_NAME = getattr(settings, 'PROJECT_NAME', None)
PROJECT_URL  = getattr(settings, 'PROJECT_URL', None)

REPORTAPI_DEBUG           = getattr(settings, 'REPORTAPI_DEBUG', settings.DEBUG)
REPORTAPI_LOGGING         = getattr(settings, 'REPORTAPI_LOGGING', not settings.DEBUG)
REPORTAPI_ROOT            = getattr(settings, 'REPORTAPI_ROOT', '%sreports/' % settings.MEDIA_ROOT)
REPORTAPI_URL             = getattr(settings, 'REPORTAPI_URL',  '%sreports/' % settings.MEDIA_URL)
REPORTAPI_ENABLE_THREADS  = getattr(settings, 'REPORTAPI_ENABLE_THREADS', False)
REPORTAPI_FILES_UNIDECODE = getattr(settings, 'REPORTAPI_FILES_UNIDECODE', False)
REPORTAPI_LANGUAGES       = getattr(settings, 'REPORTAPI_LANGUAGES', ['en', 'ru'])
REPORTAPI_UPLOADCODE_LENGTH = getattr(settings, 'REPORTAPI_UPLOADCODE_LENGTH', 12)


# For custom manager. By default used reportapi.managers.DefaultDocumentManager
REPORTAPI_DOCUMENT_MANAGER = getattr(settings, 'REPORTAPI_DOCUMENT_MANAGER', '')

REPORTAPI_UNOCONV_TO_PDF  = getattr(settings, 'REPORTAPI_UNOCONV_TO_PDF', True)
REPORTAPI_UNOCONV_TO_ODF  = getattr(settings, 'REPORTAPI_UNOCONV_TO_ODF', True)
REPORTAPI_UNOCONV_SERVERS = getattr(settings, 'REPORTAPI_UNOCONV_SERVERS', [])

# LibreOffice refuses to convert large files
# therefore exhibited an approximate value as 50 megabyte
REPORTAPI_MAXSIZE_XML = getattr(settings, 'REPORTAPI_MAXSIZE_XML', 1048576*50)

REPORTAPI_VIEW_PRIORITY = tuple(
    ( x for x in getattr(
        settings, 'REPORTAPI_VIEW_PRIORITY', ('html', 'pdf')
        ) if x in ('html', 'pdf')
    )
)
REPORTAPI_DOWNLOAD_PRIORITY = tuple(
    ( x for x in getattr(
        settings, 'REPORTAPI_DOWNLOAD_PRIORITY', ('pdf', 'odf', 'xml')
        ) if x in ('pdf', 'odf', 'xml')
    )
)

REPORTAPI_BRAND_TEXT = getattr(settings, 'REPORTAPI_BRAND_TEXT', '')
REPORTAPI_BRAND_COLOR = getattr(settings, 'REPORTAPI_BRAND_COLOR', '#303030')


class Header(object):
    min_height      = getattr(settings, 'REPORTAPI_HEADER_MIN_HEIGHT', '0.1cm')
    margin_top      = getattr(settings, 'REPORTAPI_HEADER_MARGIN_TOP', '0cm')
    margin_bottom   = getattr(settings, 'REPORTAPI_HEADER_MARGIN_BOTTOM', '0cm')
    margin_left     = getattr(settings, 'REPORTAPI_HEADER_MARGIN_LEFT', '0cm')
    margin_right    = getattr(settings, 'REPORTAPI_HEADER_MARGIN_RIGHT', '0cm')
    dynamic_spacing = getattr(settings, 'REPORTAPI_HEADER_DYNAMIC_SPACING', 'false')
    auto_height     = getattr(settings, 'REPORTAPI_HEADER_AUTO_HEIGHT', 'false')

class Footer(object):
    min_height    = getattr(settings, 'REPORTAPI_FOOTER_MIN_HEIGHT', '1.2cm')
    margin_top    = getattr(settings, 'REPORTAPI_FOOTER_MARGIN_TOP', '0.5cm')
    margin_bottom = getattr(settings, 'REPORTAPI_FOOTER_MARGIN_BOTTOM', '0cm')
    margin_left   = getattr(settings, 'REPORTAPI_FOOTER_MARGIN_LEFT', '0cm')
    margin_right  = getattr(settings, 'REPORTAPI_FOOTER_MARGIN_RIGHT', '0cm')
    border_top    = getattr(settings, 'REPORTAPI_FOOTER_BORDER_TOP', '0.002cm solid #000000')

class Page(object):
    style_name    = getattr(settings, 'REPORTAPI_PAGE_STYLE_NAME', 'A4')
    width         = getattr(settings, 'REPORTAPI_PAGE_WIDTH', '21cm')
    height        = getattr(settings, 'REPORTAPI_PAGE_HEIGHT', '29.7cm')
    margin_top    = getattr(settings, 'REPORTAPI_PAGE_MARGIN_TOP', '0.6cm')
    margin_bottom = getattr(settings, 'REPORTAPI_PAGE_MARGIN_BOTTOM', '0.6cm')
    margin_left   = getattr(settings, 'REPORTAPI_PAGE_MARGIN_LEFT', '2.0cm')
    margin_right  = getattr(settings, 'REPORTAPI_PAGE_MARGIN_RIGHT', '0.6cm')
    num_format    = getattr(settings, 'REPORTAPI_PAGE_NUM_FORMAT', '1')
    print_orientation   = getattr(settings, 'REPORTAPI_PAGE_PRINT_ORIENTATION', 'portrait')
    footnote_max_height = getattr(settings, 'REPORTAPI_PAGE_FOOTNOTE_MAX_HEIGHT', '0cm')

    header = Header()
    footer = Footer()

    def checked(self):
        w = float(self.width.replace('cm', ''))
        h = float(self.height.replace('cm', ''))
        if self.print_orientation == 'landscape' and h > w:
            self.width, self.height = self.height, self.width
        elif h < w and self.print_orientation == 'portrait':
            self.print_orientation == 'landscape'
        return self

SERVER_TZ        = get_default_timezone()
SERVER_TZ_OFFSET = int(SERVER_TZ.utcoffset(datetime.now()).total_seconds() / 60 * -1)
