# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('brotli')
hiddenimports += collect_submodules('logging')
hiddenimports += collect_submodules('webbrowser')
hiddenimports += collect_submodules('superqt')
hiddenimports += collect_submodules('requests')
hiddenimports += collect_submodules('BeautifulSoup')
hiddenimports += collect_submodules('sqlalchemy')
hiddenimports += collect_submodules('akniga_global')
hiddenimports += collect_submodules('akniga_settings')
hiddenimports += collect_submodules('akniga_sql')
hiddenimports += collect_submodules('console_tab')
hiddenimports += collect_submodules('table_books')
hiddenimports += collect_submodules('table_model')
hiddenimports += collect_submodules('time_slider')


block_cipher = None


a = Analysis(
    ['akniga_viewer.py'],
    pathex=[],
    binaries=[('dist/akniga_parser.exe', '.'), ('dist/akniga_dl.exe', '.')],
    datas=[('ui/', 'ui/'), ('akniga_settings.py', '.'), ('console_tab.py', '.'), ('table_books.py', '.'), ('table_model.py', '.'), ('time_slider.py', '.')],
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
