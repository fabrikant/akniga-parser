#! /bin/bash

python3 venv -m .venv
source .venv/bin/activate
pip install -r requirement.txt
deactivate
