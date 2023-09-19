#! /bin/bash
BASEDIR=$(dirname "$0")
cd $BASEDIR
source .venv/bin/activate
python3 akniga_db_viewer.py 
