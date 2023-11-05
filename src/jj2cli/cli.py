import io
import os
import sys
import argparse
import logging
from functools import reduce

import jinja2
import jinja2.meta
import jinja2.loaders

import imp

from . import __version__
from . import filters
from .context import FORMATS
from .context import parse_data_spec, read_context_data, dict_update_deep
from .customize import CustomizationModule
from .render import Jinja2TemplateRenderer

# available log levels, adjusted with -v at command line
LOGLEVELS = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]

# format to use for logging
LOGFORMAT = '%(levelname)s: %(message)s'


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
        description='Renders Jinja2 templates from the command line.',
        epilog='',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    p_input = parser.add_argument_group('input options')
    p_output = parser.add_argument_group('output options')
    p_custom = parser.add_argument_group('customization options')

    ### optional arguments ##########################################
    parser.add_argument('-V', '--version', action='version',
            version='jj2cli {0}, Jinja2 {1}'.format(*version_info))
    parser.add_argument('-v', '--verbose', action='count', default=0,
            help='Increase verbosity.')
    ### input options ###############################################
    p_input.add_argument('template', help='Template file to process.')
    p_input.add_argument('data', nargs='+', default=[],
            help='Input data specification. '
            'Multiple sources in different formats can be specified. '
            'The different sources will be squashed into a singled dict. '
            'The format is <source>[:<format>[:<context_dest>]]. '
            'Parts of the specification may be left empty. '
            'See examples at the end of the help.')
    p_input.add_argument('-U', '--undefined', default='strict',
            dest='undefined', choices=Jinja2TemplateRenderer.UNDEFINED.keys(),
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
            help='Load custom jj2cli behavior from a Python file.')

    args = parser.parse_args(argv[1:])
    logging.basicConfig(format=LOGFORMAT, level=LOGLEVELS[min(args.verbose, len(LOGLEVELS)-1)])
    logging.debug("PARSED_ARGS render_command: %s", args)

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

    # Squash data into a single context.
    context = reduce(dict_update_deep, data, {})

    # Apply final customizations.
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
    result = renderer.render(args.template, context)

    # -o
    if args.output_file:
        with io.open(args.output_file, 'wt', encoding='utf-8') as f:
            f.write(result.decode('utf-8'))
            f.close()
        return b''

    # Finish
    return result


def main():
    """ CLI entry point for rendering templates. """
    try:
        output = render_command(sys.argv)
    except SystemExit:
        return 1
    outstream = getattr(sys.stdout, 'buffer', sys.stdout)
    outstream.write(output)
