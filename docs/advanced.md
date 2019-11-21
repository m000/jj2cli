Customization
=============

j2cli now allows you to customize the way the application is initialized:

* Pass additional keywords to Jinja2 environment
* Modify the context before it's used for rendering
* Register custom filters and tests

This is done through *hooks* that you implement in a customization file in Python language.
Just plain functions at the module level.

The following hooks are available:

* `j2_environment_params() -> dict`: returns a `dict` of additional parameters for
    [Jinja2 Environment](http://jinja.pocoo.org/docs/2.10/api/#jinja2.Environment).
* `j2_environment(env: Environment) -> Environment`: lets you customize the `Environment` object.
* `alter_context(context: dict) -> dict`: lets you modify the context variables that are going to be
    used for template rendering. You can do all sorts of pre-processing here.
* `extra_filters() -> dict`: returns a `dict` with extra filters for Jinja2
* `extra_tests() -> dict`: returns a `dict` with extra tests for Jinja2

All of them are optional.

The example customization.py file for your reference:

```python
#
# Example customize.py file for j2cli
# Contains potional hooks that modify the way j2cli is initialized


def j2_environment_params():
    """ Extra parameters for the Jinja2 Environment """
    # Jinja2 Environment configuration
    # http://jinja.pocoo.org/docs/2.10/api/#jinja2.Environment
    return dict(
        # Just some examples

        # Change block start/end strings
        block_start_string='<%',
        block_end_string='%>',
        # Change variable strings
        variable_start_string='<<',
        variable_end_string='>>',
        # Remove whitespace around blocks
        trim_blocks=True,
        lstrip_blocks=True,
        # Enable line statements:
        # http://jinja.pocoo.org/docs/2.10/templates/#line-statements
        line_statement_prefix='#',
        # Keep \n at the end of a file
        keep_trailing_newline=True,
        # Enable custom extensions
        # http://jinja.pocoo.org/docs/2.10/extensions/#jinja-extensions
        extensions=('jinja2.ext.i18n',),
    )


def j2_environment(env):
    """ Modify Jinja2 environment

    :param env: jinja2.environment.Environment
    :rtype: jinja2.environment.Environment
    """
    env.globals.update(
        my_function=lambda v: 'my function says "{}"'.format(v)
    )
    return env


def alter_context(context):
    """ Modify the context and return it """
    # An extra variable
    context['ADD'] = '127'
    return context


def extra_filters():
    """ Declare some custom filters.

        Returns: dict(name = function)
    """
    return dict(
        # Example: {{ var | parentheses }}
        parentheses=lambda t: '(' + t + ')',
    )


def extra_tests():
    """ Declare some custom tests

        Returns: dict(name = function)
    """
    return dict(
        # Example: {% if a|int is custom_odd %}odd{% endif %}
        custom_odd=lambda n: True if (n % 2) else False
    )

#

```

