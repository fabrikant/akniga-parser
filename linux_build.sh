#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
pip install pyinstaller
pyinstaller --name akniga-parser --add-data ./ui:./ui --add-data src/:. --collect-submodules webbrowser --collect-submodules superqt src/akniga_viewer.py

