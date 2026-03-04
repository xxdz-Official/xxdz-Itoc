# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\[小绚学习]\\长时存放\\电脑技术大赛\\小小电子应用程序\\小小电子exe应用程序系列\\开发\\MidiToCZE\\runCZE\\runCZE.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='runCZE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='D:\\[小绚学习]\\长时存放\\电脑技术大赛\\小小电子应用程序\\小小电子exe应用程序系列\\开发\\MidiToCZE\\runCZE\\runCZE_version_info.txt',
    uac_admin=True,
    icon=['D:\\[小绚学习]\\长时存放\\电脑技术大赛\\小小电子应用程序\\小小电子exe应用程序系列\\开发\\MidiToCZE\\img\\icon.ico'],
)
