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
import os, datetime

def auto_remove_version_links(path, version):
    for f in os.listdir(path):
        filepath = os.path.join(path, f)
        if os.path.islink(filepath) and f.count('.') == len(version) -1:
            os.unlink(filepath)

def auto_create_version_links(init_path, version):
    """ Автоматически создаёт ссылки на статику по актуальной версии """
    str_version = '.'.join([ str(x) for x in version ])
    cwd       = os.getcwd()
    self_path = os.path.abspath(os.path.dirname(init_path))
    app_name  = os.path.basename(self_path)
    src_relation = os.path.join('..', '..', '..',)

    src_css_path = os.path.join(src_relation, 'static_src', 'css')
    css_path = os.path.join(self_path, 'static', 'css', app_name)
    ver_css_path = os.path.join(css_path, str_version)

    src_js_path = os.path.join(src_relation, 'static_src', 'js')
    js_path = os.path.join(self_path, 'static', 'js', app_name)
    ver_js_path = os.path.join(js_path, str_version)

    if os.path.exists(css_path) and not os.path.exists(ver_css_path):
        auto_remove_version_links(css_path, version)
        os.chdir(css_path)
        os.symlink(src_css_path, str_version)
    if os.path.exists(js_path) and not os.path.exists(ver_js_path):
        auto_remove_version_links(js_path, version)
        os.chdir(js_path)
        os.symlink(src_js_path, str_version)
    os.chdir(cwd)

def get_date_from_file(*args):
    """ Получает дату изменения версии из файла инициализации """
    if not args:
        return "" 
    elif isinstance(args[0], (list, tuple)):
        version_file = os.path.abspath(*args[0])
    else:
        version_file = os.path.abspath(*args)
    if version_file and os.path.exists(version_file):
        return datetime.datetime.fromtimestamp(
            os.stat(os.path.join(os.path.abspath(version_file))).st_mtime
        ).strftime("%Y-%m-%d")
    else:
        return ""
