# define the name of the virtual environment directory
VENV := venv

# default target, when make executed without arguments
all: venv

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip install -r requirements.txt

# venv is a shortcut target
venv: $(VENV)/bin/activate

install:
	python3 -m pip install -e .

clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete

test: venv
	./$(VENV)/bin/python3 -m pytest


coverage: venv
	./$(VENV)/bin/python3 -m pytest tests --cov --cov-fail-under=50 --cov-report html
	-open "htmlcov/index.html"

lint: venv
	./$(VENV)/bin/python3 -m ruff check --fix
#	./$(VENV)/bin/python3 -m pylint --disable=C,R menderbot

format: venv
	./$(VENV)/bin/python3 -m ruff format

check: test format lint

.PHONY: all venv check install clean test lint format coverage docker clean-docker