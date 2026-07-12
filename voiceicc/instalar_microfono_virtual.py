#!/usr/bin/env python3
"""Instala el microfono virtual de VoiceICC (driver estandar VB-CABLE).

Descarga el paquete oficial de VB-Audio y lanza su instalador. Es el driver
que hace de microfono virtual: la voz modulada de VoiceICC entra como "micro"
en Discord, juegos, OBS, etc.

Nota: un driver de audio FIRMADO con nombre propio requiere un certificado de
firma de kernel de Microsoft. VoiceICC usa VB-CABLE, gratuito y con el mismo
resultado.
"""

import os
import platform
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

VBCABLE_URL = "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack45.zip"


def main():
    if platform.system() != "Windows":
        print("El microfono virtual es un driver de Windows. En este sistema no aplica.")
        return 0
    print("Descargando el driver de microfono virtual (VB-CABLE)...")
    tmp = Path(tempfile.mkdtemp(prefix="voiceicc_vbcable_"))
    zip_path = tmp / "vbcable.zip"
    try:
        with urlopen(VBCABLE_URL) as r, open(zip_path, "wb") as out:
            shutil.copyfileobj(r, out)
    except Exception as exc:
        print("No se pudo descargar:", exc)
        print("Instalalo a mano desde https://vb-audio.com/Cable")
        return 1
    try:
        with zipfile.ZipFile(str(zip_path)) as z:
            z.extractall(str(tmp))
    except Exception as exc:
        print("No se pudo descomprimir:", exc)
        return 1

    prefer = "VBCABLE_Setup_x64.exe" if platform.machine().endswith("64") else "VBCABLE_Setup.exe"
    setup = None
    for cand in [tmp / prefer] + list(tmp.glob("VBCABLE_Setup*.exe")):
        if cand.exists():
            setup = cand
            break
    if setup is None:
        print("No encontre el instalador dentro del paquete.")
        return 1

    print("Abriendo el instalador. Acepta el aviso de Windows y pulsa 'Install Driver'.")
    try:
        os.startfile(str(setup))  # noqa: P204
    except Exception as exc:
        print("No se pudo abrir el instalador:", exc)
        print("Ejecutalo a mano:", setup)
        return 1
    print("Cuando termine, abre VoiceICC > Cable Virtual > 'Comprobar / enrutar'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
