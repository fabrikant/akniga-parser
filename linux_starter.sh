#!/bin/bash

SCRIPT_PATH=$(dirname $0)
cd $SCRIPT_PATH
source .venv/bin/activate
python akniga_viewer.py