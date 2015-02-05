# -*- coding: utf-8 -*-
#
#  reportapi/utils/uno.py
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
import os
import subprocess

from reportapi.conf import REPORTAPI_UNOCONV_SERVERS, REPORTAPI_UNOCONV_TO_ODF, REPORTAPI_UNOCONV_TO_PDF
from reportapi.utils.deep import to_dict as deep_to_dict
from reportapi.utils.files import remove_file

unoconv_exe = None

if REPORTAPI_UNOCONV_TO_ODF or REPORTAPI_UNOCONV_TO_PDF:
    try:
        unoconv_exe = subprocess.check_output(["which", "unoconv"]).replace('\n', '')
    except:
        REPORTAPI_UNOCONV_TO_ODF = False
        REPORTAPI_UNOCONV_TO_PDF = False


def random_unoconv_con(document=None):
    """
    Возвращает настройки соединения с сервером конвертации
    Пример
    REPORTAPI_UNOCONV_SERVERS = (
        ('-p', '2002'), # localhost on port 2002
        ('-p', '2003'), # localhost on port 2003
        ('-p', '2004'), # localhost on port 2004
        ('-s', '10.10.10.1', '-p', '2002'), # external server
        ('-s', '10.10.10.1', '-p', '2003'), # external server
    )
    """
    if not REPORTAPI_UNOCONV_SERVERS:
        return []

    count = len(REPORTAPI_UNOCONV_SERVERS)

    if document and document.pk:
        n = ((document.pk % count) or count) - 1
    else:
        n = 0

    return list(REPORTAPI_UNOCONV_SERVERS[n])


def unoconv(document, format, oldpath, newpath, remove_log=True):
    if not unoconv_exe:
        raise RuntimeError('Please install unoconv into your system.')

    newname = os.path.basename(newpath)

    dwd = os.path.dirname(newpath)
    cwd = os.getcwd()
    os.chdir(dwd)

    proc = [unoconv_exe]
    proc.extend(random_unoconv_con(document=document))
    proc.extend(['-f', format, os.path.basename(oldpath)])

    out = os.path.join(dwd, 'convert.out.%s.log' % (format if format == 'pdf' else 'odf',))
    err = os.path.join(dwd, 'convert.error.%s.log' % (format if format == 'pdf' else 'odf',))

    p = subprocess.Popen(proc, shell=False,
            stdout=open(out, 'w+b'), 
            stderr=open(err, 'w+b'),
            cwd=dwd)
    p.wait()

    ready = os.path.exists(newpath)

    f = open(err, 'r')
    err_txt = f.read().decode('utf-8')
    f.close()

    # Когда LO создаёт файл, то может несколько раз попытаться
    # создать временный каталог. Такие ошибки тоже попадают в лог
    # Поэтому единственно верным признаком успеха является
    # наличие конечного файла
    if err_txt and not ready:
        deep_to_dict(document.details, err.replace('.log', ''), err_txt)

    f = open(out, 'r')
    out_txt = f.read().decode('utf-8')
    f.close()

    if out_txt:
        deep_to_dict(document.details, out.replace('.log', ''), out_txt)

    os.chdir(cwd)

    if ready:
        if remove_log:
            remove_file(err)
            remove_file(out)
        return True
    else:
        return False

