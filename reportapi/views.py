# -*- coding: utf-8 -*-
#
#  reportapi/views.py
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
from __future__ import unicode_literals, print_function
import os, sys, traceback, threading

from django.utils.encoding import smart_text
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
#~ from django.utils import translation
from django.utils.translation import get_language, ugettext_lazy as _

from quickapi.http import JSONResponse, tojson
from quickapi.views import api as quickapi_index, get_methods
from quickapi.decorators import login_required, api_required

from reportapi.sites import site
from reportapi.conf import (settings, REPORTAPI_DEBUG,
    REPORTAPI_FILES_UNIDECODE, REPORTAPI_ENABLE_THREADS,
    REPORTAPI_LANGUAGES)
from reportapi.models import Register, Document
from reportapi.exceptions import ExceptionReporterExt, PermissionError

DOCS_PER_PAGE = 25

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
    ctx['docs'] = docs[:DOCS_PER_PAGE]

    ctx['reports'] = site.sections[section].get_reports(request)

    return render_to_response('reportapi/report_list.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def documents(request, section=None, name=None):
    """
    Returns inner html with founded documents
    """
    ctx = _default_context(request)

    docs = Document.objects.permitted(request).all()

    if section:
        ctx['section'] = site.sections.get(section, None)
        if not ctx['section'] or not ctx['section'].has_permission(request):
            return render_to_response('reportapi/404.html', ctx,
                            context_instance=RequestContext(request,))
        docs = docs.filter(register__section=section)

    if section and name:
        report, register = site.get_report_and_register(request, section, name)
        if not report or not register:
            return render_to_response('reportapi/404.html', ctx,
                            context_instance=RequestContext(request,))
        ctx['report'] = report
        docs = docs.filter(register__name=name)

    ctx['docs'] = docs[:DOCS_PER_PAGE]

    return render_to_response('reportapi/index.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def report(request, section, name):
    ctx = _default_context(request)
    report, register = site.get_report_and_register(request, section, name)
    if not report or not register:
        return render_to_response('reportapi/404.html', ctx,
                            context_instance=RequestContext(request,))

    ctx['report_as_json'] = tojson(report.get_scheme(request) or dict())
    ctx['report']  = report
    ctx['section'] = site.sections[section]

    return render_to_response('reportapi/report.html', ctx,
                            context_instance=RequestContext(request,))

@login_required
def get_document(request, pk, download=False):
    ctx = _default_context(request)
    try:
        doc = Document.objects.permitted(request).get(pk=pk)
    except Exception as e:
        ctx['remove_nav'] = True
        return render_to_response('reportapi/404.html', ctx,
                            context_instance=RequestContext(request,))
    if doc.error:
        return HttpResponse(doc.error, mimetype='text/html')

    if doc.report_file and os.path.exists(doc.report_file.path):
        return HttpResponseRedirect(doc.url)

        ### OLD CODE ###
        #~ url = doc.url # remember
#~ 
        #~ # Download or show PDF and HTML files as raw
#~ 
        #~ if download or url.endswith('.pdf') or url.endswith('.html'):
            #~ return HttpResponseRedirect(url)
#~ 
        #~ # Show ODF files in ViewerJS
#~ 
        #~ ctx['DOCUMENT'] = doc
#~ 
        #~ lang = get_language()
        #~ if lang in REPORTAPI_LANGUAGES:
            #~ lang = '.' + lang
        #~ else:
            #~ lang = ''
#~ 
        #~ return HttpResponseRedirect('%slib/ViewerJS/index%s.html#%s' %
            #~ (settings.STATIC_URL, lang, url))

    ctx['remove_nav'] = True

    return render_to_response('reportapi/404.html', ctx,
                            context_instance=RequestContext(request,))

########################################################################
# Additional functions
########################################################################

def _default_context(request):
    ctx = {}
    ctx['sections'] = site.get_sections(request)
    docs = Document.objects.permitted(request).all()
    ctx['docs'] = docs[:DOCS_PER_PAGE]
    return ctx

def create_document(request, report, document, filters):
    """ Создание отчёта """
    try:
        report.render(request=request, document=document, filters=filters)
    except Exception as e:
        msg = traceback.format_exc()
        print(msg)
        if REPORTAPI_DEBUG:
            exc_info = sys.exc_info()
            reporter = ExceptionReporterExt(request, *exc_info)
            document.error = reporter.get_traceback_html()
        else:
            document.error = '%s:\n%s' % (smart_text(_('Error in template')), msg)

    if not document.error:
        document.autoconvert()
        document.end = timezone.now()
        document.save()

        delta = document.end - document.start
        ms = int(delta.total_seconds() *1000)
        register = document.register
        if register.timeout < ms:
            register.timeout = ms
            register.save()
    else:
        document.end = timezone.now()
        document.save()

    return document

def result(request, document, old=False):
    user = request.user
    result = {
        'report_id': document.register_id,
        'id': document.id,
        'start': document.start,
        'end': document.end,
        'user': document.user.get_full_name() or document.user.username,
        'error': document.error or None,
        'timeout': document.register.timeout,
        'has_remove': False,
    }
    if old:
        result['old'] = True
    if document.end:
        result['url'] = document.get_absolute_url()
        if user.is_superuser or document.user == user:
            result['has_remove'] = True
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
def API_document_create(request, section, name, filters=None, force=False, fake=False, **kwargs):
    """ *Запускает процесс создания отчёта и/или возвращает информацию
        об уже запущенном процессе.*

        ####ЗАПРОС. Параметры:

        1. "section" - идентификационное название раздела;
        2. "name"    - идентификационное название отчёта;
        3. "filters" - фильтры для обработки результата (необязательно);
        4. "force"   - принудительное создание отчёта (необязательно).
        5. "fake"    - для готовых документов имитирует создание нового (необязательно).

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
            "timeout": 1000, // расчётное время ожидания результата в милисекундах 
        }
        ```

    """
    user = request.user
    session = request.session

    report, register = site.get_report_and_register(request, section, name)
    if not report or not register:
        raise PermissionError()

    
    filters = report.prepare_filters(filters, request)
    code = report.get_code(filters, request)
    expired = timezone.now() - timezone.timedelta(seconds=report.expiration_time)

    all_documents = register.document_set.filter(code=code, error='')
    proc_documents = all_documents.filter(end__isnull=True)
    last_documents = all_documents.filter(end__gt=expired)

    if proc_documents:
        # Создающийся отчёт
        return result(request, proc_documents[0])
    elif last_documents and (not force or not report.create_force):
        # Готовый отчёт
        if fake:
            return result(request, last_documents[0])
        return result(request, last_documents[0], old=True)
    else:
        if not report.validate_filters(filters):
            return JSONResponse(status=400, message=_('One or more filters filled in not correctly'))
        # Новый отчёт
        document = Document.objects.new(request=request, user=user, code=code, register=register)
        document.description = report.get_description_from_filters(filters)
        document.details = report.get_details(document=document, filters=filters, request=request)
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
            return result(request, document)
        else:
            # Последовательное создание отчёта
            r = create_document(**func_kwargs)
            return result(request, document)

@api_required
@login_required
def API_document_info(request, id, section, name, filters=None, **kwargs):
    """ *Возвращает информацию об определённом запущенном или
        завершённом отчёте по заданному идентификационному номеру,
        либо по другим идентификационным данным.*

        ####ЗАПРОС. Параметры:

        1. "id" - идентификатор отчёта;
        2. "section" - идентификационное название раздела;
        3. "name"    - идентификационное название отчёта;
        4. "filters" - фильтры для обработки результата (необязательно);

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
    if not id:
        return API_document_create(request, section, name, filters, fake=True)
    user = request.user
    all_documents = Document.objects.permitted(request).all()
    try:
        document = all_documents.get(id=id)
    except:
        return JSONResponse(status=404)
    else:
        return result(request, document)

@api_required
@login_required
def API_document_delete(request, id, **kwargs):
    """ *Удаляет документ по заданному идентификационному номеру.*

        ####ЗАПРОС. Параметры:

        1. "id" - идентификатор отчёта;

        ####ОТВЕТ. Формат ключа "data":

        ```
        #!javascript
        true // если удаление произведено
        ```

    """
    user = request.user
    all_documents = Document.objects.del_permitted(request).all()
    try:
        document = all_documents.get(id=id)
    except:
        return JSONResponse(status=404)
    else:
        document.delete()
        return JSONResponse(data=True)

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
    data = _filter.search(query, page, request=request)
    return JSONResponse(data=data)


_methods = [
    ('reportapi.get_scheme', API_get_scheme),
    ('reportapi.document_create', API_document_create),
    ('reportapi.document_info', API_document_info),
    ('reportapi.document_delete', API_document_delete),
    ('reportapi.object_search', API_object_search),
]

# store prepared methods
METHODS = get_methods(_methods)

@csrf_exempt
def api(request):
    return quickapi_index(request, methods=METHODS)
