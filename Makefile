PYPACKAGE=jj2cli
TOX_QUICKTEST=py3.10-pyyaml6
TOX_LINTTEST=lint

.PHONY: help all clean test test-lint test-tox test-tox-quick test-pytest test-pytest-cover

help:			##- Show this help.
	@sed -e '/#\{2\}-/!d; s/\\$$//; s/:[^#\t]*/:/; s/#\{2\}- *//' $(MAKEFILE_LIST)

all:
	@echo no default action

# Package
clean:
	@rm -rf build/ dist/ *.egg-info/ README.md README.rst
	@pip install -e .  # have to reinstall because we are using self
README.md: $(shell find src/) $(wildcard misc/_doc/**)
	@python misc/_doc/README.py | python j2cli/__init__.py -f json -o $@ misc/_doc/README.md.j2


.PHONY: build check-pyenv install-pyenv publish-test publish
build: README.md
	@./setup.py build sdist bdist_wheel
publish-test: README.md
	@twine upload --repository pypitest dist/*
publish: README.md
	@twine upload dist/*

check-pyenv:
ifeq ($(VIRTUAL_ENV),)
	$(error Not in a virtualenv)
else
	@printf "Installing in %s.\n" "$(VIRTUAL_ENV)"
endif

test-lint:		##- Run configured linters.
	prospector

test-tox:		##- Run all Tox tests.
	tox

test-tox-quick:		##- Run test only for the TOX_QUICKTEST profile.
	tox -e $(TOX_QUICKTEST)

test-tox-lint:		##- Run configured linters via Tox.
	tox -e $(TOX_LINTTEST)

test-pytest:
	pytest

#test-nose-cover:		## Use pytest to produce a test coverage report.
	#nosetests --with-coverage  --cover-package $(PYPACKAGE)
	 #75 $(COVERAGE_XML): .coveragerc
 #76     pytest --cov-report xml:$(@) --cov=.

test: test-lint test-tox test-nose			##- Run all linters and tests.

install-pyenv: check-pyenv		##- Install to the current virtualenv.
	pip install -e .
