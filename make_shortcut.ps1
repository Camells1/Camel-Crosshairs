$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $here "dist\CamelCrosshairs.exe"
if (-not (Test-Path $exe)) {
    Write-Error "CamelCrosshairs.exe not found. Run build.bat first."
    exit 1
}
$desktop = [Environment]::GetFolderPath("Desktop")

# Remove the old shortcut from before the rename, if present.
$oldShortcut = Join-Path $desktop "Crosshair Overlay.lnk"
if (Test-Path $oldShortcut) {
    Remove-Item $oldShortcut -Force
}

$shortcutPath = Join-Path $desktop "Camel Crosshairs.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = Join-Path $here "dist"
$shortcut.IconLocation = $exe
$shortcut.Description = "Camel Crosshairs - custom crosshair overlay"
$shortcut.Save()
Write-Output "Shortcut created at $shortcutPath"
