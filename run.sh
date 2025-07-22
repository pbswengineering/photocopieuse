#!/usr/bin/env bash

ENVSDIR="$HOME/.virtualenvs"

cd -P -- "$(dirname -- "$0")"
# Meant to work with a standard virtualenv-wrapper setup
if [ -f "$ENVSDIR/photocopieuse/bin/python" ]; then
    PYTHON="$ENVSDIR/photocopieuse/bin/python"
elif [ -f venv/bin/python ]; then
    PYTHON=venv/bin/python
else
    PYTHON='python3'
fi
PYTHONPATH=src/main/python "$PYTHON" src/main/python/main.py "$@"
