"""Compila VoiceICC con la misma configuracion en local y en GitHub Actions."""

import subprocess
import sys


PYINSTALLER_ARGS = [
    "--noconsole",
    "--onefile",
    "--name",
    "VoiceICC",
    "--icon",
    "assets/app_icon.ico",
    "--add-data",
    "assets;assets",
    "--collect-all",
    "onnxruntime",
    "src/voiceicc.py",
]


def main():
    cmd = [sys.executable, "-m", "PyInstaller", *PYINSTALLER_ARGS]
    print("Compilando VoiceICC con PyInstaller...")
    print(" ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
