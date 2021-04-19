install: ## [Local development] Upgrade pip, install requirements, install package.
	python -m pip install -U pip setuptools wheel
	python -m pip install -r requirements.txt
	git clone https://github.com/criteo/fromconfig.git && cd fromconfig && git checkout feature/plugins && make install
	python -m pip install -e .

install-dev: ## [Local development] Install test requirements
	python -m pip install -r requirements-test.txt

lint: ## [Local development] Run mypy, pylint and black
	python -m mypy fromconfig_mlflow
	python -m pylint fromconfig_mlflow
	python -m black --check -l 120 fromconfig_mlflow

black: ## [Local development] Auto-format python code using black
	python -m black -l 120 .

test: ## [Local development] Run unit tests, doctest and notebooks
	python -m pytest -v --cov=fromconfig_mlflow --cov-report term-missing --cov-fail-under 95 tests/unit
	python -m pytest --doctest-modules -v fromconfig_mlflow
	$(MAKE) examples

examples:  ## [Doc] Run all examples
	cd docs/examples/quickstart && fromconfig config.yaml params.yaml launcher.yaml - model - train
	cd docs/examples/multi && fromconfig config.yaml params.yaml launcher.yaml - model - train

venv-lint-test: ## [Continuous integration] Install in venv and run lint and test
	python3.6 -m venv .env && . .env/bin/activate && make install install-dev lint test && rm -rf .env

build-dist: ## [Continuous integration] Build package for pypi
	python3.6 -m venv .env
	. .env/bin/activate && pip install -U pip setuptools wheel
	. .env/bin/activate && python setup.py sdist
	rm -rf .env

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
