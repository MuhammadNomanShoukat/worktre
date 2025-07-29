#define MyAppName "WorkTre"

[Setup]
AppName={#MyAppName}
AppVersion=1.0.2
AppID={#MyAppName}App
AppPublisher=Powered by Bioncos Global
AppPublisherURL=https://personalcompany.example.com
AppSupportURL=https://personalcompany.example.com/support
AppUpdatesURL=https://personalcompany.example.com/updates
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename={#MyAppName}Installer
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\main.exe   ; ✅ EXE has icon

[Files]
Source: "dist\main\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "dist\main\version.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\main\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\main.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\main.exe"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\main.exe"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Registry]
; ✅ Auto-start on boot
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\main.exe"""; Flags: uninsdeletevalue

; ✅ Set Publisher manually for Control Panel display (fallback for old Inno Setup)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1"; \
    ValueType: string; ValueName: "Publisher"; ValueData: "WorkTre"; Flags: uninsdeletevalue

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption := 'Installer created by WorkTre';
end;
