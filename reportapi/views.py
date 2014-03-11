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
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from datetime import timedelta
import os, datetime, hashlib

from quickapi.http import JSONResponse, tojson
from quickapi.views import api as quickapi_index, get_methods
from quickapi.decorators import login_required, api_required

from reportapi.sites import site
from reportapi.conf import (settings, REPORTAPI_FILES_UNIDECODE,
    REPORTAPI_ENABLE_THREADS, REPORTAPI_DEFAULT_FORMAT)
from reportapi.models import Report, Register, Document

DOCS_PER_PAGE = 25

class PermissionError(Exception):
    message = _('Access denied')

########################################################################
# Views for URLs
########################################################################

@login_required
def index(request):
    ctx = _default_context(request)
    return render_to_response('reportapi/index.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def report_list(request, section):
    ctx = _default_context(request)
    if not section in site.sections:
        return render_to_response('reportapi/404.html', ctx,
                            context_instance=RequestContext(request,))
    ctx['section'] = site.sections[section]

    docs = Document.objects.permitted(request).all()
    docs = docs.filter(register__section=section)
    ctx['last_docs'] = docs[:DOCS_PER_PAGE]

    ctx['reports'] = site.sections[section].get_reports(request)

    return render_to_response('reportapi/report_list.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def documents(request, section=None, name=None):
    """
    """
    ctx = _default_context(request)
    docs = Document.objects.permitted(request).all()
    if section:
        docs = docs.filter(register__section=section)
    if section and name:
        docs = docs.filter(register__name=name)
    ctx['docs'] = docs[:DOCS_PER_PAGE]

    return render_to_response('reportapi/documents.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def report(request, section, name):
    ctx = _default_context(request)
    report, register = site.get_report_and_register(request, section, name)
    if not report or not register:
        return render_to_response('reportapi/404.html', ctx,
                            context_instance=RequestContext(request,))

    ctx['report_as_json'] = tojson(report.get_scheme(request) or dict())
    ctx['report'] = report

    return render_to_response('reportapi/report.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def get_document(request, pk, format=None):
    ctx = _default_context(request)
    try:
        doc = Document.objects.permitted(request).get(pk=pk)
    except:
        return render_to_response('reportapi/404.html', ctx,
                            context_instance=RequestContext(request,))

    if format:
        url = doc.format_url(format)
    else:
        url = doc.url
    if url:
        return HttpResponseRedirect(url)

    return render_to_response('reportapi/404.html', ctx,
                            context_instance=RequestContext(request,))

########################################################################
# Additional functions
########################################################################

def _default_context(request):
    ctx = {}
    ctx['sections'] = site.get_sections(request)
    docs = Document.objects.permitted(request).all()
    #~ docs_user = docs.filter(user=request.user)
    ctx['last_docs'] = docs[:DOCS_PER_PAGE]
    #~ ctx['last_docs_user'] = docs_user[:DOCS_PER_PAGE]
    ctx['DEFAULT_FORMAT'] = REPORTAPI_DEFAULT_FORMAT
    return ctx

def create_document(request, report, document, filters):
    """ Создание отчёта """
    try:
        report.render(request, document, filters)
    except Exception as e:
        document.error = unicode(e)
    document.end = timezone.now()
    document.save()
    if not document.error:
        delta = document.end - document.start
        ms = int(delta.total_seconds() *1000)
        register = document.register
        if register.timeout < ms:
            register.timeout = ms
            register.save()

    return document

def result(document, old=False):
    result = {
        'id': document.id,
        'start': document.start,
        'end': document.end,
        'user': document.user.get_full_name() or document.user.username,
        'error': document.error or None,
        'timeout': document.register.timeout,
    }
    if old:
        result['old'] = True
    if document.end:
        result['url'] = document.get_absolute_url()
    return JSONResponse(data=result)

########################################################################
# API
########################################################################

@api_required
@login_required
def API_get_scheme(request, **kwargs):
    """ *Возвращает схему ReportAPI для пользователя.*

        ####ЗАПРОС. Без параметров.

        ####ОТВЕТ. Формат ключа "data":
        Схема
    """
    data = site.get_scheme(request)
    return JSONResponse(data=data)

@api_required
@login_required
def API_create_document(request, section, name, filters=None, force=False, **kwargs):
    """ *Запускает процесс создания отчёта и/или возвращает информацию
        об уже запущенном процессе.*

        ####ЗАПРОС. Параметры:

        1. "section" - идентификационное название раздела;
        2. "name"    - идентификационное название отчёта;
        3. "filters" - фильтры для обработки результата (необязательно);
        4. "force"   - принудительное создание отчёта (необязательно).

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
            "timeout": 5000, // расчётное время ожидания результата в милисекундах 
        }
        ```

    """
    user = request.user
    session = request.session

    report, register = site.get_report_and_register(request, section, name)
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
        document = Document(user=user, code=code, register=register)
        document.save()

        func_kwargs = {
            'request': request,
            'filters': filters,
            'document': document,
            'report': report,
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
def API_object_search(request, section, name, filter_name, query=None, page=1, **kwargs):
    """ *Производит поиск для заполнения объектного фильтра экземпляром
        связанной модели.*

        ####ЗАПРОС. Параметры:

        1. "section" - идентификационное название раздела;
        2. "name"    - идентификационное название отчёта;
        3. "filter_name" - имя фильтра для связанной модели;
        4. "query" - поисковый запрос (необязательно);
        5. "page" - номер страницы (необязательно);

        ####ОТВЕТ. Формат ключа "data":
        Сериализованный объект страницы паджинатора

        ```
        #!javascript
        {
            "object_list": [
                {"pk": 1, "__unicode__": "First object"},
                {"pk": 2, "__unicode__": "Second object"}
            ],
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
    report = site.get_report(request, section, name)
    if not report:
        return JSONResponse(status=404)
    _filter = report.get_filter(filter_name)
    if not hasattr(_filter, 'search'):
        return JSONResponse(status=400)
    data = _filter.search(query, page)
    return JSONResponse(data=data)


_methods = [
    ('reportapi.get_scheme', API_get_scheme),
    ('reportapi.create_document', API_create_document),
    ('reportapi.document_info', API_document_info),
    ('reportapi.object_search', API_object_search),
]

# store prepared methods
METHODS = get_methods(_methods)

@csrf_exempt
def api(request):
    return quickapi_index(request, methods=METHODS)
