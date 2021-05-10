import six
import os
import sys
import re
import logging
import platform
import collections
from pathlib import Path

# Adjust for aliases removed in python 3.8
try:
    CollectionsAbc = collections.abc
except AttributeError:
    CollectionsAbc = collections

#region Parsers

def _parse_ini(data_string):
    """ INI data input format.

    data.ini:

    ```
    [nginx]
    hostname=localhost
    webroot=/var/www/project
    logs=/var/log/nginx/
    ```

    Usage:

        $ j2 config.j2 data.ini
        $ cat data.ini | j2 --format=ini config.j2
    """
    # Override
    class MyConfigParser(ConfigParser.ConfigParser):
        def as_dict(self):
            """ Export as dict
            :rtype: dict
            """
            d = dict(self._sections)
            for k in d:
                d[k] = dict(self._defaults, **d[k])
                d[k].pop('__name__', None)
            return d

    # Parse
    ini = MyConfigParser()
    ini.readfp(ini_file_io(data_string))

    # Export
    return ini.as_dict()

def _parse_json(data_string):
    """ JSON data input format

    data.json:

    ```
    {
        "nginx":{
            "hostname": "localhost",
            "webroot": "/var/www/project",
            "logs": "/var/log/nginx/"
        }
    }
    ```

    Usage:

        $ j2 config.j2 data.json
        $ cat data.json | j2 --format=ini config.j2
    """
    return json.loads(data_string)

def _parse_yaml(data_string):
    """ YAML data input format.

    data.yaml:

    ```
    nginx:
      hostname: localhost
      webroot: /var/www/project
      logs: /var/log/nginx
    ```

    Usage:

        $ j2 config.j2 data.yml
        $ cat data.yml | j2 --format=yaml config.j2
    """
    # Loader
    try:
        # PyYAML 5.1 supports FullLoader
        Loader = yaml.FullLoader
    except AttributeError:
        # Have to use SafeLoader for older versions
        Loader = yaml.SafeLoader
    # Done
    return yaml.load(data_string, Loader=Loader)

def _parse_env(data_string):
    """ Data input from environment variables.

    Render directly from the current environment variable values:

        $ j2 config.j2

    Or alternatively, read the values from a dotenv file:

    ```
    NGINX_HOSTNAME=localhost
    NGINX_WEBROOT=/var/www/project
    NGINX_LOGS=/var/log/nginx/
    ```

    And render with:

        $ j2 config.j2 data.env
        $ env | j2 --format=env config.j2

    If you're going to pipe a dotenv file into `j2`, you'll need to use "-" as the second argument to explicitly:

        $ j2 config.j2 - < data.env
    """
    # Parse
    if isinstance(data_string, six.string_types):
        data = dict(filter(
            lambda l: len(l) == 2 ,
            (
                list(map(
                    str.strip,
                    line.split('=', 1)
                ))
                for line in data_string.split("\n"))
        ))
    else:
        data = data_string

    # Finish
    return data


FORMATS = {
    'ini':  _parse_ini,
    'json': _parse_json,
    'yaml': _parse_yaml,
    'env': _parse_env
}

FORMATS_ALIASES = dict(zip(FORMATS.keys(), FORMATS.keys()))
FORMATS_ALIASES.update({
    'yml': 'yaml',
})

#endregion



#region Imports

# JSON: simplejson | json
try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        del FORMATS['json']

# INI: Python 2 | Python 3
try:
    import ConfigParser
    from io import BytesIO as ini_file_io
except ImportError:
    import configparser as ConfigParser
    from io import StringIO as ini_file_io

# YAML
try:
    import yaml
except ImportError:
    del FORMATS['yaml']

#endregion

def dict_update_deep(d, u):
    """ Performs a deep update of d with data from u.
    :param d: Dictionary to be updated.
    :type dict: dict
    :param u: Dictionary with updates to be applied.
    :type dict: dict
    :return: Updated version of d.
    :rtype: dict
    """
    for k, v in six.iteritems(u):
        dv = d.get(k, {})
        if not isinstance(dv, CollectionsAbc.Mapping):
            d[k] = v
        elif isinstance(v, CollectionsAbc.Mapping):
            d[k] = dict_update_deep(dv, v)
        else:
            d[k] = v
    return d

def parse_data_spec(dspec, fallback_format='ini'):
    """ Parse a data file specification.
    :param dspec: Data file specification in format <path>[:<format>[:ctx_dst]].
    :type dspec: str
    :param fallback_format: Format to fallback to if no format is set/guessed.
    :type fallback_format: str
    :return: (path, format, ctx_dst)
    :rtype: tuple
    """
    MAX_DSPEC_COMPONENTS = 3
    DSPEC_SEP = ':'

    # detect windows-style paths
    # NB: In Windows filenames matching [a-z] require a directory prefix.
    if DSPEC_SEP == ':' and platform.system() == 'Windows':
        m = re.match(r'^[a-z]:[^:]+', dspec, re.I)
    else:
        m = None

    # parse supplied components
    if m is None:
        dspec = dspec.rsplit(DSPEC_SEP, MAX_DSPEC_COMPONENTS-1)
    else:
        dspec = dspec[m.span()[1] + 1:]
        dspec = [m.group(0)] + dspec.rsplit(DSPEC_SEP, MAX_DSPEC_COMPONENTS-2)

    # pad missing components
    dspec += (MAX_DSPEC_COMPONENTS - len(dspec))*[None]

    # post-process parsed components
    path, fmt, ctx_dst = dspec
    path = Path(path) if path not in ['', '-'] else None
    if fmt in FORMATS_ALIASES:
        fmt = FORMATS_ALIASES[fmt]
    elif fmt in ['', '?', None] and path.suffix[1:] in FORMATS_ALIASES:
        fmt = FORMATS_ALIASES[path.suffix[1:]]
    else:
        fmt = FORMATS_ALIASES[fallback_format]
    ctx_dst = None if ctx_dst in ['', None] else None

    return (path, fmt, ctx_dst)

def read_context_data(source, fmt, ctx_dst, ignore_missing=False):
    """ Read context data into a dictionary
    :param source: Source file to read from.
                   Use '-' for stdin, None to read environment (requires fmt == 'env'.)
    :type source: str|None
    :param ctx_dst: Variable name that will contain the loaded data in the returned dict.
                    If None, data are loaded to the top-level of the dict.
    :type ctx_dst: str|None
    :param fmt: Data format of the loaded data.
    :type fmt: str
    :param ignore_missing: Flag whether missing files should be ignored and return
                           an empty context rather than raising an error.
    :type ignore_missing: bool|False
    :return: Dictionary with the context data.
    :rtype: dict
    """
    logging.debug("Reading data: source=%s, ctx_dst=%s, fmt=%s", source, ctx_dst, fmt)

    # Special case: environment variables
    if source == '-':
        # read data from stdin
        data = sys.stdin.read()
    elif source is not None:
        # read data from file
        try:
            with open(source, 'r') as sourcef:
                data = sourcef.read()
        except FileNotFoundError as e:
            if ignore_missing:
                logging.warning('skipping missing input data file "%s"', source)
                return {}
            raise e
    else:
        data = None

    if data is None and fmt == 'env':
        # load environment to context dict
        if sys.version_info[0] > 2:
            context = os.environ.copy()
        else:
            # python2: encode environment variables as unicode
            context = dict((k.decode('utf-8'), v.decode('utf-8')) for k, v in os.environ.items())
    elif data is not None:
        # parse data to context dict
        context = FORMATS[fmt](data)
    else:
        # this shouldn't have happened
        logging.error("Can't read data in %s format from %s.", fmt, source)
        sys.exit(1)

    if ctx_dst is not None:
        return {ctx_dst: context}

    return context
