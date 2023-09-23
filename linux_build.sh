#!/bin/bash

SCRIPT_PATH=$(dirname $0)
cd $SCRIPT_PATH

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
pip install pyinstaller

pyinstaller -y \
--collect-submodules logging \
--collect-submodules requests \
--collect-submodules BeautifulSoup \
--collect-submodules sqlalchemy \
--collect-submodules akniga_sql \
akniga_parser.py

pyinstaller -y \
--add-data selenium_srt/ca.crt:seleniumwire \
--add-data selenium_srt/ca.key:seleniumwire \
--collect-submodules brotli \
--collect-submodules pathvalidate \
--collect-submodules logging \
--collect-submodules webbrowser \
--collect-submodules requests \
--collect-submodules BeautifulSoup \
--collect-submodules m3u8 \
--collect-submodules tqdm \
akniga_dl.py

pyinstaller -y -i ui/img/book.ico --windowed \
--add-data ui/:ui/ \
--add-data akniga_settings.py:. \
--add-data console_tab.py:. \
--add-data table_books.py:. \
--add-data table_model.py:. \
--add-data time_slider.py:. \
--collect-submodules logging \
--collect-submodules superqt \
--collect-submodules sqlalchemy \
--collect-submodules  akniga_settings \
--collect-submodules akniga_sql \
--collect-submodules console_tab \
--collect-submodules table_books \
--collect-submodules table_model \
--collect-submodules time_slider \
akniga_viewer.py

