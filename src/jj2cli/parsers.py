import json
import logging
import os
import platform
import re
import sys
from pathlib import Path

import six
from six.moves import collections_abc, configparser

from .defaults import (CONTEXT_FORMATS, CONTEXT_FORMATS_ALIASES,
                       DATASPEC_COMPONENTS_MAX, DATASPEC_SEP, yaml_load)


class InputDataType:
    """Factory for creating jj2cli input data types.

    Instances of InputDataType are typically passed as type= arguments to the
    ArgumentParser add_argument() method.

    Keyword Arguments:
        - mode -- A string indicating how the file is to be opened. Accepts the
            same values as the builtin open() function.
        - bufsize -- The file's desired buffer size. Accepts the same values as
            the builtin open() function.
        - encoding -- The file's encoding. Accepts the same values as the
            builtin open() function.
        - errors -- A string indicating how encoding and decoding errors are to
            be handled. Accepts the same value as the builtin open() function.
    """
    def __init__(self, mode='r', bufsize=-1, encoding=None, errors=None):
        self._mode = mode
        self._bufsize = bufsize
        self._encoding = encoding
        self._errors = errors

    def __call__(self, dspec):
        # detect windows-style paths
        # NB: In Windows, filenames matching ^[a-z]$ always require a directory
        #     if the data spec has >1 components.
        if DATASPEC_SEP == ':' and platform.system() == 'Windows':
            m = re.match(r'^[a-z]:[^:]+', dspec, re.I)
        else:
            m = None

        # parse supplied components
        if m is None:
            # normal case
            dspec = dspec.rsplit(DATASPEC_SEP, DATASPEC_COMPONENTS_MAX-1)
        else:
            # matched windows drive at the start of the data spec
            dspec = dspec[m.span()[1] + 1:]
            dspec = [m.group(0)] + dspec.rsplit(DATASPEC_SEP, DATASPEC_COMPONENTS_MAX-2)

        # pad missing components
        dspec += (DATASPEC_COMPONENTS_MAX - len(dspec))*[None]

        # post-process parsed components
        path, fmt, ctx_dst = dspec
        path = Path(path) if path not in ['', '-'] else None
        if fmt in CONTEXT_FORMATS_ALIASES:
            # forced format is case-sensitive
            fmt = CONTEXT_FORMATS_ALIASES[fmt]
        elif fmt in ['', '?', None] and path is not None and path.suffix[1:] in CONTEXT_FORMATS_ALIASES:
            # file extensions are case-insensitive
            fmt = CONTEXT_FORMATS_ALIASES[path.suffix[1:].lower()]
        else:
            fmt = None
        ctx_dst = None if ctx_dst in ['', None] else None

        # check for formats that don't use file input
        if fmt == 'ENV' and path is not None:
            logging.warning("Ignoring source for %s format: %s", fmt, path)
            path = None

        # open stream and return InputData object
        if path is None:
            if fmt == 'ENV':
                iostr = None
            elif 'r' in self._mode:
                iostr = sys.stdin
            elif 'w' in self._mode:
                # XXX: Is there a use-case we could use this?
                iostr = sys.stdout
            else:
                raise ValueError("Invalid mode %r for std streams." % self._mode)
        else:
            try:
                iostr = path.open(self._mode, self._bufsize, self._encoding, self._errors)
            except FileNotFoundError as e:
                # FileNotFoundError will be reraised later by InputData.parse(),
                # depending on # whether the -I flag has been specified.
                iostr = e

        return InputData(iostr, fmt, ctx_dst)


class InputData:
    def __init__(self, iostr, fmt=None, ctx_dst=None):
        self._iostr = iostr
        self._fmt = fmt
        self._ctx_dst = ctx_dst

    def __repr__(self):
        ioinfo = (self._iostr
                if self._iostr is None or isinstance(self._iostr, FileNotFoundError)
                else '%s:%s:%s' % (self._iostr.name, self._iostr.mode, self._iostr.encoding))
        return '%s(%s, %s, %s)' % (type(self).__name__, ioinfo, self.fmt, self._ctx_dst)

    @property
    def fmt(self):
        return self._fmt

    @fmt.setter
    def set_fmt(self, v):
        if v in CONTEXT_FORMATS:
            self._fmt = v
        else:
            raise ValueError("Invalid format %s." % v)

    def parse(self, ignore_missing=False, fallback_format='ini'):
        """Parses the data from the data stream of the object.
        If ignore_missing is set, missing files will produce and empty dict.
        If no format is set for the object, fallback_format is used.
        """
        fmt = self._fmt if self._fmt is not None else fallback_format
        if isinstance(self._iostr, FileNotFoundError):
            if ignore_missing is True:
                return {}
            else:
                raise self._iostr
        return getattr(self, '_parse_%s' % fmt)()

    def _parse_ENV(self):
        """Loads data from shell environment.
        """
        return os.environ.copy()

    def _parse_env(self):
        """Parses an env-like format.
        XXX
        """
        normalize = lambda t: (t[0].strip(), t[1].strip())
        return dict([
            normalize(ln.split('=', 1))
            for ln in self._iostr
            if '=' in ln
        ])

    def _parse_ini(self):
        """Parses windows-style ini files.
        """
        class MyConfigParser(configparser.ConfigParser):
            def as_dict(self):
                """ Export as dict
                :rtype: dict
                """
                d = dict(self._sections)
                for k in d:
                    d[k] = dict(self._defaults, **d[k])
                    d[k].pop('__name__', None)
                return d
        ini = MyConfigParser()
        ini.readfp(self._iostr)
        return ini.as_dict()

    def _parse_json(self):
        return json.load(self._iostr)

    def _parse_yaml(self):
        if yaml_load is None:
            raise RuntimeError("YAML data parser invoked, but no YAML support is present.")
        return yaml_load(self._iostr)


def dict_squash(d, u):
    """ Squashes contents of u on d.
    :param d: Dictionary to be updated.
    :type dict: dict
    :param u: Dictionary with updates to be applied.
    :type dict: dict
    :return: Updated version of d.
    :rtype: dict
    """
    for k, v in six.iteritems(u):
        dv = d.get(k, {})
        if not isinstance(dv, collections_abc.Mapping):
            d[k] = v
        elif isinstance(v, collections_abc.Mapping):
            d[k] = dict_squash(dv, v)
        else:
            d[k] = v
    return d
