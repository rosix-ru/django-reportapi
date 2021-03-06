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

from django.utils.translation import ugettext_noop, ugettext_lazy as _
from reportapi.filters import (
    FilterObject, FilterText, FilterNumber,
    FilterDateTime, FilterDate, FilterTime,
    FilterBoolean, FilterChoice, FilterMonth, FilterWeekDay
)
from reportapi.models import Report, Spreadsheet, HtmlReport
from reportapi.sites import site


@site.register
class TestReport(Report):
    title = ugettext_noop('Test report')

    filters = (
        FilterNumber(ugettext_noop('timeout'), required=True, default_value=3,
                     conditions=['exact']),
        FilterObject(ugettext_noop('filter for objects'),
                     manager='auth.User.objects', required=True),
        FilterText(ugettext_noop('filter for text')),
        FilterNumber(ugettext_noop('filter for number')),
        # required=True as argument
        FilterDateTime(ugettext_noop('filter for date and time'), True),
        # drop default
        FilterDate(ugettext_noop('filter for date'), default_value=None),
        FilterTime(ugettext_noop('filter for time')),
        FilterChoice(ugettext_noop('filter for choice'),
                     options=((1, _('First')), (2, _('Second')))),
        FilterMonth(ugettext_noop('filter for month')),
        FilterWeekDay(ugettext_noop('filter for weekday')),
        FilterBoolean('%s 1' % 'filter for boolean',
                      verbose_name=_('filter for boolean'),
                      default_value=None),
        FilterBoolean('%s 2' % 'filter for boolean',
                      verbose_name=_('filter for boolean'),
                      default_value=True),
        FilterBoolean('%s 3' % 'filter for boolean',
                      verbose_name=_('filter for boolean'),
                      default_value=False),
        FilterBoolean('%s 4' % 'filter for boolean',
                      verbose_name=_('filter for boolean'),
                      usenone=False),
    )

    def get_context(self, document, filters, request=None):
        """
        Этот метод должен быть переопределён в наследуемых классах.
        Возвращать контекст нужно в виде словаря.
        Параметр context['DOCUMENT'] будет установлен автоматически в
        методе self.render(...)
        """
        import time
        # for test progressbar
        time.sleep(int(self.get_filter_data('timeout', filters)['value']))

        return {}


@site.register
class TestSpreadsheet(Spreadsheet):
    title = ugettext_noop('Test spreadsheet')

    filters = (
        FilterNumber(ugettext_noop('timeout'), default_value=3, required=True),
        FilterObject(ugettext_noop('filter for objects'),
                     manager='auth.User.objects', required=True),
        FilterText(ugettext_noop('filter for text')),
        FilterNumber(ugettext_noop('filter for number')),
        # required=True as argument
        FilterDateTime(ugettext_noop('filter for date and time'), True),
        FilterDate(ugettext_noop('filter for date')),
        FilterTime(ugettext_noop('filter for time')),
        FilterChoice(ugettext_noop('filter for choice'),
                     options=((1, _('First')), (2, _('Second')))),
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
        # for test progressbar
        time.sleep(int(self.get_filter_data('timeout', filters)['value']))

        return {}


@site.register
class TestHtmlReport(HtmlReport):
    title = ugettext_noop('Test HTML report')

    convert_to_pdf = True
    convert_to_odf = True

    filters = (
        FilterNumber(ugettext_noop('timeout'), default_value=3, required=True),
        FilterObject(ugettext_noop('filter for objects'),
                     manager='auth.User.objects', required=True),
        FilterText(ugettext_noop('filter for text')),
        FilterNumber(ugettext_noop('filter for number')),
        # required=True as argument
        FilterDateTime(ugettext_noop('filter for date and time'), True),
        FilterDate(ugettext_noop('filter for date')),
        FilterTime(ugettext_noop('filter for time')),
        FilterChoice(ugettext_noop('filter for choice'),
                     options=((1, _('First')), (2, _('Second')))),
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
        # for test progressbar
        time.sleep(int(self.get_filter_data('timeout', filters)['value']))

        return {}
