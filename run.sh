#!/usr/bin/env bash

cd -P -- "$(dirname -- "$0")"
# Meant to work with a standard virtualenv-wrapper setup
if [ -f "$HOME/Envs/photocopieuse/bin/python" ]; then
    PYTHON="$HOME/Envs/photocopieuse/bin/python"
elif [ -f venv/bin/python ]; then
    PYTHON=venv/bin/python
else
    PYTHON='python3'
fi
PYTHONPATH=src/main/python "$PYTHON" src/main/python/main.py "$@"
