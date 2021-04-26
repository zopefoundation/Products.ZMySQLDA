##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import os

from setuptools import find_packages
from setuptools import setup


install_requires = [
    'setuptools',
    'six',
    'Products.ZSQLMethods',
]
if not os.environ.get('READTHEDOCS') == 'True':
    install_requires += [
        'mysqlclient < 2;python_version < "3"',
        'mysqlclient;python_version >= "3"',
    ]


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(
    name='Products.ZMySQLDA',
    version='4.11.dev0',
    license='ZPL 2.1',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    url='https://zmysqlda.readthedocs.io',
    project_urls={
        'Documentation': 'https://zmysqlda.readthedocs.io',
        'Issue Tracker': ('https://github.com/zopefoundation'
                          '/Products.ZMySQLDA/issues'),
        'Sources': 'https://github.com/zopefoundation/Products.ZMySQLDA',
    },
    description='MySQL Zope adapter.',
    long_description=read('README.rst') + '\n' + read('CHANGES.rst'),
    classifiers=[
        'Development Status :: 6 - Mature',
        'Environment :: Web Environment',
        'Framework :: Zope',
        'Framework :: Zope2',
        'Framework :: Zope :: 2',
        'Framework :: Zope :: 4',
        'Framework :: Zope :: 5',
        'License :: OSI Approved :: Zope Public License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['Products'],
    zip_safe=False,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
    install_requires=install_requires,
    extras_require={
        'docs': ['Sphinx', 'repoze.sphinx.autointerface'],
    },
)
