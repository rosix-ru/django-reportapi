# -*- coding: utf-8 -*-
#
#   Copyright 2014-2015 Grigoriy Kramarenko <root@rosix.ru>
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
from django.conf.urls import include, url

from reportapi import views, api

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

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^list/(?P<section>\w+)/$', views.report_list, name='report_list'),
    url(r'^doc/(?P<pk>\d+)/view/+(?P<format>[html,pdf]+)?$', views.view_document, name='view_document'),
    url(r'^doc/(?P<pk>\d+)/download/+(?P<format>[xml,odf,pdf]+)?$', views.download_document, name='download_document'),
    url(r'^docs/$', views.documents, name='documents'),
    url(r'^docs/(?P<section>\w+)/$', views.documents, name='documents_section'),
    url(r'^docs/(?P<section>\w+)/(?P<name>\w+)/$', views.documents, name='documents_section_name'),
    url(r'^report/(?P<section>\w+)/(?P<name>\w+)/$', views.report, name='report'),
    url(r'^api/', api.api, name='api')
]

