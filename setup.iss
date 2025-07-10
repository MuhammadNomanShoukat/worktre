; Inno Setup script to package PyInstaller exe into a real Windows installer

[Setup]
AppName=WorkTre
AppVersion=1.0.0
DefaultDirName={pf}\WorkTre
DefaultGroupName=WorkTre
OutputBaseFilename=WorkTreInstaller
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes

[Files]
; Adjust path to your built exe

Source: "dist\main.exe"; DestDir: "{app}"; DestName: "WorkTre.exe"; Flags: ignoreversion
Source: "assets\js\*"; DestDir: "{app}\assets\js"; Flags: recursesubdirs createallsubdirs
Source: "assets\css\*"; DestDir: "{app}\assets\css"; Flags: recursesubdirs createallsubdirs
Source: "assets\images\*"; DestDir: "{app}\assets\images"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\WorkTre"; Filename: "{app}\WorkTre.exe"
Name: "{commondesktop}\WorkTre"; Filename: "{app}\WorkTre.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\WorkTre.exe"; Description: "Launch WorkTre"; Flags: nowait postinstall skipifsilent
