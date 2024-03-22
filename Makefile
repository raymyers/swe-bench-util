install:
	poetry install

clean:
	find . -type f -name '*.pyc' -delete

test: venv
	poetry run pytest


coverage: venv
	poetry run pytest tests --cov --cov-fail-under=50 --cov-report html
	-open "htmlcov/index.html"

lint: venv
	poetry run ruff check --fix

format: venv
	poetry run ruff format

check: test format lint

.PHONY: all venv check install clean test lint format coverage
