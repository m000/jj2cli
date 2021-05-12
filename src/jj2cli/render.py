import io
import os
import logging

import jinja2
import jinja2.loaders

import imp, inspect

from . import filters

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

    UNDEFINED = {
        'strict': jinja2.StrictUndefined, # raises errors for undefined variables
        'normal': jinja2.Undefined,       # can be printed/iterated - error on other operations
        'debug': jinja2.DebugUndefined,   # return the debug info when printed
    }

    def __init__(self, cwd, undefined='strict', no_compact=False, j2_env_params={}):
        # Custom env params
        j2_env_params.setdefault('keep_trailing_newline', True)
        j2_env_params.setdefault('undefined', self.UNDEFINED[undefined])
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
