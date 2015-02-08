# -*- coding: utf-8 -*-
#
#  reportapi/api.py
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
import sys
import traceback
import threading
import logging

from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from quickapi.decorators import login_required, api_required
from quickapi.http import JSONResponse
from quickapi.views import api as quickapi_index
from quickapi.utils.doc import (apidoc_lazy, string_lazy,
    RETURN_BOOLEAN_SUCCESS, RETURN_BOOLEAN_EXISTS, PARAMS_UPDATE_FIELD)
from quickapi.utils.method import get_methods

from reportapi.exceptions import ExceptionReporterExt, PermissionError
from reportapi.conf import (REPORTAPI_DEBUG,
    REPORTAPI_ENABLE_THREADS, REPORTAPI_LOGGING as LOGGING)
from reportapi.models import Register, Document
from reportapi.sites import site
from reportapi.utils.deep import from_dict as deep_from_dict


def create_document(request, report, document, filters):
    """ Создание отчёта """
    try:
        report.render(request=request, document=document, filters=filters)
    except Exception as e:

        if LOGGING:
            logger = logging.getLogger('reportapi.api.create_document')
            logger.error(force_text(e))

        msg = traceback.format_exc()

        if REPORTAPI_DEBUG:
            exc_info = sys.exc_info()
            reporter = ExceptionReporterExt(request, *exc_info)
            document.error = reporter.get_traceback_html()
        else:
            document.error = '%s:\n%s' % (force_text(_('Error in template')), msg)

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
        'convert_error': deep_from_dict(document.details, 'convert.error', update=False),
        'timeout': document.register.timeout,
        'has_remove': False,
    }

    if old: result['old'] = True

    if document.end:
        result['urls'] =  {
            'view': {
                'auto': document.get_view_url(),
                'html': document.get_view_url_html(),
                'pdf':  document.get_view_url_pdf(),
            },
            'download': {
                'auto': document.get_download_url(),
                'xml':  document.get_download_url_xml(),
                'odf':  document.get_download_url_odf(),
                'pdf':  document.get_download_url_pdf(),
            }
        }

        result['filenames'] = {
            'xml': document.get_filename_xml(),
            'odf': document.get_filename_odf(),
            'pdf': document.get_filename_pdf(),
        }

        if user.is_superuser or document.user == user:
            result['has_remove'] = True

    return JSONResponse(data=result)


@api_required
@login_required
def API_get_scheme(request, **kwargs):
    """
    Возвращает схему ReportAPI для пользователя.
    """
    data = site.get_scheme(request)
    return JSONResponse(data=data)

API_get_scheme.__doc__ = apidoc_lazy(
    header=_("*Returns the schema ReportAPI for the user.*"),
    data=string_lazy(
"""
```
#!javascript

{
    "icon": null,
    "label": "%s",
    "sections": {
        "icon": null,
        "label": "main",
        "reports_list": [],
        "reports": {}
    }
}
```
""", _('Reporting'))
)


@api_required
@login_required
def API_document_create(request, section, name, filters=None, force=False, fake=False, **kwargs):
    """
    Запускает процесс создания отчёта и/или возвращает информацию
    об уже запущенном процессе.
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

API_document_create.__doc__ = apidoc_lazy(
    header=_("""*Starts the process of creating a report and/or returns
information about an already running process.*"""),

    params=string_lazy(
"""
    1. "section" - %s;
    2. "name"    - %s;
    3. "filters" - %s;
    4. "force"   - %s;
    5. "fake"    - %s.
""", (
    _('identification section name'),
    _('identification report name'),
    _('filters for processing the result (optional)'),
    _('force the creation of the report (optional)'),
    _('for finished documents simulates the creation of new (optional)')
    )),

    data=string_lazy(
"""
%s

```
#!javascript
{
    "id": 1,
    "start": "2014-01-01T10:00:00+0000",
    "user": "%s",
    "end": null, // %s
    "url": "",
    "old": null, // true, %s
    "error": null, // %s
    "timeout": 1000, // %s
}
```
""", (
    _('Information about the process'),
    _('Grigoriy Kramarenko'),
    _('or creation date'),
    _('when taken already existing old report'),
    _('or description of the error'),
    _('estimated time of waiting for the result in milliseconds'),
    ))
)


@api_required
@login_required
def API_document_info(request, id, section, name, filters=None, **kwargs):
    """
    Возвращает информацию об определённом запущенном или
    завершённом отчёте по заданному идентификационному номеру,
    либо по другим идентификационным данным.
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

API_document_info.__doc__ = apidoc_lazy(
    header=_("""*Returns information about a specific running or
the completed report at the specified identification number, either
other identification data.*"""),

    params=string_lazy(
"""
    1. "id"      - %s;
    2. "section" - %s;
    3. "name"    - %s;
    4. "filters" - %s.
""", (
    _('report identificator'),
    _('identification section name'),
    _('identification report name'),
    _('filters for processing the result (optional)'),
    )),

    data=string_lazy(
"""
%s

```
#!javascript
{
    "id": 1,
    "start": "2014-01-01T10:00:00+0000",
    "user": "%s",
    "end": null, // %s
    "url": "",
    "error": null, // %s
}
```
""", (
    _('Information about the process of report generation'),
    _('Grigoriy Kramarenko'),
    _('or creation date'),
    _('or description of the error'),
    ))
)


@api_required
@login_required
def API_document_delete(request, id, **kwargs):
    """
    Удаляет документ по заданному идентификационному номеру.
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

API_document_delete.__doc__ = apidoc_lazy(
    header=_("*Deletes the document at the specified identification number.*"),
    params=string_lazy(
"""
    1. "id" - %s.
""", _('report identificator')),

    data=RETURN_BOOLEAN_SUCCESS
)


@api_required
@login_required
def API_object_search(request, section, name, filter_name, query=None, page=1, **kwargs):
    """ 
    Производит поиск для заполнения объектного фильтра экземпляром
    связанной модели.
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

API_object_search.__doc__ = apidoc_lazy(
    header=_("*Searches for filling the object filter an instance of the related model.*"),
    params=string_lazy(
"""
    1. "section" - %s;
    2. "name"    - %s;
    3. "filter_name" - %s;
    4. "query" - %s;
    5. "page" - %s;
""", (
    _('identification section name'),
    _('identification report name'),
    _('the filter name for the related model'),
    _('the search query (optional)'),
    _('page number (optional)'),
    )),
    data=string_lazy(
"""
%s

```
#!javascript
{
    "object_list": [
        {"pk": 1, "__unicode__": "%s"},
        {"pk": 2, "__unicode__": "%s"}
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
""", (_('The serialized object to the page of Paginator'), _('First object'), _('Second object'))),
    footer=_('*This is the standard output, which can be overridden separately for each report.*')
)


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
