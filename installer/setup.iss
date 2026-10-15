; installer/setup.iss - Inno Setup Compiler Script (Industrial Standard)
; AI Physics Research Agent (AI 物理科研工作站) Windows Installer
; Designed following InnoDependencyInstaller best practices for prerequisite detection and registration.

#define MyAppName "AI 物理科研工作站"
#define MyAppEnglishName "Physics Research Agent"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "AI Physics Research Team"
#define MyAppURL "https://github.com/VirtuwiseZ/agnes-harness"
#define MyAppExeName "一键启动.bat"
#define MyDoctorExeName "环境自检.bat"

[Setup]
AppId={{D37F8E49-7612-4B1C-9895-B86D22A90F84}
AppName={#MyAppName} ({#MyAppEnglishName})
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userappdata}\Programs\AIPhysicsAgent
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=.
OutputBaseFilename=AI_Physics_Agent_Setup_Inno
SetupIconFile=app.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\app.ico
UninstallDisplayName={#MyAppName} ({#MyAppEnglishName})

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "安装完成后立即启动 AI 物理科研工作站"; GroupDescription: "启动选项:"; Flags: checkedonce

[Files]
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "Uninstall.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\package.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\pnpm-workspace.yaml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\一键启动.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\一键安装.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\环境自检.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.agh\*"; DestDir: "{app}\.agh"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\physics-agent\*"; DestDir: "{app}\physics-agent"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\packages\*"; DestDir: "{app}\packages"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"
Name: "{group}\运行环境健康自检"; Filename: "{app}\{#MyDoctorExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\app.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent"; ValueType: string; ValueName: "DisplayName"; ValueData: "{#MyAppName} ({#MyAppEnglishName})"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#MyAppVersion}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent"; ValueType: string; ValueName: "Publisher"; ValueData: "{#MyAppPublisher}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\app.ico"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent"; ValueType: string; ValueName: "HelpLink"; ValueData: "{#MyAppURL}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent"; ValueType: dword; ValueName: "NoModify"; ValueData: 1
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent"; ValueType: dword; ValueName: "NoRepair"; ValueData: 1

[Code]
// Environment inspection logic following standard industry patterns
function IsNodeInstalled(): Boolean;
begin
  Result := RegKeyExists(HKLM, 'SOFTWARE\Node.js') or
            RegKeyExists(HKCU, 'SOFTWARE\Node.js') or
            FileExists(ExpandConstant('{pf}\nodejs\node.exe')) or
            FileExists(ExpandConstant('{localappdata}\Programs\node\node.exe'));
end;

function IsPythonInstalled(): Boolean;
begin
  Result := RegKeyExists(HKLM, 'SOFTWARE\Python\PythonCore') or
            RegKeyExists(HKCU, 'SOFTWARE\Python\PythonCore') or
            FileExists(ExpandConstant('{localappdata}\Programs\Python\Python313\python.exe')) or
            FileExists(ExpandConstant('{localappdata}\Programs\Python\Python312\python.exe')) or
            FileExists(ExpandConstant('{pf}\Python313\python.exe'));
end;

function InitializeSetup(): Boolean;
var
  Msg: String;
begin
  Result := True;
  Msg := '正在初始化 AI 物理科研工作站安装向导...' + #13#10 + #13#10;
  
  if IsNodeInstalled() then
    Msg := Msg + '• Node.js 运行时: [已检测到]' + #13#10
  else
    Msg := Msg + '• Node.js 运行时: [未检测到，建议安装 Node.js 24 LTS]' + #13#10;
    
  if IsPythonInstalled() then
    Msg := Msg + '• Python 科学环境: [已检测到]' + #13#10
  else
    Msg := Msg + '• Python 科学环境: [未检测到全局环境，将调用内置便携包]' + #13#10;

  // Non-blocking friendly advisory
  Log(Msg);
end;

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: shellexec postinstall nowait skipifsilent Tasks: autostart
