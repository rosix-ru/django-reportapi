# -*- coding: utf-8 -*-
#
#  reportapi/sites.py
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
from __future__ import unicode_literals, print_function
from django.utils.encoding import smart_text
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured
from django.utils.text import capfirst

from reportapi.models import Report, Register, Document
from reportapi import conf
from reportapi.conf import settings

SORTING_SECTIONS = getattr(conf, 'REPORTAPI_SORTING_SECTIONS', True)
SORTING_REPORTS = getattr(conf, 'REPORTAPI_SORTING_REPORTS', True)
SECTION_LABELS        = getattr(conf, 'SECTION_LABELS',
    {
        'admin':            _('Administration'),
        'auth':             _('Users'),
        'sites':            _('Sites'),
        'contenttypes':     _('Content types'),
    }
)

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

class Section(object):
    """ Класс раздела для регистрации экземпляров Report """
    icon = None

    def __init__(self, site, section_name, section_label):
        self.site = site
        self.name = section_name
        self.label = section_label
        self.reports_list = []
        self.reports = {}

    def get_registered(self, request):
        manager = Register.objects
        if request:
            manager = manager.permitted(request)
        return manager.filter(section=self.name)

    def has_permission(self, request):
        """
        Возвращает True, если данный HttpRequest имеет разрешение по
        крайней мере в одном экземпляре Report
        """
        return bool(self.get_registered(request).count())

    def get_available_names(self, request):
        """
        Возвращает список имён отчётов, доступных для пользователя
        """
        return self.get_registered(request).values_list('name', flat=True)

    def get_available_reports(self, request):
        """ Возвращает отчёты, доступные для пользователя """
        reports = {}
        names = self.get_available_names(request)
        for name in names:
            reports[name] = self.reports[name]
        return reports

    def get_scheme(self, request):
        """ Возвращает схему раздела для пользователя """
        reports = self.get_reports(request)
        SECTION = {
            'icon': self.icon,
            'label': self.label,
            'reports_list': [ r.name for r in reports ],
            'reports': {},
        }
        for report in reports:
            scheme = report.get_scheme(request)
            if scheme:
                SECTION['reports'][report.name] = scheme

        return SECTION

    def get_reports(self, request):
        """ Возвращает список отчётов, доступных для пользователя """
        unsorted = self.get_available_names(request)
        # По умолчанию сортировка по очереди регистрации
        names = [ x for x in self.reports_list if x in unsorted ]
        REPORTS = [ self.reports[name] for name in names ]

        if SORTING_REPORTS:
            # Сортировка по локализованному названию
            REPORTS = sorted(REPORTS, key=lambda x: unicode(x.label))

        return REPORTS

class SiteReportAPI(object):
    """
    Класс сайта для регистрации экземпляров Report
    """

    def __init__(self, icon=None, label=_('Reporting')):
        self.icon = icon
        self.label = label

        self.sections_list = []   # меню секций
        self.sections      = {}   # экземпляры Section

    def register(self, iterclass, **kwargs):
        """
        Registers the given report(s)
        """

        # Don't import the humongous validation code unless required
        # TODO: сделать валидатор
        #~ if settings.DEBUG:
            #~ from reportapi.validation import validate
        #~ else:
            #~ validate = lambda klass: None
        validate = lambda klass: None

        if issubclass(iterclass, Report):
            iterclass = [iterclass]

        for report_class in iterclass:
            validate(report_class)
            report = report_class(site=self, **kwargs)
            report.create_register()

            section_name = report.section
            report_name = report.name

            if not section_name in self.sections:
                self.sections[section_name] = Section(
                    site=self,
                    section_name=section_name,
                    section_label=SECTION_LABELS.get(section_name, report.section_label),
                    )
                self.sections_list.append(section_name)
            section = self.sections[section_name]

            if report_name in section.reports:
                raise AlreadyRegistered('The report %s is already registered' % report.__name__)

            section.reports[report_name] = report
            section.reports_list.append(report_name)

    def unregister_model(self, itername):
        """
        Unregisters the given report name(s).
        """
        if isinstance(itername, six.string_types):
            itername = [itername]
        for report_name in itername:
            section_name = report_name.split('.')[0]
            section = self.sections[section_name]
            free_report = section.reports.pop(report_name)

            if report_name in section.reports_list:
                del section.reports_list[section.reports_list.index(report_name)]

            if not section.report.keys():
                del self.sections[section_name]
                del self.sections_list[self.sections_list.index(section_name)]

            return free_report

    def get_registered(self):
        return Register.objects.all()

    def has_permission(self, request):
        """
        Возвращает True, если данный HttpRequest имеет разрешение по
        крайней мере в одном экземпляре Report
        """
        return request.user.is_active and request.user.is_staff and \
            bool(self.get_registered(request).count())

    def get_scheme(self, request):
        """ Возвращает схему приложения, доступную для пользователя и 
            состоящую из простых объектов Python, готовых к
            сериализации в любую структуру
        """

        SCHEME = {
            'icon': self.icon,
            'label': self.label,
            'sections': {},
        }

        sections_list = []

        # По умолчанию сортировка по очереди регистрации
        for section_name in self.sections_list:
            section = self.sections[section_name]
            scheme = section.get_scheme(request)
            if scheme:
                sections_list.append((section_name, smart_text(section.label)))
                SCHEME['sections'][section_name] = scheme

        if SORTING_SECTIONS:
            # Сортировка по локализованному названию
            sections_list = sorted(sections_list, key=lambda x: x[1])

        SCHEME['sections_list'] = [ x[0] for x in sections_list ]

        return SCHEME

    def get_sections(self, request):
        """ Возвращает список разделов, доступных для пользователя
        """

        SECTIONS = []

        # По умолчанию сортировка по очереди регистрации
        for section_name in self.sections_list:
            section = self.sections[section_name]
            reports = section.get_reports(request)
            if reports:
                SECTIONS.append((section, section.get_reports(request)))

        if SORTING_SECTIONS:
            # Сортировка по локализованному названию
            SECTIONS = sorted(SECTIONS, key=lambda x: smart_text(x[0].label))

        return SECTIONS

    def get_report(self, request, section, name):
        section = self.sections.get(section, None)
        if section:
            report = section.reports.get(name, None)
            if report and report.has_permission(request):
                return report
        return None

    def get_report_and_register(self, request, section, name):
        section = self.sections.get(section, None)
        if section:
            report = section.reports.get(name, None)
            if report:
                register = report.permitted_register(request)
                if register:
                    return report, register
        return None, None

# This global object represents the default ReportAPI site, for the common case.
# You can instantiate SiteReportAPI in your own code to create a custom ReportAPI site.
site = SiteReportAPI()
