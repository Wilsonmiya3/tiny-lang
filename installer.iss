; Inno Setup script - builds TinyIDE-Setup.exe
[Setup]
AppId={{B7C3A1E2-5D44-4C1B-9A57-7A1C2F0E9D31}
AppName=Tiny IDE
AppVersion=1.0
AppPublisher=Tiny Language Project
DefaultDirName={autopf}\Tiny IDE
DefaultGroupName=Tiny IDE
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=TinyIDE-Setup
SetupIconFile=assets\tiny.ico
UninstallDisplayIcon={app}\TinyIDE.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "fileassoc"; Description: "Open .tiny files with Tiny IDE"; GroupDescription: "File type:"

[Files]
Source: "dist\TinyIDE.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "examples\*"; DestDir: "{app}\examples"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Tiny IDE"; Filename: "{app}\TinyIDE.exe"
Name: "{group}\Uninstall Tiny IDE"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Tiny IDE"; Filename: "{app}\TinyIDE.exe"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\.tiny"; ValueType: string; ValueName: ""; ValueData: "TinyIDE.Program"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\TinyIDE.Program"; ValueType: string; ValueName: ""; ValueData: "Tiny Program"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\TinyIDE.Program\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\TinyIDE.exe,0"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\TinyIDE.Program\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TinyIDE.exe"" ""%1"""; Tasks: fileassoc

[Run]
Filename: "{app}\TinyIDE.exe"; Description: "Launch Tiny IDE now"; Flags: nowait postinstall skipifsilent