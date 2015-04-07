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

import copy
import json

from django.forms import CharField
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields import TextField
from django.utils import six
from django.utils.translation import ugettext_lazy as _


class JSONFormField(CharField):
    default_error_messages = {
        'invalid': _('Enter a valid JSON.'),
    }

    def to_python(self, value):
        if isinstance(value, six.string_types):
            try:
                return json.loads(value, **self.load_kwargs)
            except ValueError:
                raise ValidationError(self.error_messages['invalid'], code='invalid')
        return value

    def clean(self, value):

        if not value and not self.required:
            return None

        # Trap cleaning errors & bubble them up as JSON errors
        try:
            return super(JSONFormField, self).clean(value)
        except TypeError:
            raise ValidationError(self.error_messages['invalid'], code='invalid')


class JSONField(TextField):
    """
    JSONField is a generic textfield that serializes/deserializes
    JSON objects: '{...}', '[...]' and 'null'.
    Other objects do not validate.
    """

    description = _("JSON data")
    form_class = JSONFormField

    def __init__(self, *args, **kwargs):

        self.dump_kwargs = kwargs.pop('dump_kwargs', {
            'cls': DjangoJSONEncoder,
            'separators': (',', ':')
        })

        self.load_kwargs = kwargs.pop('load_kwargs', {})

        super(JSONField, self).__init__(*args, **kwargs)

    def _json_loads(self, value):
        try:
            return json.loads(value, **self.load_kwargs)
        except ValueError:
            raise ValidationError(_("Enter a valid JSON."))

    def from_db_value(self, value, expression, connection, context):
        """
        When the data is loaded from the database, including in 
        aggregates and values() calls. 
        """

        if value is None: return value

        if isinstance(value, six.string_types):
            return self._json_loads(value)

        return value

    def to_python(self, value):
        """
        Convert string to python if necessary.
        """
        if value is None or isinstance(value, (list, dict, tuple)):
            return value

        if isinstance(value, six.string_types):
            return self._json_loads(value)

        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        """
        Convert JSON object to a string
        """

        if self.null and value is None:
            return None

        return json.dumps(value, **self.dump_kwargs)

    def get_prep_value(self, value):

        value = super(JSONField, self).get_prep_value(value)

        if isinstance(value, six.string_types) or value is None:
            return value

        return json.dumps(value)

    def get_prep_lookup(self, lookup_type, value):
        """
        We only handle 'exact', 'isnull' and 'in'.
        All others are errors.
        """
        if lookup_type in ('exact', 'isnull'):
            return self.get_prep_value(value)
        elif lookup_type == 'in':
            return [self.get_prep_value(v) for v in value]
        else:
            raise TypeError('Lookup type %r not supported.' % lookup_type)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value, None)

    def value_from_object(self, obj):

        value = super(JSONField, self).value_from_object(obj)

        if self.null and value is None:
            return None

        return self.dumps_for_display(value)

    def dumps_for_display(self, value):

        kwargs = { "indent": 2, 'ensure_ascii': False }

        kwargs.update(self.dump_kwargs)

        return json.dumps(value, **kwargs)

    def get_default(self):
        """
        Returns the default value for this field.

        The default implementation on models.Field calls force_unicode
        on the default, which means you can't set arbitrary Python
        objects as the default. To fix this, we just return the value
        without calling force_unicode on it. Note that if you set a
        callable as a default, the field will still call it. It will
        *not* try to pickle and encode it.

        """
        if self.has_default():

            if callable(self.default):
                return self.default()

            return copy.deepcopy(self.default)

        # If the field doesn't have a default, then we punt to models.Field.
        return super(JSONField, self).get_default()

    def formfield(self, **kwargs):

        defaults = {'form_class': self.form_class, 'widget': JSONFormField}

        defaults.update(kwargs)

        field = super(JSONField, self).formfield(**defaults)

        if isinstance(field, JSONFormField):
            field.load_kwargs = self.load_kwargs

        if not field.help_text:
            field.help_text = _("Enter a valid JSON.")

        return field

    def db_type(self, connection):
        """
        Automatic select better type.
        """
        if connection.vendor == 'postgresql':
            if connection.pg_version >= 90400:
                return 'jsonb'
            elif connection.pg_version >= 90300:
                return 'json'

        return 'text'


