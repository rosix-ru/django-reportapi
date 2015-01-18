# -*- coding: utf-8 -*-
#
#  reportapi/routers.py
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

from django.conf import settings

DEFAULT = 'default'

if not 'default' in settings.DATABASES.keys():
    DEFAULT = [ x for x in settings.DATABASES.keys() if x.startswith('master') ][0]

class Router(object):
    """
    A router to control all database operations on models in the
    reportapi application.
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'reportapi':
            return DEFAULT
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'reportapi':
            return DEFAULT
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'reportapi' or \
           obj2._meta.app_label == 'reportapi':
           return True
        return None

    def allow_migrate(self, db, model):
        """
        Make sure the reportapi app only appears in the 'default'
        database.
        """
        if db == DEFAULT:
            return model._meta.app_label == 'reportapi'
        elif model._meta.app_label == 'reportapi':
            return False
        return None
