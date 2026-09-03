# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH).parents[1]
ui_root = project_root / "src" / "nemosine_mind" / "ui"
datas = [
    (str(path), "nemosine_mind/ui")
    for path in ui_root.iterdir()
    if path.suffix in {".html", ".css", ".js", ".svg"}
]
datas.extend(
    [
        (str(project_root / "LICENSE"), "."),
        (str(project_root / "NOTICE"), "."),
        (str(project_root / "TRADEMARKS.md"), "."),
        (str(project_root / "INSTALLER_LEGAL.txt"), "."),
        (str(project_root / "build-legal" / "THIRD_PARTY_NOTICES.txt"), "."),
        (
            str(project_root / "build-legal" / "THIRD_PARTY_LICENSES"),
            "THIRD_PARTY_LICENSES",
        ),
    ]
)

analysis = Analysis(
    ["../windows_launcher.py"],
    pathex=["../../src"],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="MiND-Diagnostics",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon="mind.ico",
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MiND-Diagnostics",
)
