$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $here "dist\CamelCrosshairs.exe"
if (-not (Test-Path $exe)) {
    Write-Error "CamelCrosshairs.exe not found. Run build.bat first."
    exit 1
}

function New-AppShortcut($path) {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($path)
    $shortcut.TargetPath = $exe
    $shortcut.WorkingDirectory = Join-Path $here "dist"
    $shortcut.IconLocation = $exe
    $shortcut.Description = "Camel Crosshairs - custom crosshair overlay"
    $shortcut.Save()
}

$desktop = [Environment]::GetFolderPath("Desktop")

# Remove the old shortcut from before the rename, if present.
$oldShortcut = Join-Path $desktop "Crosshair Overlay.lnk"
if (Test-Path $oldShortcut) {
    Remove-Item $oldShortcut -Force
}

$desktopShortcut = Join-Path $desktop "Camel Crosshairs.lnk"
New-AppShortcut $desktopShortcut
Write-Output "Desktop shortcut created at $desktopShortcut"

# A Desktop-only shortcut isn't reliably indexed by Windows Search (the
# Start-menu search you get from pressing the Windows key) — a Start Menu
# entry is what actually makes it findable there, same as a "real" installed app.
$startMenuPrograms = [Environment]::GetFolderPath("Programs")
$startMenuShortcut = Join-Path $startMenuPrograms "Camel Crosshairs.lnk"
New-AppShortcut $startMenuShortcut
Write-Output "Start Menu shortcut created at $startMenuShortcut"
