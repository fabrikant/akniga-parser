#! /bin/bash
BASEDIR=$(dirname "$0")
cd $BASEDIR
source .venv/bin/activate
python3 src/akniga_viewer.py
