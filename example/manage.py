#!/usr/bin/env python
#
#   Copyright 2012-2015 Grigoriy Kramarenko <root@rosix.ru>
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

import os, sys

# Set name directory of environ
ENV = ''#'env-django1.8'

def getenv():
    if ENV:
        thispath = os.path.abspath(os.path.dirname(__file__))
        while thispath:
            if thispath == '/' and not os.path.exists(os.path.join(thispath, ENV)):
                raise Exception('Environ not found')
            if os.path.exists(os.path.join(thispath, ENV)):
                return os.path.join(thispath, ENV)
            else:
                thispath = os.path.dirname(thispath)
    else:
        return None

if __name__ == "__main__":
    env = getenv()
    if env:
        python = 'python%s.%s' % sys.version_info[:2]
        packages = os.path.join(env, 'lib', python, 'site-packages')
        sys.path.insert(0, packages)

    # additional local develop folder:
    cwd = os.path.abspath(os.path.dirname(__file__))
    develop_dir = os.path.dirname(cwd)
    if os.path.exists(develop_dir):
        sys.path.insert(0, develop_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
