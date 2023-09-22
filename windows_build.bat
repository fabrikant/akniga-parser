cd /d "%~dp0"
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirement.txt
pip install pyinstaller
pyinstaller akniga-parser.spec