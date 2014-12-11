# -*- coding: utf-8 -*-
#
#  reportapi/__init__.py
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
from __future__ import unicode_literals
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from reportapi.utils.version import auto_create_version_links

__label__ = _('Reporting')

VERSION = (2, 0)
__version__ = '.'.join([ str(x) for x in VERSION ])


# При сборке пакета и установке через pip код не выполнится
# из-за отсутствия путей.
try:
    auto_create_version_links(__file__, VERSION)
except:
    pass
    auto_create_version_links(__file__, VERSION)
