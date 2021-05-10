# -*- coding: utf-8 -*-
import importlib
import logging
import os
import shlex
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from jj2cli.cli import render_command
from jj2cli.parsers import DATASPEC_SEP


@contextmanager
def stdin_from(fin, *args, **kwargs):
    """Use the contents of the specified file as stdin, and yield the original stdin."""
    if not isinstance(fin, Path):
        fin = Path(fin)
    stdin_bak = sys.stdin
    sys.stdin = fin.open(*args, **kwargs)
    logging.debug("STDIN from: %s", fin)
    try:
        yield
    finally:
        sys.stdin.close()
        sys.stdin = stdin_bak

@contextmanager
def temp_file(contents, suffix=None, text=True):
    """Create a temporary file with the specified contents, and yield its path."""
    fd, f = tempfile.mkstemp(suffix=suffix, text=text)
    fp = os.fdopen(fd, 'w')
    fp.write(contents)
    fp.close()
    f = Path(f)
    logging.debug("TEMP created: %s", f)
    try:
        yield f
    finally:
        f.unlink()

@contextmanager
def temp_files(specs):
    """Create multiple temporary files and yield their paths."""
    tempfiles = []
    for spec in specs:
        if len(spec) == 3:
            contents, suffix, text = spec
        elif len(spec) == 2:
            contents, suffix, text = spec + (True,)
        else:
            raise ValueError("Bad spec for temp file: %s" % repr(spec))
        fd, f = tempfile.mkstemp(suffix=suffix, text=text)
        fp = os.fdopen(fd, 'w')
        fp.write(contents)
        fp.close()
        f = Path(f)
        tempfiles.append(f)
        logging.debug("TEMP created: %s", f)
    try:
        yield tuple(tempfiles)
    finally:
        map(Path.unlink, tempfiles)

@contextmanager
def environment(env):
    """Temporarily set values from env in the environment."""
    env_bak = os.environ
    os.environ = env_bak.copy()
    os.environ.update(env)
    try:
        yield
    finally:
        os.environ = env_bak

class RenderTest(unittest.TestCase):
    WORKDIR = Path(__file__).parent
    TPLDIR  = Path('resources') / 'tpl'
    DATADIR = Path('resources') / 'data'
    OUTDIR  = Path('resources') / 'out'

    def setUp(self):
        os.chdir(self.WORKDIR)

    def _render_prep(self, tpl, data, expected_output, extra_args):
        """ Helper for processing common options for test runners.

            data paths are expected to be relative
        """
        tpl = self.TPLDIR / tpl
        _data = data if isinstance(data, Iterable) and not isinstance(data, str) else [data]
        data = []
        for dspec in _data:
            dspec = str(dspec) if isinstance(dspec, Path) else dspec
            p, sep, modifiers = dspec.partition(DATASPEC_SEP)
            p = str(self.DATADIR / p) if (self.DATADIR / p).is_file() else p
            data.append('%s%s%s' % (p, sep, modifiers))
        expected_output = (Path(expected_output)
            if expected_output is not None
            else self.OUTDIR / tpl.stem).read_text()
        extra_args = [] if not extra_args else shlex.split(extra_args)

        return (str(tpl), data, expected_output, extra_args)

    def _class_for_name(self, fullcname):
        """ Helper for getting a class object from its string representation.
        """
        mname, _, cname = fullcname.rpartition('.')
        try:
            m = importlib.import_module(mname if mname else 'builtins')
            c = getattr(m, cname)
            return c
        except (ImportError, AttributeError):
            return None

    # pylint: disable=too-many-arguments
    def _render_test(self, tpl, data=None, expected_output=None,
        extra_args=None, exception=None, exception_msg=None):
        """ Helper for rendering `tpl` using `data` and checking the results
            against `expected_results`. Rendering is expected to succeed
            without errors.
        """
        tpl, data, expected_output, extra_args = self._render_prep(
            tpl, data, expected_output, extra_args)
        argv = ['dummy_command_name', *extra_args, tpl, *data]
        logging.debug("PASSED_ARGS render_command: %s", argv)

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

    def test_ENV(self):
        """ Tests rendering with environment variables.
        """
        with environment({"MYVAR": "test"}), temp_files((
            ("XXX{{ MYVAR }}XXX", ".j2"),
            ("MYVAR=bad", ".env"),
            ("XXXtestXXX", ".out"),
        )) as (tpl, in_ignored, out_normal):
            self._render_test(tpl, ":ENV",  out_normal)
            self._render_test(tpl, "-:ENV",  out_normal, extra_args='--')
            self._render_test(tpl, "%s:ENV" % (in_ignored),  out_normal)

    def test_env(self):
        """ Tests rendering with a single data file in env format.
        """
        # simple render
        self._render_test("nginx-env.conf.j2", "nginx_data.env")
        # file + fallback format
        self._render_test("nginx-env.conf.j2", "nginx_data_env", extra_args='--fallback-format=env')
        # file + format override
        self._render_test("nginx-env.conf.j2", "badext_nginx_data_env.json:env")
        # stdin + fallback format
        with stdin_from(self.DATADIR / "nginx_data_env"):
            self._render_test("nginx-env.conf.j2", "-", extra_args='--fallback-format=env')
        # stdin + format override
        with stdin_from(self.DATADIR / "nginx_data_env"):
            self._render_test("nginx-env.conf.j2", ":env")
        with stdin_from(self.DATADIR / "nginx_data_env"):
            self._render_test("nginx-env.conf.j2", "-:env", extra_args='--')
        # file + default fallback format - failure
        self._render_test("nginx.conf.j2", "nginx_data_env",
            exception='configparser.MissingSectionHeaderError',
            exception_msg='no section headers')

    def test_ini(self):
        """ Tests rendering with a single data file in ini format.
        """
        # simple render
        self._render_test("nginx.conf.j2", "nginx_data.ini")
        # file + fallback format
        self._render_test("nginx.conf.j2", "nginx_data_ini", extra_args='--fallback-format=ini')
        # file + format override
        self._render_test("nginx.conf.j2", "badext_nginx_data_ini.json:ini")
        # stdin + fallback format
        with stdin_from(self.DATADIR / "nginx_data_ini"):
            self._render_test("nginx.conf.j2", "-", extra_args='--fallback-format=ini')
        # stdin + format override
        with stdin_from(self.DATADIR / "nginx_data_ini"):
            self._render_test("nginx.conf.j2", ":ini")
        with stdin_from(self.DATADIR / "nginx_data_ini"):
            self._render_test("nginx.conf.j2", "-:ini", extra_args='--')
        # file + default fallback format - success
        self._render_test("nginx.conf.j2", "nginx_data_ini")

    def test_json(self):
        """ Tests rendering with a single data file in json format.
        """
        # simple render
        self._render_test("nginx.conf.j2", "nginx_data.json")
        # file + fallback format
        self._render_test("nginx.conf.j2", "nginx_data_json", extra_args='--fallback-format=json')
        # file + format override
        self._render_test("nginx.conf.j2", "badext_nginx_data_json.ini:json")
        # stdin + fallback format
        with stdin_from(self.DATADIR / "nginx_data_json"):
            self._render_test("nginx.conf.j2", "-", extra_args='--fallback-format=json')
        # stdin + format override
        with stdin_from(self.DATADIR / "nginx_data_json"):
            self._render_test("nginx.conf.j2", ":json")
        with stdin_from(self.DATADIR / "nginx_data_json"):
            self._render_test("nginx.conf.j2", "-:json", extra_args='--')
        # file + default fallback format - failure
        self._render_test("nginx.conf.j2", "nginx_data_json",
            exception='configparser.MissingSectionHeaderError',
            exception_msg='no section headers')

    def test_yaml(self):
        """ Tests rendering with a single data file in yaml format.
        """
        try:
            importlib.import_module('yaml')
        except ImportError:
            raise unittest.SkipTest('yaml module not available')
        # simple render
        self._render_test("nginx.conf.j2", "nginx_data.yaml")
        self._render_test("nginx.conf.j2", "nginx_data.yml")
        # file + fallback format
        self._render_test("nginx.conf.j2", "nginx_data_yaml", extra_args='--fallback-format=yaml')
        # file + format override
        self._render_test("nginx.conf.j2", "badext_nginx_data_yaml.json:yaml")
        # stdin + fallback format
        with stdin_from(self.DATADIR / "nginx_data_yaml"):
            self._render_test("nginx.conf.j2", "-", extra_args='--fallback-format=yaml')
        # stdin + format override
        with stdin_from(self.DATADIR / "nginx_data_yaml"):
            self._render_test("nginx.conf.j2", ":yaml")
        with stdin_from(self.DATADIR / "nginx_data_yaml"):
            self._render_test("nginx.conf.j2", "-:yaml", extra_args='--')
        # file + default fallback format - failure
        self._render_test("nginx.conf.j2", "nginx_data_yaml",
                exception='configparser.MissingSectionHeaderError',
                exception_msg='no section headers')

    def test_ignore_missing(self):
        """ Tests the -I/--ignore missing flag.
        """
        self._render_test("nginx.conf.j2", ["nginx_data_json", "nginx_data_missing"],
                exception='FileNotFoundError',
                exception_msg='nginx_data_missing',
                extra_args='-f json')
        self._render_test("nginx.conf.j2", ["nginx_data_json", "nginx_data_missing"],
                extra_args='-I -f json')
        self._render_test("nginx.conf.j2", ["nginx_data_json", "nginx_data_missing"],
                extra_args='--ignore-missing -f json')

    def test_undefined(self):
        """ Tests the -U/--undefined flag.
        """
        with temp_files((
            ("XXX{{ undefined_var }}XXX", ".j2"),
            ("{}", ".json"),
            ("XXXXXX", ".out"),
            ("XXX{{ undefined_var }}XXX", ".out"),
        )) as (tpl, data, out_normal, out_debug):
            # default (strict)
            self._render_test(tpl, data, out_normal,
                    exception='jinja2.exceptions.UndefinedError',
                    exception_msg='undefined_var')
            # strict
            self._render_test(tpl, data, out_normal,
                    exception='jinja2.exceptions.UndefinedError',
                    exception_msg='undefined_var',
                    extra_args='--undefined strict')
            # normal
            self._render_test(tpl, data, out_normal, extra_args='--undefined normal')
            # debug
            self._render_test(tpl, data, out_debug, extra_args='--undefined debug')
