@echo off
title Crear instalador Windows - Modulador V81
if not exist "dist\ModuladorVozDirectoV81.exe" (
    echo Primero ejecuta crear_exe.bat
    pause
    exit /b
)
set INNO="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %INNO% set INNO="%ProgramFiles%\Inno Setup 6\ISCC.exe"
%INNO% "instalador\ModuladorVozDirectoV81.iss"
pause
