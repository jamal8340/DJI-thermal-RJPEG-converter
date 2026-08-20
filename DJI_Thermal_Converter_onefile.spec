# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_dir = Path(SPECPATH)
tools_dir = project_dir / "tools"
assets_dir = project_dir / "assets"

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

    datas.append((str(source), "tools"))

icon_ico = assets_dir / "app_icon.ico"
icon_png = assets_dir / "app_icon.png"

if not icon_ico.exists():
    raise FileNotFoundError(
        f"Missing EXE icon file: {icon_ico}"
    )

if not icon_png.exists():
    raise FileNotFoundError(
        f"Missing GUI icon file: {icon_png}"
    )

datas.append((str(icon_png), "assets"))


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
    name="Thermal_RJPEG_Converter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(icon_ico),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
