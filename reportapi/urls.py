# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
