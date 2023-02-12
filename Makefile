PIP_VERSION := 22.1.2

.PHONY: help
help: Makefile
	@sed -n 's/^\(## \)\([a-zA-Z]\)/\2/p' $<


###########
# Install #
###########

## install-base:                installs minimum requirements to run the API
.PHONY: install-base
install-base: install-base-pip-packages

## install:                     installs all test and dev requirements
.PHONY: install
install: install-base install-test install-dev

.PHONY: install-base-pip-packages
install-base-pip-packages:
	python3 -m pip install pip==${PIP_VERSION}
	pip install -r requirements/base.txt

.PHONY: install-test
install-test:
	pip install -r requirements/test.txt

.PHONY: install-dev
install-dev:
	pip install -r requirements/dev.txt

.PHONY: install-ci
install-ci: install-base install-test

## pip-compile:                 compiles all base/dev/test requirements
.PHONY: pip-compile
pip-compile:
	pip-compile requirements/base.in
	pip-compile requirements/dev.in
	pip-compile requirements/test.in


#################
# Test and Lint #
#################

## test:                        runs core tests
.PHONY: test
test:
	PYTHONPATH=. pytest test_projects --cov=uns_{doc_processor,source_reader,writer} --cov-report term-missing

.PHONY: check-coverage
check-coverage:
	coverage report --fail-under=90

## check:                       runs linters (includes tests)
.PHONY: check
check: check-src check-tests check-version

## check-src:                   runs linters (source only, no tests)
.PHONY: check-src
check-src:
	black --line-length 100 uns_* --check --exclude
	flake8 uns_*
	mypy uns_* --ignore-missing-imports --install-types --non-interactive --implicit-optional

.PHONY: check-tests
check-tests:
	black --line-length 100 test_projects --check
	flake8 test_projects

## tidy:                        run black
.PHONY: tidy
tidy:
	black --line-length 100 uns_*
	black --line-length 100 test_projects
