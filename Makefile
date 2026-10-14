export PRETTY_LOG_LEVEL ?= DEBUG

OUTPUT ?= dist

build: prepare
	poetry build --output=$(OUTPUT)

test: prepare
	poetry run -- pytest --showlocals --show-capture=all

prepare: .venv
.venv: pyproject.toml poetry.lock
	poetry install --extras=yaml --with=test
	@touch "$@"

update:
	poetry show --no-cache --latest --top-level
	poetry update

deepclean:
	rm -rf .venv

.PHONY: build test prepare update
