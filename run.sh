#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

VENVPATH="./venv"

venv() {
    if [[ -d "${VENVPATH}/bin" ]]; then
        echo "source ${VENVPATH}/bin/activate"
    else
        echo "source ${VENVPATH}/Scripts/activate"
    fi
}

make_venv() {
    python -m venv "${VENVPATH}"
}

reset_venv() {
    rm -rf "${VENVPATH}"
    make_venv
}

wrapped_python() {
    if [[ -d "${VENVPATH}/bin" ]]; then
        "${VENVPATH}"/bin/python "$@"
    else
        "${VENVPATH}"/Scripts/python "$@"
    fi
}

wrapped_pip() {
    wrapped_python -m pip "$@"
}

python_deps() {
    wrapped_pip install --upgrade pip setuptools wheel

    local pip_extras="${1:-}"
    if [[ -z "${pip_extras}" ]]; then
        wrapped_pip install -e .
    else
        wrapped_pip install -e ".[${pip_extras}]"
    fi
}

install() {
    if [[ -d "${VENVPATH}" ]]; then
        python_deps "$@"
    else
        make_venv && python_deps "$@"
    fi
}

build() {
    python -m build
}

publish() {
    lint && tests && clean && build
    python -m twine upload dist/*
}

clean() {
    rm -rf dist/
    rm -rf .eggs/
    rm -rf build/
    find . -name '*.pyc' -exec rm -f {} +
    find . -name '*.pyo' -exec rm -f {} +
    find . -name '*~' -exec rm -f {} +
    find . -name '__pycache__' -exec rm -fr {} +
    find . -name '.mypy_cache' -exec rm -fr {} +
    find . -name '.pytest_cache' -exec rm -fr {} +
    find . -name '*.egg-info' -exec rm -fr {} +
}

lint() {
    clean
    wrapped_python -m flake8 src/ &&
    wrapped_python -m mypy src/
}

tests() {
    TIMECLOCK_TESTING=True TIMECLOCK_DB=test.db wrapped_python -m pytest -rA tests/
}

test_one() {
    TIMECLOCK_TESTING=True TIMECLOCK_DB=test.db wrapped_python -m pytest -rA "${1}"
}

line_count() {
    clean &&
    cloc --exclude-lang=JavaScript --exclude-dir=venv .
}

collectstatic() {
    rm -rf ./www && mkdir www
    rsync -azP src/timeclock/static www
}

initdb() {
    TIMECLOCK_DB=timeclock.db wrapped_python init_db.py
}

devserver() {
    rm -f timeclock.db &&
    initdb &&
    TIMECLOCK_DB=timeclock.db \
        wrapped_python -m flask --app timeclock --debug run -h 0.0.0.0 -p 5000
}

prodserver() {
    TIMECLOCK_DB=timeclock.db \
        TIMECLOCK_UPLOAD_PATH="www/static/uploads" \
        TIMECLOCK_SECRET_KEY="$(head -c 64 /dev/urandom | base64)" \
        "${VENVPATH}"/bin/uwsgi --http-socket 127.0.0.1:5000 --master -p 2 -w wsgi:app
}

default() {
    collectstatic &&
    rm -f timeclock.db &&
    initdb &&
    (trap 'kill 0' SIGINT; caddy run --config Caddyfile.dev & prodserver)
}

TIMEFORMAT="Task completed in %3lR"
time "${@:-default}"
