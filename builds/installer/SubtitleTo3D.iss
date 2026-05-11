#define AppName "Subtitle to 3D"
#define AppVersion "0.1.0"
#define AppPublisher "Michael Atsma"
#define AppExeName "SubtitleTo3D-0.1.0.exe"
#define AppDistDir "..\..\dist\SubtitleTo3D"

[Setup]
AppId={{8E26B4DA-38F7-4801-8C69-41DB5BBE3684}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=output
OutputBaseFilename=SubtitleTo3D-Setup-{#AppVersion}
SetupIconFile=..\..\src\gui\assets\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "{#AppDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
