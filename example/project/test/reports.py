# -*- coding: utf-8 -*-
#
#  django-reportapi/example/project/test/reports.py
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
from django.utils.translation import ugettext_noop, ugettext_lazy as _
from reportapi.filters import (FilterObject, FilterText, FilterNumber,
    FilterDateTime, FilterDate, FilterTime,
    FilterBoolean, FilterChoice, FilterMonth, FilterWeekDay,)
from reportapi.models import Report, Spreadsheet, HtmlReport
from reportapi.sites import site
from reportapi.conf import settings

@site.register
class TestReport(Report):
    title = ugettext_noop('Test report')

    filters = (
        FilterNumber(ugettext_noop('timeout'), required=True, default_value=3, conditions=['exact']),
        FilterObject(ugettext_noop('filter for objects'), manager='auth.User.objects', required=True),
        FilterText(ugettext_noop('filter for text')),
        FilterNumber(ugettext_noop('filter for number')),
        FilterDateTime(ugettext_noop('filter for date and time'), True), # required=True as argument
        FilterDate(ugettext_noop('filter for date'), default_value=None), # drop default
        FilterTime(ugettext_noop('filter for time')),
        FilterChoice(ugettext_noop('filter for choice'), options=((1, _('First')),(2, _('Second')))),
        FilterMonth(ugettext_noop('filter for month')),
        FilterWeekDay(ugettext_noop('filter for weekday')),
        FilterBoolean('%s 1' % 'filter for boolean', verbose_name=_('filter for boolean'), default_value=None),
        FilterBoolean('%s 2' % 'filter for boolean', verbose_name=_('filter for boolean'), default_value=True),
        FilterBoolean('%s 3' % 'filter for boolean', verbose_name=_('filter for boolean'), default_value=False),
        FilterBoolean('%s 4' % 'filter for boolean', verbose_name=_('filter for boolean'), usenone=False),
    )

    def get_context(self, document, filters, request=None):
        """
        Этот метод должен быть переопределён в наследуемых классах.
        Возвращать контекст нужно в виде словаря.
        Параметр context['DOCUMENT'] будет установлен автоматически в
        методе self.render(...)
        """
        import time
        time.sleep(int(self.get_filter_data('timeout', filters)['value'])) # for test progressbar

        return {}


@site.register
class TestSpreadsheet(Spreadsheet):
    title = ugettext_noop('Test spreadsheet')

    filters = (
        FilterNumber(ugettext_noop('timeout'), default_value=3, required=True),
        FilterObject(ugettext_noop('filter for objects'), manager='auth.User.objects', required=True),
        FilterText(ugettext_noop('filter for text')),
        FilterNumber(ugettext_noop('filter for number')),
        FilterDateTime(ugettext_noop('filter for date and time'), True), # required=True as argument
        FilterDate(ugettext_noop('filter for date')),
        FilterTime(ugettext_noop('filter for time')),
        FilterChoice(ugettext_noop('filter for choice'), options=((1, _('First')),(2, _('Second')))),
        FilterMonth(ugettext_noop('filter for month')),
        FilterWeekDay(ugettext_noop('filter for weekday')),
        FilterBoolean(ugettext_noop('filter for boolean')),
    )

    def get_context(self, document, filters, request=None):
        """
        Этот метод должен быть переопределён в наследуемых классах.
        Возвращать контекст нужно в виде словаря.
        Параметр context['DOCUMENT'] будет установлен автоматически в
        методе self.render(...)
        """
        import time
        time.sleep(int(self.get_filter_data('timeout', filters)['value'])) # for test progressbar

        return {}


@site.register
class TestHtmlReport(HtmlReport):
    title = ugettext_noop('Test HTML report')

    convert_to_pdf = True
    convert_to_odf = True

    filters = (
        FilterNumber(ugettext_noop('timeout'), default_value=3, required=True),
        FilterObject(ugettext_noop('filter for objects'), manager='auth.User.objects', required=True),
        FilterText(ugettext_noop('filter for text')),
        FilterNumber(ugettext_noop('filter for number')),
        FilterDateTime(ugettext_noop('filter for date and time'), True), # required=True as argument
        FilterDate(ugettext_noop('filter for date')),
        FilterTime(ugettext_noop('filter for time')),
        FilterChoice(ugettext_noop('filter for choice'), options=((1, _('First')),(2, _('Second')))),
        FilterMonth(ugettext_noop('filter for month')),
        FilterWeekDay(ugettext_noop('filter for weekday')),
        FilterBoolean(ugettext_noop('filter for boolean')),
    )

    def get_context(self, document, filters, request=None):
        """
        Этот метод должен быть переопределён в наследуемых классах.
        Возвращать контекст нужно в виде словаря.
        Параметр context['DOCUMENT'] будет установлен автоматически в
        методе self.render(...)
        """
        import time
        time.sleep(int(self.get_filter_data('timeout', filters)['value'])) # for test progressbar

        return {}

