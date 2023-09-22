#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
pip install pyinstaller
pyinstaller -y --name akniga-parser --add-data ui/:ui/ \
--add-data akniga_dl.py:. \
--add-data akniga_global.py:. \
--add-data akniga_parser.py:. \
--add-data akniga_settings.py:. \
--add-data akniga_sql.py:. \
--add-data akniga_viewer.py:. \
--add-data console_tab.py:. \
--add-data table_books.py:. \
--add-data table_model.py:. \
--add-data time_slider.py:. \
--collect-all brotli \
--collect-all logging \
--collect-all webbrowser \
--collect-all superqt \
--collect-all requests \
--collect-all BeautifulSoup \
--collect-all sqlalchemy \
--collect-all m3u8 \
--collect-all tqdm \
--collect-all akniga_global \
--collect-all  akniga_dl \
--collect-all  akniga_parser \
--collect-all  akniga_settings \
--collect-all akniga_sql \
--collect-all console_tab \
--collect-all table_books \
--collect-all table_model \
--collect-all time_slider \
akniga_viewer.py
