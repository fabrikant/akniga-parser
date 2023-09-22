# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('ui/', 'ui/'), ('akniga_settings.py', '.'), ('console_tab.py', '.'), ('table_books.py', '.'), ('table_model.py', '.'), ('time_slider.py', '.')]
binaries = [('dist/akniga_parser.exe', '.'), ('dist/akniga_dl.exe', '.')]
hiddenimports = []
hiddenimports += collect_submodules('brotli')
hiddenimports += collect_submodules('logging')
hiddenimports += collect_submodules('requests')
hiddenimports += collect_submodules('akniga_global')
hiddenimports += collect_submodules('akniga_settings')
hiddenimports += collect_submodules('akniga_sql')
hiddenimports += collect_submodules('console_tab')
hiddenimports += collect_submodules('table_books')
hiddenimports += collect_submodules('table_model')
hiddenimports += collect_submodules('time_slider')
tmp_ret = collect_all('webbrowser')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('superqt')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('BeautifulSoup')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sqlalchemy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


block_cipher = None


a = Analysis(
    ['akniga_viewer.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='akniga_viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
