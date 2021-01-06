#!/bin/sh

set -e

if which python3 > /dev/null ; then
    # Create a virtual environment if it doesn't exist.
    [ -d venv ] || python3 -m venv venv

    # Activate the virtual environment and install requirements.
    . venv/bin/activate
    pip3 install -r requirements.txt
else
    >&2 echo "Please install Python3."
    exit 1
fi

# Create config.ini if it does not exist.
[ -f config.ini ] || cp config.ini.default config.ini
