@echo off
title Crear EXE - Modulador de Voz 1.0
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller ^
  --noconsole ^
  --onefile ^
  --name ModuladorVoz ^
  --icon assets\app_icon.ico ^
  --add-data "assets;assets" ^
  src\modulador_voz.py
echo.
echo EXE creado en dist\ModuladorVoz.exe
pause
