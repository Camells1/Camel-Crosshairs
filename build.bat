@echo off
cd /d "%~dp0"
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "CamelCrosshairs" --icon "assets\icon.ico" --add-data "assets;assets" main.py
echo.
echo Build finished. Find CamelCrosshairs.exe in the dist folder.
pause
