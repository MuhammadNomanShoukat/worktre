; Inno Setup script to package PyInstaller exe into a real Windows installer

[Setup]
AppName=WorkTree
AppVersion=1.0.0
DefaultDirName={pf}\WorkTree
DefaultGroupName=WorkTree
OutputBaseFilename=WorkTreeInstaller
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes

[Files]
; Adjust path to your built exe

Source: "dist\main.exe"; DestDir: "{app}"; DestName: "WorkTree.exe"; Flags: ignoreversion
Source: "assets\js\*"; DestDir: "{app}\assets\js"; Flags: recursesubdirs createallsubdirs
Source: "assets\css\*"; DestDir: "{app}\assets\css"; Flags: recursesubdirs createallsubdirs
Source: "assets\images\*"; DestDir: "{app}\assets\images"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\WorkTree"; Filename: "{app}\WorkTree.exe"
Name: "{commondesktop}\WorkTree"; Filename: "{app}\WorkTree.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\WorkTree.exe"; Description: "Launch WorkTree"; Flags: nowait postinstall skipifsilent
