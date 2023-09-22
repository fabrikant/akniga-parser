#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
pip install pyinstaller

pyinstaller -y -F \
--add-data akniga_sql.py:. \
--collect-submodules logging \
--collect-submodules requests \
--collect-all BeautifulSoup \
--collect-all sqlalchemy \
--collect-submodules akniga_sql \
akniga_parser.py

pyinstaller -y -F \
--add-data akniga_global.py:. \
--add-data akniga_parser.py:. \
--collect-submodules brotli \
--collect-submodules pathvalidate \
--collect-submodules logging \
--collect-all webbrowser \
--collect-submodules requests \
--collect-all BeautifulSoup \
--collect-submodules m3u8 \
--collect-submodules tqdm \
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
--collect-submodules brotli \
--collect-submodules logging \
--collect-all webbrowser \
--collect-all superqt \
--collect-submodules requests \
--collect-all BeautifulSoup \
--collect-all sqlalchemy \
--collect-submodules akniga_global \
--collect-submodules  akniga_settings \
--collect-submodules akniga_sql \
--collect-submodules console_tab \
--collect-submodules table_books \
--collect-submodules table_model \
--collect-submodules time_slider \
akniga_viewer.py

sed -i 's/dist\/akniga_parser/dist\/akniga_parser.exe/' akniga_viewer.spec
sed -i 's/dist\/akniga_dl/dist\/akniga_dl.exe/' akniga_viewer.spec
