from setuptools import setup, find_packages
import reportapi

setup(
    name='django-reportapi',
    version=reportapi.__version__,
    description='Easy mechanism building reports in Django projects.',
    author='Grigoriy Kramarenko',
    author_email='root@rosix.ru',
    url='https://bitbucket.org/rosix/django-reportapi/',
    license='GNU General Public License v3 or later (GPLv3+)',
    platforms='any',
    zip_safe=False,
    packages=find_packages(),
    include_package_data = True,
    install_requires=['django-quickapi>=2.6', 'jsonfield>=1.0'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
