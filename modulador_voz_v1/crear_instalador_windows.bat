@echo off
title Crear instalador Windows - Modulador de Voz 1.0
if not exist "dist\ModuladorVoz.exe" (
    echo Primero ejecuta crear_exe.bat
    pause
    exit /b
)
set INNO="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %INNO% set INNO="%ProgramFiles%\Inno Setup 6\ISCC.exe"
%INNO% "instalador\ModuladorVoz.iss"
echo.
echo Instalador creado en salida_instalador\
pause
