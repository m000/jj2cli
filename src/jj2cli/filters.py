""" Additional Jinja2 filters """
import os
import re
import sys
from jinja2 import is_undefined, pass_context

if sys.version_info >= (3,0):
    from shutil import which
elif sys.version_info >= (2,5):
    from shutilwhich import which
else:
    assert False, "Unsupported Python version: %s" % sys.version_info

if sys.version_info >= (3,3):
    from shlex import quote as sh_quote
elif sys.version_info >= (2,7):
    from pipes import quote as sh_quote
else:
    assert False, "Unsupported Python version: %s" % sys.version_info

def docker_link(value, format='{addr}:{port}'):
    """ Given a Docker Link environment variable value, format it into something else.
        XXX: The name of the filter is not very informative. This is actually a partial URI parser.

    This first parses a Docker Link value like this:

        DB_PORT=tcp://172.17.0.5:5432

    Into a dict:

    ```python
    {
      'proto': 'tcp',
      'addr': '172.17.0.5',
      'port': '5432'
    }
    ```

    And then uses `format` to format it, where the default format is '{addr}:{port}'.

    More info here: [Docker Links](https://docs.docker.com/userguide/dockerlinks/)

    :param value: Docker link (from an environment variable)
    :param format: The format to apply. Supported placeholders: `{proto}`, `{addr}`, `{port}`
    :return: Formatted string
    """
    # pass undefined values on down the pipeline
    if is_undefined(value):
        return value

    # Parse the value
    m = re.match(r'(?P<proto>.+)://' r'(?P<addr>.+):' r'(?P<port>.+)$', value)
    if not m:
        raise ValueError('The provided value does not seems to be a Docker link: {0}'.format(value))
    d = m.groupdict()

    # Format
    return format.format(**d)


def env(varname, default=None):
    """ Use an environment variable's value inside your template.

        This filter is available even when your data source is something other that the environment.

        Example:

        ```jinja2
        User: {{ user_login }}
        Pass: {{ "USER_PASSWORD"|env }}
        ```

        You can provide the default value:

        ```jinja2
        Pass: {{ "USER_PASSWORD"|env("-none-") }}
        ```

        For your convenience, it's also available as a function:

        ```jinja2
        User: {{ user_login }}
        Pass: {{ env("USER_PASSWORD") }}
        ```

        Notice that there must be quotes around the environment variable name
    """
    if default is not None:
        # With the default, there's never an error
        return os.getenv(varname, default)
    else:
        # Raise KeyError when not provided
        return os.environ[varname]

def align_suffix(text, delim, column=None, spaces_after_delim=1):
    """ Align the suffixes of lines in text, starting from the specified delim.
    """
    s=''

    if column is None or column == 'auto':
        column = max(map(lambda l: l.find(delim), text.splitlines()))
    elif column == 'previous':
        column = align_suffix.column_previous

    for l in map(lambda s: s.split(delim, 1), text.splitlines()):
        if len(l) < 2:
            # no delimiter occurs
            s += l[0].rstrip() + os.linesep
        elif l[0].strip() == '':
            # no content before delimiter - leave as-is
            s += l[0] + delim + l[1] + os.linesep
        else:
            # align
            s += l[0].rstrip().ljust(column) + delim + spaces_after_delim*' ' + l[1].strip() + os.linesep

    align_suffix.column_previous = column
    return s

align_suffix.column_previous = None


@pass_context
def ctxlookup(context, key):
    """ Lookup the value of a key in the template context.
    """
    v = context
    try:
        for k in key.split('.'):
            v = v[k]
        return v
    except KeyError:
        return context.environment.undefined(name=key)

def sh_opt(text, name, delim=" ", quote=False):
    """ Format text as a command line option.
    """
    if not text:
        return ''
    if quote:
        text = sh_quote(text)
    return '%s%s%s' % (name, delim, text)

def sh_optq(text, name, delim=" "):
    """ Quote text and format as a command line option.
    """
    return sh_opt(text, name, delim, quote=True)

# Filters to be loaded
EXTRA_FILTERS = {
    'sh_quote': sh_quote,
    'sh_which': which,
    'sh_expand': lambda s: os.path.expandvars(os.path.expanduser(s)),
    'sh_expanduser': os.path.expanduser,
    'sh_expandvars': os.path.expandvars,
    'sh_realpath': os.path.realpath,
    'sh_opt': sh_opt,
    'sh_optq': sh_optq,
    'ifelse': lambda t, truev, falsev: truev if t else falsev,
    'onoff': lambda t: 'on' if t else 'off',
    'yesno': lambda t: 'yes' if t else 'no',
    'docker_link': docker_link,
    'env': env,
    'align_suffix': align_suffix,
    'ctxlookup': ctxlookup,
}

