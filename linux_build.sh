#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
pip install pyinstaller
pyinstaller -y --name akniga-parser --add-data ui/:ui/ --add-data src/:. --add-data src/:src/ \
--icon ui/img/book_white_background.png \
--collect-submodules brotli \
--collect-submodules logging \
--collect-submodules webbrowser \
--collect-submodules superqt \
--collect-submodules requests \
--collect-submodules BeautifulSoup \
--collect-submodules sqlalchemy \
--collect-submodules m3u8 \
--collect-submodules tqdm \
src/akniga_viewer.py

