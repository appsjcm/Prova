#define MyAppName "VoiceICC"
#define MyAppVersion "3.7"
#define MyAppPublisher "Modulador de Voz Premium"
#define MyAppExeName "VoiceICC.exe"

[Setup]
AppId={{2B843A25-A3E3-4E5C-8FC3-5D8EC384FA11}
AppName=VoiceICC
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Modulador de Voz Premium
DefaultGroupName=Modulador de Voz Premium
OutputDir=salida
OutputBaseFilename=VoiceICC_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\VoiceICC.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\GUIA_RAPIDA.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\PRIVACIDAD.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Modulador de Voz Premium"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Modulador de Voz Premium"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Modulador de Voz Premium"; Flags: nowait postinstall skipifsilent
