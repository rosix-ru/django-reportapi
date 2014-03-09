# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2012 Grigoriy Kramarenko.
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
from django.conf.urls import *
import os, copy
from reportapi.conf import settings
from reportapi.sites import site
from django.utils.importlib import import_module

def autodiscover():
    """
    Автообнаружение в приложениях INSTALLED_APPS модулей reports.py.
    """

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        moddir = os.path.normpath(os.path.dirname(mod.__file__))
        testpath = os.path.join(moddir, 'reports.py')
        if os.path.exists(testpath):
            import_module('%s.reports' % app)

autodiscover()

urlpatterns = patterns('reportapi.views',
    url(r'^$', 'index', name='index'),
    url(r'^api/', 'api', name='api'),
    url(r'^list/(?P<section>\w+)/$', 'report_list', name='report_list'),
    url(r'^docs/(?P<pk>\d+)/$', 'get_document', name='get_document'),
    url(r'^docs/(?P<pk>\d+)/(?P<format>\w+)/$', 'get_document', name='get_document_format'),
    url(r'^docs/$', 'documents', name='documents'),
    url(r'^docs/(?P<section>\w+)/$', 'documents', name='documents_section'),
    url(r'^docs/(?P<section>\w+)/(?P<name>\w+)/$', 'documents', name='documents_section_name'),
    url(r'^report/(?P<section>\w+)/(?P<name>\w+)/$', 'report', name='report'),
    #~ url(r'^test/$', 'test',  name='reportapi_test'),
)

#~ urlpatterns += patterns('',
    #~ url(r'^api/',   include('quickapi.urls'), name='reportapi')
#~ )
