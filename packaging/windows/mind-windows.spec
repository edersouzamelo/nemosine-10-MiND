# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


datas = collect_data_files("nemosine_mind.ui")
hiddenimports = (
    collect_submodules("uvicorn")
    + collect_submodules("openai")
    + collect_submodules("anthropic")
)

analysis = Analysis(
    ["packaging/windows_launcher.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="MiND",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # Avoid executable packing. Packed binaries are more likely to trigger
    # heuristic antivirus checks, especially before the app is code-signed.
    upx=False,
    console=False,
    icon="packaging/windows/mind.ico",
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MiND",
)
