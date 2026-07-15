@echo off
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python validar_voiceicc.py
python compilar_voiceicc.py
echo EXE creado en dist\VoiceICC.exe
pause
