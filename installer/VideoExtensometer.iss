; =============================================================================
; Video Extensometer - Inno Setup Installer Script
; Publisher : Shaktikrupa Automation
; Version   : 1.0.0
;
; Build prerequisites:
;   1. Build the application with PyInstaller:
;        pyinstaller installer\VideoExtensometer.spec
;   2. Place vc_redist.x64.exe in installer\redist\
;   3. Compile this script with Inno Setup 6.x
; =============================================================================

#define MyAppName        "Video Extensometer"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "Shaktikrupa Automation"
#define MyAppExeName     "VideoExtensometer.exe"
#define MyAppId          "{A4E8F2C1-9B3D-4F6A-8C2E-1D5A7B9E4F30}"
#define SourceBuildDir   "..\dist\VideoExtensometer"
#define SeedDatabase     "seed\database\extensometer.db"
#define VCRedistFile     "redist\vc_redist.x64.exe"
#define AppIconFile      "..\assets\branding\app.ico"

#if not exist AddBackslash(SourceBuildDir) + MyAppExeName
  #error "Build output not found. Run: pyinstaller installer\VideoExtensometer.spec"
#endif

#if not exist VCRedistFile
  #error "VC++ redistributable not found. Place vc_redist.x64.exe in installer\redist\"
#endif

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://www.shaktikrupa.com
AppSupportURL=https://www.shaktikrupa.com
AppUpdatesURL=https://www.shaktikrupa.com
DefaultDirName={autopf}\VideoExtensometer
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
LicenseFile=
InfoBeforeFile=
OutputBaseFilename=VideoExtensometer_Setup
OutputDir=output
SetupIconFile={#AppIconFile}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
WizardStyle=modern
WizardResizable=no
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
ChangesAssociations=no
CloseApplications=yes
RestartApplications=no
ShowLanguageDialog=no
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "Create a &Quick Launch shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Application binaries produced by PyInstaller
Source: "{#SourceBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "database\*,assets\company\*"

; Seed database (only on first install)
Source: "{#SeedDatabase}"; DestDir: "{commonappdata}\VideoExtensometer\database"; Flags: onlyifdoesntexist uninsneveruninstall

; Visual C++ runtime redistributable (extracted to temp at install time)
Source: "{#VCRedistFile}"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: VCRedistNeedsInstall

[Dirs]
; Writable application data directories
Name: "{commonappdata}\VideoExtensometer"; Permissions: users-modify
Name: "{commonappdata}\VideoExtensometer\database"; Permissions: users-modify
Name: "{commonappdata}\VideoExtensometer\reports"; Permissions: users-modify
Name: "{commonappdata}\VideoExtensometer\backups"; Permissions: users-modify
Name: "{commonappdata}\VideoExtensometer\logs"; Permissions: users-modify
Name: "{commonappdata}\VideoExtensometer\company"; Permissions: users-modify
Name: "{commonappdata}\VideoExtensometer\settings"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
Root: HKLM; Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "DataPath"; ValueData: "{commonappdata}\VideoExtensometer"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Microsoft Visual C++ 2015-2022 Runtime (x64)..."; Check: VCRedistNeedsInstall; Flags: waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
const
  VCRedistRoot = 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64';
  VCRedistRootWow = 'SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64';

function IsVCRedistInstalled: Boolean;
var
  Installed: Cardinal;
begin
  Result := False;
  if RegQueryDWordValue(HKLM, VCRedistRoot, 'Installed', Installed) then
  begin
    if Installed = 1 then
    begin
      Result := True;
      Exit;
    end;
  end;

  if RegQueryDWordValue(HKLM, VCRedistRootWow, 'Installed', Installed) then
  begin
    if Installed = 1 then
      Result := True;
  end;
end;

function VCRedistNeedsInstall: Boolean;
begin
  Result := not IsVCRedistInstalled;
end;

function VCRedistFileExists: Boolean;
begin
  Result := FileExists(ExpandConstant('{tmp}\vc_redist.x64.exe'));
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if VCRedistNeedsInstall and not VCRedistFileExists then
  begin
    Result :=
      'The Microsoft Visual C++ 2015-2022 Redistributable (x64) is required, ' +
      'but vc_redist.x64.exe was not bundled with this installer package.';
  end;
end;

function ExecHidden(const Cmd, Params: String): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec(Cmd, Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

procedure RemoveDirectoryIfExists(const DirPath: String);
begin
  if DirExists(DirPath) then
    ExecHidden(ExpandConstant('{cmd}'), '/C rmdir /S /Q "' + DirPath + '"');
end;

procedure CreateDirectoryJunction(const JunctionPath, TargetPath: String);
var
  ParentDir: String;
begin
  if not DirExists(TargetPath) then
    ForceDirectories(TargetPath);

  if DirExists(JunctionPath) then
    RemoveDirectoryIfExists(JunctionPath);

  ParentDir := ExtractFileDir(JunctionPath);
  if (ParentDir <> '') and (not DirExists(ParentDir)) then
    ForceDirectories(ParentDir);

  ExecHidden(ExpandConstant('{cmd}'), '/C mklink /J "' + JunctionPath + '" "' + TargetPath + '"');
end;

procedure ConfigureDataDirectories;
var
  AppDir, DataRoot: String;
begin
  AppDir := ExpandConstant('{app}');
  DataRoot := ExpandConstant('{commonappdata}\VideoExtensometer');

  if not DirExists(AppDir + '\assets') then
    ForceDirectories(AppDir + '\assets');

  CreateDirectoryJunction(AppDir + '\database', DataRoot + '\database');
  CreateDirectoryJunction(AppDir + '\assets\company', DataRoot + '\company');
  CreateDirectoryJunction(AppDir + '\reports', DataRoot + '\reports');
  CreateDirectoryJunction(AppDir + '\backups', DataRoot + '\backups');
  CreateDirectoryJunction(AppDir + '\logs', DataRoot + '\logs');
  CreateDirectoryJunction(AppDir + '\settings', DataRoot + '\settings');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    ConfigureDataDirectories;
end;

function InitializeUninstall: Boolean;
begin
  Result := True;
  if MsgBox(
    'Application files will be removed from Program Files.' + #13#10#13#10 +
    'Your data in:' + #13#10 +
    ExpandConstant('{commonappdata}\VideoExtensometer') + #13#10#13#10 +
    'will be preserved.',
    mbConfirmation, MB_YESNO) = IDNO then
    Result := False;
end;
