@echo off
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller --noconsole --onefile --name VoiceICC --icon assets\app_icon.ico --add-data "assets;assets" --collect-all onnxruntime src\voiceicc.py
echo EXE creado en dist\VoiceICC.exe
pause
