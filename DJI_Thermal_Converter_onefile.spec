# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_dir = Path(SPECPATH)
tools_dir = project_dir / "tools"

runtime_files = [
    "libdirp.dll",
    "libv_dirp.dll",
    "libv_girp.dll",
    "libv_iirp.dll",
    "libv_cirp.dll",
    "libv_hirp.dll",
    "libv_list.ini",
    "MicroIA_Release_x64.dll",
    "MicroJPEG_Release_x64.dll",
    "MicroTA_Release_x64.dll",
    "libexif.dll",
    "libintl-8.dll",
    "libiconv-2.dll",
]

datas = []

for filename in runtime_files:
    source = tools_dir / filename

    if not source.exists():
        raise FileNotFoundError(
            f"Missing required runtime file: {source}"
        )

    datas.append(
        (
            str(source),
            "tools"
        )
    )


a = Analysis(
    ["src/gui.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
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
    name="DJI_Thermal_Converter",
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
)