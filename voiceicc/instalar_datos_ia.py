#!/usr/bin/env python3
"""Instalador de los DATOS de Voces IA (RVC) para VoiceICC.

Deja todo lo que necesitan las voces IA en la carpeta personal del usuario,
para que funcionen sin Internet y sin enviar la voz a ningun servidor:

  ~/VoiceICC/voces_ia   -> modelos de voz .pth (+ .index)
  ~/VoiceICC/base_ia    -> modelos base de RVC (hubert_base.pt, rmvpe.pt)

Funciona de dos maneras:

  * OFFLINE: si al lado hay una carpeta "datos_ia" (la que trae el .zip de
    datos), copia de ahi los modelos y, si existe "datos_ia/wheels", instala
    el motor (rvc-python + torch) desde esos wheels sin descargar nada.
  * ONLINE: si no hay datos locales, descarga los modelos base y, con --pip,
    instala el motor desde PyPI.

Uso:
  python instalar_datos_ia.py            # copia modelos desde datos_ia si existe
  python instalar_datos_ia.py --pip      # ademas instala el motor de IA
  python instalar_datos_ia.py --online   # permite descargar de Internet
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Modelos base oficiales de RVC (repositorio publico).
BASE_MODELS = {
    "hubert_base.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt",
    "rmvpe.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt",
}


def home_dirs():
    base = Path(os.path.expanduser("~")) / "VoiceICC"
    voces = base / "voces_ia"
    base_ia = base / "base_ia"
    for d in (voces, base_ia):
        d.mkdir(parents=True, exist_ok=True)
    return voces, base_ia


def copiar(src, dst):
    """Copia un archivo mostrando el resultado. Devuelve True si quedo."""
    try:
        shutil.copy2(str(src), str(dst))
        print(f"  + {Path(dst).name}")
        return True
    except Exception as exc:
        print(f"  ! No se pudo copiar {src}: {exc}")
        return False


def copiar_datos_locales(datos_dir, voces, base_ia):
    """Copia modelos de voz y modelos base desde la carpeta datos_ia."""
    copiados = 0
    voces_src = datos_dir / "voces"
    if voces_src.is_dir():
        for f in list(voces_src.glob("*.pth")) + list(voces_src.glob("*.index")):
            copiados += copiar(f, voces / f.name)
    base_src = datos_dir / "base"
    if base_src.is_dir():
        for f in base_src.glob("*"):
            if f.is_file():
                copiados += copiar(f, base_ia / f.name)
    return copiados


def descargar(url, destino):
    """Descarga un archivo por HTTPS a la ruta destino."""
    try:
        from urllib.request import urlopen
        print(f"  descargando {Path(destino).name} ...")
        with urlopen(url) as r, open(destino, "wb") as out:
            shutil.copyfileobj(r, out)
        print(f"  + {Path(destino).name}")
        return True
    except Exception as exc:
        print(f"  ! No se pudo descargar {url}: {exc}")
        return False


def asegurar_base_online(base_ia):
    """Descarga los modelos base que falten."""
    ok = 0
    for nombre, url in BASE_MODELS.items():
        destino = base_ia / nombre
        if destino.exists() and destino.stat().st_size > 0:
            print(f"  = {nombre} ya presente")
            ok += 1
            continue
        ok += descargar(url, destino)
    return ok


def instalar_motor(datos_dir, online):
    """Instala rvc-python + torch: offline desde wheels o desde PyPI."""
    wheels = datos_dir / "wheels" if datos_dir else None
    req = None
    for cand in (Path(__file__).parent / "requirements_ia.txt",
                 (datos_dir / "requirements_ia.txt") if datos_dir else None):
        if cand and cand.exists():
            req = cand
            break
    cmd = [sys.executable, "-m", "pip", "install"]
    if wheels and wheels.is_dir() and any(wheels.iterdir()):
        print("Instalando el motor de IA desde wheels locales (sin Internet)...")
        cmd += ["--no-index", "--find-links", str(wheels)]
    elif online:
        print("Instalando el motor de IA desde PyPI...")
    else:
        print("No hay wheels locales y --online no esta activado: se omite el motor.")
        print("Puedes instalarlo luego con: pip install rvc-python torch")
        return False
    if req:
        cmd += ["-r", str(req)]
    else:
        cmd += ["rvc-python", "torch"]
    print("  " + " ".join(cmd))
    try:
        subprocess.check_call(cmd)
        print("Motor de IA instalado.")
        return True
    except Exception as exc:
        print(f"! La instalacion del motor fallo: {exc}")
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description="Instala los datos de Voces IA de VoiceICC.")
    parser.add_argument("--datos", default=None, help="Carpeta datos_ia (por defecto, junto a este script).")
    parser.add_argument("--pip", action="store_true", help="Instalar tambien el motor de IA.")
    parser.add_argument("--online", action="store_true", help="Permitir descargas de Internet.")
    parser.add_argument("--models-only", action="store_true", help="Solo copiar/descargar modelos, sin motor.")
    args = parser.parse_args(argv)

    voces, base_ia = home_dirs()
    print("Carpeta de voces IA:", voces)
    print("Carpeta de modelos base:", base_ia)

    datos_dir = Path(args.datos) if args.datos else (Path(__file__).parent / "datos_ia")
    copiados = 0
    if datos_dir.is_dir():
        print(f"\nUsando datos locales: {datos_dir}")
        copiados = copiar_datos_locales(datos_dir, voces, base_ia)
    else:
        print("\nNo hay carpeta datos_ia local.")

    # Completar modelos base por Internet si hace falta y se permite.
    faltan_base = [n for n in BASE_MODELS if not (base_ia / n).exists()]
    if faltan_base:
        if args.online:
            print("\nDescargando modelos base que faltan...")
            asegurar_base_online(base_ia)
        else:
            print("\nFaltan modelos base:", ", ".join(faltan_base))
            print("Ejecuta con --online para descargarlos, o copialos en", base_ia)

    if args.pip and not args.models_only:
        print()
        instalar_motor(datos_dir if datos_dir.is_dir() else None, args.online)

    print("\nListo. Abre VoiceICC y ve a la pestana 'Voces IA'.")
    print(f"Modelos de voz copiados: {copiados}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
