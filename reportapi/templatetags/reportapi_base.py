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
from django import template
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from reportapi import conf

register = template.Library()

@register.simple_tag
def SETTINGS(key):
    return getattr(conf, key, getattr(conf.settings, key, ''))

@register.simple_tag
def mini_library():
    if conf.settings.DEBUG:
        return ''
    return '.min'

@register.simple_tag
def navactive(request, urls):
    if request.path in ( reverse(url) for url in urls.split() ):
        return "active"
    return ""

@register.simple_tag
def subnavactive(request, key, val=None):
    if val == None and (key in request.GET):
        return "active"
    if (val in ('', 0)) and (key not in request.GET):
        return "active"
    if key in request.GET:
        if isinstance(val, int):
            try:
                get_val = int(request.GET.get(key))
            except:
                get_val = None
        if isinstance(val, str):
            try:
                get_val = str(request.GET.get(key))
            except:
                get_val = None
        if get_val == val:
                return "active"
    return ""

@register.simple_tag
def addGET(request, key, val=''):
    dic = request.GET.copy()
    if val:
        dic[key] = val
    else:
        try:
            del dic[key]
        except:
            pass
    L = ['%s=%s' % (k, v) for k,v in dic.items()] 
    return "?" + '&'.join(L)

@register.simple_tag
def short_username(user):
    if user.is_anonymous():
        return _('Anonymous')
    if not user.last_name and not user.first_name:
        return user.username
    return u'%s %s.' % (user.last_name, unicode(user.first_name)[0])

@register.simple_tag
def full_username(user):
    if user.is_anonymous():
        return _('Anonymous')
    if not user.last_name and not user.first_name:
        return user.username
    return u'%s %s' % (user.last_name, user.first_name)

@register.simple_tag
def pagination(request, paginator):
    """ paginator.paginator.count
        paginator.paginator.num_pages
        paginator.paginator.page_range
        paginator.object_list
        paginator.number
        paginator.has_next()
        paginator.has_previous()
        paginator.has_other_pages()
        paginator.next_page_number()
        paginator.previous_page_number()
        paginator.start_index()
        paginator.end_index()
    """
    temp = '<li class="%s"><a href="%s">%s</a></li>'
    number = paginator.number
    num_pages = paginator.paginator.num_pages
    DOT = '.'
    ON_EACH_SIDE = 3
    ON_ENDS = 2
    page_range = paginator.paginator.page_range
    if num_pages > 9:
        page_range = []
        if number > (ON_EACH_SIDE + ON_ENDS):
            page_range.extend(range(1, ON_EACH_SIDE))
            page_range.append(DOT)
            page_range.extend(range(number +1 - ON_EACH_SIDE, number + 1))
        else:
            page_range.extend(range(1, number + 1))
        if number < (num_pages - ON_EACH_SIDE - ON_ENDS + 1):
            page_range.extend(range(number + 1, number + ON_EACH_SIDE))
            page_range.append(DOT)
            page_range.extend(range(num_pages - ON_ENDS +1, num_pages+1))
        else:
            page_range.extend(range(number + 1, num_pages+1))
    L = []
    for num in page_range:
        css = ""
        link = '#'
        if num == DOT:
            css = "disabled"
            num = '...'
        elif num == paginator.number:
            css = "active"
        else:
            link = addGET(request, 'page', num)
        L.append(temp % (css, link, num))
    return u''.join(L)

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
