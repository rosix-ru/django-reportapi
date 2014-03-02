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
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_noop, ugettext_lazy as _
from django.utils import timezone
from django.template import Context
from django.template.loader import get_template
from django.core.files.base import ContentFile

from reportapi.filters import FilterObject, FilterDateTime, FilterText, FilterDigit
from reportapi.conf import (settings, REPORTAPI_CODE_HASHLIB,
    REPORTAPI_UPLOAD_HASHLIB, REPORTAPI_FILES_UNIDECODE,
    AUTH_USER_MODEL, AUTH_GROUP_MODEL)

if REPORTAPI_FILES_UNIDECODE:
    from unidecode import unidecode
    prep_filename = lambda x: unidecode(x).replace(' ', '_').replace("'", "")
else:
    prep_filename = lambda x: x

import os, re, hashlib

REPORTAPI_CODE_LENGTH = len(hashlib.new(REPORTAPI_CODE_HASHLIB).hexdigest())

class Report(object):
    enable_threads  = True
    create_force    = True
    expiration_time = 86400 # 1 day
    name_ending     = 'html'
    icon            = None

    def __init__(self, site=None, section=None, section_label=None, \
        filters=None, title=None, **kwargs):
        """
        Установка значений по-умолчанию
        """
        class_name = self.__class__.__name__

        self.site = site or getattr(self, 'site', None) or raise_set_site(class_name)
        self.section = section or getattr(self, 'section', None) or raise_set_section(class_name)
        if not isinstance(self.section, (str, unicode)) or not validate_section(self.section):
            raise ValueError('Attribute `section` most be string in '
                'English without digits, spaces and hyphens.')
        self.section_label = section_label or getattr(self, 'section_label', _(self.section))
        filters = filters or getattr(self, 'filters', None)
        if filters:
            self.set_filters(filters)
        self.title = title or getattr(self, 'title')
        if not isinstance(self.title, (str, unicode)) or not validate_title(self.title):
            raise ValueError('Attribute `title` most be string in '
                'English without translation.')
        self.verbose_name = _(self.title)

        self.name = '.'.join([self.section, class_name.lower()])

    @property
    def label(self):
        return self.verbose_name

    def permitted_register(self, request):
        """
        Возвращает объект зарегистрированного отчёта согласно прав
        доступа. Все отчёты доступны суперпользователю.
        """
        registers = Register.objects.filter(name=self.name)
        user = request.user
        if user.is_superuser:
            if registers:
                return registers[0]
            # Если данный отчёт не зарегистрирован, то создаём его
            return Register.objects.create(name=self.name)

        registers = registers.permitted(request)
        if registers:
            return registers[0]
        return None
    
    def has_permission(self, request):
        return bool(self.permitted_register(request))

    def filters_to_string(self, filters):
        if not isinstance(filters, dict):
            return str(filters)

        for k,v in filters.items():
            if isinstance(v, (list,tuple)):
                filters[k] = list(set(v))
        return str(filters)

    def get_code(self, request, filters):
        """
        Этот метод может быть переопределён для тех отчётов, где 
        уникальный код следует генерировать иначе.
        """
        if not filters:
            return ''
        code = hashlib.new(REPORTAPI_CODE_HASHLIB)
        code.update(self.filters_to_string(filters))
        return code.hexdigest()

    def get_filename(self):
        filename = self.verbose_name + '.' + self.name_ending
        filename = prep_filename(filename)
        return filename

    def get_context(self, request, document, filters):
        """
        Этот метод должен быть переопределён в наследуемых классах.
        """
        raise NotImplementedError()

    def render(self, request, document, filters, save=False):
        """
        Формирование файла отчёта.
        """
        context = self.get_context(request, document, filters)
        context['DOCUMENT'] = document
        template = get_template(self.template_name)
        content  = template.render(Context(context)).encode('utf-8')
        _file    = ContentFile(content)
        document.report_file.save(self.get_filename(), _file, save=save)
        return document

    def get_scheme(self, request):
        
        return {}

    def get_filter(self, filter_name):
        
        return None

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

class Register(models.Model):
    """
    Зарегистрированные отчёты.
    Модель служит для определения прав доступа к отчётам.
    """
    name = models.CharField(_('name'), max_length=255)
    title = models.CharField(_('title without translation'), max_length=255)
    all_users = models.BooleanField(_('allow all users'), default=False)
    users = models.ManyToManyField(AUTH_USER_MODEL, null=True, blank=True,
        verbose_name=_('allow list users'))
    groups = models.ManyToManyField(AUTH_GROUP_MODEL, null=True, blank=True,
        verbose_name=_('allow list groups'))

    objects = RegisterManager()

    class Meta:
        ordering = ['name']
        verbose_name = _('registered report')
        verbose_name_plural = _('registered reports')

    def __unicode__(self):
        try:
            return _(self.title)
        except:
            return self.title

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
    user = models.ForeignKey(AUTH_USER_MODEL, editable=False, null=True,
        verbose_name=_('user'))
    code  = models.CharField(_('process key'), editable=False,
        blank=True, db_index=True, max_length=REPORTAPI_CODE_LENGTH)
    error = models.TextField(_('error message'), editable=False, blank=True)
    start = models.DateTimeField(_('start create'), auto_now_add=True)
    end   = models.DateTimeField(_('end create'), null=True, blank=True)
    report_file = models.FileField(_('report file'), blank=True,
        upload_to=lambda x,y: x.upload_to(y), max_length=512)

    objects = DocumentManager()

    def __unicode__(self):
        return unicode(self.register)

    class Meta:
        ordering = ['-end', '-start']
        verbose_name = _('generated report')
        verbose_name_plural = _('generated reports')

    def upload_to(self, filename):
        dt = timezone.now()
        date = dt.date()
        dic = {
            'filename':filename,
            'date': date.isoformat(),
        }
        code = hashlib.new(REPORTAPI_UPLOAD_HASHLIB)
        code.update(str(dt.isoformat()))
        code.update('reportapi'+settings.SECRET_KEY)
        dic['code'] = code.hexdigest()
        return u'reports/%(date)s/%(code)s/%(filename)s' % dic

    @property
    def url(self):
        if self.report_file:
            return self.report_file.url
        return None

    def delete(self):
        remove_file(self.report_file.path)
        remove_dirs(os.path.dirname(self.report_file.path))
        super(Document, self).delete()

    def save(self):
        if self.id:
            old = Document.objects.get(id=self.id)
            try:
                presave_obj.report_file.path
            except:
                pass
            else:
                if self.report_file != old.report_file:
                    remove_file(old.report_file.path)
        super(Document, self).save()

    def delete(self):
        remove_file(self.report_file.path)
        super(Document, self).delete()


def remove_dirs(dirname):
    """ Замалчивание ошибки удаления каталога """
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

pattern_section = re.compile('^[a-z,A-Z]+$')
def validate_section(s):
    return bool(pattern_section.match(s))

pattern_title = re.compile('^[ ,\-,\w]+$')
def validate_title(s):
    return bool(pattern_title.match(s))

