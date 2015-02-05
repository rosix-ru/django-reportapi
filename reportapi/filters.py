# -*- coding: utf-8 -*-
#
#  reportapi/filters.py
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
import re
import operator

from django.db import models
from django.db.models import Q
from django.core.paginator import Paginator, Page, PageNotAnInteger, EmptyPage
from django.template.defaultfilters import slugify
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils import six, timezone
from django.utils.dates import WEEKDAYS, MONTHS
from django.utils.translation import ugettext_noop, ugettext_lazy as _
from django.utils.dateparse import parse_datetime, parse_date, parse_time
from django.utils.dateformat import format as date_format

from reportapi import conf
from reportapi.exceptions import PeriodsError, ObjectFoundError
from reportapi.python_serializer import serialize
from reportapi.utils import periods
from reportapi.utils.compat import get_model

DEFAULT_SEARCH_FIELDS = getattr(conf, 'DEFAULT_SEARCH_FIELDS',
    (# Основные классы, от которых наследуются другие
        models.CharField,
        models.TextField,
    )
)
DEFAULT_SEARCH_DATE_FIELDS = getattr(conf, 'DEFAULT_SEARCH_DATE_FIELDS',
    (# Основные классы, от которых наследуются другие
        models.DateTimeField,
        models.DateField,
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

DB_OPERATORS = {
        'exact': '=', 'gt': '>', 'gte': '>=', 'lt': '<', 'lte': '<=',
        'isnull': 'IS NULL', 'range': 'BETWEEN %s AND %s'
    }

@python_2_unicode_compatible
class BaseFilter(object):
    required = None
    _type = None
    conditions = ('isnull', 'exact', 'gt', 'gte', 'lt', 'lte', 'range')
    placeholder = None
    verbose_name = None
    boolean_labels = {'TRUE': _('yes'), 'FALSE': _('no'), 'NONE': _('any')}

    db_operators = DB_OPERATORS

    def __str__(self):
        return '%s:%s' % (self.__class__.__name__, self.name)

    def __init__(self, name, required=False, conditions=None,
        verbose_name=None, placeholder=None, **kwargs):

        if self.required is None:
            self.required = required

        if conditions:
            self.conditions = conditions

        if 'default_condition' in kwargs:
            self.default_condition = kwargs['default_condition']

        if 'default_value' in kwargs:
            default_value = kwargs['default_value']
            if callable(default_value):
                self.default_value = lambda s: default_value()
            else:
                self.default_value = default_value

            if not hasattr(self, 'default_condition'):
                self.default_condition = self.conditions[0] if self.conditions else 'truth'

        self.name = slugify(name)

        if not verbose_name is None:
            self.verbose_name = verbose_name
        else:
            self.verbose_name = self.verbose_name or _(name)

        if not placeholder is None:
            self.placeholder = placeholder

    def get_value(self, condition, value, request=None):
        return value

    def get_value_range_label(self, condition, value, request=None):
        if condition == 'range':
            value = list(self.get_value_label(condition, value, request=request))
            return value[0], value[-1] 
        return None

    def get_value_label(self, condition, value, request=None):
        if condition == 'truth':
            return self.boolean_labels.get(str(value).upper(), _('any'))
        elif condition in ('isnull', 'empty'):
            return self.boolean_labels.get(str(bool(value)).upper())
        return self.get_value(condition, value, request=request)

    def data(self, condition=ugettext_noop('truth'), value=None, inverse=False, request=None, **options):
        """
        Метод получения информации об установленном фильтре.
        """
        options['name'] = self.name
        options['label'] = self.verbose_name
        options['type'] = self._type
        options['inverse'] = inverse
        options['condition'] = condition
        options['condition_label'] = _(condition)
        options['value'] = self.get_value(condition, value, request=request)
        options['value_label'] = self.get_value_label(condition, value, request=request)
        if condition == 'range':
            options['value_range_label'] = self.get_value_range_label(condition, value, request=request)

        return options

    def condition_list(self):
        return [(x, _(x)) for x in self.conditions or ()]

    def serialize(self, request=None, **kwargs):
        D = {
            'required': self.required or False,
            'name': self.name,
            'label': self.verbose_name,
            'type': self._type,
            'conditions': self.condition_list(),
            'boolean_labels': self.boolean_labels,
        }

        if self.placeholder:
            D['placeholder'] = self.placeholder

        if hasattr(self, 'options'):
            o = self.options
            if callable(o):
                D['options'] = o(request=request)
            else:
                D['options'] = o

        if hasattr(self, 'get_default_value'):
            # для получения доступных пользователю объектов передаём request
            try:
                D['value'] = self.get_default_value(request=request)
            except:
                pass
            # для datetime, date, time
            if hasattr(self, 'get_default_server_value'):
                try:
                    D['server_value'] = self.get_default_server_value()
                except:
                    pass

            if hasattr(self, 'default_condition'):
                D['condition'] = self.default_condition

        elif hasattr(self, 'default_value'):
            if callable(self.default_value):
                D['value'] = self.default_value(request=request)
            else:
                D['value'] = self.default_value

            if hasattr(self, 'default_condition'):
                D['condition'] = self.default_condition

        if hasattr(self, 'search_on_date'):
            D['search_on_date'] = self.search_on_date

        if hasattr(self, 'fields_search'):
            D['fields_search'] = self.fields_search

        if hasattr(self, 'unicode_key'):
            D['unicode_key'] = self.unicode_key

        if hasattr(self, 'usenone'):
            D['usenone'] = self.usenone

        if hasattr(self, 'format'):
            D['format'] = self.format

        if hasattr(self, 'formatDate'):
            D['formatDate'] = self.formatDate

        if hasattr(self, 'formatTime'):
            D['formatTime'] = self.formatTime

        if hasattr(self, 'use_tz'):
            D['use_tz'] = self.use_tz

        if hasattr(self, 'use_mask'):
            D['use_mask'] = self.use_mask

        return self.name, D

class FilterObject(BaseFilter):
    _type = 'object'
    conditions = ('isnull', 'exact', 'in', 'range')
    model = None
    manager = None
    fields_search = None
    search_on_date = False
    placeholder = _('Object search')
    max_options = 10
    unicode_key = '__unicode__'
    secret_fields = ['password', 'settings', 'details']

    def __init__(self, name, model=None, manager=None, fields_search=None, **kwargs):
        """
        Параметр manager приоритетнее параметра model и может быть как
        полной строкой, включающей название приложения, модели и
        атрибута менеджера в модели, разделённых точками:
        'app.model.objects'
        так и готовым экземпляром менеджера модели
        """
        super(FilterObject, self).__init__(name=name, **kwargs)

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
        elif isinstance(model, six.string_types):
            app, model = model.split('.')
            self.model = get_model(app, model)
            if not self.model:
                raise AttributeError('Model `%s.%s` not found.' % (app, model))
        else:
            raise AttributeError('Model must be subclass of models.Model or string: `app.model`.')

    def set_manager(self, manager):
        if isinstance(manager, models.Manager):
            self.manager = manager
            self.model = manager.model
        elif isinstance(manager, six.string_types):
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
        Устанавливает доступные текстовые поля или поля с датой
        для поиска по ним.
        Если параметр пуст, то установит все доступные текстовые поля
        из модели.
        Также производит исключение полей self.secret_fields
        """
        if not fields_search:
            all_fields = self.opts.get_fields_with_model()
            if self.search_on_date:
                fields_search = [ x[0].name for x in all_fields \
                            if isinstance(x[0], DEFAULT_SEARCH_DATE_FIELDS) ]
            else:
                fields_search = [ x[0].name for x in all_fields \
                            if isinstance(x[0], DEFAULT_SEARCH_FIELDS) ]

        self.fields_search = [ x for x in fields_search if not x in self.secret_fields ]

    @property
    def objects(self):
        """
        Возвращает все данные из менеждера модели
        """
        return self.manager.all()

    def options(self, request=None, **kwargs):
        qs = self.get_queryset(request=request, **kwargs)[:self.max_options]
        return serialize(qs, attrs=self.fields_search, unicode_key=self.unicode_key)

    def get_queryset(self, request=None, **kwargs):
        """
        Этот метод может быть переопределён в наследуемых классах,
        например, если требуется получить определённый набор данных в
        зависимости от запроса.
        """
        return self.objects

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

    def search(self, query, page=1, request=None):
        """
        Регистронезависимый поиск по строковым полям, либо по полям с датой
        """
        qs = self.get_queryset(request=request)
        if self.search_on_date:
            qs = _date_search_in_fields(qs, self.fields_search, query)
        else:
            qs = _search_in_fields(qs, self.fields_search, query)
        page_queryset = self.get_page_queryset(qs, page=page)
        return serialize(page_queryset, attrs=self.fields_search,
            unicode_key=self.unicode_key)

    def get_value(self, condition, value, request=None):
        qs = self.get_queryset(request=request)
        if condition == 'isnull':
            return bool(value)
        elif condition == 'exact':
            try:
                return qs.get(pk=value)
            except:
                raise ObjectFoundError()
        elif condition == 'range':
            qs = qs.filter(pk__in=value).order_by('pk')
            if len(qs) != 2:
                raise ObjectFoundError()
            return qs[0], qs[1]
        else:
            qs = qs.filter(pk__in=list(value)).order_by('pk')
            if not qs:
                raise ObjectFoundError()
            return qs

class FilterText(BaseFilter):
    _type = 'text'
    conditions = ('exact', 'iexact', 'contains', 'icontains', 
        'startswith', 'istartswith', 'endswith', 'iendswith', 'empty')

class FilterNumber(BaseFilter):
    _type = 'number'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte')

# Translated date and time formats
DATE_FORMAT         = _('Y-m-d')
TIME_FORMAT         = _('H:i')
TIME_FORMAT_SEC     = _('H:i:s')
DATETIME_FORMAT     = _('Y-m-d H:i')
DATETIME_FORMAT_SEC = _('Y-m-d H:i:s')

class BaseDateTime(BaseFilter):
    use_mask = True
    default_condition = 'exact'

    def time_replace(self, value):
        def _replace(v):
            v = timezone.localtime(v)
            if hasattr(v, 'second'):
                v = v.replace(microsecond=0)
                if not getattr(self, 'withseconds', False):
                    v = v.replace(second=0)
            return v

        if isinstance(value, (list, tuple)):
            return [_replace(x) for x in value]

        return _replace(value)

    def get_default_value(self, **kwargs):
        if callable(self.default_value):
            value = self.default_value()
        else:
            value = self.default_value

        value = self.time_replace(value)

        cond = getattr(self, 'default_condition', None)

        if cond and cond == 'range':
            if not isinstance(value, (list, tuple)):
                value = date_format(value, '%s' % self.format)
                return (value, value)

        return date_format(value, '%s' % self.format)

    def get_default_server_value(self, **kwargs):
        if callable(self.default_value):
            value = self.default_value()
        else:
            value = self.default_value

        value = self.time_replace(value)

        cond = getattr(self, 'default_condition', None)

        if cond and cond == 'range':
            if not isinstance(value, (list, tuple)):
                return (value, value)
            else:
                return value
        return value

class FilterDateTime(BaseDateTime):
    _type = 'datetime'
    withseconds = False
    use_tz = conf.settings.USE_TZ

    default_value = lambda s: timezone.now()

    formatDate = DATE_FORMAT

    @property
    def format(self):
        if self.withseconds:
            return DATETIME_FORMAT_SEC
        return DATETIME_FORMAT

    @property
    def formatTime(self):
        if self.withseconds:
            return TIME_FORMAT_SEC
        return TIME_FORMAT

    def get_value(self, condition, value, request=None):
        if isinstance(value, six.string_types):
            value = parse_datetime(value)
        elif isinstance(value, (list, tuple)):
            _value = list(set([ parse_datetime(v) for v in value ]))
            if len(_value) == len(value):
                value = _value
            else:
                value = None
        if value is None:
            raise ValueError('One or more values not valid in `%s` filter.' % force_text(self))
        if condition == 'range':
            value = [min(value), max(value)]
        return value

class FilterDate(BaseDateTime):
    _type = 'date'
    format = DATE_FORMAT
    default_value = lambda s: timezone.localtime(timezone.now()).date()

    def get_value(self, condition, value, request=None):
        if isinstance(value, six.string_types):
            value = parse_date(value)
        elif isinstance(value, (list, tuple)):
            _value = list(set([ parse_date(v) for v in value ]))
            if len(_value) == len(value):
                value = _value
            else:
                value = None
        if value is None:
            raise ValueError('One or more values not valid in `%s` filter.' % force_text(self))
        if condition == 'range':
            value = [min(value), max(value)]
        return value

class FilterTime(BaseDateTime):
    _type = 'time'
    withseconds = False
    default_value = lambda s: timezone.localtime(timezone.now()).time()

    @property
    def format(self):
        if self.withseconds:
            return TIME_FORMAT_SEC
        return TIME_FORMAT

    def get_value(self, condition, value, request=None):
        if isinstance(value, six.string_types):
            value = parse_time(value)
        elif isinstance(value, (list, tuple)):
            _value = list(set([ parse_time(v) for v in value ]))
            if len(_value) == len(value):
                value = _value
            else:
                value = None
        if value is None:
            raise ValueError('One or more values not valid in `%s` filter.' % force_text(self))
        if condition == 'range':
            value = [min(value), max(value)]
        return value

class FilterBoolean(BaseFilter):
    _type = 'boolean'
    conditions = None
    usenone = True
    default_value = None
    default_condition = 'truth'

    def __init__(self, name, usenone=None, **kwargs):
        super(FilterBoolean, self).__init__(name=name, **kwargs)

        if not usenone is None:
            self.usenone = usenone
            if self.default_value is None:
                self.required = True

class FilterChoice(BaseFilter):
    _type = 'choice'
    conditions = ('exact', 'gt', 'gte', 'lt', 'lte', 'range', 'in')
    placeholder = _('Choice')
    keytype = int
    _options = None

    def __init__(self, name, options=None, **kwargs):
        if options:
            self._options = dict(options)
        elif not hasattr(self, '_options'):
            self._options = {}
        super(FilterChoice, self).__init__(name=name, **kwargs)

    @property
    def options(self):
        return [ {'value':x,'label':y} for x,y in self._options.items() ]

    def get_value_label(self, condition, value, request=None):
        dic = self._options
        if condition in ('range', 'in'):
            return [ dic[self.keytype(x)] for x in set(list(value)) if self.keytype(x) in dic ]
        else:
            return dic.get(self.keytype(value), None)

    def get_value(self, condition, value, request=None):
        dic = self._options
        if condition in ('range', 'in'):
            value = [ self.keytype(x) for x in set(list(value)) if self.keytype(x) in dic ]
            if condition == 'range':
                value = [min(value), max(value)]
            return value
        else:
            return self.keytype(value)

class FilterChoiceStr(FilterChoice):
    keytype = six.text_type

class FilterWeekDay(FilterChoice):
    _type = 'weekday'
    placeholder = _('Select weekday')
    _options = WEEKDAYS

class FilterMonth(FilterChoice):
    _type = 'month'
    placeholder = _('Select month')
    _options = MONTHS

PERIODS = {
        'today': _('Today'),
        'tomorrow': _('Tomorrow'),
        'tomorrow2': _('Day after tomorrow'),
        'yesterday': _('Yesterday'),
        'yesterday2': _('Two days ago'),

        'next2days': _('Next two days'),
        'next3days': _('Next three days'),
        'last2days': _('Last two days'),
        'last3days': _('Last three days'),

        'week': _('Current week'),
        'next_week': _('Next week'),
        'previous_week': _('Previous week'),

        'month': _('Current month'),
        'next_month': _('Next month'),
        'previous_month': _('Previous month'),

        'quarter1': _('First quarter'),
        'quarter2': _('Second quarter'),
        'quarter3': _('Third quarter'),
        'quarter4': _('Fourth quarter'),

        'halfyear1': _('First half year'),
        'halfyear2': _('Second half year'),

        'year': _('Current year'),
        'next_year': _('Next year'),
        'previous_year': _('Previous year'),
    }

# test
for x in PERIODS.keys():
    if not hasattr(periods, x):
        raise PeriodsError(_('Function `%s` not found in reportapi.utils.periods') % x)

class FilterPeriod(FilterChoice):
    _type = 'period'
    placeholder = _('Select period')
    conditions = ('exact',)
    keytype = str
    _options = PERIODS
    withtime = True

    def get_value_label(self, condition, value, request=None):
        return self._options.get(self.keytype(value), None)

    def get_value(self, condition, value, request=None):
        """
        Если периоды втроенные, то для них есть функции получения
        объектов datetime. Если нет, то программист должен сам
        обработать это значение при формировании отчёта.
        """
        if value in PERIODS:
            f = getattr(periods, value)
            return f(withtime=self.withtime)
        return value

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
        orm_lookups = [construct_search(force_text(search_field))
                       for search_field in fields]
        if not query in ('', None, False, True):
            for bit in query.split():
                or_queries = [Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))

    return queryset

date_re = re.compile(
    r'(?P<year>\d{4})-?(?P<month>\d{2})?-?(?P<day>\d{2})?$'
)

def _date_search_in_fields(queryset, fields, query, regexp=date_re):
    """ Фильтрация по дате"""
    query = query.strip()
    match = regexp.match(query)

    if match and fields:

        kv = list((k, int(v)) for k, v in match.groupdict().iteritems() if v)

        for name in fields:
            for k,v in kv:
                queryset = queryset.filter(**{"%s__%s" % (name, k): v})

    return queryset
