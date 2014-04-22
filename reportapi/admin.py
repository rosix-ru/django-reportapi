# -*- coding: utf-8 -*-
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
    list_display = ('register', 'id')
    search_fields = ['register__title', 'id']
    list_filter = ('register__section', 'register__title')
    raw_id_fields = ('register', 'user')
    ordering = ['-end', 'start']
admin.site.register(Document, DocumentAdmin)
