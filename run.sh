#!/usr/bin/env bash

cd -P -- "$(dirname -- "$0")"
ANACONDA="$HOME/anaconda3/bin/python"
if [ -f "$ANACONDA" ]; then
    PYTHON="$ANACONDA"
elif [ -f venv/bin/python ]; then
    PYTHON=venv/bin/python
else
    PYTHON='python3'
fi
PYTHONPATH=src/main/python "$PYTHON" src/main/python/main.py "$@"
