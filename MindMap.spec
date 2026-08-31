# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path


root = Path(SPECPATH)
source = root / "源代码" / "源代码"
is_macos = sys.platform == "darwin"
icon = root / "build-assets" / ("MindMap.icns" if is_macos else "MindMap.ico")
datas = [
    (str(source / "images"), "images"),
    (str(source / "icons"), "icons"),
    (str(source / "files"), "files"),
]

a = Analysis(
    [str(source / "main.py")],
    pathex=[str(source)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

if is_macos:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="MindMap",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=str(icon),
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="MindMap",
    )
    app = BUNDLE(
        coll,
        name="MindMap.app",
        icon=str(icon),
        bundle_identifier="cn.qiushi0919.mindmap",
        info_plist={
            "CFBundleDisplayName": "MindMap",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="MindMap",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=str(icon),
    )
