cd /d "%~dp0"
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirement.txt
pip install pyinstaller
pyinstaller akniga_parser.spec
pyinstaller akniga_dl.spec
pyinstaller akniga_viewer.spec