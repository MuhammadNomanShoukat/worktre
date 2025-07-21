[Setup]
AppName=WorkTre
AppVersion=1.0.3
DefaultDirName={localappdata}\WorkTre
DefaultGroupName=WorkTre
OutputBaseFilename=WorkTreInstaller
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes

[Files]
; ✅ Package all files in dist\main (your full app)
Source: "dist\main\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "dist\main\version.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\WorkTre"; Filename: "{app}\main.exe"
Name: "{commondesktop}\WorkTre"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\main.exe"; Description: "Launch WorkTre"; Flags: nowait postinstall skipifsilent