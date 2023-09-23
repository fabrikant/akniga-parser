# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('brotli')
hiddenimports += collect_submodules('pathvalidate')
hiddenimports += collect_submodules('logging')
hiddenimports += collect_submodules('webbrowser')
hiddenimports += collect_submodules('requests')
hiddenimports += collect_submodules('BeautifulSoup')
hiddenimports += collect_submodules('m3u8')
hiddenimports += collect_submodules('tqdm')
hiddenimports += collect_submodules('akniga_global')


block_cipher = None


a = Analysis(
    ['akniga_dl.py'],
    pathex=[],
    binaries=[],
    datas=[('selenium_srt/ca.crt', 'seleniumwire'), ('selenium_srt/ca.key', 'seleniumwire')],
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
    [],
    exclude_binaries=True,
    name='akniga_dl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='akniga_dl',
)
