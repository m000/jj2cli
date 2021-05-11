# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import importlib
import io
import os
import sys
import shlex
import tempfile
import unittest
from contextlib import contextmanager
from jinja2.exceptions import UndefinedError
from pathlib import Path
from six import string_types
from jj2cli.cli import render_command

@contextmanager
def mktemp(contents):
    """ Create a temporary file with the given contents, and yield its path """
    _, path = tempfile.mkstemp()
    fp = io.open(path, 'wt+', encoding='utf-8')
    fp.write(contents)
    fp.flush()
    try:
        yield path
    finally:
        fp.close()
        os.unlink(path)


@contextmanager
def mock_environ(new_env):
    old_env = os.environ.copy()
    os.environ.update(new_env)
    yield
    os.environ.clear()
    os.environ.update(old_env)


class RenderTest(unittest.TestCase):
    WORKDIR = Path(__file__).parent
    TPLDIR  = Path('resources') / 'tpl'
    DATADIR = Path('resources') / 'data'
    OUTDIR  = Path('resources') / 'out'

    def setUp(self):
        os.chdir(self.WORKDIR)

    def _data_prep(self, *items):
        """ Helper for creating lists of data files, relative to `self.DATADIR`.
        """
        return [str(self.DATADIR / it) for it in items]

    def _render_prep(self, tpl, data, expected_output, extra_args):
        """ Helper for processing common options for test runners.
        """
        tpl = self.TPLDIR / tpl
        data = [] if not data else (
            self._data_prep(data)
            if isinstance(data, string_types)
            else self._data_prep(*data))
        expected_output = (Path(expected_output)
            if expected_output is not None
            else self.OUTDIR / tpl.stem).read_text()
        extra_args = [] if not extra_args else shlex.split(extra_args)

        return (str(tpl), data, expected_output, extra_args)

    def _class_for_name(self, fullcname):
        """ Helper for getting a class object from its string representation.
        """
        # source: https://stackoverflow.com/a/13808375
        mname, cname = fullcname.rsplit('.', 1)
        try:
            m = importlib.import_module(mname)
            c = getattr(m, cname)
            return c
        except (ImportError, AttributeError):
            return None

    # pylint: disable=too-many-arguments
    def _render_test(self, tpl, data=None, expected_output=None,
        extra_args=None, env=None, exception=None, exception_msg=None):
        """ Helper for rendering `tpl` using `data` and checking the results
            against `expected_results`. Rendering is expected to succeed
            without errors.
        """
        tpl, data, expected_output, extra_args = self._render_prep(
            tpl, data, expected_output, extra_args)
        argv = ['dummy_command_name', *extra_args, tpl, *data]

        with mock_environ(env or {}):
            if exception is None:
                result = render_command(argv)
                if isinstance(result, bytes):
                    # XXX: maybe render_command() should just return utf-8?
                    result = result.decode('utf-8')
                self.assertEqual(result, expected_output)
            elif exception_msg is None:
                c = self._class_for_name(exception)
                self.assertRaises(c, render_command, argv)
            else:
                c = self._class_for_name(exception)
                self.assertRaisesRegex(c, exception_msg, render_command, argv)
    # pylint: enable=too-many-arguments

    def test_ini(self):
        """ Tests rendering with a single data file in ini format.
        """
        # simple render
        self._render_test("nginx.conf.j2", "nginx_data.ini")
        # fallback format
        self._render_test("nginx.conf.j2", "nginx_data_ini",
            extra_args='--fallback-format=ini')
        self._render_test("nginx.conf.j2", "nginx_data_ini",
            extra_args='-f ini')
        # default fallback format
        self._render_test("nginx.conf.j2", "nginx_data_ini")

        # Stdin
        #self._testme_std(['--format=ini', 'resources/tpl/nginx.j2'], stdin=open('resources/data.ini'))
        #self._testme_std(['--format=ini', 'resources/tpl/nginx.j2', '-'], stdin=open('resources/data.ini'))

    def test_json(self):
        """ Tests rendering with a single data file in json format.
        """
        # simple render
        self._render_test("nginx.conf.j2", "nginx_data.json")
        # fallback format
        self._render_test("nginx.conf.j2", "nginx_data_json",
            extra_args='--fallback-format=json')
        self._render_test("nginx.conf.j2", "nginx_data_json",
            extra_args='-f json')
        # default fallback format - failure
        self._render_test("nginx.conf.j2", "nginx_data_json",
            exception='configparser.MissingSectionHeaderError',
            exception_msg='no section headers')
        # Stdin
        #self._testme_std(['--format=json', 'resources/tpl/nginx.j2'], stdin=open('resources/data.json'))
        #self._testme_std(['--format=json', 'resources/tpl/nginx.j2', '-'], stdin=open('resources/data.json'))

    def rest_yaml(self):
        """ Tests rendering with a single data file in yaml format.
        """
        try:
            importlib.import_module('yaml')
        except ImportError:
            raise unittest.SkipTest('yaml module not available')

        # Filename
        self._testme_std(['resources/tpl/nginx.j2', 'resources/data.yml'])
        self._testme_std(['resources/tpl/nginx.j2', 'resources/data.yaml'])
        # Format
        self._testme_std(['--format=yaml', 'resources/tpl/nginx.j2', 'resources/data.yml'])
        # Stdin
        self._testme_std(['--format=yaml', 'resources/tpl/nginx.j2'], stdin=open('resources/data.yml'))
        self._testme_std(['--format=yaml', 'resources/tpl/nginx.j2', '-'], stdin=open('resources/data.yml'))

    def rest_env(self):
        """ Tests rendering with a single data file in env format.
        """
        # Filename
        self._testme_std(['--format=env', 'resources/tpl/nginx-env.j2', 'resources/data.env'])
        self._testme_std([                'resources/tpl/nginx-env.j2', 'resources/data.env'])
        # Format
        self._testme_std(['--format=env', 'resources/tpl/nginx-env.j2', 'resources/data.env'])
        self._testme_std([                'resources/tpl/nginx-env.j2', 'resources/data.env'])
        # Stdin
        self._testme_std(['--format=env', 'resources/tpl/nginx-env.j2', '-'], stdin=open('resources/data.env'))
        self._testme_std([                'resources/tpl/nginx-env.j2', '-'], stdin=open('resources/data.env'))

        # Environment!
        # In this case, it's not explicitly provided, but implicitly gotten from the environment
        env = dict(NGINX_HOSTNAME='localhost', NGINX_WEBROOT='/var/www/project', NGINX_LOGS='/var/log/nginx/')
        self._testme_std(['--format=env', 'resources/tpl/nginx-env.j2'], env=env)
        self._testme_std([                'resources/tpl/nginx-env.j2'], env=env)

    def rest_import_env(self):
        # Import environment into a variable
        with mktemp('{{ a }}/{{ env.B }}') as template:
            with mktemp('{"a":1}') as context:
                self._testme(['--format=json', '--import-env=env', template, context], '1/2', env=dict(B='2'))
        # Import environment into global scope
        with mktemp('{{ a }}/{{ B }}') as template:
            with mktemp('{"a":1,"B":1}') as context:
                self._testme(['--format=json', '--import-env=', template, context], '1/2', env=dict(B='2'))

    def rest_env_file__equals_sign_in_value(self):
        # Test whether environment variables with "=" in the value are parsed correctly
        with mktemp('{{ A|default('') }}/{{ B }}/{{ C }}') as template:
            with mktemp('A\nB=1\nC=val=1\n') as context:
                self._testme(['--format=env', template, context], '/1/val=1')

    def rest_unicode(self):
        # Test how unicode is handled
        # I'm using Russian language for unicode :)
        with mktemp('Проверка {{ a }} связи!') as template:
            with mktemp('{"a": "широкополосной"}') as context:
                self._testme(['--format=json', template, context], 'Проверка широкополосной связи!')

        # Test case from issue #17: unicode environment variables
        if sys.version_info[0] == 2:
            # Python 2: environment variables are bytes
            self._testme(['resources/tpl/name.j2'], u'Hello Jürgen!\n', env=dict(name=b'J\xc3\xbcrgen'))
        else:
            # Python 3: environment variables are unicode strings
            self._testme(['resources/tpl/name.j2'], u'Hello Jürgen!\n', env=dict(name=u'Jürgen'))

    def rest_filters__env(self):
        with mktemp('user_login: kolypto') as yml_file:
            with mktemp('{{ user_login }}:{{ "USER_PASS"|env }}') as template:
                # Test: template with an env variable
                self._testme(['--format=yaml', template, yml_file], 'kolypto:qwerty123', env=dict(USER_PASS='qwerty123'))

                # environment cleaned up
                assert 'USER_PASS' not in os.environ

                # Test: KeyError
                with self.assertRaises(KeyError):
                    self._testme(['--format=yaml', template, yml_file], 'kolypto:qwerty123', env=dict())

            # Test: default
            with mktemp('{{ user_login }}:{{ "USER_PASS"|env("-none-") }}') as template:
                self._testme(['--format=yaml', template, yml_file], 'kolypto:-none-', env=dict())

            # Test: using as a function
            with mktemp('{{ user_login }}:{{ env("USER_PASS") }}') as template:
                self._testme(['--format=yaml', template, yml_file], 'kolypto:qwerty123', env=dict(USER_PASS='qwerty123'))

                with self.assertRaises(KeyError):
                    # Variable not set
                    self._testme(['--format=yaml', template, yml_file], '', env=dict())

            # Test: using as a function, with a default
            with mktemp('{{ user_login }}:{{ env("USER_PASS", "-none-") }}') as template:
                self._testme(['--format=yaml', template, yml_file], 'kolypto:qwerty123', env=dict(USER_PASS='qwerty123'))
                self._testme(['--format=yaml', template, yml_file], 'kolypto:-none-', env=dict())


    def rest_custom_filters(self):
        with mktemp('{{ a|parentheses }}') as template:
            self._testme(['--format=env', '--filters=resources/custom_filters.py', template], '(1)', env=dict(a='1'))

    #def rest_custom_tests(self):
        #with mktemp('{% if a|int is custom_odd %}odd{% endif %}') as template:
            #self._testme(['--format=env', '--tests=resources/custom_tests.py', template], 'odd', env=dict(a='1'))

    def rest_output_file(self):
        with mktemp('{{ a }}') as template:
            try:
                self._testme(['-o', '/tmp/j2-out', template], '', env=dict(a='123'))
                self.assertEqual('123', io.open('/tmp/j2-out', 'r').read())
            finally:
                os.unlink('/tmp/j2-out')

    def rest_undefined(self):
        """ Test --undefined """
        # `name` undefined: error
        self.assertRaises(UndefinedError, self._testme, ['resources/tpl/name.j2'], u'Hello !\n', env=dict())
        # `name` undefined: no error
        self._testme(['--undefined', 'resources/tpl/name.j2'], u'Hello !\n', env=dict())

    def rest_jinja2_extensions(self):
        """ Test that an extension is enabled """
        with mktemp('{% do [] %}') as template:
            # `do` tag is an extension
            self._testme([template], '')


    def rest_customize(self):
        """  Test --customize """
        # Test: j2_environment_params()
        # Custom tag start/end
        with mktemp('<% if 1 %>1<% else %>2<% endif %>') as template:
            self._testme(['--customize=resources/customize.py', template], '1')

        # Test: j2_environment()
        # custom function: my_function
        with mktemp('<< my_function("hey") >>') as template:
            self._testme(['--customize=resources/customize.py', template], 'my function says "hey"')

        # Test: alter_context()
        # Extra variable: ADD=127
        with mktemp('<< ADD >>') as template:
            self._testme(['--customize=resources/customize.py', template], '127')

        # Test: extra_filters()
        with mktemp('<< ADD|parentheses >>') as template:
            self._testme(['--customize=resources/customize.py', template], '(127)')

        # Test: extra_tests()
        with mktemp('<% if ADD|int is custom_odd %>odd<% endif %>') as template:
            self._testme(['--customize=resources/customize.py', template], 'odd')

        # reset
        # otherwise it will load the same module even though its name has changed
        del sys.modules['customize-module']

        # Test: no hooks in a file
        # Got to restore to the original configuration and use {% %} again
        with mktemp('{% if 1 %}1{% endif %}') as template:
            self._testme(['--customize=render-test.py', template], '1')

# vim: ts=4 sts=4 sw=4 et noai :
