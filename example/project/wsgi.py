"""
WSGI config for project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys

# Set name directory of environ
ENV = ''#'env-django1.8'

def getenv():
    """ Find full path for name directory of environ """
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

env = getenv()

if env:
    python = 'python%s.%s' % ( str(sys.version_info[0]),  str(sys.version_info[1]) )
    packages = os.path.join(env, 'lib', python, 'site-packages')
    sys.path.insert(0, packages)

# additional local develop folder:
cwd = os.path.abspath(os.path.dirname(__file__))
example_dir = os.path.dirname(cwd)
develop_dir = os.path.dirname(example_dir)
if os.path.exists(develop_dir):
    sys.path.insert(0, develop_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
