[![Build Status](https://travis-ci.org/kolypto/j2cli.svg)](https://travis-ci.org/kolypto/j2cli)
[![Pythons](https://img.shields.io/badge/python-2.6%20%7C%202.7%20%7C%203.4%E2%80%933.7%20%7C%20pypy-blue.svg)](.travis.yml)

# j2cli - Jinja2 command-line tool

`j2cli` is a command-line tool for templating in shell-scripts, leveraging the
[Jinja2](http://jinja.pocoo.org/docs/) library.
It supports [several formats](#supported-formats) for loading the context
used for rendering the Jinja2 templates. Loading environment variables
as rendering context is also supported, which makes j2cli a great pair with
[Docker][docker].
Moreover, j2cli supports using [multiple input data files](#context-squashing),
eliminating the need to seperately preprocess data files with external tools.

## Getting started

### Installation
```sh
# simple install
$ pip install j2cli

# install with yaml support
$ pip install j2cli[yaml]
```

### Basic usage
```sh
# render config from template config.j2
$ j2 config.j2 config.json -o config

# render using yaml data from stdin
$ wget -O - http://example.com/config.yml | j2 --format=yml config.j2
```

For an extensive list of examples, see [docs/examples.md](docs/examples.md).

## Context data

### Supported formats
j2cli supports importing context from several different sources:
  
  * [JSON][json]: A language-independent data-serialization format, originally derived
    from JavaScript.
  * [YAML][yaml]: A data-serialization language, designed to be human-readable.
  * [INI][ini]: Windows-style configuration files.
  * env: Simple [unix-style][ini] environment variable assignments.

For examples with each supported format, see [docs/formats.md](docs/formats.md).

### Context squashing
One of the main strengths of j2cli is that it is not limited to using a single
data file as context. Several data files—perhaps in different formats—can be
used to construct the rendering context.
As the contents of the data files may "overlap", j2cli *recursively squashes*
their contents to produce the context that will be used for rendering.
The order of squashing is *from left to right*. I.e. the contents of a data file
may be overriden by any data files specified *after it* on the command line.

Here is a simple example illustrating how context squashing works:

  * `a.json` contents:
     ```json
     {"a": 1, "c": {"x": 2, "y": 3}}
     ```
  * `b.json` contents:
     ```json
     {"b": 2, "c": {"y": 4}}
     ```
  * effective context when rendering with `a.json` and `b.json` (in that order):
     ```json
     {"a": 1, "b": 2, "c": {"x": 2, "y": 4}}
     ```

### Loading data as a context subtree
By default, loaded data are squashed with the top-level context. However, this
may not always be desired, especially when . E.g., when you load all the environment variables
from the shell, the variables may overwri

For this, j2cli supports attaching the data from a
source under a variable of the top-level context.


## Reference
`j2` accepts the following arguments:

* `template`: Jinja2 template file to render
* `data`: (optional) path to the data used for rendering.
    The default is `-`: use stdin. Specify it explicitly when using env!

Options:

* `--format, -f`: format for the data file. The default is `?`: guess from file extension.
* `--import-env VAR, -e EVAR`: import all environment variables into the template as `VAR`.
    To import environment variables into the global scope, give it an empty string: `--import-env=`.
    (This will overwrite any existing variables!)
* `-o outfile`: Write rendered template to a file
* `--undefined`: Allow undefined variables to be used in templates (no error will be raised)

* `--filters filters.py`: Load custom Jinja2 filters and tests from a Python file.
    Will load all top-level functions and register them as filters.
    This option can be used multiple times to import several files.
* `--tests tests.py`: Load custom Jinja2 filters and tests from a Python file.
* `--customize custom.py`: A Python file that implements hooks to fine-tune the j2cli behavior.
    This is fairly advanced stuff, use it only if you really need to customize the way Jinja2 is initialized.
    See [Customization](#customization) for more info.

There is some special behavior with environment variables:

* When `data` is not provided (data is `-`), `--format` defaults to `env` and thus reads environment variables
* When `--format=env`, it can read a special "environment variables" file made like this: `env > /tmp/file.env`

## Extras

### Filters
For convenience, j2cli offers several additional Jinja2 filters that can be used
in your templates. These filters should help you avoid having to implement an 
[advanced customization module](#advanced-customization) for many use cases.

See [docs/filters.md](docs/filters.md) for details on the available filters.

### Advanced customization
j2cli offers several *hooks* that allow for more advanced customization of its
operation. This includes:

  * passing additional keywords to Jinja2 environment
  * modifying the context before it's used for rendering
  * registering custom filters and tests

See [docs/advanced.md](docs/advanced.md) for details on advanced customization.

## Credits
j2cli is inspired by Matt Robenolt's [jinja2-cli][jinja2-cli].

[docker]: http://www.docker.com/
[json]: https://en.wikipedia.org/wiki/JSON
[yaml]: https://en.wikipedia.org/wiki/YAML
[ini]: https://en.wikipedia.org/wiki/INI_file
[env]: https://en.wikipedia.org/wiki/Environment_variable#Unix
[jinja2-cli]: https://github.com/mattrobenolt/jinja2-cli

