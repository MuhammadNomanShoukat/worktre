; Inno Setup script to package PyInstaller app

[Setup]
AppName=WorkTree
AppVersion=1.0.0
DefaultDirName={pf}\WorkTree
DefaultGroupName=WorkTree
OutputDir=output
OutputBaseFilename=WorkTree_Installer_v1.0.0
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
PrivilegesRequired=admin

[Files]
; ✅ Main app executable
Source: "dist\main.exe"; DestDir: "{app}"; DestName: "WorkTree.exe"; Flags: ignoreversion

; ✅ HTML entry point
Source: "index.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "break.html"; DestDir: "{app}"; Flags: ignoreversion

; ✅ All assets recursively in one line
Source: "assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\WorkTree"; Filename: "{app}\WorkTree.exe"
Name: "{commondesktop}\WorkTree"; Filename: "{app}\WorkTree.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\WorkTree.exe"; Description: "Launch WorkTree"; Flags: nowait postinstall skipifsilent
