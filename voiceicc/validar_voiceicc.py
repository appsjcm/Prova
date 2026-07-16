"""Validacion rapida de VoiceICC antes de compilar el ejecutable."""

import py_compile
from pathlib import Path


MODULES = [
    "src/voiceicc.py",
    "src/voces_ia.py",
    "src/audio_engine.py",
    "src/voicebank.py",
    "compilar_voiceicc.py",
    "instalar_datos_ia.py",
    "instalar_microfono_virtual.py",
]


def main():
    root = Path(__file__).resolve().parent
    for rel in MODULES:
        path = root / rel
        if not path.exists():
            raise FileNotFoundError(rel)
        py_compile.compile(str(path), doraise=True)
        print(f"OK py_compile: {rel}")
    print("Validacion rapida completada.")


if __name__ == "__main__":
    main()
