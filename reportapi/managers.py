# -*- coding: utf-8 -*-
#
#  reportapi/managers.py
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

from django.utils.translation import ugettext_lazy as _
from django.utils import six
from django.db import models

from reportapi.conf import REPORTAPI_DOCUMENT_MANAGER as CustomManager

class DefaultDocumentManager(models.Manager):
    use_for_related_fields = True

    def new(self, request, **kwargs):
        """
        Analog Document(user=user, code=code, register=register),
        but in another Manager here you can define restrictions by request
        """
        return self.model(**kwargs)

    def permitted(self, request):
        user = request.user
        if not user.is_authenticated():
            return self.get_query_set().none()
        if user.is_superuser:
            return self.get_query_set()
        return self.get_query_set().filter(
            Q(register__all_users=True)
            | Q(register__users=user)
            | Q(register__groups__in=user.groups.all())
        )

    def del_permitted(self, request):
        user = request.user
        if not user.is_authenticated():
            return self.get_query_set().none()
        if user.is_superuser:
            return self.get_query_set().all()
        return self.get_query_set().filter(user=user).all()

if CustomManager:
    if isinstance(CustomManager, six.string_types):
        from django.utils.importlib import import_module

        split = CustomManager.split('.')
        module = '.'.join(split[:-1])
        klass  = split[-1]

        m = import_module(module)

        DocumentManager = getattr(m, klass)
    else:
        DocumentManager = CustomManager
else:
    DocumentManager = DefaultDocumentManager
