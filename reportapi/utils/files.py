# -*- coding: utf-8 -*-
#
#   Copyright 2014-2015 Grigoriy Kramarenko <root@rosix.ru>
#
#   This file is part of ReportAPI.
#
#   ReportAPI is free software: you can redistribute it and/or
#   modify it under the terms of the GNU Affero General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.
#
#   ReportAPI is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public
#   License along with ReportAPI. If not, see
#   <http://www.gnu.org/licenses/>.
#

from __future__ import unicode_literals
import os

from reportapi.conf import REPORTAPI_FILES_UNIDECODE

if REPORTAPI_FILES_UNIDECODE:
    from unidecode import unidecode
    prep_filename = lambda x: unidecode(x).replace(' ', '_').replace("'", "")
else:
    prep_filename = lambda x: x

def remove_file(filename):
    """ Замалчивание ошибки удаления файла """
    try:
        os.remove(filename)
        return True
    except:
        return False

def remove_dirs(dirname, withfiles=False):
    """ Замалчивание ошибки удаления каталога """
    if withfiles and os.path.exists(dirname):
        for f in os.listdir(dirname):
            remove_file(os.path.join(dirname, f))
    try:
        os.removedirs(dirname)
        return True
    except:
        return False



