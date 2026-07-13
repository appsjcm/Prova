#define MyAppName "VoiceICC"
#define MyAppVersion "6.5"
#define MyAppPublisher "Modulador de Voz Premium"
#define MyAppExeName "VoiceICC.exe"

[Setup]
AppId={{2B843A25-A3E3-4E5C-8FC3-5D8EC384FA11}
AppName=VoiceICC
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Modulador de Voz Premium
DefaultGroupName=Modulador de Voz Premium
OutputDir=..\salida_instalador
OutputBaseFilename=VoiceICC_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
WizardImageFile=..\assets\installer_side.png
WizardSmallImageFile=..\assets\app_icon.png
SetupIconFile=..\assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\VoiceICC.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\GUIA_RAPIDA.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\PRIVACIDAD.md"; DestDir: "{app}"; Flags: ignoreversion
; Herramientas para instalar los datos de Voces IA (siempre disponibles).
Source: "..\instalar_datos_ia.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\instalar_datos_ia.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements_ia.txt"; DestDir: "{app}"; Flags: ignoreversion
; Instalador del microfono virtual (VB-CABLE), siempre disponible.
Source: "..\instalar_microfono_virtual.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\instalar_microfono_virtual.bat"; DestDir: "{app}"; Flags: ignoreversion
; Datos de IA opcionales: solo se copian si el usuario marca la tarea y si la
; carpeta existe junto al instalador (el .zip de datos descomprimido).
Source: "..\datos_ia\*"; DestDir: "{app}\datos_ia"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Tasks: datosia

[Icons]
Name: "{autoprograms}\Modulador de Voz Premium"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\Instalar Voces IA (datos)"; Filename: "{app}\instalar_datos_ia.bat"
Name: "{autoprograms}\Instalar microfono virtual"; Filename: "{app}\instalar_microfono_virtual.bat"
Name: "{autodesktop}\Modulador de Voz Premium"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked
Name: "microvirtual"; Description: "Instalar el microfono virtual (VB-CABLE) para usar la voz en cualquier app"; GroupDescription: "Extras:"; Flags: unchecked
Name: "datosia"; Description: "Anadir datos de Voces IA (modelos RVC y motor local, requiere varios GB)"; GroupDescription: "Extras:"; Flags: unchecked

[Run]
; Si el usuario marca "microvirtual", instala el microfono virtual al terminar.
Filename: "{app}\instalar_microfono_virtual.bat"; Description: "Instalar el microfono virtual ahora"; Flags: nowait postinstall skipifsilent; Tasks: microvirtual
; Si el usuario marca "datosia", instala los datos de IA al terminar.
Filename: "{app}\instalar_datos_ia.bat"; Description: "Instalar los datos de Voces IA ahora"; Flags: nowait postinstall skipifsilent; Tasks: datosia
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Modulador de Voz Premium"; Flags: nowait postinstall skipifsilent
