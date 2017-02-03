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

import os
import sys


# Set name directory of environ, like '.virtualenvs/django1.8'
ENV = ''


def getenv():
    path = os.path.abspath(os.path.dirname(__file__))
    while path:
        env = os.path.join(path, ENV)
        found = os.path.exists(env)
        if path == '/' and not found:
            raise EnvironmentError('Path `%s` not found' % ENV)
        elif found:
            return env
        else:
            path = os.path.dirname(path)


if __name__ == "__main__":

    if ENV:
        env = getenv()
        activate_this = os.path.join(env, 'bin/activate_this.py')
        execfile(activate_this, dict(__file__=activate_this))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
