@echo off
title Crear EXE - Modulador V80 Revisión Total Pro
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller ^
  --noconsole ^
  --onefile ^
  --name ModuladorVozDirectoV80 ^
  --icon assets\app_icon.ico ^
  --add-data "assets;assets" ^
  src\modulador_voz_directo_v80.py
echo.
echo EXE creado en dist\ModuladorVozDirectoV80.exe
pause
