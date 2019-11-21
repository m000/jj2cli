[![Build Status](https://travis-ci.com/m000/j2cli.svg?branch=heresy-refactor)](https://travis-ci.com/m000/j2cli/tree/heresy-refactor)
[![Pythons](https://img.shields.io/badge/python%7B3.8%2C%203.9%7D-blue.svg)](.travis.yml)
# jj2cli - Juiced Jinja2 command-line tool

jj2cli (previously `j2cli`) is a command-line tool for templating in
shell-scripts, leveraging the [Jinja2](http://jinja.pocoo.org/docs/)
library.
It supports [several formats](#supported-formats) for loading the context
used for rendering the Jinja2 templates. Loading environment variables as
rendering context is also supported.

> **Warning**
> This branch is WIP, towards completely spinning-off the tool from
> the [upstream][j2cli]. The aim is to keep the HEAD of the branch
> usable. However, until the spin-off is complete you should expect:
>   - frequent history rewrites
>   - cli option changes
>   - breakage if you use an older Python (<3.10)
>
> Having said that, you are welcome to use this branch and start an
> issue if you encounter any problems or have feedback.

## jj2cli features and roadmap

The following planned/implemented features differentiate jj2cli from
its upstreams.

- [ ] Focus on modern Python, initially ≥3.10. This is to allow modernizing
      the codebase. Support for Python ≥3.8 may be considered later, if there
      are appealing reasons for that.
- [ ] Switch to more modern tooling.
  * [x] [pytest][pytest] (to replace [nose][nose])
  * [ ] [ruff][ruff] (to replace [prospector][prospector])
- [ ] Rendering of multiple templates using the same context in one go.
      Rendering a couple of dozens template one-by-one is fairly slow.
      This should make the tool snappier to use, but also means that
      the command line interface will need to change.
- [ ] Template dependency analysis to allow better integration with tools
      like [make][make]. Such tools are otherwise oblivious to Jinja2 template
      inheritance/inclusion.
- [ ] Extended library of Jinja2 filters. This should allow using jj2cli
      out of the box in a wider range of use cases.
- [x] Support of *context squashing* (see [below](#context-squashing)),
      to eliminate the need to preprocess context data with external tools.

## Getting started

### Installation
```sh
# simple install
$ pip install jj2cli 
# install with yaml support
$ pip install jj2cli yaml]
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
jj2cli supports importing context from several different sources:
  
  * [JSON][json]: A language-independent data-serialization format, originally derived
    from JavaScript.
  * [YAML][yaml]: A data-serialization language, designed to be human-readable.
  * [INI][ini]: Windows-style configuration files.
  * env: Simple [unix-style][ini] environment variable assignments.

For examples with each supported format, see [docs/formats.md](docs/formats.md).

### Context squashing
One of the main strengths of jj2cli is that it is not limited to using a single
data file as context. Several data files—perhaps in different formats—can be
used to construct the rendering context.
As the contents of the data files may "overlap", jj2cli *recursively squashes*
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

For this, jj2cli supports attaching the data from a
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
* `--undefined={strict, normal, debug}`: Specify the behaviour of jj2 for undefined
    variables. Refer to [Jinja2 docs][jinja2-undefined] for details.
* `--filters filters.py`: Load custom Jinja2 filters and tests from a Python file.
    Will load all top-level functions and register them as filters.
    This option can be used multiple times to import several files.
* `--tests tests.py`: Load custom Jinja2 filters and tests from a Python file.
* `--customize custom.py`: A Python file that implements hooks to fine-tune the jj2cli behavior.
    This is fairly advanced stuff, use it only if you really need to customize the way Jinja2 is initialized.
    See [Customization](#customization) for more info.

There is some special behavior with environment variables:

* When `data` is not provided (data is `-`), `--format` defaults to `env` and thus reads environment variables
* When `--format=env`, it can read a special "environment variables" file made like this: `env > /tmp/file.env`

## Extras

### Filters
For convenience, jj2cli offers several additional Jinja2 filters that can be used
in your templates. These filters should help you avoid having to implement an 
[advanced customization module](#advanced-customization) for many use cases.

See [docs/filters.md](docs/filters.md) for details on the available filters.

### Advanced customization
jj2cli offers several *hooks* that allow for more advanced customization of its
operation. This includes:

  * passing additional keywords to Jinja2 environment
  * modifying the context before it's used for rendering
  * registering custom filters and tests

See [docs/advanced.md](docs/advanced.md) for details on advanced customization.

## Credits
jj2cli is inspired by and builds on [kolypto/j2cli][j2cli] and
[mattrobenolt/jinja2-cli][jinja2-cli] tools.

[docker]: http://www.docker.com/
[env]: https://en.wikipedia.org/wiki/Environment_variable#Unix
[ini]: https://en.wikipedia.org/wiki/INI_file
[j2cli]: https://github.com/kolypto/j2cli
[jinja2-cli]: https://github.com/mattrobenolt/jinja2-cli
[jinja2-undefined]: https://jinja.palletsprojects.com/en/2.10.x/api/#undefined-types
[json]: https://en.wikipedia.org/wiki/JSON
[make]: https://www.gnu.org/software/make/
[nose]: https://nose.readthedocs.io/
[prospector]: https://prospector.landscape.io/en/master/
[pytest]: https://docs.pytest.org/
[ruff]: https://docs.astral.sh/ruff/
[yaml]: https://en.wikipedia.org/wiki/YAML
