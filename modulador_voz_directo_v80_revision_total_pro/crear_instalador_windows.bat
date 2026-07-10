@echo off
title Crear instalador Windows - Modulador V80
if not exist "dist\ModuladorVozDirectoV80.exe" (
    echo Primero ejecuta crear_exe.bat
    pause
    exit /b
)
set INNO="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %INNO% set INNO="%ProgramFiles%\Inno Setup 6\ISCC.exe"
%INNO% "instalador\ModuladorVozDirectoV80.iss"
pause
