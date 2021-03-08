import io, os, sys
import argparse
import logging
from functools import reduce

import jinja2
import jinja2.loaders
from . import __version__

import imp, inspect

from .context import FORMATS
from .context import parse_data_spec, read_context_data, dict_update_deep
from .extras import filters
from .extras.customize import CustomizationModule

# available log levels, adjusted with -v at command line
LOGLEVELS = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]

# format to use for logging
LOGFORMAT = '%(levelname)s: %(message)s'

# map keywords to to Jinja2 error handlers
UNDEFINED = {
    'strict': jinja2.StrictUndefined, # raises errors for undefined variables
    'normal': jinja2.Undefined,       # can be printed/iterated - error on other operations
    'debug': jinja2.DebugUndefined,   # return the debug info when printed
}

class FilePathLoader(jinja2.BaseLoader):
    """ Custom Jinja2 template loader which just loads a single template file """

    def __init__(self, cwd, encoding='utf-8'):
        self.cwd = cwd
        self.encoding = encoding

    def get_source(self, environment, template):
        # Path
        filename = os.path.join(self.cwd, template)

        # Read
        try:
            with io.open(template, 'rt', encoding=self.encoding) as f:
                contents = f.read()
        except IOError:
            raise jinja2.TemplateNotFound(template)

        # Finish
        uptodate = lambda: False
        return contents, filename, uptodate


class Jinja2TemplateRenderer(object):
    """ Template renderer """

    ENABLED_EXTENSIONS=(
        'jinja2.ext.i18n',
        'jinja2.ext.do',
        'jinja2.ext.loopcontrols',
    )

    def __init__(self, cwd, undefined='strict', no_compact=False, j2_env_params={}):
        # Custom env params
        j2_env_params.setdefault('keep_trailing_newline', True)
        j2_env_params.setdefault('undefined', UNDEFINED[undefined])
        j2_env_params.setdefault('trim_blocks', not no_compact)
        j2_env_params.setdefault('lstrip_blocks', not no_compact)
        j2_env_params.setdefault('extensions', self.ENABLED_EXTENSIONS)
        j2_env_params.setdefault('loader', FilePathLoader(cwd))

        # Environment
        self._env = jinja2.Environment(**j2_env_params)
        self._env.globals.update(dict(
            env=filters.env
        ))

    def register_filters(self, filters):
        self._env.filters.update(filters)

    def register_tests(self, tests):
        self._env.tests.update(tests)

    def import_filters(self, filename):
        self.register_filters(self._import_functions(filename))

    def import_tests(self, filename):
        self.register_tests(self._import_functions(filename))

    def _import_functions(self, filename):
        m = imp.load_source('imported-funcs', filename)
        return dict((name, func) for name, func in inspect.getmembers(m) if inspect.isfunction(func))

    def render(self, template_path, context):
        """ Render a template
        :param template_path: Path to the template file
        :type template_path: basestring
        :param context: Template data
        :type context: dict
        :return: Rendered template
        :rtype: basestring
        """
        return self._env \
            .get_template(template_path) \
            .render(context) \
            .encode('utf-8')


def render_command(argv):
    """ Pure render command
    :param argv: Command-line arguments
    :type argv: list
    :return: Rendered template
    :rtype: basestring
    """
    version_info = (__version__, jinja2.__version__)
    formats_names = list(FORMATS.keys())
    parser = argparse.ArgumentParser(
        description='Command-line interface to Jinja2 for templating in shell scripts.',
        epilog='',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    p_input = parser.add_argument_group('input options')
    p_output = parser.add_argument_group('output options')
    p_custom = parser.add_argument_group('customization options')

    ### optional arguments ##########################################
    parser.add_argument('-V', '--version', action='version',
            version='j2cli {0}, Jinja2 {1}'.format(*version_info))
    parser.add_argument('-v', '--verbose', action='count', default=0,
            help='Increase verbosity.')
    ### input options ###############################################
    p_input.add_argument('template', help='Template file to process.')
    p_input.add_argument('data', nargs='+', default=[],
            help='Input data specification. '
            'Multiple sources in different formats can be specified. '
            'The different sources will be squashed into a singled dict. '
            'The format is <source>:<context_dest>:<format>. '
            'Parts of the specification that are not needed can be ommitted. '
            'See examples at the end of the help.')
    p_input.add_argument('-U', '--undefined', default='strict',
            dest='undefined', choices=UNDEFINED.keys(),
            help='Set the Jinja2 beahaviour for undefined variables.)')
    p_input.add_argument('-I', '--ignore-missing', action='store_true',
            help='Ignore any missing data files.')
    p_input.add_argument('-f', '--fallback-format',
            default='ini', choices=formats_names,
            help='Specify fallback data format. '
            'Used for data with no specified format and no appropriate extension.')
    ### output options ##############################################
    p_output.add_argument('-o', metavar='outfile', dest='output_file',
            help="Output to a file instead of stdout.")
    p_output.add_argument('--no-compact', action='store_true', dest='no_compact',
            help='Do not compact space around Jinja2 blocks.')
    ### customization ###############################################
    p_custom.add_argument('--filters', nargs='+', default=[],
            metavar='python-file', dest='filters',
            help='Load the top-level functions from the specified file(s) as Jinja2 filters.')
    p_custom.add_argument('--tests', nargs='+', default=[],
            metavar='python-file', dest='tests',
            help='Load the top-level functions from the specified file(s) as Jinja2 tests.')
    p_custom.add_argument('--customize', default=None,
            metavar='python-file', dest='customize',
            help='Load custom j2cli behavior from a Python file.')

    args = parser.parse_args(argv[1:])
    logging.basicConfig(format=LOGFORMAT, level=LOGLEVELS[min(args.verbose, len(LOGLEVELS)-1)])
    logging.debug("Parsed arguments: %s", args)

    # Parse data specifications
    dspecs = [parse_data_spec(d, fallback_format=args.fallback_format) for d in args.data]

    # Customization
    if args.customize is not None:
        customize = CustomizationModule(
            imp.load_source('customize-module', args.customize)
        )
    else:
        customize = CustomizationModule(None)

    # Read data based on specs
    data = [read_context_data(*dspec, args.ignore_missing) for dspec in dspecs]

    # Squash data into a single context
    context = reduce(dict_update_deep, data, {})

    # Apply final customizations
    context = customize.alter_context(context)

    # Renderer
    renderer = Jinja2TemplateRenderer(os.getcwd(), args.undefined, args.no_compact, j2_env_params=customize.j2_environment_params())
    customize.j2_environment(renderer._env)

    # Filters, Tests
    renderer.register_filters(filters.EXTRA_FILTERS)
    for fname in args.filters:
        renderer.import_filters(fname)
    for fname in args.tests:
        renderer.import_tests(fname)

    renderer.register_filters(customize.extra_filters())
    renderer.register_tests(customize.extra_tests())

    # Render
    try:
        result = renderer.render(args.template, context)
    except jinja2.exceptions.UndefinedError as e:
        # When there's data at stdin, tell the user they should use '-'
        try:
            stdin_has_data = stdin is not None and not stdin.isatty()
            if args.format == 'env' and args.data == None and stdin_has_data:
                extra_info = (
                    "\n\n"
                    "If you're trying to pipe a .env file, please run me with a '-' as the data file name:\n"
                    "$ {cmd} {argv} -".format(cmd=os.path.basename(sys.argv[0]), argv=' '.join(sys.argv[1:]))
                )
                e.args = (e.args[0] + extra_info,) + e.args[1:]
        except:
            # The above code is so optional that any, ANY, error, is ignored
            pass

        # Proceed
        raise

    # -o
    if args.output_file:
        with io.open(args.output_file, 'wt', encoding='utf-8') as f:
            f.write(result.decode('utf-8'))
            f.close()
        return b''

    # Finish
    return result



def main():
    """ CLI Entry point """
    try:
        output = render_command(sys.argv)
    except SystemExit:
        return 1
    outstream = getattr(sys.stdout, 'buffer', sys.stdout)
    outstream.write(output)
