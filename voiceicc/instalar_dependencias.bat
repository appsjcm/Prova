@echo off
title Instalar dependencias - Modulador V9 Premium
echo Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Listo. Ejecuta ejecutar_modulador.bat
pause
