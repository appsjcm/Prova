@echo off
title Crear instalador Windows - Modulador V57
if not exist "dist\ModuladorVozDirectoV57.exe" (
    echo Primero ejecuta crear_exe.bat
    pause
    exit /b
)
set INNO="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %INNO% set INNO="%ProgramFiles%\Inno Setup 6\ISCC.exe"
%INNO% "instalador\ModuladorVozDirectoV57.iss"
pause
