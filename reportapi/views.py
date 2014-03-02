# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2012 Grigoriy Kramarenko.
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
from django.contrib.auth import authenticate, login
from django.core.mail import mail_admins
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from datetime import timedelta
import os, datetime, hashlib

from quickapi.views import api as quickapi_index, get_methods
from quickapi.decorators import login_required, api_required

from reportapi.sites import site
from reportapi.conf import (settings, REPORTAPI_FILES_UNIDECODE,
    REPORTAPI_ENABLE_THREADS)
from reportapi.models import Report, Register, Document

class PermissionError(Exception):
    message = _('Access denied')

########################################################################
# Views for URLs
########################################################################

@login_required
def index(request):
    ctx = {}
    
    return render_to_response('reportapi/index.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def report_list(request, section):
    ctx = {}
    
    return render_to_response('reportapi/report_list.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def documents(request, section=None, name=None):
    ctx = {}
    
    return render_to_response('reportapi/documents.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def report(request, name):
    ctx = {}
    
    return render_to_response('reportapi/report.html', ctx,
                            context_instance=RequestContext(request,))

########################################################################
# Additional functions
########################################################################

def create_document(request, report, document, filters):
    """ Создание отчёта """
    try:
        report.render(request, document, filters)
    except Exception as e:
        document.error = unicode(e)
    document.end = timezone.now()
    document.save()
    return document

def result(document, old=False):
    result = {
        'id': document.id,
        'start': document.start,
        'end': document.end,
        'user': document.user,
        'error': document.error or None,
    }
    if old:
        result['old'] = True
    if document.end:
        document.url
    return JSONResponse(data=result)

########################################################################
# API
########################################################################

@api_required
@login_required
def API_create_document(request, name, filters=None, force=False, **kwargs):
    """ *Запускает процесс создания отчёта и/или возвращает информацию
        об уже запущенном процессе.*

        ####ЗАПРОС. Параметры:

        1. "name"    - идентификационное название отчёта;
        2. "filters" - фильтры для обработки результата (необязательно);
        3. "force"   - принудительное создание отчёта (необязательно).

        ####ОТВЕТ. Формат ключа "data":
        Информация о процессе

        ```
        #!javascript
        {
            "id": 1,
            "start": "2014-01-01T10:00:00+0000",
            "user": "Гадя Петрович Хренова",
            "end": null, // либо дата создания
            "url": "",
            "old": null, // true, когда взят уже существующий старый отчёт
            "error": null, // или описание ошибки
        }
        ```

    """
    user = request.user
    session = request.session

    report, register = site.get_report_and_register(request, name)
    if not report or not register:
        raise PermissionError()

    code = report.get_code(request, filters)
    expired = timezone.now() - timedelta(seconds=report.expiration_time)

    all_documents = register.document_set.filter(code=code)
    proc_documents = all_documents.filter(end__isnull=True)
    last_documents = all_documents.filter(end__gt=expired)

    if proc_documents:
        # Создающийся отчёт
        return result(proc_documents[0])
    elif last_documents and (not force or not report.create_force):
        # Готовый отчёт
        return result(last_documents[0], old=True)
    else:
        # Новый отчёт
        document = Document(user=user, code=code)
        document.save()

        func_kwargs = {
            'filters': filters,
            'document': document,
            'report': report
        }

        if report.enable_threads and REPORTAPI_ENABLE_THREADS:
            # Создание нового потока в режиме демона
            t = threading.Thread(target=create_document, kwargs=func_kwargs)
            t.setDaemon(True)
            t.start()
            return result(document)
        else:
            # Последовательное создание отчёта
            r = create_document(**func_kwargs)
            return result(document)

@api_required
@login_required
def API_document_info(request, id, **kwargs):
    """ *Возвращает информацию об определённом запущенном или
        завершённом отчёте по заданному идентификационному номеру.*

        ####ЗАПРОС. Параметры:

        1. "id" - идентификатор отчёта;

        ####ОТВЕТ. Формат ключа "data":
        Информация о процессе формирования отчёта

        ```
        #!javascript
        {
            "id": 1,
            "start": "2014-01-01T10:00:00+0000",
            "user": "Гадя Петрович Хренова",
            "end": null, // либо дата создания
            "url": "",
            "error": null, // или описание ошибки
        }
        ```

    """
    user = request.user
    all_documents = Document.objects.permitted(request)
    try:
        document = all_documents.get(id=id)
    except:
        return JSONResponse(status=404)
    else:
        return result(document)

@api_required
@login_required
def API_search(request, name, filter_name, query=None, page=1, **kwargs):
    """ *Производит поиск для заполнения фильтра экземпляром связанной
        модели.*

        ####ЗАПРОС. Параметры:

        1. "name" - идентификационное название отчёта;
        2. "filter_name" - имя фильтра для связанной модели;
        3. "query" - поисковый запрос;
        4. "page" - номер страницы;

        ####ОТВЕТ. Формат ключа "data":
        Сериализованный объект страницы паджинатора

        ```
        #!javascript
        {
            "object_list": [[1, "First object"], [1, "Second object"]],
            "number": 2,
            "count": 99,
            "per_page": 10
            "num_pages": 10,
            "page_range": [1,2,3,'...',9,10],
            "start_index": 1,
            "end_index": 10,
            "has_previous": true,
            "has_next": true,
            "has_other_pages": true,
            "previous_page_number": 1,
            "next_page_number": 3,
        }
        ```
        Это стандартный вывод, который может быть переопределён
        отдельно для каждого отчёта.

    """
    user = request.user
    report = site.get_report(request, name)
    _filter = report.get_filter(filter_name)
    if not hasattr(_filter, 'search'):
        return JSONResponse(status=400)
    data = _filter.search(query, page)
    return JSONResponse(data=data)


_methods = [
    ('create_document', API_create_document),
    ('document_info', API_document_info),
    ('search', API_search),
]

# store prepared methods
METHODS = get_methods(_methods)

@csrf_exempt
def api(request):
    return quickapi_index(request, methods=METHODS)
