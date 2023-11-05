import itertools

# Jinja2 extensions loaded by jj2cli.
JINJA2_ENABLED_EXTENSIONS = (
        'jinja2.ext.i18n',
        'jinja2.ext.do',
        'jinja2.ext.loopcontrols',
)

# Set yaml_loader for parsers.
try:
    import yaml
    try:
        _yaml_loader = yaml.FullLoader
    except AttributeError:
        _yaml_loader = yaml.SafeLoader
    yaml_load = lambda iostr: yaml.load(iostr, Loader=_yaml_loader)
except ImportError:
    yaml_load = None

# Supported context formats.
CONTEXT_FORMATS = ['env', 'ENV', 'ini', 'json', 'yaml']
if yaml_load is None:
    CONTEXT_FORMATS.remove('yaml')

# Format aliases dictionary.
# COMPAT: Chaining used instead of unpacking (*) for backwards compatibility.
CONTEXT_FORMATS_ALIASES = dict(itertools.chain(
        zip(CONTEXT_FORMATS, CONTEXT_FORMATS),
        filter(lambda t: t[1] in CONTEXT_FORMATS, [('yml', 'yaml')])
))

# Variables for parsing dataspecs.
DATASPEC_SEP = ':'
DATASPEC_COMPONENTS_MAX = 3

# Supported formats for outputting template dependencies.
DEPENDENCIES_OUTPUT_FORMATS = ['make', 'json', 'yaml', 'delim']
if yaml_load is None:
    DEPENDENCIES_OUTPUT_FORMATS.remove('yaml')
