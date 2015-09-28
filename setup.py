# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

import codecs
import sys


version = '0.1.dev0'


def read(filename):
    try:
        with codecs.open(filename, encoding='utf-8') as f:
            return unicode(f.read())
    except NameError:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()


desc = 'Release facilities to ease the management of buildout based projects.'
long_description = u'\n\n'.join([
    read('README.rst'),
    read('CHANGES.rst'),
])
if sys.version_info < (3,):
    long_description = long_description.encode('utf-8')


setup(
    name='freitag.releaser',
    version=version,
    description=desc,
    long_description=long_description,
    classifiers=[
        'Development Status :: 3 - Alpha'
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['releasing', 'packaging', 'pypi', ],
    author='Gil Forcada Codinachs',
    author_email='gil.gnome@gmail.com',
    url='https://github.com/derFreitag/freitag.releaser',
    license='GPL',
    packages=find_packages(exclude=['ez_setup', ]),
    namespace_packages=['freitag', ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'plone.releaser',
        'setuptools',
        'zest.releaser[recommended]',
    ],
    extras_require={
        'test': [
            'testfixtures',
        ],
    },
    entry_points={
        'zest.releaser.prereleaser.before': [
            'vcs_updated = freitag.releaser.prerelease:vcs_updated',
        ],
        'zest.releaser.postreleaser.after': [
            'update_branches = freitag.releaser.postrelease:update_branches'
        ],
    },
)
