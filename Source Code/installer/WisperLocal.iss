; Inno Setup script for WisperLocal.
; Build the app first (build.bat) so dist\WisperLocal\ exists, then compile:
;   iscc installer\WisperLocal.iss

#define MyAppName "WisperLocal"
#define MyAppVersion "0.5.2"
#define MyAppPublisher "WisperLocal"
#define MyAppExeName "WisperLocal.exe"

[Setup]
AppId={{A2F4C8E1-7B3D-4E6A-9C2F-1D5B8E0A3C77}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\installer_output
OutputBaseFilename=WisperLocal-Setup-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "startupicon"; Description: "Start {#MyAppName} automatically when Windows starts"; GroupDescription: "Startup:"; Flags: unchecked
Name: "ollama"; Description: "Install Ollama for local AI enhancement (downloads ~1.3 GB)"; GroupDescription: "AI enhancement (optional):"

[Files]
Source: "..\dist\WisperLocal\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{tmp}\OllamaSetup.exe"; Parameters: "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART"; StatusMsg: "Installing Ollama (this can take a minute)..."; Tasks: ollama; Check: ShouldInstallOllama; Flags: skipifdoesntexist
Filename: "{localappdata}\Programs\Ollama\ollama app.exe"; StatusMsg: "Starting Ollama..."; Tasks: ollama; Flags: nowait skipifdoesntexist
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent

[Code]
var
  DownloadPage: TDownloadWizardPage;

function OllamaInstalled: Boolean;
begin
  Result := FileExists(ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe')) or
            FileExists(ExpandConstant('{localappdata}\Programs\Ollama\ollama app.exe'));
end;

function ShouldInstallOllama: Boolean;
begin
  Result := WizardIsTaskSelected('ollama') and (not OllamaInstalled);
end;

procedure InitializeWizard;
begin
  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), nil);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpReady then begin
    if ShouldInstallOllama() then begin
      DownloadPage.Clear;
      DownloadPage.Add('https://ollama.com/download/OllamaSetup.exe', 'OllamaSetup.exe', '');
      DownloadPage.Show;
      try
        try
          DownloadPage.Download;
        except
          SuppressibleMsgBox('Could not download Ollama: ' + AddPeriod(GetExceptionMessage) + #13#10 +
            'WisperLocal will still install; you can add Ollama later from ollama.com.',
            mbInformation, MB_OK, IDOK);
        end;
      finally
        DownloadPage.Hide;
      end;
    end;
  end;
end;
