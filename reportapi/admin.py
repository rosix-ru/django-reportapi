# -*- coding: utf-8 -*-
#
#  reportapi/admin.py
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
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from .models import *

class RegisterAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'section', 'name', 'timeout', 'id')
    search_fields = ['title', 'id']
    list_filter = ('section',)
    filter_horizontal = ('users', 'groups')
    ordering = ['title']
admin.site.register(Register, RegisterAdmin)

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('register', 'user', 'start', 'end', 'id')
    search_fields = ['register__title', 'id']
    list_filter = ('register__section', 'register__title')
    raw_id_fields = ('user',)
    ordering = ['-end', 'start']
admin.site.register(Document, DocumentAdmin)
