# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['rumps', 'pynput', 'pynput.keyboard', 'pynput.mouse'],
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
    a.binaries,
    a.datas,
    name='MacSnap',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

app = BUNDLE(
    exe,
    name='MacSnap.app',
    icon=None,
    bundle_identifier='com.macsnap',
    info_plist={
        'CFBundleName':               'MacSnap',
        'CFBundleDisplayName':        'MacSnap',
        'CFBundleVersion':            '1.0.0',
        'CFBundleShortVersionString': '1.0',
        'LSUIElement':                True,    # menu bar only, no Dock icon
        'NSHighResolutionCapable':    True,
    },
)
