# -*- coding: utf-8 -*-
#
#  reportapi/fields.py
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
import json as jsonlib

from django.db.models import SubfieldBase, TextField
from django.conf import settings
from quickapi.http import JSONEncoder

class InternalJSONField(TextField):
    __metaclass__ = SubfieldBase

    def contribute_to_class(self, cls, name):
        super(InternalJSONField, self).contribute_to_class(cls, name)

        def get_json(model):
            return self.get_db_prep_value(getattr(model, self.attname))
        setattr(cls, 'get_%s_json' % self.name, get_json)

        def set_json(model, json):
            setattr(model, self.attname, self.to_python(json))
        setattr(cls, 'set_%s_json' % self.name, set_json)

    def formfield(self, **kwargs):
        kwargs['widget'] = JSONWidget(attrs={'class': 'vLargeTextField'})
        return super(InternalJSONField, self).formfield(**kwargs)

    def get_db_prep_save(self, value, **kwargs):
        """Convert our JSON object to a string before we save"""

        if value == "":
            return None

        if isinstance(value, dict):
            value = jsonlib.dumps(value, cls=JSONEncoder)

        return super(InternalJSONField, self).get_db_prep_save(value, **kwargs)

    def to_python(self, value, **kwargs):
        """Convert our string value to JSON after we load it from the DB"""

        if value == "":
            return None

        if not isinstance(value, basestring):
            return value

        try:
            return jsonlib.loads(value, encoding=settings.DEFAULT_CHARSET)
        except ValueError, e:
            # If string could not parse as JSON it's means that it's Python
            # string saved to JSONField.
            return value

try:
    from jsonfield import JSONField
except:
    JSONField = InternalJSONField
