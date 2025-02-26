from pathlib import Path
from setuptools import setup


version = '4.0.1'


def read(filename):
    with open(filename) as file_obj:
        return file_obj.read()


desc = 'Release facilities to ease the management of buildout based projects.'
long_description = f"""
{Path('README.md').read_text()}
\n\n
{Path('CHANGES.md').read_text()}
"""

setup(
    name='freitag.releaser',
    version=version,
    description=desc,
    long_description=long_description,
    # Get more strings from
    # https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['releasing', 'packaging', 'pypi'],
    author='Gil Forcada Codinachs',
    author_email='gil.gnome@gmail.com',
    url='https://github.com/derFreitag/freitag.releaser',
    license='GPL',
    packages=['freitag.releaser'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.11',
    install_requires=[
        'gitpython',
        'gocept.zestreleaser.customupload',
        'paramiko',
        'plone.releaser',
        'scp',
        'setuptools',
        'zest.releaser[recommended]',
    ],
    extras_require={'test': ['testfixtures']},
    entry_points={
        'console_scripts': [
            'freitag_manage = freitag.releaser.manage:manage',
        ],
        'zest.releaser.prereleaser.before': [
            'i18n = freitag.releaser.prerelease:check_translations',
        ],
    },
)
