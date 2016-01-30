# -*- coding: utf-8 -*-
#
#   Copyright 2015 Grigoriy Kramarenko <root@rosix.ru>
#
#   This file is part of ReportAPI.
#
#   ReportAPI is free software: you can redistribute it and/or
#   modify it under the terms of the GNU Affero General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.
#
#   ReportAPI is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public
#   License along with ReportAPI. If not, see
#   <http://www.gnu.org/licenses/>.
#

from __future__ import unicode_literals
from distutils.version import LooseVersion as V

from django import VERSION

v = V('%d.%d' % VERSION[:2])

# compatibility from 1.4 to 1.8 and above
if v < V('1.8'):
    from django.template import RequestContext, loader
    def render_to_string(template, context, request):
        return loader.render_to_string(template, context,
                            context_instance=RequestContext(request,))
else:
    from django.template import loader
    def render_to_string(template, context, request):
        return loader.render_to_string(template, context, request=request)


# compatibility from 1.4 to 1.7 and above
if v < V('1.7'):
    from django.db.models import get_model
else:
    from django.apps import apps
    get_model = apps.get_model


# compatibility from 1.4 to 1.5 and above
if v < V('1.5'):
    from django.contrib.auth.models import User
    get_user_model = lambda: User
else:
    from django.contrib.auth import get_user_model
