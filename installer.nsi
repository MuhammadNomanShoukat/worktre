!define APPNAME "WorkTree"
!define VERSION "1.0.0"
!define COMPANY "YourCompany"
!define DESCRIPTION "A desktop app built with pywebview"
!define INSTALL_DIR "$PROGRAMFILES\${APPNAME}"
!define EXE_NAME "main.exe"

Outfile "${APPNAME}_Installer.exe"
InstallDir "${INSTALL_DIR}"
RequestExecutionLevel admin

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\${EXE_NAME}"
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXE_NAME}"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\${EXE_NAME}"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$DESKTOP\${APPNAME}.lnk"
    RMDir "$INSTDIR"
SectionEnd
