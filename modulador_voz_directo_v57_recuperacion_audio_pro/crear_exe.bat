@echo off
title Crear EXE - Modulador V57 Recuperación de Audio Pro
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller ^
  --noconsole ^
  --onefile ^
  --name ModuladorVozDirectoV57 ^
  --icon assets\app_icon.ico ^
  --add-data "assets;assets" ^
  src\modulador_voz_directo_v57.py
echo.
echo EXE creado en dist\ModuladorVozDirectoV57.exe
pause
