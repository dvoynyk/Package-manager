#!/bin/sh
if [ "$1" = "test" ]; then
    python3 -m unittest discover -s tests -t .
else
    python3 src/main.py "$@"
fi