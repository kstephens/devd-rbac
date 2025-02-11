###################################
# see .env:
PYTHON_VERSION=3.11 # 3.11.10
export PYTHONPATH:=${PWD}/lib:${PYTHONPATH}
export PATH:=${PWD}/bin:${PWD}/venv/bin:${PATH}
###################################

CWD:=$(realpath .)
PWD:=$(CWD)
BASE_DIR:=$(CWD)
export LIB_DIR:=$(CWD)/lib
# include $(CWD)/.env
# export PYTHON_VERSION
export PYTHONPATH

# Note: scripts/ do not pass checks
SCRIPTS = $(CWD)/scripts
SRC = $(LIB_DIR)
FORMAT_SRC = $(SRC)
TEST_DIR = $(LIB_DIR)
TEST_SRC = $(shell find '$(TEST_DIR)' -name '*_test.py' | sort)
SPELL_CHECK_FILES=README.md

venv=. venv/bin/activate &&

default: check format

all: reformat check

setup: venv deps pre-commit-install

venv:
	python$(PYTHON_VERSION) -m venv venv

deps:
	$(venv) pip install $(foreach f,$(REQUIREMENTS_TXT),-r $(f) )
REQUIREMENTS_TXT=$(wildcard *requirements*.txt)

pre-commit-install:
	$(venv) pre-commit install

check: test lint typing spelling

PYTEST_OPTS=-s # --capture=no --verbose --failed-first
test:
	-rm -rf coverage/*
	mkdir -p coverage
	$(venv) coverage run -m pytest $(PYTEST_OPTS) $(TEST_SRC)
	$(venv) coverage report | tee coverage/coverage.txt
	$(venv) coverage html --directory coverage/html

find_test_data__py = $(shell find '$(TEST_DIR)' -name '*__$(1).py' | sort)
find_test_data_out = $(shell find '$(TEST_DIR)' -name '*.out.$(1)' | sort)
TEST_DATA_ACTUAL := $(call find_test_data__py,actual) $(call find_test_data_out,actual)
TEST_DATA_EXPECT := $(call find_test_data__py,expect) $(call find_test_data_out,expect)
TEST_DATA := $(TEST_DATA_ACTUAL) $(TEST_DATA_EXPECT)
test-data: clean-test-data-actual
	$(MAKE) test; $(MAKE) test
	$(MAKE) reformat FORMAT_SRC='$$(TEST_DATA)'
regen-test-data: clean-test-data-expect test-data

lint:
	$(venv) pylint $(SRC)

MYPY_REPORTS=--txt-report --html-report --any-exprs-report
MYPY_OPTS=--config-file ./.mypy.ini --pretty --show-column-numbers --warn-redundant-casts
MYPY_OPTS+=$(foreach v,$(MYPY_REPORTS),$(v) mypy/)
typing:
	mkdir -p mypy
	$(venv) mypy $(MYPY_OPTS) $(SRC); rtn=$$?; head -999 mypy/*.txt; exit $$rtn

format:
	$(venv) black --check $(FORMAT_SRC)

reformat:
	$(venv) black $(FORMAT_SRC)

spelling:
	$(venv) codespell --summary $(SPELL_CHECK_FILES)

fix-spelling:
	$(venv) codespell --write-changes $(SPELL_CHECK_FILES)

clean: clean-test-data-actual
	find '$(SRC_BASE)' -name '__pycache__' -exec echo rm -rf '{}' \;
	rm -rf .coverage
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/

clean-test-data-all: clean-test-data-actual clean-test-data-expect

clean-test-data-actual:
	rm -f $(TEST_DATA_ACTUAL)

clean-test-data-expect:
	rm -f $(TEST_DATA_EXPECT)

very-clean: clean
	rm -rf venv/

sort-requirements:
	@export LC_ALL=C ;\
	for f in *requirements*.txt ;\
	do \
		(set -x; sort -o "$$f" "$$f") ;\
	done

# Print a make var:
#   make v v=MAKE_VAR
v:
	@echo $($(v))
