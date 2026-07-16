@echo off
REM Instalador de los datos de Voces IA (RVC) para VoiceICC.
REM Copia los modelos a la carpeta personal y, con --pip, instala el motor.
setlocal
cd /d "%~dp0"

set PYEXE=
where py >nul 2>nul && set PYEXE=py -3
if "%PYEXE%"=="" (
  where python >nul 2>nul && set PYEXE=python
)

if "%PYEXE%"=="" (
  echo No se encontro Python en este equipo.
  echo Instala Python 3 desde https://www.python.org y vuelve a ejecutar.
  echo (Los modelos base tambien puedes copiarlos a mano en %%USERPROFILE%%\VoiceICC\base_ia)
  pause
  exit /b 1
)

echo Instalando datos de Voces IA con %PYEXE% ...
%PYEXE% "%~dp0instalar_datos_ia.py" --pip --online %*
echo.
pause
endlocal
