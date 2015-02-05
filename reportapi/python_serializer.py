# -*- coding: utf-8 -*-
#
#  reportapi/python_serializer.py
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
from StringIO import StringIO
from types import MethodType

from django.db import models
from django.core.paginator import Page
from django.core.serializers.python import Serializer as OrignSerializer
from django.utils.encoding import force_text


class SerializerWrapper(object):
    """ Обёртка вокруг базовых классов Django.
        Переопределяет их методы.
    """
    def handle_field(self, obj, field):
        value = field._get_val_from_obj(obj)
        self._current[field.name] = value
        return value

    def handle_property(self, obj, name):
        if hasattr(obj, name):
            value = getattr(obj, name)
        elif '__' in name and not name.startswith('_'): 
            names = name.split('__')
            o = obj
            for n in names:
                value = getattr(o, n)
                o = value
        else:
            raise AttributeError(name)

        if callable(value):
            value = value()
        if isinstance(value, models.Model):
            app, model = force_text(value._meta).split('.')
            value = {
                self.unicode_key: force_text(value),
                'pk': value.pk,
                'app': app,
                'model': model,
            }
        self._current[name] = value
        return value

    def handle_fk_field(self, obj, field):
        if obj.pk:
            related = getattr(obj, field.name)
            if related:
                #~ value = (related.pk, force_text(related))
                app, model = force_text(related._meta).split('.')
                value = {
                    self.unicode_key: force_text(related),
                    'pk': related.pk,
                    'app': app,
                    'model': model,
                }
            else:
                value = None
        else:
            value = getattr(obj, field.get_attname())
            rel_model = field.rel.to
            try:
                related = rel_model._default_manager.get(pk=value)
                #~ value = (related.pk, force_text(related))
                app, model = force_text(related._meta).split('.')
                value = {
                    self.unicode_key: force_text(related),
                    'pk': related.pk,
                    'app': app,
                    'model': model,
                }
            except:
                value = None

        self._current[field.name] = value
        return value

    def handle_m2m_field(self, obj, field):
        value = []
        if obj.pk and field.rel.through._meta.auto_created:
            #~ m2m_value = lambda value: (value.pk, force_text(value))
            app, model = force_text(field.rel.through._meta).split('.')
            def m2m_value(related):
                return {
                    self.unicode_key: force_text(related),
                    'pk': related.pk,
                    'app': app,
                    'model': model,
                }
            value = [m2m_value(related)
                            for related in getattr(obj, field.name).iterator()]

        self._current[field.name] = value
        return value

    def serialize_objects(self, objects, **options):
        """
        Практически в точности копирует оригинальный метод serialize,
        но не запускает в конце метод окончания сериализации
        """

        self.stream = options.pop("stream", StringIO())
        self.attrs = options.pop("attrs", [])
        self.unicode_key = options.pop("unicode_key", '__unicode__')
        # Простой список для <select> в HTML: ключ и сроковое представление
        self.simple_select_list = options.pop("simple_select_list", False)
        if self.simple_select_list:
            self.attrs = []

        self.start_serialization()

        if isinstance(objects, models.Model):
            opts = objects._meta
            objects = [objects]
        else:
            opts = objects.model._meta
            objects = objects.select_related()

        local_fields = [x.name for x in opts.local_fields]
        many_to_many = [x.name for x in opts.many_to_many]

        for obj in objects:

            self.start_object(obj)

            for attr in self.attrs:
                if attr in local_fields:
                    field = opts.local_fields[local_fields.index(attr)]
                    if field.rel is None:
                        self.handle_field(obj, field)
                    else:
                        self.handle_fk_field(obj, field)
                elif attr in many_to_many:
                    field = opts.many_to_many[many_to_many.index(attr)]
                    self.handle_m2m_field(obj, field)
                elif not attr in ('pk', '__unicode__', '__str__'):
                    self.handle_property(obj, attr)

            self.end_object(obj)

        return self.objects

    def serialize(self, objects, **options):
        """
        Serialize a Model insnance, QuerySet or page of Paginator.
        """
        if isinstance(objects, Page):
            result = {}
            wanted = ("end_index", "has_next", "has_other_pages", "has_previous",
                    "next_page_number", "number", "start_index", "previous_page_number")
            for attr in wanted:
                v = getattr(objects, attr)
                if isinstance(v, MethodType):
                    try:
                        result[attr] = v()
                    except:
                        result[attr] = None
                elif isinstance(v, (str, int)):
                    result[attr] = v
            result['count']       = objects.paginator.count
            result['num_pages']   = objects.paginator.num_pages
            result['per_page']    = objects.paginator.per_page
            result['object_list'] = self.serialize_objects(objects.object_list, **options)
            self.objects = result
        else:
            self.serialize_objects(objects, **options)

        self.end_serialization() # Окончательно сериализуем
        value = self.getvalue()

        if isinstance(objects, models.Model):
            return value[0]
        else:
            return value

    def start_object(self, obj):
        self._current = {}

    def end_object(self, obj):
        _unicode = ""
        try:
            _unicode = force_text(obj)
        except:
            pass
        pk = force_text(obj._get_pk_val())
        if self.simple_select_list:
            self._current = (pk, _unicode)
        else:
            self._current[self.unicode_key] = _unicode
            self._current["pk"] = pk
        self.objects.append(self._current)
        self._current = None

class Serializer(SerializerWrapper, OrignSerializer):
    """
    Serializes a QuerySet or page of Paginator to basic Python objects.
    """
    pass

def serialize(queryset, **options):
    """
    Serialize a queryset (or any iterator that returns database objects).
    """
    s = Serializer()
    s.serialize(queryset, **options)
    return s.getvalue()
