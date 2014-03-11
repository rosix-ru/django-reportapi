# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2014 Grigoriy Kramarenko.
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
from django.utils.translation import ugettext_noop, ugettext_lazy as _
from reportapi.filters import (FilterObject, FilterText, FilterNumber,
    FilterDateTime, FilterDate, FilterTime,
    FilterYear, FilterMonth, FilterDay, FilterWeekDay,
    FilterHour, FilterMinute, FilterSecond,
    FilterBoolean)
from reportapi.models import Report
from reportapi.sites import site
from reportapi.conf import settings

@site.register
class TestReport(Report):
    title = 'Test report'
    create_force = False
    filters = (
        FilterObject('user', manager='auth.User.objects', required=True),
        FilterText('filter for text'),
        FilterNumber('filter for number'),
        FilterDateTime('filter for date and time', True), # required=True as argument
        FilterDate('filter for date'),
        FilterTime('filter for time'),
        # In the future:
        #~ FilterYear('filter for year'),
        #~ FilterMonth('filter for month'),
        #~ FilterDay('filter for day'),
        #~ FilterWeekDay('filter for weekday'),
        #~ FilterHour('filter for hour'),
        #~ FilterMinute('filter for minute'),
        #~ FilterSecond('filter for second'),
        FilterBoolean('filter for boolean'),
    )

    def get_context(self, request, document, filters):
        """
        Этот метод должен быть переопределён в наследуемых классах.
        Возвращать контекст нужно в виде словаря.
        Параметр context['DOCUMENT'] будет установлен автоматически в
        методе self.render(...)
        """
        import time
        time.sleep(120)

        return {}
