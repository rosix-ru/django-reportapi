# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from reportapi.utils.version import auto_create_version_links

__label__ = _('Reporting')

VERSION = (0, 3)
__version__ = '.'.join([ str(x) for x in VERSION ])


# При сборке пакета и установке через pip код не выполнится
# из-за отсутствия путей.
try:
    auto_create_version_links(__file__, VERSION)
except:
    pass
    auto_create_version_links(__file__, VERSION)
