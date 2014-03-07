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
from django.db import models
from django.db.models import Q, get_model
from django.utils.dates import WEEKDAYS, MONTHS
from django.utils.translation import ugettext_lazy as _
from django.core.paginator import Paginator, Page, PageNotAnInteger, EmptyPage
from django.utils.encoding import python_2_unicode_compatible
from django.template.defaultfilters import slugify
import operator, re

from reportapi import conf
from reportapi.python_serializer import serialize

DEFAULT_SEARCH_FIELDS = getattr(conf, 'DEFAULT_SEARCH_FIELDS',
    (# Основные классы, от которых наследуются другие
        models.CharField,
        models.TextField,
    )
)

__conditions__ = (_('isnull'), _('empty'),# _('bool'),
    _('exact'), _('iexact'), 
    _('gt'), _('gte'), _('lt'), _('lte'),
    _('range'), _('in'),
    _('contains'), _('icontains'), 
    _('startswith'), _('istartswith'), _('endswith'), _('iendswith')
)

@python_2_unicode_compatible
class BaseFilter(object):
    required = None
    _type = None
    conditions = ('isnull', 'exact', 'gt', 'gte', 'lt', 'lte', 'range')

    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name)

    def __init__(self, name, required=False):
        if self.required is None:
            self.required = required
        self.name = slugify(name)
        self.verbose_name = _(name)

    def data(self, condition=None, inverse=False, fragment=None, **options):
        """
        Метод получения информации об установленном фильтре.
        """
        options['name'] = self.name
        options['name_locale'] = self.verbose_name
        options['type'] = self._type
        options['inverse'] = inverse
        options['fragment'] = fragment
        options['condition'] = condition
        if condition:
            options['condition_locale'] = _(condition)
        if fragment:
            options['fragment_locale'] = _(fragment)

        return options

    def condition_list(self):
        return [(x, _(x)) for x in self.conditions or ()]

    def serialize(self):
        return self.name, {
            'required': self.required or False,
            'name': self.name,
            'label': self.verbose_name,
            'type': self._type,
            'conditions': self.condition_list(),
        }

class FilterObject(BaseFilter):
    _type = 'object'
    conditions = ('isnull', 'exact', 'in', 'range')
    model = None
    manager = None
    fields_search = None

    def __init__(self, name, model=None, manager=None, fields_search=None, **kwargs):
        """
        Параметр manager приоритетнее параметра model и может быть как
        полной строкой, включающей название приложения, модели и
        атрибута менеджера в модели, разделённых точками:
        'app.model.objects'
        так и готовым экземпляром менеджера модели
        """
        super(FilterObject, self).__init__(name, **kwargs)

        manager = manager or getattr(self, 'manager', None)
        model = model or getattr(self, 'model', None)
        fields_search = fields_search or getattr(self, 'fields_search', None)
        if not manager and not model:
            raise AttributeError('First set manager for filter')
        elif manager:
            self.set_manager(manager)
        elif model:
            self.set_model(model)
            self.set_manager(None)
        self.opts = self.model._meta
        self.set_fields_search(fields_search)

    def set_model(self, model):
        if issubclass(model, models.ModelBase):
            self.model = model
        elif isinstance(model, (str, unicode)):
            app, model = model.split('.')
            self.model = get_model(app, model)
            if not self.model:
                raise AttributeError('Model `%s.%s` not found.' % (app, model))
        else:
            raise AttributeError('Model must be subclass of models.Model or string: `app.model`.')

    def set_manager(self, manager):
        if isinstance(manager, models.Manager):
            self.manager = manager
        elif isinstance(manager, (str, unicode)):
            app, model, manager = manager.split('.')
            self.model = get_model(app, model)
            if not self.model:
                raise AttributeError('Model `%s.%s` not found.' % (app, model))
            self.manager = getattr(self.model, manager)
        elif not manager and self.model:
            self.manager = self.model._default_manager
        else:
            raise AttributeError('First set manager for filter')

    def set_fields_search(self, fields_search):
        """
        Устанавливает доступные текстовые поля для поиска по ним.
        Если параметр пуст, то установит все доступные текстовые поля
        из модели.
        """
        all_fields = self.opts.get_fields_with_model()
        self.fields_search = [
            x[0].name for x in all_fields \
            if isinstance(x[0], DEFAULT_SEARCH_FIELDS) and (
                not fields_search or x[0].name in fields_search
            )
        ]

    @property
    def objects(self):
        return self.manager.all()

    def get_paginator(self, queryset, per_page=25, orphans=0,
        allow_empty_first_page=True, **kwargs):
        return Paginator(
                queryset, per_page=per_page, orphans=orphans,
                allow_empty_first_page=allow_empty_first_page
            )

    def get_page_queryset(self, queryset, page=1, **kwargs):
        """
        Возвращает объект страницы паджинатора для набора объектов
        """

        paginator = self.get_paginator(queryset=queryset, **kwargs)

        try:
            page = int(page)
        except:
            page=1
        try:
            page_queryset = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            page_queryset = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page_queryset = paginator.page(paginator.num_pages)
        return page_queryset

    def search(self, query, page=1):
        """
        Регистронезависимый поиск по строковым полям
        """
        qs = _search_in_fields(self.objects, self.fields_search, query)
        page_queryset = self.get_page_queryset(qs, page=page)
        return serialize(page_queryset)

    def get_value(self, condition, keys):
        if condition == 'exact':
            return self.objects.get(pk=keys)
        else:
            return self.objects.filter(pk__in=list(keys))

class FilterText(BaseFilter):
    _type = 'text'
    conditions = ('exact', 'iexact', 'contains', 'icontains', 
        'startswith', 'istartswith', 'endswith', 'iendswith', 'empty')

class FilterNumber(BaseFilter):
    _type = 'number'

class FilterDateTime(BaseFilter):
    _type = 'datetime'

class FilterDate(BaseFilter):
    _type = 'date'

class FilterTime(BaseFilter):
    _type = 'time'

class FilterYear(BaseFilter):
    _type = 'year'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte', 'range')

class FilterMonth(BaseFilter):
    _type = 'month'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte', 'range')

    def serialize(self):
        name, dic = super(FilterMonth, self).serialize()
        dic['MONTHS'] = MONTHS
        return name, dic

class FilterDay(BaseFilter):
    _type = 'day'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte', 'range')

class FilterWeekDay(BaseFilter):
    _type = 'weekday'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte', 'range')

    def serialize(self):
        name, dic = super(FilterWeekDay, self).serialize()
        dic['WEEKDAYS'] = WEEKDAYS
        return name, dic

class FilterHour(BaseFilter):
    _type = 'hour'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte', 'range')

class FilterMinute(BaseFilter):
    _type = 'minute'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte', 'range')

class FilterSecond(BaseFilter):
    _type = 'second'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte', 'range')

class FilterBoolean(BaseFilter):
    _type = 'boolean'
    conditions = None

    def serialize(self):
        name, dic = super(FilterBoolean, self).serialize()
        dic['YESNO'] = _('yes'), _('no')
        return name, dic

def _search_in_fields(queryset, fields, query):
    """ Фильтрация """
    if fields:
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name
        orm_lookups = [construct_search(str(search_field))
                       for search_field in fields]
        if not query in ('', None, False, True):
            for bit in query.split():
                or_queries = [Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))

    return queryset
