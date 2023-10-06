# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('logging')
hiddenimports += collect_submodules('superqt')
hiddenimports += collect_submodules('sqlalchemy')
hiddenimports += collect_submodules('akniga_settings')
hiddenimports += collect_submodules('akniga_sql')
hiddenimports += collect_submodules('console_tab')
hiddenimports += collect_submodules('table_books')
hiddenimports += collect_submodules('table_model')
hiddenimports += collect_submodules('time_slider')


a = Analysis(
    ['akniga_viewer.py'],
    pathex=[],
    binaries=[],
    datas=[('ui/', 'ui/'), ('akniga_settings.py', '.'), ('console_tab.py', '.'), ('table_books.py', '.'), ('table_model.py', '.'), ('time_slider.py', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='akniga_viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['ui/img/book.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='akniga_viewer',
)
