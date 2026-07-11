@echo off
title Verificar Release V1.4
python -m py_compile src\voiceicc.py
if errorlevel 1 goto error
python tools\release_audit.py
if errorlevel 1 goto error
echo.
echo Release V1.4 validada correctamente.
pause
exit /b 0
:error
echo.
echo La validacion ha encontrado errores.
pause
exit /b 1
