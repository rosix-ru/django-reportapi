# -*- coding: utf-8 -*-
#
#  reportapi/urls.py
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
from django.conf.urls import patterns, include, url


def autodiscover():
    """
    Автообнаружение в приложениях INSTALLED_APPS модулей reports.py.
    """
    import os
    from importlib import import_module
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        moddir = os.path.normpath(os.path.dirname(mod.__file__))
        testpath = os.path.join(moddir, 'reports.py')
        if os.path.exists(testpath):
            import_module('%s.reports' % app)

autodiscover()

urlpatterns = patterns('reportapi.views',
    url(r'^$', 'index', name='index'),
    url(r'^list/(?P<section>\w+)/$', 'report_list', name='report_list'),
    url(r'^doc/(?P<pk>\d+)/view/+(?P<format>[html,pdf]+)?$', 'view_document', name='view_document'),
    url(r'^doc/(?P<pk>\d+)/download/+(?P<format>[xml,odf,pdf]+)?$', 'download_document', name='download_document'),
    url(r'^docs/$', 'documents', name='documents'),
    url(r'^docs/(?P<section>\w+)/$', 'documents', name='documents_section'),
    url(r'^docs/(?P<section>\w+)/(?P<name>\w+)/$', 'documents', name='documents_section_name'),
    url(r'^report/(?P<section>\w+)/(?P<name>\w+)/$', 'report', name='report'),
)

urlpatterns += patterns('reportapi.api', url(r'^api/', 'api', name='api'))
