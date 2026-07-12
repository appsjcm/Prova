@echo off
REM Instala el microfono virtual de VoiceICC (driver VB-CABLE).
setlocal
cd /d "%~dp0"

set PYEXE=
where py >nul 2>nul && set PYEXE=py -3
if "%PYEXE%"=="" (
  where python >nul 2>nul && set PYEXE=python
)

if "%PYEXE%"=="" (
  echo No se encontro Python. Abre VoiceICC y usa Cable Virtual ^> Instalar microfono virtual,
  echo o instala VB-CABLE a mano desde https://vb-audio.com/Cable
  pause
  exit /b 1
)

%PYEXE% "%~dp0instalar_microfono_virtual.py" %*
echo.
pause
endlocal
