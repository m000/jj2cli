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


setup(
    long_description=__doc__,
    long_description_content_type='text/markdown',

    packages=find_packages('src'),
    package_dir={'': 'src'},
    #py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,

    scripts=[],
    entry_points={
        'console_scripts': [
            'j2 = jj2cli:render',  # temporarily keep the old entry point
            'jj2 = jj2cli:render',
            'jj2dep = jj2cli:dependencies',
        ]
    },
    extras_require=dict(packages_extra),
    zip_safe=False,
    platforms='any',
)
