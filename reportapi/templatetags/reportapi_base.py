# -*- coding: utf-8 -*-
#
#  reportapi/templatetags/reportapi_base.py
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
from django.template import Library
from django.utils.translation import ugettext_lazy as _

from reportapi import conf

register = Library()

@register.simple_tag
def SETTINGS(key):
    return getattr(conf, key, getattr(conf.settings, key, ''))

@register.simple_tag
def mini_library():
    if conf.settings.DEBUG:
        return ''
    return '.min'

@register.simple_tag
def short_username(user):
    if user.is_anonymous():
        return _('Anonymous')
    if not user.last_name and not user.first_name:
        return user.username
    return '%s %s.' % (user.last_name, unicode(user.first_name)[0])

@register.simple_tag
def full_username(user):
    if user.is_anonymous():
        return _('Anonymous')
    if not user.last_name and not user.first_name:
        return user.username
    return '%s %s' % (user.last_name, user.first_name)

@register.filter
def multiply(obj, digit):
    if obj is None:
        return 0
    try:
        return obj * digit
    except:
        return 'filter error'

@register.filter
def divide(obj, digit):
    if obj is None or digit == 0:
        return 0
    try:
        return 1.0 * obj / digit
    except:
        return 'filter error'
