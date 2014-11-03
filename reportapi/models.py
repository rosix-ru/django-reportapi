# -*- coding: utf-8 -*-
#
#  reportapi/models.py
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
import os, re, hashlib, subprocess

from django.utils.encoding import smart_text, force_text, python_2_unicode_compatible
from django.utils.crypto import get_random_string
from django.utils import six
from django.db import models
from django.db.models import Q, get_model
from django.utils.translation import ugettext_noop, ugettext, ugettext_lazy as _
from django.utils import timezone
from django.template import RequestContext, loader
from django.template.defaultfilters import slugify
from django.core.files.base import ContentFile

from reportapi.conf import (
    settings,
    REPORTAPI_CODE_HASHLIB,
    REPORTAPI_UPLOAD_HASHLIB,
    REPORTAPI_FILES_UNIDECODE,
    AUTH_USER_MODEL,
    REPORTAPI_UNOCONV_TO_ODF,
    REPORTAPI_UNOCONV_TO_PDF,
    REPORTAPI_BRAND_TEXT,
    Header, Footer, Page
)

UNOCONV_EXE = "unoconv"

if REPORTAPI_UNOCONV_TO_ODF or REPORTAPI_UNOCONV_TO_PDF:
    import subprocess

    try:
        UNOCONV_EXE = subprocess.check_output(["which", "unoconv"]).replace('\n', '')
    except:
        REPORTAPI_UNOCONV_TO_ODF = False
        REPORTAPI_UNOCONV_TO_PDF = False

from reportapi.fields import JSONField

User = get_model(*AUTH_USER_MODEL.split('.'))
Group = User.groups.field.rel.to

if REPORTAPI_FILES_UNIDECODE:
    from unidecode import unidecode
    prep_filename = lambda x: unidecode(x).replace(' ', '_').replace("'", "")
else:
    prep_filename = lambda x: x

REPORTAPI_CODE_LENGTH = len(hashlib.new(REPORTAPI_CODE_HASHLIB).hexdigest())

class Report(object):
    enable_threads  = True
    create_force    = True
    expiration_time = 86400 # 1 day
    mimetype        = 'application/vnd.oasis.opendocument.text'
    format          = 'fodt'
    icon            = None
    template_name   = 'reportapi/flatxml/standard_text.html'
    filters         = None
    site            = None
    name            = None
    title           = None
    verbose_name    = None # do not change
    section         = ugettext_noop('main')
    section_label   = None # do not change
    page            = Page()

    def __init__(self, site=None, section=None, section_label=None, \
        filters=None, title=None, name=None, **kwargs):
        """
        Установка значений по-умолчанию
        """
        class_name = self.__class__.__name__

        self.site = site or getattr(self, 'site', None) or raise_set_site(class_name)

        self.section = section or getattr(self, 'section')
        if not isinstance(self.section, six.string_types) or not validate_name(self.section):
            raise ValueError('Attribute `section` most be string in '
                'English without digits, spaces and hyphens.')
        self.section_label = section_label or getattr(self, 'section_label', None) or _(self.section)

        self.name = name or getattr(self, 'name', None) or class_name.lower()
        if not isinstance(self.name, six.string_types) or not validate_name(self.name):
            raise ValueError('Attribute `name` most be string in '
                'English without digits, spaces and hyphens.')

        if self.filters is None:
            self.filters = filters or ()

        if not isinstance(self.filters, (list, tuple)):
            raise ValueError('Attribute `filters` most be list or tuple.')

        self._filters = dict([ (f.name, f) for f in self.filters ])
        # unique
        self.filters = [ f for f in self.filters if f in self._filters.values() ]

        self.title = title or getattr(self, 'title')
        if not isinstance(self.title, six.string_types) or not validate_title(self.title):
            raise ValueError('Attribute `title` most be string in '
                'English without translation.')
        self.verbose_name = _(self.title)

    def slugify(self, name):
        return slugify(name)

    @property
    def label(self):
        return self.verbose_name

    def create_register(self):
        """
        Создаёт в базе данных объект регистрации отчёта
        """
        registers = Register.objects.filter(section=self.section, name=self.name)
        if registers:
            register = registers[0]
            if register.title != self.title:
                register.title = self.title
                register.save()
            return register
        # Если данный отчёт не зарегистрирован, то создаём его
        return Register.objects.create(
            section=self.section, name=self.name, title=self.title)

    def permitted_register(self, request):
        """
        Возвращает объект зарегистрированного отчёта согласно прав
        доступа. Все отчёты доступны суперпользователю.
        """
        user = request.user
        if user.is_superuser:
            return self.create_register()

        registers = Register.objects.permitted(request)
        registers = registers.filter(section=self.section, name=self.name)
        if registers:
            return registers[0]
        return None
    
    def has_permission(self, request):
        return bool(self.permitted_register(request))

    def get_code(self, request, filters):
        """
        Этот метод может быть переопределён для тех отчётов, где 
        уникальный код следует генерировать иначе.
        """
        if not filters:
            return getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
        code = hashlib.new(REPORTAPI_CODE_HASHLIB)
        code.update(self.filters_to_string(filters))
        code.update(getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE))
        return code.hexdigest()

    def get_filename(self):
        filename = smart_text(self.verbose_name) + '.' + self.format
        filename = prep_filename(filename)
        return filename

    def get_context(self, request, document, filters):
        """
        Этот метод должен быть переопределён в наследуемых классах.
        Возвращать контекст нужно в виде словаря.
        Параметр context['DOCUMENT'] будет установлен автоматически в
        методе self.render(...)
        """
        raise NotImplementedError()

    def get_description_from_filters(self, filters):
        """
        Получаем описание из фильтров
        """

        filters = self.get_filters_data(filters)
        L = []
        for f in filters:
            label = (f['label']).lower()
            clabel = (f['condition_label']).lower()

            if f['condition'] in ('isnull', 'empty'):
                cond = _('empty') if f['value'] else _('no empty')
                s = '%s: %s' % (label, cond)
            elif f['condition'] == 'in':
                cond = ', '.join([ smart_text(x) for x in f['value_label']])
                s = '%s: %s [%s]' % (label, clabel, cond)
            elif f['condition'] == 'range':
                cond = [ smart_text(x) for x in f['value_label']]
                s = _('%(label)s: from %(cond0)s to %(cond1)s') % {
                    'label': label, 'cond0': cond[0], 'cond1': cond[1]
                }
            else:
                cond = f['value_label']
                s = '%s: %s %s' % (label, clabel, cond)

            L.append(s)
        return ';\n'.join(L)

    def get_details(self, request, document, filters):
        """
        Этот метод может быть переопределён в наследуемых классах.
        """
        return {}

    def render(self, request, document, filters, save=False):
        """
        Формирование файла отчёта.
        """
        context = self.get_context(request, document, filters)
        if not 'BRAND_TEXT' in context:
            context['BRAND_TEXT'] = REPORTAPI_BRAND_TEXT
        document.mimetype   = self.mimetype
        context['PAGE']     = self.page.checked()
        context['DOCUMENT'] = document
        context['FILTERS'] = self.get_filters_data(filters)
        content = loader.render_to_string(self.template_name, context,
                            context_instance=RequestContext(request,))
        _file = ContentFile(content.encode('utf-8') or \
            smart_text(_('Unspecified render error in template.')))
        document.report_file.save(self.get_filename(), _file, save=save)
        return document

    def filters_to_string(self, filters):
        if not isinstance(filters, dict):
            return str(filters)

        for k,v in filters.items():
            if isinstance(v, (list,tuple)):
                filters[k] = list(set(v))
        return smart_text(filters)

    def filters_list(self):
        return [ x.serialize() for x in self.filters ]

    def validate_filters(self, filters):
        """
        Raise Exception from filter if not valid
        """
        try:
            data = self.get_filters_data(filters)
        except Exception as e:
            print filters
            raise e
        return True

    def get_filters_data(self, filters):
        L = []
        for key,dic in filters.items():
            f = self.get_filter(key)
            if f:
                L.append(f.data(**dic))
        return L

    def get_filter_data(self, name, filters):
        f = self.get_filter(name)
        kw = filters.get(self.slugify(name), None)
        if f and kw:
            return f.data(**kw)
        return None

    def get_filter_clean_value(self, name, filters):
        data = self.get_filter_data(name, filters)
        if data:
            return data.get('value', None)
        return None

    def get_filter(self, name):
        return self._filters.get(self.slugify(name), None)

    def get_scheme(self, request=None):
        SCHEME = {
            'name': self.name,
            'section': self.section,
            'label': self.label,
            'icon': self.icon,
            'format': self.format,
            'enable_threads': self.enable_threads,
            'create_force': self.create_force,
            'expiration_time': self.expiration_time,
            'timeout': self.timeout,
        }
        filters_list = self.filters_list()
        SCHEME['filters'] = dict(filters_list)
        SCHEME['filters_list'] = [ x[0] for x in filters_list ]

        return SCHEME

    @property
    def timeout(self):
        return self.create_register().timeout

class Spreadsheet(Report):
    mimetype      = "application/vnd.oasis.opendocument.spreadsheet"
    format        = 'fods'
    template_name = 'reportapi/flatxml/standard_spreadsheet.html'

class RegisterManager(models.Manager):
    use_for_related_fields = True

    def permitted(self, request):
        user = request.user
        if not user.is_authenticated():
            return self.get_query_set().none()
        if user.is_superuser:
            return self.get_query_set()
        return self.get_query_set().filter(
            Q(all_users=True)
            | Q(users=user)
            | Q(groups__in=user.groups.all())
        )

@python_2_unicode_compatible
class Register(models.Model):
    """
    Зарегистрированные отчёты.
    Модель служит для определения прав доступа к отчётам.
    """
    section = models.CharField(_('section'), max_length=255)
    name    = models.CharField(_('name'), max_length=255)
    title = models.CharField(_('title without translation'), max_length=255)
    all_users = models.BooleanField(_('allow all users'), default=False)
    users = models.ManyToManyField(User, null=True, blank=True,
        verbose_name=_('allow list users'))
    groups = models.ManyToManyField(Group, null=True, blank=True,
        verbose_name=_('allow list groups'))
    timeout = models.IntegerField(_('max of timeout'), default=1000, editable=False)

    objects = RegisterManager()

    class Meta:
        ordering = ['title']
        verbose_name = _('registered report')
        verbose_name_plural = _('registered reports')
        unique_together = ('section', 'name')

    def __str__(self):
        try:
            return ugettext(self.title)
        except:
            return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('reportapi:report', [self.section, self.name])

class DocumentManager(models.Manager):
    use_for_related_fields = True

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

@python_2_unicode_compatible
class Document(models.Model):
    """
    Файл сформированного документа.

    Поле `code` по умолчанию рассчитано на длину md5, заданного
    настройкой REPORTAPI_CODE_HASHLIB. Если вы измените эту настройку
    после создания модели в базе данных, то в базу нужно будет вручную
    внести соотвествующие изменения.

    """
    register = models.ForeignKey(Register, editable=False,
        verbose_name=_('registered report'))
    user = models.ForeignKey(User, editable=False, null=True,
        verbose_name=_('user'))
    code  = models.CharField(_('process key'), editable=False,
        blank=True, db_index=True, max_length=REPORTAPI_CODE_LENGTH)
    error = models.TextField(_('error message'), editable=False, blank=True)
    start = models.DateTimeField(_('start create'), auto_now_add=True)
    end   = models.DateTimeField(_('end create'), null=True, blank=True)
    report_file = models.FileField(_('report file'), blank=True,
        upload_to=lambda x,y: x.upload_to(y), max_length=512)
    description = models.TextField(_('description'), blank=True)
    details = JSONField(_('details'), null=True, blank=True)

    objects = DocumentManager()

    def __str__(self):
        return force_text(self.register)

    class Meta:
        ordering = ['-start', '-end']
        verbose_name = _('generated report')
        verbose_name_plural = _('generated reports')
        get_latest_by = 'end'

    def upload_to(self, filename):
        dt = timezone.now()
        date = dt.date()
        dic = {
            'filename':filename,
            'date': date.isoformat(),
        }
        code = hashlib.new(REPORTAPI_UPLOAD_HASHLIB)
        code.update(str(dt.isoformat()))
        code.update('reportapi')
        code.update(get_random_string())
        dic['code'] = code.hexdigest()
        return smart_text('reports/%(date)s/%(code)s/%(filename)s' % dic)

    @models.permalink
    def get_absolute_url(self):
        return ('reportapi:get_document', [self.pk])

    @property
    def created(self):
        return self.end

    @property
    def url(self):
        if self.report_file:
            return self.report_file.url
        return None

    def autoconvert(self, remove=True):
        """
        Конвертирует из FlatXML в заданный формат если на сервере
        установлен `unoconv`
        Поддерживаются:
            1. ODF (ODT, ODS, ODP)
            2. PDF

        Устанавливает путь к новому файлу относительно
        расположения хранилища: self.report_file.name
        
        Возвращает булево исполнения операции.
        """

        location = self.report_file.storage.location
        oldpath = self.report_file.path
        oldname = self.report_file.name
        basename, ext = os.path.splitext(oldname)
        ext = ext.lower()

        ExtODF = {'.fodt': '.odt', '.fods': '.ods', '.fodp': '.odp'}

        if REPORTAPI_UNOCONV_TO_PDF and ext != '.pdf':
            format = 'pdf'
            newname = basename + '.pdf'
        elif REPORTAPI_UNOCONV_TO_ODF and ext in ExtODF:
            format = ExtODF[ext][1:]
            newname = basename + ExtODF[ext]
        else:
            return False

        newpath = os.path.join(location, newname)
        if remove and os.path.exists(newpath):
            remove_file(newpath)

        if not os.path.exists(newpath):
            dwd = os.path.dirname(newpath)
            cwd = os.getcwd()
            os.chdir(dwd)

            proc = [UNOCONV_EXE, '-f', format, os.path.basename(oldpath)]

            out = 'out' #if settings.DEBUG else "/dev/null"
            err = 'err' #if settings.DEBUG else "/dev/null"
            p = subprocess.Popen(proc, shell=False,
                    stdout=open(out, 'w+b'), 
                    stderr=open(err, 'w+b'),
                    cwd=dwd)
            a = p.wait()

            os.chdir(cwd)

            if os.path.exists(newpath):
                self.report_file.name = newname
                if remove:
                    remove_file(oldpath)
                return True

        return False


    def save(self):
        if self.id:
            old = Document.objects.get(id=self.id)
            try:
                old.report_file.path
            except:
                pass
            else:
                if self.report_file != old.report_file:
                    remove_file(old.report_file.path)
        super(Document, self).save()

    def delete(self):
        if self.report_file:
            remove_dirs(os.path.dirname(self.report_file.path), withfiles=True)
        super(Document, self).delete()


def remove_dirs(dirname, withfiles=False):
    """ Замалчивание ошибки удаления каталога """
    if withfiles:
        for f in os.listdir(dirname):
            remove_file(os.path.join(dirname, f))
    try:
        os.removedirs(dirname)
        return True
    except:
        return False

def remove_file(filename):
    """ Замалчивание ошибки удаления файла """
    try:
        os.remove(filename)
        return True
    except:
        return False

def raise_set_site(class_name):
    raise NotImplementedError('Set the "site" in %s.' % class_name)

def raise_set_section(class_name):
    raise NotImplementedError('Set the "section" in %s.' % class_name)

pattern_name = re.compile('^[a-z,A-Z]+$')
def validate_name(s):
    return bool(pattern_name.match(s))

pattern_title = re.compile('^[ ,\-,\w]+$')
def validate_title(s):
    return bool(pattern_title.match(s))

