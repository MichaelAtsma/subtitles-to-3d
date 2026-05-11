from pathlib import Path

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)


APP_NAME = "Subtitle to 3D"
APP_DIST_NAME = "SubtitleTo3D"
APP_VERSION = "1.0.0"
APP_COMPANY = "Michael Atsma"
APP_DESCRIPTION = "Convert subtitles into 3D-compatible ASS files"
APP_EXE_NAME = f"{APP_DIST_NAME}-{APP_VERSION}"


project_root = Path(globals().get("SPECPATH", Path.cwd())).resolve()
asset_dir = project_root / "src" / "gui" / "assets"
version_parts = tuple(int(part) for part in APP_VERSION.split("."))
file_version = version_parts + (0,) * (4 - len(version_parts))

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=file_version,
        prodvers=file_version,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", APP_COMPANY),
                        StringStruct("FileDescription", APP_DESCRIPTION),
                        StringStruct("FileVersion", APP_VERSION),
                        StringStruct("InternalName", APP_DIST_NAME),
                        StringStruct("OriginalFilename", f"{APP_EXE_NAME}.exe"),
                        StringStruct("ProductName", APP_NAME),
                        StringStruct("ProductVersion", APP_VERSION),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

datas = [
    (str(asset_dir / "app_icon.png"), "src/gui/assets"),
    (str(asset_dir / "app_icon.ico"), "src/gui/assets"),
    (str(asset_dir / "splash.png"), "src/gui/assets"),
]


a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_EXE_NAME,
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
    version=version_info,
    icon=str(asset_dir / "app_icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_DIST_NAME,
)