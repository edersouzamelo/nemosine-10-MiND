#ifndef MindVersion
  #define MindVersion "0.0.0-dev"
#endif

[Setup]
AppId={{76F8D8E1-73E3-4D87-95B4-09E39ECA0D48}
AppName=MiND
AppVersion={#MindVersion}
AppPublisher=Edervaldo José de Souza Melo
AppPublisherURL=https://github.com/edersouzamelo/nemosine-10-MiND
AppSupportURL=https://github.com/edersouzamelo/nemosine-10-MiND/issues
DefaultDirName={autopf}\MiND
DefaultGroupName=MiND
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist-installer
OutputBaseFilename=MiND-Setup-{#MindVersion}-windows-x64
SetupIconFile=mind.ico
UninstallDisplayIcon={app}\MiND.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
Source: "..\..\dist\MiND\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\MiND"; Filename: "{app}\MiND.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\MiND"; Filename: "{app}\MiND.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\MiND.exe"; Description: "Abrir o MiND"; Flags: nowait postinstall skipifsilent
