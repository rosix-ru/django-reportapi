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
from django.utils.translation import ugettext_noop, ugettext_lazy as _
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

__conditions__ = (ugettext_noop('isnull'), ugettext_noop('empty'),# ugettext_noop('bool'),
    ugettext_noop('exact'), ugettext_noop('iexact'), 
    ugettext_noop('gt'), ugettext_noop('gte'),
    ugettext_noop('lt'), ugettext_noop('lte'),
    ugettext_noop('range'), ugettext_noop('in'),
    ugettext_noop('contains'), ugettext_noop('icontains'), 
    ugettext_noop('startswith'), ugettext_noop('istartswith'),
    ugettext_noop('endswith'), ugettext_noop('iendswith')
)

@python_2_unicode_compatible
class BaseFilter(object):
    required = None
    _type = None
    conditions = ('isnull', 'exact', 'gt', 'gte', 'lt', 'lte', 'range')
    placeholder = None

    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name)

    def __init__(self, name, required=False):
        if self.required is None:
            self.required = required
        self.name = slugify(name)
        self.verbose_name = _(name)

    def get_value(self, condition, val):
        return val

    def data(self, condition=None, value=None, inverse=False, **options):
        """
        Метод получения информации об установленном фильтре.
        """
        options['name'] = self.name
        options['label'] = self.verbose_name
        options['type'] = self._type
        options['inverse'] = inverse
        options['condition'] = condition
        options['condition_label'] = _(condition)
        options['value'] = self.get_value(condition, value)

        return options

    def condition_list(self):
        return [(x, _(x)) for x in self.conditions or ()]

    def serialize(self):
        D = {
            'required': self.required or False,
            'name': self.name,
            'label': self.verbose_name,
            'type': self._type,
            'conditions': self.condition_list(),
        }

        if self.placeholder:
            D['placeholder'] = self.placeholder

        if hasattr(self, 'options'):
            o = self.options
            D['options'] = o() if callable(o) else o

        if hasattr(self, 'withseconds'):
            D['withseconds'] = self.withseconds

        return self.name, D

class FilterObject(BaseFilter):
    _type = 'object'
    conditions = ('isnull', 'exact', 'in', 'range')
    model = None
    manager = None
    fields_search = None
    placeholder = _('Object search')
    max_options = 10

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

        if not manager and not model:
            raise AttributeError('First set manager for filter')
        elif manager:
            self.set_manager(manager)
        elif model:
            self.set_model(model)
            self.set_manager(None)
        self.opts = self.model._meta

        self.set_fields_search(fields_search or getattr(self, 'fields_search', None))
        self.max_options = kwargs.pop('max_options', self.max_options)

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

    @property
    def options(self):
        return serialize(self.manager.all()[:self.max_options])

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

    def get_value(self, condition, value):
        if condition == 'isnull':
            return value
        elif condition == 'exact':
            return self.objects.get(pk=value)
        else:
            return self.objects.filter(pk__in=list(value))

class FilterText(BaseFilter):
    _type = 'text'
    conditions = ('exact', 'iexact', 'contains', 'icontains', 
        'startswith', 'istartswith', 'endswith', 'iendswith', 'empty')

class FilterNumber(BaseFilter):
    _type = 'number'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte')

class FilterDateTime(BaseFilter):
    _type = 'datetime'
    withseconds = False

class FilterDate(BaseFilter):
    _type = 'date'

class FilterTime(BaseFilter):
    _type = 'time'
    withseconds = False

class FilterBoolean(BaseFilter):
    _type = 'boolean'
    conditions = None

    def serialize(self):
        name, dic = super(FilterBoolean, self).serialize()
        dic['YESNO'] = _('yes'), _('no')
        return name, dic

class FilterChoice(BaseFilter):
    _type = 'choice'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte', 'range', 'in')
    placeholder = _('Choice')
    keytype = int
    _options = None

    def __init__(self, name, options=None, **kwargs):
        if options:
            self._options = dict(options)
        else:
            self._options = self._options or {}
        super(FilterChoice, self).__init__(name, **kwargs)

    @property
    def options(self):
        return [ {'value':x,'label':y} for x,y in self._options.items() ]

    def get_value(self, condition, value):
        dic = self._options
        if condition in ('range', 'in'):
            return [ dic[self.keytype(x)] for x in list(value) if self.keytype(x) in dic ]
        else:
            return dic.get(self.keytype(value), None)

class FilterChoiceStr(FilterChoice):
    keytype = str

class FilterWeekDay(FilterChoice):
    _type = 'weekday'
    placeholder = _('Select weekday')
    _options = WEEKDAYS

class FilterMonth(FilterChoice):
    _type = 'month'
    placeholder = _('Select month')
    _options = MONTHS


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
