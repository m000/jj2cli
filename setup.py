#!/usr/bin/env python
""" # jj2cli - Juiced Jinja2 command-line tool

`jj2cli` (previously `j2cli`) is a command-line tool for templating in
shell-scripts, leveraging the [Jinja2](http://jinja.pocoo.org/docs/)
library.

Features:

* Jinja2 templating with support
* Support for data sources in various formats (ini, yaml, json, env)
* Mixing and matching data sources
* Template dependency analysis

Inspired by [kolypto/j2cli](https://github.com/kolypto/j2cli) and
[mattrobenolt/jinja2-cli](https://github.com/mattrobenolt/jinja2-cli).
"""

from setuptools import setup, find_packages
from sys import version_info as PYVER


### Compatibility packages.
packages_compat = []
# Jinja2
if PYVER < (2, 7) or (3, 0) <= PYVER < (3, 5):
    packages_compat.append('jinja2 ~= 2.10.0')
else:
    packages_compat.append('jinja2 ~= 2.11.0')
# Misc.
if PYVER < (3, 0):
    packages_compat.append('shutilwhich ~= 1.1')
    packages_compat.append('pathlib ~= 1.0')

### Packages for optional functionality.
packages_extra = []
# yaml support
if PYVER < (2, 7) or (2, 7) < PYVER  < (3, 4):
    # XXX: Python2.6
    packages_extra.append(('yaml', 'pyyaml <= 3.11'))
else:
    packages_extra.append(('yaml', 'pyyaml > 5.4'))


setup(
    name='jj2cli',
    version='0.4.0',
    author='Manolis Stamatogiannakis',
    author_email='mstamat@gmail.com',

    url='https://github.com/m000/j2cli',  # XXX: fix before release
    license='BSD',
    description='Juiced Jinja2 command-line tool.',
    long_description=__doc__,  # can't do open('README.md').read() because we're describing self
    long_description_content_type='text/markdown',
    keywords=['Jinja2', 'templating', 'command-line', 'CLI'],

    packages=find_packages('src'),
    package_dir={'': 'src'},
    #py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,

    scripts=[],
    entry_points={
        'console_scripts': [
            'j2 = jj2cli:render',  # temporarily keep the old entry point
            'jj2 = jj2cli:render',
        ]
    },
    install_requires=[
        'six >= 1.13',
        packages_compat,
    ],
    extras_require=dict(packages_extra),
    zip_safe=False,
    test_suite='nose.collector',

    platforms='any',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
