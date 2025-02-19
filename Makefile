BASE_DIR:=$(realpath .)
PWD:=$(CWD)
export LIB_DIR:=$(BASE_DIR)/lib

###################################
# see .env:
PYTHON_VERSION=3.12
export PYTHONPATH:=${BASE_DIR}/lib:${PYTHONPATH}
export PATH:=${BASE_DIR}/bin:${BASE_DIR}/venv/bin:${PATH}
###################################

SRC_DIR = $(LIB_DIR)
TEST_DIR = $(LIB_DIR)
TEST_SRC = $(shell find '$(TEST_DIR)' -name '*_test.py' | sort)
PY_FILES = $(shell find '$(SRC_DIR)' -name '*.py' | sort)
LINT_FILES = $(PY_FILES)
FORMAT_FILES = $(PY_FILES)
TYPING_FILES = $(PY_FILES)
SPELL_CHECK_FILES = README.md
SPELL_CHECK_FILES += $(PY_FILES)

venv=. venv/bin/activate &&

default: check format                  #

all: reformat check                    #

setup: venv deps pre-commit-install    #

venv:                                  # create an empty venv/
	rm -rf venv; python$(PYTHON_VERSION) -m venv venv

deps:                                  # install *requirements*.txt
	$(venv) pip install $(foreach f,$(REQUIREMENTS_TXT),-r $(f) )
REQUIREMENTS_TXT=$(wildcard *requirements*.txt)

pre-commit-install:                    # install precommits
	$(venv) pre-commit install

check: test lint typing spelling       #

PYTEST_OPTS=-s # --capture=no --verbose --failed-first
test:                                  # run tests w/ coverage
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
	$(MAKE) reformat FORMAT_FILES='$$(TEST_DATA)'
regen-test-data: clean-test-data-expect test-data

lint:                                  # lint sources
	$(venv) pylint $(PY_FILES)

MYPY_REPORTS=--txt-report --html-report --any-exprs-report
MYPY_OPTS=--config-file ./.mypy.ini --pretty --show-column-numbers --warn-redundant-casts
MYPY_OPTS+=$(foreach v,$(MYPY_REPORTS),$(v) mypy/)
typing:                                # static type checking
	mkdir -p mypy
	-mypy --install-types --non-interactive
	-stubgen -o $(LIB_DIR) $(PY_FILES)
	$(venv) mypy $(MYPY_OPTS) $(TYPING_FILES); rtn=$$?; head -999 mypy/*.txt; exit $$rtn

format:                                # check formatting
	$(venv) black --check $(FORMAT_FILES)

reformat:                              # reformat
	$(venv) black $(FORMAT_FILES)

spelling:                              # check spelling
	$(venv) codespell --summary $(SPELL_CHECK_FILES)

fix-spelling:                          # fix spelling
	$(venv) codespell --write-changes $(SPELL_CHECK_FILES)

clean:                                 # clean up
	$(MAKE) clean-test-data-actual
	find '$(SRC_BASE)' -name '__pycache__' -exec echo rm -rf '{}' \;
	rm -rf .coverage
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/

clean-test-data-all: clean-test-data-actual clean-test-data-expect

clean-test-data-actual:
	rm -f $(TEST_DATA_ACTUAL)

clean-test-data-expect:
	rm -f $(TEST_DATA_EXPECT)

very-clean: clean                      # clean and remove venv/
	rm -rf venv/

sort-requirements:                     # sort *requirements*.txt
	@export LC_ALL=C ;\
	for f in *requirements*.txt ;\
	do \
		(set -x; sort -o "$$f" "$$f") ;\
	done

v:                                     # print a var named `v`
	@echo $($(v))

help:                                  # this help
	@grep -Ee "^[-a-z]+:.+# +.*" Makefile
