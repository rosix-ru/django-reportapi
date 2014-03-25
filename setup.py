from setuptools import setup, find_packages
import os
import reportapi

def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except:
        return ''

setup(
    name='django-reportapi',
    version=reportapi.__version__,
    description='Is an easy way to setup mechanism building and \
                getting reports for Django projects.',
    long_description=read('README.md'),
    author='Grigoriy Kramarenko',
    author_email='root@rosix.ru',
    url='https://bitbucket.org/rosix/django-reportapi/',
    license='GNU General Public License v3 or later (GPLv3+)',
    platforms='any',
    zip_safe=False,
    packages=find_packages(),
    include_package_data = True,
    install_requires=['django-quickapi', 'pytz'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: Russian',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
