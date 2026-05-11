# Subtitle to 3D ASS

Desktop Python app that converts subtitle files into 3D-compatible .ASS subtitles.

## Features

- Supports input subtitle formats: SRT, ASS, VTT
- Converts to ASS with duplicated subtitle events for:
  - HSBS (Half Side-by-Side)
  - FSBS (Full Side-by-Side)
  - HOU (Half Over-Under)
  - ALL in one run
- Resolution sources:
  - Standard presets (480p to 8K, default 1080p)
  - Custom width/height
  - From a selected video file
- Subtitle positioning controls:
  - Horizontal offset
  - Vertical offset
  - Pop-out effect
- Batch conversion of multiple subtitle files
- Drag-and-drop subtitle files into the GUI
- Validation and error summary panel
- Auto output naming with optional override base name

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Build Windows EXE

This app can be packaged into a standalone Windows executable with PyInstaller.

1. Activate your virtual environment.
2. Install PyInstaller.
3. Build using the included spec file.

```powershell
.venv\Scripts\activate
pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller --noconfirm subtitle_to_3d.spec
```

Important:

- Use the virtual-environment Python to run PyInstaller.
- Do not rely on a globally installed `pyinstaller` command if it points at another Python installation.

The packaged app will be created here:

- `dist\SubtitleTo3DAss\SubtitleTo3DAss-1.0.0.exe`

Notes:

- The included spec file already bundles the app icon and splash image.
- The packaged executable now includes Windows version metadata.
- The runtime asset loader in `main.py` supports both normal Python runs and PyInstaller builds.
- `opencv-python` can make the build fairly large. That is normal for a self-contained GUI executable.
- If you want to share the app, send the whole `dist\SubtitleTo3DAss` folder, not just the `.exe` file.

## One-Click Build

You can build the executable by double-clicking:

- `build_exe.bat`

Or run the PowerShell version directly:

```powershell
.\build_exe.ps1
```

What it does:

- installs or updates PyInstaller in the virtual environment,
- runs the test suite,
- builds the EXE,
- builds the installer too if Inno Setup 6 is installed.

If you want a single-file executable instead of a folder build, you can also run:

```powershell
.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name SubtitleTo3DAss --icon src\gui\assets\app_icon.ico --add-data "src\gui\assets\app_icon.png;src\gui\assets" --add-data "src\gui\assets\app_icon.ico;src\gui\assets" --add-data "src\gui\assets\splash.png;src\gui\assets" main.py
```

That produces one `.exe`, but startup is usually slower than the folder build because the bundled files must be unpacked on launch.

Using the build script for one-file mode:

```powershell
.\build_exe.ps1 -OneFile -SkipInstaller
```

Important:

- `--onefile` is not allowed when building from a `.spec` file.
- If you pass a `.spec` file, PyInstaller expects the build shape from the spec itself (folder build in this project).

## Windows Installer

An Inno Setup script is included here:

- `builds\installer\SubtitleTo3DAss.iss`

If Inno Setup 6 is installed, `build_exe.ps1` will automatically compile the installer after the EXE build.

Manual installer build:

```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "builds\installer\SubtitleTo3DAss.iss"
```

The installer output will be written here:

- `builds\installer\output\SubtitleTo3DAss-Setup-1.0.0.exe`

## Troubleshooting

### EXE opens with `ModuleNotFoundError: No module named 'PyQt6'`

Cause:

- The executable was built with a different Python environment (often a global `pyinstaller`) that does not have your project dependencies installed.

Fix:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller --noconfirm subtitle_to_3d.spec
```

Then run:

- `dist\SubtitleTo3DAss\SubtitleTo3DAss-1.0.0.exe`

Optional checks:

```powershell
where pyinstaller
.venv\Scripts\python.exe -c "import PyQt6, pysubs2, cv2; print('ok')"
```

## Output naming

Default output names are generated next to each source subtitle file:

- `<input>_HSBS.ass`
- `<input>_HOU.ass`

If a file already exists, the app creates a suffixed filename (for example `_1`, `_2`) to avoid overwriting.

## Notes

- Timing from the source subtitle file is preserved.
- When the input is ASS, style names are preserved where possible.
