# Video Extensometer Installer

Professional Windows installer for **Video Extensometer v1.0.0**  
Publisher: **Shaktikrupa Automation**

## Output

`installer\output\VideoExtensometer_Setup.exe`

## Install Locations

| Path | Purpose |
|------|---------|
| `C:\Program Files\VideoExtensometer` | Application binaries |
| `C:\ProgramData\VideoExtensometer` | Writable application data |

### ProgramData folders created automatically

- `database`
- `reports`
- `backups`
- `logs`
- `company`
- `settings`

The installer links the application's writable folders to ProgramData so standard users can save data without writing to Program Files.

## Build Steps

### 1. Prerequisites

- Windows 10/11 x64
- Python virtual environment (`pyspin_env`)
- [Inno Setup 6](https://jrsoftware.org/isinfo.php)
- Microsoft VC++ 2015-2022 Redistributable (x64)

### 2. Add VC++ Runtime

Download:

`https://aka.ms/vs/17/release/vc_redist.x64.exe`

Save as:

`installer\redist\vc_redist.x64.exe`

### 3. Build Everything

From the repository root:

```bat
installer\build_release.bat
```

Or manually:

```bat
pyspin_env\Scripts\pip install pyinstaller
pyspin_env\Scripts\pyinstaller installer\VideoExtensometer.spec --noconfirm
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\VideoExtensometer.iss
```

## Installer Features

- Desktop shortcut
- Start Menu shortcut and uninstall entry
- Application icon (`assets\branding\app.ico`)
- VC++ runtime detection and silent install when missing
- Registry entries for install/data paths
- Preserves `C:\ProgramData\VideoExtensometer` on uninstall
- LZMA2 compression
- 64-bit only installation

## Files

| File | Description |
|------|-------------|
| `VideoExtensometer.iss` | Inno Setup script |
| `VideoExtensometer.spec` | PyInstaller build spec |
| `build_release.bat` | One-click build helper |
| `seed\database\extensometer.db` | Fresh database schema for first install |
| `redist\vc_redist.x64.exe` | VC++ runtime (not included in repo) |
