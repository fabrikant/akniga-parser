#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
pip install pyinstaller

pyinstaller -y -F \
--add-data akniga_sql.py:. \
--collect-all brotli \
--collect-all logging \
--collect-all requests \
--collect-all BeautifulSoup \
--collect-all sqlalchemy \
--collect-all akniga_sql \
akniga_parser.py

pyinstaller -y -F \
--add-data akniga_global.py:. \
--add-data akniga_parser.py:. \
--collect-all brotli \
--collect-all logging \
--collect-all webbrowser \
--collect-all requests \
--collect-all BeautifulSoup \
--collect-all m3u8 \
--collect-all tqdm \
--collect-all akniga_global \
--collect-all  akniga_parser \
akniga_dl.py

pyinstaller -y -F --add-data ui/:ui/ \
--add-binary dist/akniga_parser:. \
--add-binary dist/akniga_dl:. \
--add-data akniga_global.py:. \
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
--collect-all  akniga_settings \
--collect-all akniga_sql \
--collect-all console_tab \
--collect-all table_books \
--collect-all table_model \
--collect-all time_slider \
akniga_viewer.py

sed -i 's/dist\/akniga_parser/dist\/akniga_parser.exe/' akniga_viewer.spec
sed -i 's/dist\/akniga_dl/dist\/akniga_dl.exe/' akniga_viewer.spec
