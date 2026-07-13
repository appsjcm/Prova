"""Voces IA locales de VoiceICC: conversion de voz RVC (RVCBackend, con
onnxruntime/rvc-python) y texto a voz Piper (PiperTTS). Sin dependencias de
interfaz. Extraido de voiceicc.py (fase A.3)."""

import os
import sys
import json
import shutil
import zipfile
import platform
import threading
import subprocess
from pathlib import Path
import numpy as np


def find_system_python():
    """Python del sistema para instalar/usar paquetes de IA (copia local
    de la utilidad de voiceicc; se consolidara en core_utils en la fase A.4)."""
    if not getattr(sys, "frozen", False):
        return [sys.executable]
    for cand in (["py", "-3"], ["python"], ["python3"]):
        try:
            if shutil.which(cand[0]):
                return cand
        except Exception:
            pass
    return None


class RVCBackend:
    """Conversión de voz neuronal LOCAL (RVC), sin enviar el audio a ningún
    servidor. Todo el procesamiento ocurre en el PC del usuario.

    El backend pesado (PyTorch + rvc-python) es OPCIONAL: si no está
    instalado, VoiceICC sigue funcionando con su motor DSP de siempre y esta
    capa queda inactiva. Cuando el usuario instala el backend y descarga un
    modelo .pth en la carpeta de voces, las voces IA se activan solas.

    Ventajas de hacerlo local: funciona sin Internet, más privacidad, sin
    costes por uso, y los usuarios pueden descargar nuevas voces."""

    BASE_FILES = ("hubert_base.pt", "rmvpe.pt")
    BASE_URLS = {
        "hubert_base.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt",
        "rmvpe.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt",
    }

    def __init__(self, models_dir=None, base_dir=None):
        base = models_dir or os.path.join(os.path.expanduser("~"), "VoiceICC", "voces_ia")
        self.models_dir = base
        self.base_dir = base_dir or os.path.join(os.path.expanduser("~"), "VoiceICC", "base_ia")
        try:
            os.makedirs(self.models_dir, exist_ok=True)
            os.makedirs(self.base_dir, exist_ok=True)
        except Exception:
            pass
        self.enabled = False
        self.active_model = None
        self.pitch = 0           # semitonos de transposición
        self.index_rate = 0.5    # peso del índice (timbre) 0..1
        self.device = "cpu"
        self._impl = None        # objeto de inferencia cargado (rvc-python)
        self._loaded_name = None
        self._backend_ok = None
        self._backend_reason = ""
        self.lock = threading.Lock()
        # Buffer de streaming para tiempo real (ventana con contexto).
        self._buf = np.zeros(0, dtype=np.float32)
        self._tail = np.zeros(0, dtype=np.float32)
        # Aceleración ONNX (inferencia nativa, más rápida que PyTorch puro).
        self._onnx_session = None
        self.onnx_provider = None

    # -- detección de ONNX Runtime (inferencia acelerada) --
    def onnx_info(self):
        """Devuelve (disponible, lista_de_providers). Los providers indican la
        aceleración: CUDA (NVIDIA), DmlExecutionProvider (DirectML: AMD/Intel),
        CPUExecutionProvider (CPU)."""
        try:
            import onnxruntime as ort
            provs = list(ort.get_available_providers())
            return True, provs
        except Exception:
            return False, []

    def _best_onnx_provider(self, provs):
        for pref in ("CUDAExecutionProvider", "DmlExecutionProvider", "CPUExecutionProvider"):
            if pref in provs:
                return pref
        return provs[0] if provs else "CPUExecutionProvider"

    # -- detección del backend opcional --
    def detect(self, force=False):
        """Comprueba si el backend de IA está instalado. Devuelve (ok, motivo)."""
        if self._backend_ok is not None and not force:
            return self._backend_ok, self._backend_reason
        onnx_ok, provs = self.onnx_info()
        onnx_txt = ""
        if onnx_ok:
            onnx_txt = " · ONNX activo (" + self._best_onnx_provider(provs).replace("ExecutionProvider", "") + ")"
        try:
            import torch  # noqa: F401
        except Exception:
            # Sin torch pero con ONNX y un modelo .onnx, aún se puede inferir.
            if onnx_ok:
                self._backend_ok = True
                self._backend_reason = ("Motor ONNX disponible (rápido, local)" + onnx_txt +
                                        ". Para modelos .pth instala también: pip install rvc-python torch")
                return self._backend_ok, self._backend_reason
            self._backend_ok = False
            self._backend_reason = ("Falta el motor de IA. Rápido: pip install onnxruntime  ·  "
                                    "completo: pip install rvc-python torch")
            return self._backend_ok, self._backend_reason
        try:
            import rvc_python  # noqa: F401
        except Exception:
            self._backend_ok = False
            self._backend_reason = ("Falta rvc-python. Instálalo con: "
                                    "pip install rvc-python")
            return self._backend_ok, self._backend_reason
        self._backend_ok = True
        self._backend_reason = "Motor de IA disponible (procesamiento local)" + onnx_txt + "."
        return True, self._backend_reason

    @property
    def ready(self):
        return bool(self.enabled and self._impl is not None)

    def base_models_present(self):
        """Devuelve la lista de modelos base de RVC que faltan por descargar."""
        faltan = []
        for nombre in self.BASE_FILES:
            ruta = Path(self.base_dir) / nombre
            if not (ruta.exists() and ruta.stat().st_size > 0):
                faltan.append(nombre)
        return faltan

    def download_base_models(self, progress=None):
        """Descarga (online) los modelos base de RVC que falten a base_dir.
        Devuelve (ok_count, total_faltan). progress(str) es opcional."""
        faltan = self.base_models_present()
        ok = 0
        for nombre in faltan:
            url = self.BASE_URLS.get(nombre)
            if not url:
                continue
            destino = Path(self.base_dir) / nombre
            try:
                if progress:
                    progress(f"Descargando {nombre}…")
                from urllib.request import urlopen
                with urlopen(url) as r, open(destino, "wb") as out:
                    shutil.copyfileobj(r, out)
                ok += 1
            except Exception as exc:
                print(f"No se pudo descargar {nombre}: {exc}")
        return ok, len(faltan)

    def _apply_base_env(self):
        """Apunta rvc-python a nuestros modelos base locales (uso offline).
        No pasa nada si la librería no usa estas variables."""
        try:
            os.environ.setdefault("RVC_MODELDIR", self.base_dir)
            os.environ.setdefault("rmvpe_root", self.base_dir)
            os.environ.setdefault("hubert_path", str(Path(self.base_dir) / "hubert_base.pt"))
        except Exception:
            pass

    def readiness(self):
        """Checklist estructurado del estado de la ruta IA, para guiar al
        usuario paso a paso. Los modelos base solo hacen falta para .pth."""
        def _imp(mod):
            try:
                __import__(mod)
                return True
            except Exception:
                return False
        torch_ok = _imp("torch")
        rvc_ok = _imp("rvc_python")
        onnx_ok, provs = self.onnx_info()
        motor_ok = onnx_ok or (torch_ok and rvc_ok)
        provider = self._best_onnx_provider(provs).replace("ExecutionProvider", "") if onnx_ok else ("PyTorch" if torch_ok else "-")
        modelos = self.list_models()
        sel = next((m for m in modelos if m["name"] == self.active_model), None)
        usa_onnx = bool(sel and sel.get("onnx"))
        faltan_base = self.base_models_present()
        # El motor que necesita el modelo SELECCIONADO:
        #  · .onnx  -> onnxruntime (viene incluido en el .exe).
        #  · .pth   -> rvc-python + torch (motor completo) + modelos base.
        sel_es_pth = bool(sel and not sel.get("onnx"))
        motor_sel_ok = (torch_ok and rvc_ok) if sel_es_pth else onnx_ok
        need_base = sel_es_pth
        base_ok = (not need_base) or (not faltan_base)
        listo = bool(modelos and motor_sel_ok and base_ok)
        if not modelos and not motor_ok:
            siguiente = "Importa un modelo de voz .onnx (funciona ya, sin instalar nada)."
        elif not modelos:
            siguiente = "Importa un modelo de voz .onnx (recomendado, ya funciona) o .pth."
        elif sel_es_pth and not (torch_ok and rvc_ok):
            siguiente = "Este modelo .pth necesita el motor completo (botón «Instalar motor completo») o usa un modelo .onnx."
        elif need_base and faltan_base:
            siguiente = "Descarga los modelos base (botón «Descargar modelos base»)."
        elif not motor_sel_ok:
            siguiente = "Falta el motor para este modelo. Usa un modelo .onnx (ya incluido)."
        elif not self.enabled:
            siguiente = "Activa la voz IA y elige tu voz."
        else:
            siguiente = "Todo listo: habla y saldrá con la voz IA."
        return {
            "motor_ok": motor_ok, "onnx": onnx_ok, "torch": torch_ok and rvc_ok,
            "provider": provider, "modelos": len(modelos), "usa_onnx": usa_onnx,
            "base_ok": base_ok, "need_base": need_base, "faltan_base": faltan_base,
            "listo": listo, "siguiente": siguiente,
        }

    def data_report(self):
        """Resumen legible del estado de los datos de IA (para la interfaz),
        en forma de checklist con el siguiente paso."""
        r = self.readiness()
        motor = f"✅ Motor IA ({r['provider']})" if r["motor_ok"] else "⬜ Motor IA (falta instalar)"
        voces = f"✅ Modelos de voz: {r['modelos']}" if r["modelos"] else "⬜ Sin modelos de voz"
        if not r["need_base"]:
            base = "✅ Base no necesaria (ONNX)"
        elif r["base_ok"]:
            base = "✅ Modelos base"
        else:
            base = "⬜ Faltan modelos base: " + ", ".join(r["faltan_base"])
        return f"{motor}   ·   {voces}   ·   {base}\n➡ {r['siguiente']}"

    # -- biblioteca de modelos de voz --
    def list_models(self):
        """Lista los modelos de voz de la carpeta: .onnx (inferencia rápida) y
        .pth (con su .index si existe)."""
        out = []
        try:
            base = Path(self.models_dir)
            vistos = set()
            for f in sorted(base.glob("*.onnx")):
                out.append({"name": f.stem, "pth": str(f), "index": None, "onnx": True})
                vistos.add(f.stem)
            for f in sorted(base.glob("*.pth")):
                if f.stem in vistos:
                    continue
                idx = None
                cand = f.with_suffix(".index")
                if cand.exists():
                    idx = str(cand)
                else:
                    otros = list(base.glob(f"{f.stem}*.index"))
                    if otros:
                        idx = str(otros[0])
                out.append({"name": f.stem, "pth": str(f), "index": idx, "onnx": False})
        except Exception:
            pass
        return out

    def import_model(self, src_path):
        """Copia un modelo (.onnx o .pth, con su .index si viene al lado) a la
        carpeta de voces."""
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(src_path)
        dst = Path(self.models_dir) / src.name
        shutil.copy2(str(src), str(dst))
        idx = src.with_suffix(".index")
        if idx.exists():
            shutil.copy2(str(idx), str(Path(self.models_dir) / idx.name))
        return dst.stem

    @staticmethod
    def _url_filename(url):
        from urllib.parse import urlparse, unquote
        nombre = os.path.basename(unquote(urlparse(url).path))
        return nombre or "modelo"

    def download_model_from_url(self, pth_url, index_url=None, name=None, progress=None):
        """Descarga un modelo de voz desde una URL directa. Acepta .pth/.onnx
        (opcionalmente con su .index) o un .zip que los contenga (típico de
        voice-models.com): en ese caso extrae el .pth/.onnx y el .index.
        Devuelve el nombre del modelo importado."""
        from urllib.request import urlopen, Request
        def _bajar(url, destino):
            if progress:
                progress(f"Descargando {Path(destino).name}…")
            req = Request(url, headers={"User-Agent": "VoiceICC"})
            with urlopen(req) as r, open(destino, "wb") as out:
                shutil.copyfileobj(r, out)

        fname = self._url_filename(pth_url)
        stem = name or os.path.splitext(fname)[0]
        ext = os.path.splitext(fname)[1].lower()

        # ZIP: descarga a temporal, extrae el modelo y el índice.
        if ext == ".zip" or "zip" in ext:
            import tempfile
            tmp = Path(tempfile.mkdtemp()) / "modelo.zip"
            _bajar(pth_url, str(tmp))
            return self._import_from_zip(str(tmp), name)

        if ext not in (".pth", ".onnx"):
            ext = ".pth"
        destino = Path(self.models_dir) / f"{stem}{ext}"
        _bajar(pth_url, str(destino))
        if index_url:
            _bajar(index_url, str(Path(self.models_dir) / f"{stem}.index"))
        return stem

    def _import_from_zip(self, zip_path, name=None):
        """Extrae el primer .pth/.onnx (y un .index si hay) de un zip a la
        carpeta de voces. Devuelve el nombre del modelo."""
        with zipfile.ZipFile(zip_path) as z:
            nombres = z.namelist()
            modelo = next((n for n in nombres if n.lower().endswith((".pth", ".onnx"))), None)
            if not modelo:
                raise ValueError("El zip no contiene ningún modelo .pth o .onnx.")
            indice = next((n for n in nombres if n.lower().endswith(".index")), None)
            mext = os.path.splitext(modelo)[1].lower()
            stem = name or os.path.splitext(os.path.basename(modelo))[0]
            with z.open(modelo) as src, open(Path(self.models_dir) / f"{stem}{mext}", "wb") as out:
                shutil.copyfileobj(src, out)
            if indice:
                with z.open(indice) as src, open(Path(self.models_dir) / f"{stem}.index", "wb") as out:
                    shutil.copyfileobj(src, out)
        return stem

    # -- carga / descarga del modelo --
    def load(self, name):
        """Carga un modelo por nombre. Devuelve True si quedó listo."""
        self.active_model = name
        ok, _ = self.detect()
        if not ok or not name:
            with self.lock:
                self._impl = None
            return False
        model = next((m for m in self.list_models() if m["name"] == name), None)
        if not model:
            return False
        # Ruta ONNX (rápida): modelos .onnx con onnxruntime.
        if model.get("onnx"):
            onnx_ok, provs = self.onnx_info()
            if not onnx_ok:
                print("Modelo .onnx pero falta onnxruntime (pip install onnxruntime)")
                return False
            try:
                import onnxruntime as ort
                provider = self._best_onnx_provider(provs)
                sess = ort.InferenceSession(model["pth"], providers=[provider])
                with self.lock:
                    self._onnx_session = sess
                    self.onnx_provider = provider
                    self._impl = sess     # marca "cargado" (ready)
                    self._loaded_name = name
                    self._buf = np.zeros(0, dtype=np.float32)
                    self._tail = np.zeros(0, dtype=np.float32)
                return True
            except Exception as exc:
                print("No se pudo cargar el modelo ONNX:", exc)
                with self.lock:
                    self._impl = None
                    self._onnx_session = None
                return False
        # Ruta PyTorch (rvc-python) para .pth.
        try:
            self._apply_base_env()
            from rvc_python.infer import RVCInference
            impl = RVCInference(device=self.device)
            impl.load_model(model["pth"], index_path=model.get("index"))
            try:
                impl.set_params(f0up_key=int(self.pitch), index_rate=float(self.index_rate))
            except Exception:
                pass
            with self.lock:
                self._impl = impl
                self._onnx_session = None
                self._loaded_name = name
                self._buf = np.zeros(0, dtype=np.float32)
                self._tail = np.zeros(0, dtype=np.float32)
            return True
        except Exception as exc:
            print("No se pudo cargar el modelo RVC:", exc)
            with self.lock:
                self._impl = None
            return False

    def unload(self):
        with self.lock:
            self._impl = None
            self._onnx_session = None
            self.onnx_provider = None
            self._loaded_name = None
            self._buf = np.zeros(0, dtype=np.float32)
            self._tail = np.zeros(0, dtype=np.float32)

    def set_params(self, pitch=None, index_rate=None):
        if pitch is not None:
            self.pitch = pitch
        if index_rate is not None:
            self.index_rate = index_rate
        impl = self._impl
        if impl is not None:
            try:
                impl.set_params(f0up_key=int(self.pitch), index_rate=float(self.index_rate))
            except Exception:
                pass

    def _infer_array(self, audio, sr):
        """Ejecuta la inferencia del modelo cargado sobre un array mono.
        Usa ONNX (rápido) si hay sesión cargada; si no, rvc-python."""
        sess = self._onnx_session
        if sess is not None:
            try:
                x = np.asarray(audio, dtype=np.float32).reshape(1, -1)
                inp = sess.get_inputs()[0].name
                out = sess.run(None, {inp: x})[0]
                return np.asarray(out, dtype=np.float32).reshape(-1)
            except Exception as exc:
                print("Inferencia ONNX falló:", exc)
                return None
        impl = self._impl
        if impl is None:
            return None
        for meth in ("infer_array", "infer_data", "infer_np"):
            fn = getattr(impl, meth, None)
            if callable(fn):
                try:
                    out = fn(audio, sr)
                    return np.asarray(out, dtype=np.float32).reshape(-1)
                except Exception as exc:
                    print(f"RVC {meth} falló:", exc)
                    return None
        return None

    def process_block(self, x, sr):
        """Conversión en tiempo real por bloques, con contexto y crossfade.

        Devuelve el bloque convertido (mismo tamaño que x) o None para que el
        motor use su cadena DSP como respaldo. Toda la conversión es local."""
        if not self.ready:
            return None
        n = len(x)
        if n == 0:
            return x
        # RVC necesita ventanas amplias para estimar el tono con estabilidad.
        win = max(sr // 2, n * 4)   # ~0.5 s de contexto
        with self.lock:
            self._buf = np.concatenate([self._buf, x])[-win:].astype(np.float32)
            ctx = self._buf.copy()
            tail_prev = self._tail
        conv = self._infer_array(ctx, sr)
        if conv is None or len(conv) < n:
            return None
        y = conv[-n:].astype(np.float32)   # las muestras más recientes
        # Crossfade corto contra la cola anterior para evitar clics de bloque.
        f = min(64, n)
        if len(tail_prev) >= f and f > 0:
            ramp = np.linspace(0.0, 1.0, f, dtype=np.float32)
            y[:f] = tail_prev[-f:] * (1 - ramp) + y[:f] * ramp
        with self.lock:
            self._tail = y.copy()
        return y


class PiperTTS:
    """Texto a voz (TTS) LOCAL con modelos Piper (.onnx). Escribes texto y lo
    dice con una voz sintetica, todo en el PC. Es distinto de RVC: RVC
    transforma TU voz en directo; Piper crea voz a partir de texto.

    Un modelo Piper son dos archivos: <voz>.onnx y <voz>.onnx.json (config).
    Ambos deben estar en la carpeta de voces TTS."""

    def __init__(self, voices_dir=None):
        base = voices_dir or os.path.join(os.path.expanduser("~"), "VoiceICC", "tts_voces")
        self.voices_dir = base
        try:
            os.makedirs(self.voices_dir, exist_ok=True)
        except Exception:
            pass
        self._voice = None
        self._loaded_name = None
        self.sample_rate = 22050
        self._mode = None        # "import" | "subprocess" | None
        self._python = None      # comando de Python del sistema (modo subproceso)

    def install(self, progress=None):
        """Instala el motor TTS (piper-tts) con el Python del sistema.
        Devuelve (ok, mensaje)."""
        py = find_system_python()
        if py is None:
            return False, "No encuentro Python. Instala Python 3 desde python.org y reintenta."
        if progress:
            progress("Instalando piper-tts… (puede tardar unos minutos)")
        try:
            p = subprocess.run(py + ["-m", "pip", "install", "--upgrade", "piper-tts"],
                               capture_output=True, text=True, timeout=1800)
            if p.returncode == 0:
                self._mode = None  # forzar re-deteccion
                return True, "Motor TTS instalado."
            return False, "Fallo al instalar: " + (p.stderr or p.stdout or "")[-300:]
        except Exception as exc:
            return False, f"Error al instalar: {exc}"

    def available(self):
        """(ok, motivo). Funciona con piper importable (modo desarrollo) o con
        piper instalado en el Python del sistema (modo .exe, vía subproceso)."""
        try:
            import piper  # noqa: F401
            self._mode = "import"
            return True, "Motor TTS (Piper) disponible."
        except Exception:
            pass
        py = find_system_python()
        if py:
            try:
                p = subprocess.run(py + ["-c", "import piper"],
                                   capture_output=True, text=True, timeout=20)
                if p.returncode == 0:
                    self._mode = "subprocess"
                    self._python = py
                    return True, "Motor TTS (Piper) disponible en Python del sistema."
            except Exception:
                pass
        self._mode = None
        return False, "Falta el motor TTS. Púlsa «Instalar motor TTS» (o pip install piper-tts)."

    def list_voices(self):
        try:
            return sorted(p.stem for p in Path(self.voices_dir).glob("*.onnx"))
        except Exception:
            return []

    def _config_for(self, onnx_path):
        p = Path(onnx_path)
        cand = Path(str(p) + ".json")          # <voz>.onnx.json
        if cand.exists():
            return cand
        cand2 = p.with_suffix(".json")          # <voz>.json
        if cand2.exists():
            return cand2
        return None

    def import_voice(self, src_path):
        """Copia un modelo .onnx (y su .onnx.json si viene al lado) a la carpeta."""
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(src_path)
        shutil.copy2(str(src), str(Path(self.voices_dir) / src.name))
        cfg = self._config_for(src)
        if cfg is not None:
            shutil.copy2(str(cfg), str(Path(self.voices_dir) / cfg.name))
        return src.stem

    # Voces Piper en español conocidas (repo oficial rhasspy/piper-voices).
    # El .onnx.json se deriva anadiendo ".json" a la URL del .onnx.
    ES_VOICES = {
        "es_ES-carlfm-x_low": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/x_low/es_ES-carlfm-x_low.onnx",
        "es_ES-davefx-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx",
        "es_ES-sharvard-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx",
        "es_ES-mls_10246-low": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/low/es_ES-mls_10246-low.onnx",
        "es_MX-ald-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx",
        "es_MX-claude-high": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx",
    }

    def download_voice_from_url(self, onnx_url, json_url=None, name=None, progress=None):
        """Descarga una voz Piper (.onnx) y su config (.onnx.json). Si no se da
        json_url, se deriva anadiendo '.json' a la URL del .onnx."""
        from urllib.request import urlopen, Request
        if "/blob/" in onnx_url:
            onnx_url = onnx_url.replace("/blob/", "/resolve/")
        if not json_url:
            json_url = onnx_url + ".json"
        elif "/blob/" in json_url:
            json_url = json_url.replace("/blob/", "/resolve/")

        from urllib.parse import urlparse, unquote
        fname = os.path.basename(unquote(urlparse(onnx_url).path)) or "voz.onnx"
        stem = name or (fname[:-5] if fname.endswith(".onnx") else os.path.splitext(fname)[0])

        def _bajar(url, destino):
            if progress:
                progress(f"Descargando {Path(destino).name}…")
            req = Request(url, headers={"User-Agent": "VoiceICC"})
            with urlopen(req) as r, open(destino, "wb") as out:
                shutil.copyfileobj(r, out)

        onnx_dst = Path(self.voices_dir) / f"{stem}.onnx"
        _bajar(onnx_url, str(onnx_dst))
        try:
            _bajar(json_url, str(Path(self.voices_dir) / f"{stem}.onnx.json"))
        except Exception as exc:
            print("No se pudo descargar el .onnx.json:", exc)
        return stem

    def load(self, name):
        ok, _ = self.available()
        if not ok or not name:
            self._voice = None
            return False
        onnx = Path(self.voices_dir) / f"{name}.onnx"
        if not onnx.exists():
            return False
        cfg = self._config_for(onnx)
        if cfg is None:
            print(f"Falta la config {name}.onnx.json junto al modelo.")
            return False
        # Leer la tasa de muestreo de la config (JSON), sin importar piper.
        try:
            with open(str(cfg), "r", encoding="utf-8") as f:
                self.sample_rate = int(json.load(f).get("audio", {}).get("sample_rate", 22050))
        except Exception:
            self.sample_rate = 22050
        if self._mode == "subprocess":
            # No se importa piper: se sintetiza por subproceso al hablar.
            self._voice = None
            self._loaded_name = name
            return True
        try:
            from piper import PiperVoice
            self._voice = PiperVoice.load(str(onnx), config_path=str(cfg))
            self._loaded_name = name
            try:
                self.sample_rate = int(self._voice.config.sample_rate)
            except Exception:
                pass
            return True
        except Exception as exc:
            print("No se pudo cargar la voz TTS:", exc)
            self._voice = None
            return False

    def _read_wav(self, path):
        import wave as _wave
        with _wave.open(str(path), "rb") as wf:
            sr = wf.getframerate()
            data = wf.readframes(wf.getnframes())
        audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        return audio, sr

    def synthesize(self, text):
        """Devuelve (audio_float32_mono, sample_rate) para el texto dado."""
        if not text.strip() or not self._loaded_name:
            return None, self.sample_rate
        # Modo subproceso (.exe): llama a piper del sistema y lee el WAV.
        if self._mode == "subprocess" and self._python:
            try:
                import tempfile
                onnx = Path(self.voices_dir) / f"{self._loaded_name}.onnx"
                tmp = Path(tempfile.mkdtemp()) / "tts.wav"
                cmd = self._python + ["-m", "piper", "--model", str(onnx),
                                      "--output_file", str(tmp)]
                subprocess.run(cmd, input=text, text=True,
                               capture_output=True, timeout=120)
                if tmp.exists():
                    return self._read_wav(tmp)
            except Exception as exc:
                print("Síntesis TTS (subproceso) falló:", exc)
            return None, self.sample_rate
        # Modo import (desarrollo).
        if self._voice is None:
            return None, self.sample_rate
        try:
            trozos = []
            for b in self._voice.synthesize_stream_raw(text):
                trozos.append(np.frombuffer(b, dtype=np.int16))
            if trozos:
                audio = np.concatenate(trozos).astype(np.float32) / 32768.0
                return audio, self.sample_rate
        except Exception as exc:
            print("synthesize_stream_raw no disponible:", exc)
        try:
            import wave as _wave
            import tempfile
            tmp = Path(tempfile.mkdtemp()) / "tts.wav"
            with _wave.open(str(tmp), "wb") as wf:
                self._voice.synthesize(text, wf)
            return self._read_wav(tmp)
        except Exception as exc:
            print("Sintesis TTS fallo:", exc)
            return None, self.sample_rate
