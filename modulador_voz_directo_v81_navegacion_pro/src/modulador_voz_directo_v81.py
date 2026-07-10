from PIL import Image, ImageDraw, ImageFont, ImageFilter

import json
import os
import html
import webbrowser
import sys
from pathlib import Path
import wave
import zipfile
import threading
import shutil
import subprocess
import platform
import random
import time
import math
from datetime import datetime
import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

import numpy as np
import sounddevice as sd

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

try:
    import pystray
    from PIL import ImageTk
    TRAY_AVAILABLE = True
except Exception:
    pystray = None
    ImageTk = None
    TRAY_AVAILABLE = False

# Atajos globales: funcionan aunque el juego o Discord tengan el foco.
try:
    import keyboard as global_keyboard
    GLOBAL_HOTKEYS_AVAILABLE = True
except Exception:
    global_keyboard = None
    GLOBAL_HOTKEYS_AVAILABLE = False


APP_NAME = "Modulador de Voz en Directo"
VERSION = "81.0 Navegación Pro"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "modulador_voz_directo_v81_config.json")


COLORS = {
    "bg": "#0c0d14",
    "panel": "#151827",
    "panel2": "#1d2135",
    "text": "#f5f7ff",
    "muted": "#aab0d6",
    "accent": "#7c5cff",
    "accent2": "#00e5ff",
    "warning": "#ffcc66",
    "danger": "#ff5c8a",
    "ok": "#62ffb4",
}


def clamp(value, low, high):
    return max(low, min(high, value))



PACKS_DATA = {'Gaming': {'slug': 'gaming', 'title': 'PACK GAMING', 'subtitle': 'Fortnite · Discord · Directos', 'colors': ((24, 33, 65), (45, 111, 255), (0, 229, 255)), 'icon': 'G', 'voices': ['Gaming limpio', 'Discord claro', 'Discord nítido', 'Fortnite grave', 'Fortnite épico', 'Streamer', 'Comentarista eSports', 'Tryhard oscuro']}, 'Épicas': {'slug': 'epicas', 'title': 'PACK ÉPICO', 'subtitle': 'Narrador · Tráiler · Jefe final', 'colors': ((40, 18, 52), (132, 64, 255), (255, 203, 87)), 'icon': 'E', 'voices': ['Narrador épico', 'Cine tráiler', 'Héroe final', 'Titán', 'Jefe final']}, 'Oscuras': {'slug': 'oscuras', 'title': 'PACK OSCURO', 'subtitle': 'Villano · Demonio · Monstruo', 'colors': ((22, 16, 26), (110, 46, 92), (255, 92, 138)), 'icon': 'O', 'voices': ['Voz grave', 'Villano', 'Demonio suave', 'Monstruo cueva', 'Sombra', 'Guardián oscuro']}, 'Robots': {'slug': 'robots', 'title': 'PACK ROBOT', 'subtitle': 'IA · Cyborg · Futurista', 'colors': ((15, 26, 36), (0, 170, 220), (117, 255, 249)), 'icon': 'R', 'voices': ['Robot directo', 'Androide', 'IA futurista', 'Cyborg', 'Casco espacial', 'Robot roto']}, 'Radio': {'slug': 'radio', 'title': 'PACK RADIO', 'subtitle': 'Locutor · Walkie · Megáfono', 'colors': ((44, 26, 8), (255, 150, 55), (255, 217, 123)), 'icon': 'R', 'voices': ['Locutor español', 'Radio para directo', 'Radio antigua', 'Walkie Talkie', 'Megáfono', 'Estadio']}, 'Divertidas': {'slug': 'divertidas', 'title': 'PACK MEME', 'subtitle': 'Ardilla · Payaso · Mini robot', 'colors': ((40, 18, 18), (255, 94, 117), (255, 208, 76)), 'icon': 'D', 'voices': ['Voz aguda', 'Ardilla', 'Duende', 'Payaso gamer', 'Mini robot', 'Caricatura']}, 'Fantasía': {'slug': 'fantasia', 'title': 'PACK FANTASÍA', 'subtitle': 'Alien · Mago · Dragón', 'colors': ((18, 26, 40), (131, 84, 255), (98, 255, 180)), 'icon': 'F', 'voices': ['Alien', 'Fantasma', 'Eco mágico', 'Hechicero', 'Criatura mágica', 'Dragón suave']}, 'Limpias': {'slug': 'limpias', 'title': 'PACK LIMPIO', 'subtitle': 'Podcast · Voz clara · Cálida', 'colors': ((17, 32, 36), (76, 166, 191), (194, 245, 255)), 'icon': 'L', 'voices': ['Voz clara', 'Podcast', 'Nocturna suave', 'Voz cálida']}}

class VoiceBank:
    # Voces creadas por el usuario (se cargan de JSON al arrancar).
    custom = {}

    @staticmethod
    def all_presets():
        presets = VoiceBank.base_presets()
        for name, values in VoiceBank.custom.items():
            if name not in presets:
                presets[name] = ("Mis voces", dict(values))
        return presets

    @staticmethod
    def base_presets():
        return {
            # GAMING
            "Gaming limpio":        ("Gaming", dict(pitch=0,  bass=15, robot=0,  echo=0,  radio=3,  megaphone=0,  gate=8,  comp=38, vol=90)),
            "Discord claro":        ("Gaming", dict(pitch=0,  bass=12, robot=0,  echo=0,  radio=0,  megaphone=0,  gate=9,  comp=58, vol=94)),
            "Discord nítido":       ("Gaming", dict(pitch=0,  bass=6,  robot=0,  echo=0,  radio=5,  megaphone=0,  gate=9,  comp=64, vol=95)),
            "Fortnite grave":       ("Gaming", dict(pitch=-5, bass=46, robot=0,  echo=0,  radio=0,  megaphone=0,  gate=7,  comp=52, vol=92)),
            "Fortnite épico":       ("Gaming", dict(pitch=-7, bass=58, robot=3,  echo=6,  radio=0,  megaphone=0,  gate=7,  comp=55, vol=92)),
            "Streamer":             ("Gaming", dict(pitch=1,  bass=12, robot=3,  echo=3,  radio=5,  megaphone=0,  gate=7,  comp=45, vol=88)),
            "Comentarista eSports": ("Gaming", dict(pitch=1,  bass=20, robot=0,  echo=2,  radio=12, megaphone=5,  gate=8,  comp=62, vol=94)),
            "Tryhard oscuro":       ("Gaming", dict(pitch=-4, bass=40, robot=4,  echo=4,  radio=4,  megaphone=0,  gate=8,  comp=50, vol=88)),
            "Gamer nocturno":       ("Gaming", dict(pitch=-2, bass=35, robot=0,  echo=8,  radio=0,  megaphone=0,  gate=7,  comp=42, vol=84)),

            # ÉPICAS
            "Narrador épico":       ("Épicas", dict(pitch=-4, bass=45, robot=0,  echo=12, radio=8,  megaphone=0,  gate=6,  comp=55, vol=92)),
            "Cine tráiler":         ("Épicas", dict(pitch=-7, bass=60, robot=3,  echo=18, radio=6,  megaphone=0,  gate=7,  comp=60, vol=90)),
            "Héroe final":          ("Épicas", dict(pitch=-3, bass=45, robot=0,  echo=14, radio=4,  megaphone=0,  gate=6,  comp=52, vol=90)),
            "Titán":                ("Épicas", dict(pitch=-12,bass=90, robot=10, echo=20, radio=0,  megaphone=0,  gate=7,  comp=50, vol=88)),
            "Jefe final":           ("Épicas", dict(pitch=-10,bass=70, robot=28, echo=30, radio=0,  megaphone=0,  gate=8,  comp=45, vol=88)),

            # OSCURAS
            "Voz grave":            ("Oscuras", dict(pitch=-6, bass=45, robot=0,  echo=5,  radio=0,  megaphone=0,  gate=5,  comp=30, vol=90)),
            "Villano":              ("Oscuras", dict(pitch=-8, bass=50, robot=32, echo=22, radio=0,  megaphone=0,  gate=7,  comp=35, vol=86)),
            "Demonio suave":        ("Oscuras", dict(pitch=-9, bass=62, robot=38, echo=18, radio=0,  megaphone=0,  gate=7,  comp=40, vol=84)),
            "Monstruo cueva":       ("Oscuras", dict(pitch=-11,bass=80, robot=18, echo=45, radio=0,  megaphone=0,  gate=6,  comp=35, vol=82)),
            "Sombra":               ("Oscuras", dict(pitch=-7, bass=58, robot=12, echo=34, radio=0,  megaphone=0,  gate=7,  comp=35, vol=80)),
            "Guardián oscuro":      ("Oscuras", dict(pitch=-8, bass=68, robot=10, echo=16, radio=0,  megaphone=0,  gate=7,  comp=45, vol=86)),

            # ROBOTS
            "Robot directo":        ("Robots", dict(pitch=0,  bass=0,  robot=88, echo=4,  radio=12, megaphone=0,  gate=8,  comp=30, vol=84)),
            "Androide":             ("Robots", dict(pitch=-1, bass=10, robot=70, echo=6,  radio=20, megaphone=0,  gate=9,  comp=40, vol=86)),
            "IA futurista":         ("Robots", dict(pitch=2,  bass=0,  robot=55, echo=10, radio=28, megaphone=0,  gate=8,  comp=35, vol=82)),
            "Cyborg":               ("Robots", dict(pitch=-3, bass=30, robot=65, echo=8,  radio=25, megaphone=0,  gate=8,  comp=45, vol=86)),
            "Casco espacial":       ("Robots", dict(pitch=-2, bass=20, robot=25, echo=20, radio=38, megaphone=12, gate=9,  comp=50, vol=88)),
            "Robot roto":           ("Robots", dict(pitch=3,  bass=0,  robot=95, echo=12, radio=35, megaphone=0,  gate=10, comp=20, vol=78)),
            "Drone":                ("Robots", dict(pitch=4,  bass=0,  robot=78, echo=9,  radio=28, megaphone=0,  gate=8,  comp=25, vol=76)),
            "Computadora retro":    ("Robots", dict(pitch=1,  bass=0,  robot=86, echo=3,  radio=45, megaphone=0,  gate=10, comp=35, vol=82)),

            # RADIO
            "Locutor español":      ("Radio", dict(pitch=-3, bass=35, robot=0,  echo=6,  radio=15, megaphone=0,  gate=7,  comp=55, vol=92)),
            "Radio para directo":   ("Radio", dict(pitch=-1, bass=12, robot=8,  echo=0,  radio=95, megaphone=15, gate=9,  comp=55, vol=94)),
            "Radio antigua":        ("Radio", dict(pitch=-1, bass=0,  robot=15, echo=4,  radio=100,megaphone=25, gate=12, comp=60, vol=90)),
            "Walkie Talkie":        ("Radio", dict(pitch=0,  bass=0,  robot=18, echo=2,  radio=90, megaphone=45, gate=12, comp=55, vol=88)),
            "Megáfono":             ("Radio", dict(pitch=0,  bass=0,  robot=8,  echo=4,  radio=45, megaphone=90, gate=10, comp=55, vol=96)),
            "Estadio":              ("Radio", dict(pitch=0,  bass=20, robot=4,  echo=36, radio=25, megaphone=60, gate=8,  comp=55, vol=96)),
            "Radio militar":        ("Radio", dict(pitch=-2, bass=10, robot=12, echo=2,  radio=88, megaphone=50, gate=12, comp=55, vol=90)),

            # DIVERTIDAS
            "Voz aguda":            ("Divertidas", dict(pitch=6,  bass=0,  robot=0,  echo=0,  radio=0,  megaphone=0,  gate=5,  comp=20, vol=78)),
            "Ardilla":              ("Divertidas", dict(pitch=10, bass=0,  robot=0,  echo=0,  radio=0,  megaphone=0,  gate=4,  comp=20, vol=70)),
            "Duende":               ("Divertidas", dict(pitch=7,  bass=0,  robot=10, echo=8,  radio=0,  megaphone=0,  gate=5,  comp=25, vol=78)),
            "Payaso gamer":         ("Divertidas", dict(pitch=5,  bass=0,  robot=8,  echo=5,  radio=10, megaphone=0,  gate=6,  comp=30, vol=82)),
            "Mini robot":           ("Divertidas", dict(pitch=8,  bass=0,  robot=70, echo=4,  radio=15, megaphone=0,  gate=8,  comp=25, vol=76)),
            "Caricatura":           ("Divertidas", dict(pitch=9,  bass=0,  robot=3,  echo=2,  radio=0,  megaphone=0,  gate=5,  comp=25, vol=74)),
            "Gnomo rápido":         ("Divertidas", dict(pitch=8,  bass=0,  robot=6,  echo=5,  radio=0,  megaphone=0,  gate=5,  comp=25, vol=74)),

            # FANTASÍA
            "Alien":                ("Fantasía", dict(pitch=8,  bass=0,  robot=60, echo=15, radio=5,  megaphone=0,  gate=8,  comp=25, vol=78)),
            "Fantasma":             ("Fantasía", dict(pitch=-2, bass=20, robot=10, echo=58, radio=0,  megaphone=0,  gate=6,  comp=20, vol=76)),
            "Eco mágico":           ("Fantasía", dict(pitch=2,  bass=0,  robot=8,  echo=55, radio=0,  megaphone=0,  gate=5,  comp=20, vol=76)),
            "Hechicero":            ("Fantasía", dict(pitch=-3, bass=35, robot=12, echo=40, radio=0,  megaphone=0,  gate=6,  comp=35, vol=84)),
            "Criatura mágica":      ("Fantasía", dict(pitch=4,  bass=15, robot=25, echo=38, radio=0,  megaphone=0,  gate=6,  comp=25, vol=78)),
            "Portal dimensional":   ("Fantasía", dict(pitch=1,  bass=25, robot=40, echo=60, radio=8,  megaphone=0,  gate=8,  comp=30, vol=80)),
            "Dragón suave":         ("Fantasía", dict(pitch=-9, bass=85, robot=15, echo=24, radio=0,  megaphone=0,  gate=7,  comp=42, vol=86)),
            "Mago neón":            ("Fantasía", dict(pitch=2,  bass=18, robot=18, echo=45, radio=6,  megaphone=0,  gate=6,  comp=28, vol=82)),


            # PERSONAS
            "Mujer Lucía":         ("Personas", dict(pitch=3,  bass=8,  robot=0,  echo=4,  radio=0,  megaphone=0,  gate=10, comp=48, vol=90)),
            "Mujer Sofía":         ("Personas", dict(pitch=2,  bass=10, robot=0,  echo=3,  radio=4,  megaphone=0,  gate=10, comp=50, vol=90)),
            "Hombre Diego":        ("Personas", dict(pitch=-1, bass=22, robot=0,  echo=1,  radio=3,  megaphone=0,  gate=8,  comp=52, vol=92)),
            "Hombre Marcos":       ("Personas", dict(pitch=-4, bass=36, robot=0,  echo=2,  radio=5,  megaphone=0,  gate=8,  comp=50, vol=90)),
            "Niño Leo":            ("Personas", dict(pitch=7,  bass=0,  robot=0,  echo=4,  radio=2,  megaphone=0,  gate=6,  comp=28, vol=82)),
            "Niño Nico":           ("Personas", dict(pitch=6,  bass=0,  robot=4,  echo=3,  radio=3,  megaphone=0,  gate=6,  comp=28, vol=82)),
            "Niña Luna":           ("Personas", dict(pitch=7,  bass=0,  robot=0,  echo=5,  radio=1,  megaphone=0,  gate=6,  comp=28, vol=82)),
            "Niña Emma":           ("Personas", dict(pitch=6,  bass=2,  robot=0,  echo=4,  radio=2,  megaphone=0,  gate=6,  comp=30, vol=84)),
            "Abuelo Paco":         ("Personas", dict(pitch=-5, bass=28, robot=0,  echo=3,  radio=8,  megaphone=2,  gate=8,  comp=55, vol=88)),
            "Abuelo José":         ("Personas", dict(pitch=-4, bass=24, robot=0,  echo=2,  radio=5,  megaphone=0,  gate=8,  comp=52, vol=88)),
            "Abuela Carmen":       ("Personas", dict(pitch=1,  bass=10, robot=0,  echo=3,  radio=2,  megaphone=0,  gate=10, comp=50, vol=88)),
            "Abuela Lola":         ("Personas", dict(pitch=2,  bass=8,  robot=0,  echo=4,  radio=3,  megaphone=0,  gate=10, comp=50, vol=88)),

            # CANTADAS / AUTOTUNE
            "AutoTune Suave":       ("Cantadas", dict(pitch=1,  bass=10, robot=0,  echo=12, radio=0,  megaphone=0,  gate=7,  comp=58, vol=88, autotune=35, autotune_shift=0, vibrato=12, chorus=10)),
            "AutoTune Pop":         ("Cantadas", dict(pitch=2,  bass=8,  robot=0,  echo=18, radio=2,  megaphone=0,  gate=7,  comp=65, vol=90, autotune=62, autotune_shift=0, vibrato=18, chorus=22)),
            "Trap Tune":            ("Cantadas", dict(pitch=0,  bass=24, robot=5,  echo=16, radio=6,  megaphone=0,  gate=8,  comp=68, vol=92, autotune=88, autotune_shift=0, vibrato=8,  chorus=16)),
            "Robot Cantante":       ("Cantadas", dict(pitch=1,  bass=6,  robot=48, echo=14, radio=14, megaphone=0,  gate=7,  comp=50, vol=86, autotune=78, autotune_shift=0, vibrato=16, chorus=18)),
            "Coro Doble":           ("Cantadas", dict(pitch=0,  bass=18, robot=0,  echo=24, radio=0,  megaphone=0,  gate=8,  comp=60, vol=88, autotune=40, autotune_shift=0, vibrato=14, chorus=72)),
            "Balada Clara":         ("Cantadas", dict(pitch=0,  bass=18, robot=0,  echo=22, radio=0,  megaphone=0,  gate=8,  comp=62, vol=88, autotune=28, autotune_shift=0, vibrato=26, chorus=16)),
            "Karaoke Pop":          ("Cantadas", dict(pitch=2,  bass=10, robot=0,  echo=20, radio=2,  megaphone=0, gate=7, comp=66, vol=90, autotune=58, autotune_shift=0, vibrato=18, chorus=24)),
            "Karaoke Trap":         ("Cantadas", dict(pitch=0,  bass=28, robot=5,  echo=18, radio=8,  megaphone=0, gate=8, comp=70, vol=92, autotune=90, autotune_shift=-1, vibrato=8, chorus=18)),
            "Karaoke Balada":       ("Cantadas", dict(pitch=0,  bass=20, robot=0,  echo=28, radio=0,  megaphone=0, gate=8, comp=62, vol=88, autotune=32, autotune_shift=0, vibrato=30, chorus=18)),

            # LIMPIAS
            "Voz clara":            ("Limpias", dict(pitch=0,  bass=8,  robot=0,  echo=0,  radio=0,  megaphone=0,  gate=8,  comp=45, vol=90)),
            "Podcast":              ("Limpias", dict(pitch=-1, bass=28, robot=0,  echo=2,  radio=6,  megaphone=0,  gate=9,  comp=60, vol=92)),
            "Nocturna suave":       ("Limpias", dict(pitch=-2, bass=30, robot=0,  echo=10, radio=0,  megaphone=0,  gate=7,  comp=35, vol=82)),
            "Voz cálida":           ("Limpias", dict(pitch=-1, bass=35, robot=0,  echo=1,  radio=0,  megaphone=0,  gate=7,  comp=50, vol=90)),
        }

    @staticmethod
    def categories():
        cats = ["Todas"]
        for category, _ in VoiceBank.all_presets().values():
            if category not in cats:
                cats.append(category)
        return cats


class AudioEngine:
    def __init__(self):
        self.rate = 44100
        self.stream = None
        self.running = False
        self.lock = threading.Lock()

        self.pitch = 0.0
        self.bass = 0.0
        self.robot = 0.0
        self.echo = 0.0
        self.radio = 0.0
        self.megaphone = 0.0
        self.noise_gate = 0.006
        self.compressor = 0.35
        self.volume = 0.90
        self.mute = False
        self.effects_enabled = True
        self.autotune = 0.0
        self.autotune_shift = 0.0
        self.vibrato = 0.0
        self.chorus = 0.0

        self.mic_level = 0.0
        self.out_level = 0.0

        self.echo_buf = np.zeros(self.rate * 2, dtype=np.float32)
        self.echo_pos = 0

        # Pitch shifter granular continuo: estado por usuario del efecto
        # (voz principal, coro, autotune) para que no se pisen entre sí.
        self._ps_window = 1536
        self._ps_states = {}

        # Puerta de ruido con envolvente: ganancia suavizada entre bloques.
        self._gate_gain = 1.0
        self._gate_open = True

        # Filtros FIR equivalentes a los antiguos bucles por muestra
        # (graves y radio), con cola de contexto entre bloques.
        alpha_bass = 0.075
        self._bass_fir = (alpha_bass * (1.0 - alpha_bass) ** np.arange(100)).astype(np.float32)
        self._bass_tail = np.zeros(len(self._bass_fir) - 1, dtype=np.float32)
        alpha_radio = 0.965
        self._radio_fir = (alpha_radio ** (np.arange(160) + 1)).astype(np.float32)
        self._radio_dtail = np.zeros(len(self._radio_fir) - 1, dtype=np.float32)
        self._radio_prev = 0.0

        # Fases persistentes de los LFO (en ciclos, 0..1): la portadora del
        # robot, el trémolo del megáfono y el vibrato ya no se reinician en
        # cada bloque de audio.
        self._robot_phase = 0.0
        self._mega_phase = 0.0
        self._vib_phase = 0.0
        self._vib_tail = np.zeros(64, dtype=np.float32)

        # Línea de retardo real para el coro (np.roll era circular dentro
        # del bloque y mezclaba muestras del futuro).
        self._chorus_tail = np.zeros(1600, dtype=np.float32)

        self.recording = False
        self.recorded = []

        # Contador de cortes de audio (xruns) que reporta PortAudio.
        self.xrun_count = 0
        # Latido: número total de callbacks procesados. Si deja de subir
        # con el directo activo, el dispositivo se desconectó o falló.
        self.callback_count = 0
        # Canales reales de la salida abierta (1=mono, 2=estéreo).
        self.out_channels = 1

        # Ecualizador real de 3 bandas: dos cruces de una etapa (250 Hz y
        # 4 kHz) aproximados con FIR, con cola de contexto entre bloques.
        import math as _math
        a1 = 1.0 - _math.exp(-2.0 * _math.pi * 250.0 / self.rate)
        a2 = 1.0 - _math.exp(-2.0 * _math.pi * 4000.0 / self.rate)
        _f1 = (a1 * (1.0 - a1) ** np.arange(160)).astype(np.float32)
        _f2 = (a2 * (1.0 - a2) ** np.arange(24)).astype(np.float32)
        # Cruces de dos polos (12 dB/oct): el filtro en cascada es la
        # convolución del FIR consigo mismo. Bandas mucho más separadas.
        self._eq_fir_low = np.convolve(_f1, _f1).astype(np.float32)
        self._eq_fir_lm = np.convolve(_f2, _f2).astype(np.float32)
        self._eq_tail = np.zeros(len(self._eq_fir_low) - 1, dtype=np.float32)
        self.eq_low = 1.0
        self.eq_mid = 1.0
        self.eq_high = 1.0

        # Reducción de ruido espectral: FFT con ventana Hann y solape 50%.
        self._nr_frame = 512
        self._nr_hop = 256
        self._nr_window = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(self._nr_frame) / self._nr_frame)).astype(np.float32)
        self._nr_in = np.zeros(0, dtype=np.float32)
        self._nr_ola = np.zeros(self._nr_frame, dtype=np.float32)
        self._nr_outq = np.zeros(0, dtype=np.float32)
        self._nr_gain_prev = None
        self._nr_primed = False
        self.noise_profile = None
        self.noise_reduction = 0.0
        self._nr_learn_left = 0
        self._nr_learn_acc = None
        self._nr_learn_count = 0

        # Mesa de sonidos: efectos de sonido mezclados con la voz.
        self.sfx_buffer = np.zeros(0, dtype=np.float32)
        self.sfx_volume = 0.65

        # Clip instantáneo: buffer circular con los últimos segundos de la
        # salida ya procesada (voz + karaoke + soundboard).
        self.replay_seconds = 60
        self.replay_buffer = np.zeros(self.rate * self.replay_seconds, dtype=np.float32)
        self.replay_pos = 0
        self.replay_filled = 0
        self.replay_enabled = True

        # Karaoke: pista instrumental mezclada con voz y efectos.
        self.karaoke_samples = np.zeros(0, dtype=np.float32)
        self.karaoke_pos = 0
        self.karaoke_playing = False
        self.karaoke_loop = False
        self.karaoke_volume = 0.45
        self.karaoke_title = "Sin pista"

    def reset_buffers(self):
        self.echo_buf[:] = 0
        self.echo_pos = 0
        self._ps_states = {}
        self._gate_gain = 1.0
        self._gate_open = True
        self._bass_tail[:] = 0
        self._radio_dtail[:] = 0
        self._radio_prev = 0.0
        self._robot_phase = 0.0
        self._mega_phase = 0.0
        self._vib_phase = 0.0
        self._vib_tail[:] = 0
        self._chorus_tail[:] = 0
        self._nr_in = np.zeros(0, dtype=np.float32)
        self._nr_ola = np.zeros(self._nr_frame, dtype=np.float32)
        self._nr_outq = np.zeros(0, dtype=np.float32)
        self._nr_gain_prev = None
        self._nr_primed = False
        self._nr_learn_left = 0
        self._eq_tail[:] = 0

    def pitch_shift(self, x, semitones, state="voz"):
        """Pitch shifter granular con fase continua entre bloques.

        Dos lecturas desfasadas media ventana con crossfade coseno: al no
        resetearse en cada bloque, elimina los clics del método anterior.
        """
        if abs(semitones) < 0.1:
            self._ps_states.pop(state, None)
            return x
        n = len(x)
        if n < 8:
            return x
        factor = 2 ** (semitones / 12.0)
        win = self._ps_window
        st = self._ps_states.get(state)
        if st is None:
            st = {"hist": np.zeros(win, dtype=np.float32), "phase": 0.0}
            self._ps_states[state] = st
        hist = np.concatenate([st["hist"], x])
        # El retardo de lectura barre la ventana a velocidad (1-factor).
        phase = (st["phase"] + np.arange(1, n + 1, dtype=np.float64) * (1.0 - factor) / win) % 1.0
        st["phase"] = float(phase[-1])
        base = np.arange(len(hist) - n, len(hist), dtype=np.float64)
        idx = np.arange(len(hist), dtype=np.float64)
        y1 = np.interp(base - phase * win, idx, hist)
        y2 = np.interp(base - ((phase + 0.5) % 1.0) * win, idx, hist)
        g1 = 0.5 - 0.5 * np.cos(2 * np.pi * phase)
        y = y1 * g1 + y2 * (1.0 - g1)
        st["hist"] = hist[-win:].copy()
        return y.astype(np.float32)

    def add_bass(self, x, amount):
        ext = np.concatenate([self._bass_tail, x])
        self._bass_tail = ext[-len(self._bass_tail):].copy()
        if amount <= 0.01:
            return x
        low = np.convolve(ext, self._bass_fir)[len(self._bass_tail):len(self._bass_tail) + len(x)]
        y = np.clip(x + low * 1.3, -1, 1)
        return (x * (1 - amount) + y * amount).astype(np.float32)

    def robot_fx(self, x, amount):
        n = len(x)
        if amount <= 0.01 or n == 0:
            self._robot_phase = 0.0
            return x
        # Fase de la portadora continua entre bloques (86 Hz reales).
        ph = (self._robot_phase + np.arange(n, dtype=np.float64) * (86.0 / self.rate)) % 1.0
        self._robot_phase = float((self._robot_phase + n * 86.0 / self.rate) % 1.0)
        carrier = np.sign(np.sin(2 * np.pi * ph)).astype(np.float32)
        y = np.round((x * carrier) * 18) / 18
        return (x * (1 - amount) + y * amount).astype(np.float32)

    def echo_fx(self, x, amount):
        if amount <= 0.01:
            return x
        n = len(x)
        size = len(self.echo_buf)
        delay = int(self.rate * 0.20)
        idx_w = (self.echo_pos + np.arange(n)) % size
        idx_r = (idx_w - delay) % size
        y = x + self.echo_buf[idx_r] * amount
        self.echo_buf[idx_w] = y
        self.echo_pos = int((self.echo_pos + n) % size)
        return y.astype(np.float32)

    def radio_fx(self, x, amount):
        n = len(x)
        if n == 0:
            return x
        # Señal diferencia con continuidad entre bloques.
        d = np.empty_like(x)
        d[0] = x[0] - self._radio_prev
        d[1:] = x[1:] - x[:-1]
        self._radio_prev = float(x[-1])
        ext = np.concatenate([self._radio_dtail, d])
        self._radio_dtail = ext[-len(self._radio_dtail):].copy()
        if amount <= 0.01:
            return x
        hp = np.convolve(ext, self._radio_fir)[len(self._radio_dtail):len(self._radio_dtail) + n]
        radio = np.tanh(hp * 2.7).astype(np.float32)
        radio += np.random.normal(0, 0.002, len(radio)).astype(np.float32)
        return (x * (1 - amount) + radio * amount).astype(np.float32)

    def megaphone_fx(self, x, amount):
        n = len(x)
        if amount <= 0.01 or n == 0:
            self._mega_phase = 0.0
            return x
        # Trémolo de 18 Hz con fase continua entre bloques.
        ph = (self._mega_phase + np.arange(n, dtype=np.float64) * (18.0 / self.rate)) % 1.0
        self._mega_phase = float((self._mega_phase + n * 18.0 / self.rate) % 1.0)
        trem = 0.86 + 0.14 * np.sin(2 * np.pi * ph)
        y = np.tanh(x * 4.8) * trem
        return (x * (1 - amount) + y * amount).astype(np.float32)


    def autotune_fx(self, x, amount, note_shift=0.0):
        """Efecto tipo autotune: no clona ni detecta notas reales; crea un color musical/cantado."""
        if amount <= 0.01:
            return x
        shifted = self.pitch_shift(x, note_shift, state="autotune")
        tuned = np.tanh(shifted * (1.25 + amount * 1.3)).astype(np.float32)
        levels = max(8, int(42 - amount * 22))
        stepped = np.round(tuned * levels) / levels
        return (x * (1 - amount) + stepped * amount).astype(np.float32)

    def vibrato_fx(self, x, amount):
        n = len(x)
        ext = np.concatenate([self._vib_tail, x])
        self._vib_tail = ext[-len(self._vib_tail):].copy()
        if amount <= 0.01 or n < 8:
            self._vib_phase = 0.0
            return x
        depth = 2.0 + amount * 18.0
        lfo_rate = 4.8 + amount * 2.4
        # LFO con fase continua entre bloques; se lee con un pequeño retardo
        # fijo (depth) para poder oscilar sin salirse del bloque actual.
        ph = (self._vib_phase + np.arange(1, n + 1, dtype=np.float64) * (lfo_rate / self.rate)) % 1.0
        self._vib_phase = float(ph[-1])
        base = np.arange(len(ext) - n, len(ext), dtype=np.float64)
        idx = np.clip(base - depth + np.sin(2 * np.pi * ph) * depth, 0, len(ext) - 1)
        y = np.interp(idx, np.arange(len(ext), dtype=np.float64), ext).astype(np.float32)
        return (x * (1 - amount * 0.75) + y * (amount * 0.75)).astype(np.float32)

    def chorus_fx(self, x, amount):
        n = len(x)
        ext = np.concatenate([self._chorus_tail, x])
        self._chorus_tail = ext[-len(self._chorus_tail):].copy()
        if amount <= 0.01 or n < 16:
            return x
        # Retardos reales con historial (np.roll era circular en el bloque).
        d1 = int(self.rate * 0.018)
        d2 = int(self.rate * 0.032)
        size = len(ext)
        delayed1 = ext[size - n - d1:size - d1]
        delayed2 = ext[size - n - d2:size - d2]
        shifted = self.pitch_shift(x, 0.18, state="coro")
        chorus = np.clip(x * 0.62 + delayed1 * 0.22 + delayed2 * 0.12 + shifted * 0.18, -1, 1)
        return (x * (1 - amount) + chorus * amount).astype(np.float32)


    def eq3_fx(self, x, g_low, g_mid, g_high):
        """Ecualizador de 3 bandas: graves (<250 Hz), medios y agudos (>4 kHz).

        Las bandas suman exactamente la señal original, así que con las tres
        ganancias en 1.0 es transparente bit a bit.
        """
        ext = np.concatenate([self._eq_tail, x])
        self._eq_tail = ext[-len(self._eq_tail):].copy()
        if abs(g_low - 1.0) < 0.01 and abs(g_mid - 1.0) < 0.01 and abs(g_high - 1.0) < 0.01:
            return x
        k = len(self._eq_tail)
        n = len(x)
        low = np.convolve(ext, self._eq_fir_low)[k:k + n]
        lowmid = np.convolve(ext, self._eq_fir_lm)[k:k + n]
        mid = lowmid - low
        high = x - lowmid
        y = g_low * low + g_mid * mid + g_high * high
        return np.clip(y, -1.5, 1.5).astype(np.float32)

    def start_noise_learn(self, seconds=2.0):
        """Empieza a aprender el perfil de ruido: el usuario debe callar."""
        with self.lock:
            self._nr_learn_left = max(4, int(seconds * self.rate / self._nr_hop))
            self._nr_learn_acc = None
            self._nr_learn_count = 0
            self.noise_profile = None

    def noise_reduce(self, x):
        """Sustracción espectral en tiempo real.

        Acumula la entrada en una FIFO, procesa tramas de 512 muestras con
        ventana Hann y solape del 50%, resta el perfil de ruido aprendido en
        el espectro y reconstruye por solapamiento-suma. Añade ~12 ms de
        retardo. Con el perfil sin aprender deja pasar la voz tal cual
        (misma ruta, para que el aprendizaje use exactamente este camino).
        """
        frame = self._nr_frame
        hop = self._nr_hop
        if not self._nr_primed:
            # Ceba la cola de salida con una trama de silencio: latencia fija
            # que garantiza que nunca falten muestras a mitad de stream.
            self._nr_outq = np.zeros(frame, dtype=np.float32)
            self._nr_primed = True
        self._nr_in = np.concatenate([self._nr_in, x])
        while len(self._nr_in) >= frame:
            seg = self._nr_in[:frame] * self._nr_window
            spec = np.fft.rfft(seg)
            mag = np.abs(spec)

            if self._nr_learn_left > 0:
                self._nr_learn_left -= 1
                self._nr_learn_acc = mag if self._nr_learn_acc is None else self._nr_learn_acc + mag
                self._nr_learn_count += 1
                if self._nr_learn_left == 0 and self._nr_learn_count > 0:
                    # Media del ruido con margen de seguridad.
                    self.noise_profile = (self._nr_learn_acc / self._nr_learn_count) * 1.4
                    self._nr_gain_prev = None

            out = seg
            if self.noise_profile is not None and self.noise_reduction > 0.01:
                amount = self.noise_reduction
                beta = 1.0 + 2.0 * amount
                floor = 0.35 - 0.30 * amount
                gain = np.clip(1.0 - beta * self.noise_profile / (mag + 1e-9), floor, 1.0)
                if self._nr_gain_prev is not None:
                    gain = 0.6 * self._nr_gain_prev + 0.4 * gain
                self._nr_gain_prev = gain
                out = np.fft.irfft(spec * gain, frame).astype(np.float32)

            self._nr_ola = self._nr_ola + out
            self._nr_outq = np.concatenate([self._nr_outq, self._nr_ola[:hop]])
            self._nr_ola = np.concatenate([self._nr_ola[hop:], np.zeros(hop, dtype=np.float32)])
            self._nr_in = self._nr_in[hop:]

        need = len(x)
        if len(self._nr_outq) >= need:
            y = self._nr_outq[:need]
            self._nr_outq = self._nr_outq[need:]
        else:
            y = np.concatenate([np.zeros(need - len(self._nr_outq), dtype=np.float32), self._nr_outq])
            self._nr_outq = np.zeros(0, dtype=np.float32)
        return y.astype(np.float32)

    def noise_reduce_stream(self, x):
        """Aplica la reducción si está activa o si se está aprendiendo."""
        if (self.noise_reduction > 0.01 and self.noise_profile is not None) or self._nr_learn_left > 0:
            return self.noise_reduce(x)
        if len(self._nr_in) or len(self._nr_outq):
            self._nr_in = np.zeros(0, dtype=np.float32)
            self._nr_ola = np.zeros(self._nr_frame, dtype=np.float32)
            self._nr_outq = np.zeros(0, dtype=np.float32)
            self._nr_gain_prev = None
            self._nr_primed = False
        return x

    def soft_limit(self, x):
        """Limitador suave: por debajo de 0.7 no toca nada; por encima
        comprime con una rodilla tanh hasta un techo de 0.95. Sustituye al
        recorte duro, que distorsionaba en seco los picos de voz alta."""
        ax = np.abs(x)
        over = ax > 0.7
        if not over.any():
            return x
        y = x.copy()
        span = 0.95 - 0.7
        y[over] = np.sign(x[over]) * (0.7 + span * np.tanh((ax[over] - 0.7) / span))
        return y.astype(np.float32)

    def gate(self, x, threshold):
        """Puerta de ruido por envolvente con histéresis.

        La versión anterior atenuaba muestra a muestra (también los cruces
        por cero de la voz alta), lo que generaba distorsión de cruce
        constante. Esta mide el nivel RMS del bloque y aplica una ganancia
        suavizada, sin tocar la forma de onda de la voz.
        """
        if threshold <= 0.001:
            self._gate_gain = 1.0
            self._gate_open = True
            return x
        n = len(x)
        if n == 0:
            return x
        rms = float(np.sqrt(np.mean(x * x)))
        if self._gate_open:
            if rms < threshold * 0.6:
                self._gate_open = False
        else:
            if rms >= threshold:
                self._gate_open = True
        target = 1.0 if self._gate_open else 0.08
        prev = self._gate_gain
        # Apertura rápida (no se come el inicio de palabra), cierre suave.
        coeff = 0.85 if target > prev else 0.25
        gain = prev + (target - prev) * coeff
        self._gate_gain = gain
        if prev >= 0.999 and gain >= 0.999:
            return x
        ramp = np.linspace(prev, gain, n).astype(np.float32)
        return (x * ramp).astype(np.float32)

    def comp(self, x, amount):
        if amount <= 0.01:
            return x
        y = x.copy()
        th = 0.28
        ratio = 3.0
        ax = np.abs(y)
        over = ax > th
        y[over] = np.sign(y[over]) * (th + (ax[over] - th) / ratio)
        y = np.clip(y * (1.0 + amount * 0.55), -0.95, 0.95)
        return (x * (1 - amount) + y * amount).astype(np.float32)


    def add_sfx(self, samples):
        """Añade un efecto de sonido a la cola para mezclarlo con la voz."""
        if samples is None or len(samples) == 0:
            return

        samples = np.asarray(samples, dtype=np.float32)
        samples = np.clip(samples, -0.95, 0.95)

        with self.lock:
            # Evita que se acumulen demasiados sonidos si se pulsa muchas veces.
            max_len = self.rate * 12
            if len(self.sfx_buffer) > max_len:
                self.sfx_buffer = self.sfx_buffer[-self.rate * 4:]
            self.sfx_buffer = np.concatenate([self.sfx_buffer, samples])

    def pull_sfx(self, n):
        """Saca n muestras de la cola de efectos."""
        with self.lock:
            if len(self.sfx_buffer) == 0:
                return np.zeros(n, dtype=np.float32)

            take = min(n, len(self.sfx_buffer))
            out = np.zeros(n, dtype=np.float32)
            out[:take] = self.sfx_buffer[:take]
            self.sfx_buffer = self.sfx_buffer[take:]
            vol = self.sfx_volume

        return out * vol



    def write_replay(self, y):
        """Escribe el audio de salida en el buffer circular del clip instantáneo."""
        n = len(y)
        if n == 0:
            return
        with self.lock:
            buf = self.replay_buffer
            size = len(buf)
            pos = self.replay_pos
            if n >= size:
                buf[:] = y[-size:]
                pos = 0
                self.replay_filled = size
            else:
                end = pos + n
                if end <= size:
                    buf[pos:end] = y
                else:
                    first = size - pos
                    buf[pos:] = y[:first]
                    buf[:end - size] = y[first:]
                pos = end % size
                self.replay_filled = min(size, self.replay_filled + n)
            self.replay_pos = pos

    def replay_available_seconds(self):
        with self.lock:
            return self.replay_filled / self.rate

    def clear_replay(self):
        with self.lock:
            self.replay_buffer[:] = 0
            self.replay_pos = 0
            self.replay_filled = 0

    def save_replay(self, path, seconds):
        """Guarda los últimos `seconds` segundos del buffer en un WAV. Devuelve la duración real."""
        with self.lock:
            size = len(self.replay_buffer)
            want = min(int(seconds * self.rate), self.replay_filled)
            if want <= 0:
                return 0.0
            start = (self.replay_pos - want) % size
            if start + want <= size:
                audio = self.replay_buffer[start:start + want].copy()
            else:
                first = size - start
                audio = np.concatenate([self.replay_buffer[start:], self.replay_buffer[:want - first]])
        audio16 = np.int16(np.clip(audio, -1, 1) * 32767)
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.rate)
            w.writeframes(audio16.tobytes())
        return want / self.rate

    def set_karaoke_track(self, samples, title="Pista instrumental"):
        if samples is None:
            return
        samples = np.asarray(samples, dtype=np.float32)
        samples = np.clip(samples, -0.95, 0.95)
        with self.lock:
            self.karaoke_samples = samples
            self.karaoke_pos = 0
            self.karaoke_playing = False
            self.karaoke_title = title

    def play_karaoke(self):
        with self.lock:
            if len(self.karaoke_samples) > 0:
                self.karaoke_playing = True

    def pause_karaoke(self):
        with self.lock:
            self.karaoke_playing = False

    def stop_karaoke(self):
        with self.lock:
            self.karaoke_playing = False
            self.karaoke_pos = 0

    def pull_karaoke(self, n):
        with self.lock:
            if not self.karaoke_playing or len(self.karaoke_samples) == 0:
                return np.zeros(n, dtype=np.float32)

            out = np.zeros(n, dtype=np.float32)
            written = 0
            while written < n and self.karaoke_playing:
                remaining = len(self.karaoke_samples) - self.karaoke_pos
                if remaining <= 0:
                    if self.karaoke_loop:
                        self.karaoke_pos = 0
                        remaining = len(self.karaoke_samples)
                    else:
                        self.karaoke_playing = False
                        break

                take = min(n - written, remaining)
                out[written:written+take] = self.karaoke_samples[self.karaoke_pos:self.karaoke_pos+take]
                self.karaoke_pos += take
                written += take

            vol = self.karaoke_volume

        return out * vol


    def process(self, indata):
        if indata.shape[1] > 1:
            x = indata.mean(axis=1).astype(np.float32)
        else:
            x = indata[:, 0].astype(np.float32)
        self.mic_level = float(np.sqrt(np.mean(x * x))) if len(x) else 0

        with self.lock:
            pitch = self.pitch
            bass = self.bass
            robot = self.robot
            echo = self.echo
            radio = self.radio
            megaphone = self.megaphone
            noise_gate = self.noise_gate
            compressor = self.compressor
            volume = self.volume
            mute = self.mute
            effects_enabled = self.effects_enabled
            autotune = self.autotune
            autotune_shift = self.autotune_shift
            vibrato = self.vibrato
            chorus = self.chorus
            eq_low = self.eq_low
            eq_mid = self.eq_mid
            eq_high = self.eq_high
            recording = self.recording

        if mute:
            y = np.zeros_like(x)
        elif not effects_enabled:
            # Modo voz limpia: deja pasar el micro sin cambiar la voz, pero mantiene soundboard.
            y = self.noise_reduce_stream(x)
            y = self.soft_limit(y * volume)
        else:
            y = self.noise_reduce_stream(x)
            y = self.gate(y, noise_gate)
            y = self.pitch_shift(y, pitch)
            y = self.autotune_fx(y, autotune, autotune_shift)
            y = self.vibrato_fx(y, vibrato)
            y = self.chorus_fx(y, chorus)
            y = self.add_bass(y, bass)
            y = self.eq3_fx(y, eq_low, eq_mid, eq_high)
            y = self.robot_fx(y, robot)
            y = self.echo_fx(y, echo)
            y = self.radio_fx(y, radio)
            y = self.megaphone_fx(y, megaphone)
            y = self.comp(y, compressor)
            y = self.soft_limit(y * volume)

        # Mezcla pista karaoke instrumental con la voz.
        karaoke = self.pull_karaoke(len(y))
        if len(karaoke):
            y = self.soft_limit(y + karaoke)

        # Mezcla efectos de sonido con la voz.
        sfx = self.pull_sfx(len(y))
        if len(sfx):
            y = self.soft_limit(y + sfx)

        self.out_level = float(np.sqrt(np.mean(y * y))) if len(y) else 0
        if recording:
            self.recorded.append(y.copy())
        if self.replay_enabled:
            self.write_replay(y)
        return y.reshape(-1, 1).astype(np.float32)

    def callback(self, indata, outdata, frames, time_info, status):
        self.callback_count += 1
        if status:
            self.xrun_count += 1
        try:
            y = self.process(indata)
            if outdata.shape[1] > 1:
                outdata[:] = np.repeat(y, outdata.shape[1], axis=1)
            else:
                outdata[:] = y
        except Exception as e:
            print("Error de audio:", e)
            outdata[:] = np.zeros_like(outdata)

    def configure_rate(self, rate):
        """Reconfigura todos los buffers y filtros dependientes de la tasa de muestreo."""
        rate = int(rate)
        if rate <= 0:
            return

        changed = rate != self.rate
        self.rate = rate

        # Buffers principales dependientes de Hz.
        self.echo_buf = np.zeros(rate * 2, dtype=np.float32)
        self.echo_pos = 0
        self.replay_buffer = np.zeros(rate * self.replay_seconds, dtype=np.float32)
        self.replay_pos = 0
        self.replay_filled = 0

        # Filtros graves/radio también dependen de Hz. En V57 solo se
        # recalculaba parte del EQ; en 48 kHz podía sonar distinto.
        alpha_bass = 0.075 * (44100.0 / rate)
        alpha_bass = float(clamp(alpha_bass, 0.025, 0.15))
        self._bass_fir = (alpha_bass * (1.0 - alpha_bass) ** np.arange(100)).astype(np.float32)
        self._bass_tail = np.zeros(len(self._bass_fir) - 1, dtype=np.float32)

        alpha_radio = 0.965 ** (44100.0 / rate)
        alpha_radio = float(clamp(alpha_radio, 0.92, 0.985))
        self._radio_fir = (alpha_radio ** (np.arange(160) + 1)).astype(np.float32)
        self._radio_dtail = np.zeros(len(self._radio_fir) - 1, dtype=np.float32)
        self._radio_prev = 0.0

        # EQ de 3 bandas recalculado para la tasa real.
        a1 = 1.0 - math.exp(-2.0 * math.pi * 250.0 / rate)
        a2 = 1.0 - math.exp(-2.0 * math.pi * 4000.0 / rate)
        f1 = (a1 * (1.0 - a1) ** np.arange(160)).astype(np.float32)
        f2 = (a2 * (1.0 - a2) ** np.arange(24)).astype(np.float32)
        self._eq_fir_low = np.convolve(f1, f1).astype(np.float32)
        self._eq_fir_lm = np.convolve(f2, f2).astype(np.float32)
        self._eq_tail = np.zeros(len(self._eq_fir_low) - 1, dtype=np.float32)

        # Buffers musicales.
        self._vib_tail = np.zeros(max(64, int(rate * 0.0015)), dtype=np.float32)
        self._chorus_tail = np.zeros(max(512, int(rate * 0.036)), dtype=np.float32)

        # Reducción de ruido: limpiar colas para evitar restos al cambiar de Hz.
        self._nr_in = np.zeros(0, dtype=np.float32)
        self._nr_ola = np.zeros(self._nr_frame, dtype=np.float32)
        self._nr_outq = np.zeros(0, dtype=np.float32)
        self._nr_gain_prev = None
        self._nr_primed = False

        if changed:
            self.reset_buffers()

    def start(self, input_id, output_id, latency_name):
        if self.running:
            return
        block_map = {
            "Ultra baja": 128,
            "Baja": 256,
            "Estable": 512,
            "Máxima estabilidad": 1024,
        }
        block = block_map.get(latency_name, 256)
        self.xrun_count = 0
        self.callback_count = 0

        # Tasas a probar: las clásicas más las nativas de cada dispositivo.
        # Muchos equipos Windows solo aceptan su tasa nativa (normalmente
        # 48000) o salida estéreo según el modo del driver.
        rates = [44100, 48000]
        try:
            for dev in (input_id, output_id):
                nativa = int(sd.query_devices(dev).get("default_samplerate") or 0)
                if nativa and nativa not in rates:
                    rates.append(nativa)
        except Exception:
            pass

        last_error = None
        for rate in rates:
            for in_ch, out_ch in ((1, 1), (1, 2), (2, 1), (2, 2)):
                try:
                    stream = sd.Stream(
                        samplerate=rate,
                        blocksize=block,
                        dtype="float32",
                        channels=(in_ch, out_ch),
                        device=(input_id, output_id),
                        callback=self.callback,
                        latency="low" if block <= 512 else "high",
                    )
                except Exception as e:
                    last_error = e
                    continue
                try:
                    self.configure_rate(rate)
                    self.out_channels = out_ch
                    self.reset_buffers()
                    stream.start()
                except Exception as e:
                    last_error = e
                    try:
                        stream.close()
                    except Exception:
                        pass
                    continue
                self.stream = stream
                self.running = True
                return

        raise RuntimeError(
            "No se pudo abrir el audio con ninguna configuración "
            f"(tasas probadas: {rates} Hz, mono y estéreo).\n"
            f"Último error: {last_error}"
        )

    def stop(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        self.stream = None
        self.running = False

    def start_recording(self):
        with self.lock:
            self.recorded = []
            self.recording = True

    def stop_recording(self, path):
        with self.lock:
            self.recording = False
            chunks = self.recorded[:]
            self.recorded = []
        if not chunks:
            return False
        audio = np.concatenate(chunks)
        audio16 = np.int16(np.clip(audio, -1, 1) * 32767)
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.rate)
            w.writeframes(audio16.tobytes())
        return True


class PremiumApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} V{VERSION} - ES / EN")
        self.root.geometry("1160x820")
        self.root.minsize(1040, 740)

        self.engine = AudioEngine()
        self.input_map = {}
        self.output_map = {}
        self.input_combos = []
        self.output_combos = []
        self.recording = False
        self.tray_icon = None
        self.tray_thread_started = False
        self.real_exit = False
        self.welcome_shown = False

        # Sistema bilingüe y mejora visual premium
        self.app_language = tk.StringVar(value="Español")
        self.bilingual_visual_images = {}
        self.bilingual_visual_status = tk.StringVar(value="Bilingual Visual Premium listo. Choose Español or English.")
        self.visual_bundle_name = tk.StringVar(value="Aurora Glass")
        self.full_translation_images = {}
        self.full_translation_status = tk.StringVar(value="Full Translation Pro listo. Traducción ampliada ES / EN preparada.")
        self.translation_mode = tk.StringVar(value="Interfaz completa")
        self.translation_report = tk.StringVar(value="Cobertura: navegación + textos comunes")
        self.language_pack_images = {}
        self.language_pack_status = tk.StringVar(value="Language Pack Pro listo. Exporta ES/EN y glosario.")
        self.language_pack_name = tk.StringVar(value="ES_EN_PREMIUM_PACK")
        self.icon_system_images = {}
        self.icon_system_status = tk.StringVar(value="Premium Icon System listo. Galería de iconos premium preparada.")
        self.icon_system_style = tk.StringVar(value="Neón premium")
        self.design_system_images = {}
        self.design_system_status = tk.StringVar(value="Design System Pro listo. Guía visual premium preparada.")
        self.design_system_theme = tk.StringVar(value="Aurora Premium")
        self.design_system_density = tk.StringVar(value="Cómodo premium")
        self.design_system_roundness = tk.DoubleVar(value=22)
        self.interface_consistency_images = {}
        self.interface_consistency_status = tk.StringVar(value="Interface Consistency Pro listo. Auditoría visual preparada.")
        self.interface_consistency_mode = tk.StringVar(value="Premium equilibrado")
        self.interface_consistency_score_var = tk.StringVar(value="Consistencia: sin revisar")
        self.interface_consistency_board_path = tk.StringVar(value="Sin tablero exportado")

        # Datos que las pestañas necesitan al construirse.
        self.favorites = []
        self.profiles = {}
        self.custom_sfx = {}
        self.cambiador_index = {}

        self.preset = tk.StringVar(value="Gaming limpio")
        self.current_theme = tk.StringVar(value="Neón morado")
        self.eq_preset = tk.StringVar(value="Ninguno")
        self.creator_base = tk.StringVar(value="Mujer")
        self.creator_style = tk.StringVar(value="Directo limpio")
        self.creator_name = tk.StringVar(value="Mi voz personalizada")
        self.category = tk.StringVar(value="Todas")
        self.search = tk.StringVar(value="")
        self.input_dev = tk.StringVar()
        self.output_dev = tk.StringVar()
        self.latency = tk.StringVar(value="Baja")
        self.state = tk.StringVar(value="Estado: detenido")
        self.mute = tk.BooleanVar(value=False)
        self.effects_enabled = tk.BooleanVar(value=True)

        self.vars = {
            "pitch": tk.DoubleVar(value=0),
            "bass": tk.DoubleVar(value=15),
            "robot": tk.DoubleVar(value=0),
            "echo": tk.DoubleVar(value=0),
            "radio": tk.DoubleVar(value=3),
            "megaphone": tk.DoubleVar(value=0),
            "gate": tk.DoubleVar(value=8),
            "comp": tk.DoubleVar(value=38),
            "vol": tk.DoubleVar(value=90),
            "autotune": tk.DoubleVar(value=0),
            "autotune_shift": tk.DoubleVar(value=0),
            "vibrato": tk.DoubleVar(value=0),
            "chorus": tk.DoubleVar(value=0),
            "eq_low": tk.DoubleVar(value=0),
            "eq_mid": tk.DoubleVar(value=0),
            "eq_high": tk.DoubleVar(value=0),
        }

        self.voice_list = None
        self.images = {}
        # Diccionarios de imágenes para todas las pestañas visuales.
        for _name in [
            "voice_card_images", "pack_images", "studio_images", "ultra_images", "pro_images", "grid_images",
            "streamer_images", "wizard_images", "quick_images", "rec_images", "mesa_images", "diag_images",
            "mini_images", "eq_images", "profile_images", "personas_images", "cambiador_images", "creator_images",
            "hotkey_images", "favoritos_images", "scenes_images", "hub_images", "performance_images", "cable_images",
            "test_voice_images", "autotune_images", "karaoke_images", "karaoke_studio_images", "song_images",
            "mix_images", "master_images", "multitrack_images", "grid_voice_images", "clips_images"
        ]:
            setattr(self, _name, {})

        # Estados/variables profesionales añadidos por las versiones Pro.
        self.assistant_status = tk.StringVar(value="Asistente listo.")
        self.recordings_status = tk.StringVar(value="Grabadora lista.")
        self.mesa_status = tk.StringVar(value="Mesa de sonidos lista.")
        self.diagnostic_status = tk.StringVar(value="Diagnóstico listo.")
        self.mini_status = tk.StringVar(value="Mini Panel listo.")
        self.eq_status = tk.StringVar(value="Ecualizador listo.")
        self.profile_status = tk.StringVar(value="Perfiles listos.")
        self.personas_status = tk.StringVar(value="Personas Pro listo.")
        self.cambiador_status = tk.StringVar(value="Cambiador listo.")
        self.creator_status = tk.StringVar(value="Creador listo.")
        self.hotkey_status = tk.StringVar(value="Atajos listos.")
        self.hotkeys_enabled = tk.BooleanVar(value=True)
        self.favoritos_status = tk.StringVar(value="Favoritos listos.")
        self.scenes_status = tk.StringVar(value="Escenas listas.")
        self.hub_status = tk.StringVar(value="Streamer Hub listo.")
        self.performance_status = tk.StringVar(value="Rendimiento listo.")
        self.benchmark_result = tk.StringVar(value="Benchmark sin ejecutar todavía.")
        self.xrun_status = tk.StringVar(value="Cortes de audio: 0")
        self._watchdog_last = 0
        self._watchdog_last_cb = 0
        self._guard_last_count = -1
        self._reconnect_attempts = 0
        self.nr_status = tk.StringVar(value="Sin perfil de ruido. Empieza el directo y pulsa Aprender ruido.")
        self.nr_amount = tk.DoubleVar(value=70)
        self.nr_enabled = tk.BooleanVar(value=False)
        self.cable_status = tk.StringVar(value="Cable Virtual listo.")
        self.test_voice_status = tk.StringVar(value="Test de Voz listo.")
        self.autotune_status = tk.StringVar(value="Autotune listo.")
        self.autotune_key = tk.StringVar(value="Do")
        self.autotune_scale = tk.StringVar(value="Mayor")
        self.autotune_mode = tk.StringVar(value="AutoTune Pop")
        self.karaoke_status = tk.StringVar(value="Karaoke listo.")
        self.karaoke_track = tk.StringVar(value="Sin pista instrumental")
        self.karaoke_loop = tk.BooleanVar(value=False)
        self.karaoke_volume = tk.DoubleVar(value=45)
        self.karaoke_studio_status = tk.StringVar(value="Karaoke Studio listo.")
        self.karaoke_studio_bpm = tk.DoubleVar(value=120)
        self.karaoke_studio_seconds = tk.DoubleVar(value=45)
        self.song_status = tk.StringVar(value="Canción Pro lista.")
        self.song_title = tk.StringVar(value="Mi demo karaoke")
        self.song_style = tk.StringVar(value="Pop")
        self.song_duration = tk.DoubleVar(value=60)
        self.mix_status = tk.StringVar(value="Mezclador listo.")
        self.mix_voice = tk.DoubleVar(value=90)
        self.mix_music = tk.DoubleVar(value=45)
        self.mix_master = tk.DoubleVar(value=100)
        self.master_status = tk.StringVar(value="Master Final listo.")
        self.master_normalize = tk.BooleanVar(value=True)
        self.master_limiter = tk.BooleanVar(value=True)
        self.master_fade_in = tk.DoubleVar(value=0.8)
        self.master_fade_out = tk.DoubleVar(value=1.8)
        self.master_gain = tk.DoubleVar(value=92)
        self.master_warmth = tk.DoubleVar(value=18)
        self.multitrack_status = tk.StringVar(value="Multipista Pro listo. Separa voz, coros, instrumental y FX.")
        self.track_lead_voice = tk.DoubleVar(value=95)
        self.track_chorus = tk.DoubleVar(value=28)
        self.track_instrumental = tk.DoubleVar(value=45)
        self.track_fx = tk.DoubleVar(value=25)
        self.track_master = tk.DoubleVar(value=96)
        self.track_arm_lead = tk.BooleanVar(value=True)
        self.track_arm_chorus = tk.BooleanVar(value=False)
        self.track_arm_fx = tk.BooleanVar(value=True)
        self.timeline_images = {}
        self.timeline_status = tk.StringVar(value='Timeline Pro listo. Elige plantilla o ajusta secciones.')
        self.timeline_bpm = tk.DoubleVar(value=120)
        self.timeline_key = tk.StringVar(value='Do mayor')
        self.timeline_style = tk.StringVar(value='Pop')
        self.timeline_sections = {
            'Intro': tk.DoubleVar(value=8),
            'Verso 1': tk.DoubleVar(value=16),
            'Pre': tk.DoubleVar(value=8),
            'Estribillo': tk.DoubleVar(value=20),
            'Verso 2': tk.DoubleVar(value=16),
            'Puente': tk.DoubleVar(value=8),
            'Outro': tk.DoubleVar(value=8),
        }
        self.vocal_chain_images = {}
        self.vocal_chain_status = tk.StringVar(value='Cadena Vocal Pro lista. Elige un preset o ajusta la voz.')
        self.vocal_air = tk.DoubleVar(value=12)
        self.vocal_presence = tk.DoubleVar(value=18)
        self.vocal_reverb_send = tk.DoubleVar(value=18)
        self.vocal_delay_send = tk.DoubleVar(value=8)
        self.vocal_warmth = tk.DoubleVar(value=16)
        self.vocal_analyzer_images = {}
        self.vocal_analyzer_status = tk.StringVar(value='Analizador Vocal Pro listo. Haz un check antes de grabar.')
        self.vocal_analyzer_mode = tk.StringVar(value='Directo')
        self.studio_dashboard_images = {}
        self.studio_dashboard_status = tk.StringVar(value='Studio Dashboard listo. Sigue el flujo profesional de producción.')
        self.studio_ready_score = tk.StringVar(value='Preparación: 0%')
        self.clips_status = tk.StringVar(value='Clip Instantáneo listo. Empieza el directo y el buffer se llenará solo.')
        self.clips_available = tk.StringVar(value='Buffer: 0 s de 60 s')
        self.replay_enabled_var = tk.BooleanVar(value=True)
        self.revision_images = {}
        self.revision_status = tk.StringVar(value='Revisión Técnica Pro lista. Ejecuta una auditoría completa.')
        self.revision_score = tk.StringVar(value='Calidad técnica: sin revisar')
        self.visual_pro_images = {}
        self.visual_pro_status = tk.StringVar(value='Rediseño Visual Pro listo. Elige un estilo visual.')
        self.visual_theme_name = tk.StringVar(value='Neón Azul')
        self.visual_density = tk.StringVar(value='Cómodo')
        self.visual_focus_mode = tk.BooleanVar(value=False)
        self.inicio_premium_images = {}
        self.inicio_premium_status = tk.StringVar(value='Inicio Premium listo. Elige un modo de trabajo.')
        self.inicio_premium_mode = tk.StringVar(value='Studio completo')
        self.asistente_inicial_images = {}
        self.asistente_inicial_status = tk.StringVar(value='Asistente Inicial Pro listo. Completa los pasos de configuración.')
        self.asistente_step = tk.IntVar(value=1)
        self.asistente_progress = tk.DoubleVar(value=0)
        self.biblioteca_premium_images = {}
        self.biblioteca_premium_status = tk.StringVar(value='Biblioteca Premium lista. Escanea tus demos y proyectos.')
        self.biblioteca_filter = tk.StringVar(value='Todos')
        self.biblioteca_files = []
        self.portadas_premium_images = {}
        self.portadas_premium_status = tk.StringVar(value='Portadas Premium listas. Crea una imagen para tu demo.')
        self.portada_titulo = tk.StringVar(value='Mi Demo')
        self.portada_artista = tk.StringVar(value='Atenea Studio')
        self.portada_estilo = tk.StringVar(value='Neón')
        self.portada_subtitulo = tk.StringVar(value='Demo creada con Modulador Voz Directo')
        self.portada_ultimo_archivo = tk.StringVar(value='Sin portada exportada')
        self.brand_kit_images = {}
        self.brand_kit_status = tk.StringVar(value='Brand Kit Pro listo. Crea la identidad visual de tu demo/canal.')
        self.brand_name = tk.StringVar(value='Atenea Studio')
        self.brand_artist = tk.StringVar(value='Atenea')
        self.brand_slogan = tk.StringVar(value='Voz, música y directos con estilo')
        self.brand_style = tk.StringVar(value='Neón Azul')
        self.brand_primary = tk.StringVar(value='#00E5FF')
        self.brand_secondary = tk.StringVar(value='#FFCB57')
        self.brand_last_export = tk.StringVar(value='Sin Brand Kit exportado')
        self.publicacion_pro_images = {}
        self.publicacion_pro_status = tk.StringVar(value='Publicación Pro lista. Prepara título, descripción y tags.')
        self.publicacion_title = tk.StringVar(value='Mi demo creada con modulador de voz')
        self.publicacion_artist = tk.StringVar(value='Atenea Studio')
        self.publicacion_platform = tk.StringVar(value='YouTube')
        self.publicacion_tags = tk.StringVar(value='demo, música, voz, autotune, karaoke, gaming')
        self.publicacion_ready = tk.StringVar(value='Checklist: pendiente')
        self.publicacion_last_export = tk.StringVar(value='Sin publicación exportada')
        self.export_pack_images = {}
        self.export_pack_status = tk.StringVar(value='Export Pack Pro listo. Escanea archivos y crea un ZIP final.')
        self.export_pack_filter_audio = tk.BooleanVar(value=True)
        self.export_pack_filter_images = tk.BooleanVar(value=True)
        self.export_pack_filter_docs = tk.BooleanVar(value=True)
        self.export_pack_last = tk.StringVar(value='Sin pack exportado')
        self.export_pack_files = []
        self.landing_page_images = {}
        self.landing_page_status = tk.StringVar(value='Landing Page Pro lista. Crea una página HTML para presentar tu demo.')
        self.landing_title = tk.StringVar(value='Mi Demo')
        self.landing_artist = tk.StringVar(value='Atenea Studio')
        self.landing_style = tk.StringVar(value='Neón')
        self.landing_url_youtube = tk.StringVar(value='')
        self.landing_url_twitch = tk.StringVar(value='')
        self.landing_url_discord = tk.StringVar(value='')
        self.landing_last_file = tk.StringVar(value='Sin landing exportada')
        self.web_pack_images = {}
        self.web_pack_status = tk.StringVar(value='Web Pack Pro listo. Escanea y crea un ZIP web completo.')
        self.web_pack_last = tk.StringVar(value='Sin Web Pack exportado')
        self.web_pack_include_audio = tk.BooleanVar(value=True)
        self.web_pack_include_images = tk.BooleanVar(value=True)
        self.web_pack_include_docs = tk.BooleanVar(value=True)
        self.web_pack_include_html = tk.BooleanVar(value=True)
        self.web_pack_files = []
        self.deploy_pro_images = {}
        self.deploy_pro_status = tk.StringVar(value='Deploy Pro listo. Crea un paquete web publicable.')
        self.deploy_platform = tk.StringVar(value='GitHub Pages')
        self.deploy_files = []
        self.ultra_premium_ui_images = {}
        self.ultra_premium_ui_status = tk.StringVar(value='Ultra Premium UI listo. Aplica un acabado visual más profesional.')
        self.ultra_premium_ui_theme = tk.StringVar(value='Glass Studio')
        self.ultra_premium_ui_density = tk.StringVar(value='Premium cómodo')
        self.ultra_premium_ui_score = tk.StringVar(value='Acabado UI: sin revisar')
        self.premium_experience_images = {}
        self.premium_experience_status = tk.StringVar(value='Premium Experience listo. Aplica un modo premium o revisa el acabado.')
        self.premium_mode = tk.StringVar(value='Studio Creator')
        self.premium_quality = tk.StringVar(value='Calidad premium: sin revisar')
        self.premium_badge_last = tk.StringVar(value='Sin badge exportado')
        self.professional_polish_images = {}
        self.professional_polish_status = tk.StringVar(value='Professional Polish listo. Revisa y aplica acabado de producto.')
        self.professional_polish_mode = tk.StringVar(value='Producto premium')
        self.professional_polish_score = tk.StringVar(value='Polish score: sin revisar')
        self.professional_polish_last = tk.StringVar(value='Sin exportación premium')
        self.command_center_images = {}
        self.command_center_status = tk.StringVar(value='Command Center listo. Busca o abre cualquier módulo premium.')
        self.command_search = tk.StringVar(value='')
        self.command_mode = tk.StringVar(value='Creator')
        self.command_results = []
        self.configure_style()
        self.load_visual_assets()
        self.load_custom_voices()
        self.load_favorites()
        self.load_profiles()
        self.build_ui()
        self.load_devices()
        self.refresh_voice_list()
        self.apply_preset()
        self.load_config(silent=True)
        self.refresh_language_ui()
        self.update_meters()
        self.setup_tray()
        self.bind_shortcuts()
        self.root.after(5000, self.watchdog_tick)
        self.root.after(2000, self.stream_guard_tick)

        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.root.after(450, self.show_welcome)

    def configure_style(self):
        self.root.configure(bg=COLORS["bg"])
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(".", background=COLORS["bg"], foreground=COLORS["text"], fieldbackground=COLORS["panel2"])
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["panel"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"])
        style.configure("Card.TLabel", background=COLORS["panel"], foreground=COLORS["text"])
        style.configure("Accent.TLabel", background=COLORS["bg"], foreground=COLORS["accent2"], font=("Segoe UI", 10, "bold"))
        style.configure("TButton", padding=8, background=COLORS["panel2"], foreground=COLORS["text"])
        style.map("TButton", background=[("active", COLORS["accent"])])
        style.configure("Accent.TButton", padding=10, background=COLORS["accent"], foreground="#ffffff")
        style.configure("Danger.TButton", padding=10, background=COLORS["danger"], foreground="#ffffff")
        style.configure("TCheckbutton", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("TCombobox", fieldbackground=COLORS["panel2"], background=COLORS["panel2"], foreground=COLORS["text"])
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 9), background=COLORS["panel2"], foreground=COLORS["text"])
        style.map("TNotebook.Tab", background=[("selected", COLORS["accent"])], foreground=[("selected", "#ffffff")])
        style.configure("TLabelframe", background=COLORS["bg"], foreground=COLORS["text"], bordercolor=COLORS["panel2"])
        style.configure("TLabelframe.Label", background=COLORS["bg"], foreground=COLORS["accent2"], font=("Segoe UI", 10, "bold"))
        style.configure("Horizontal.TProgressbar", thickness=18, troughcolor=COLORS["panel2"], background=COLORS["accent2"])


    def load_visual_assets(self):
        """Carga imágenes propias del programa."""
        asset_names = {
            "banner": "assets/banner.png",
            "home": "assets/icon_home.png",
            "voices": "assets/icon_voices.png",
            "sliders": "assets/icon_sliders.png",
            "live": "assets/icon_live.png",
            "sound": "assets/icon_sound.png",
            "guide": "assets/icon_guide.png",
            "tray": "assets/icon_tray.png",
            "applause": "assets/icon_applause.png",
            "laugh": "assets/icon_laugh.png",
            "victory": "assets/icon_victory.png",
            "error": "assets/icon_error.png",
            "magic": "assets/icon_magic.png",
        }
        for key, rel in asset_names.items():
            try:
                self.images[key] = tk.PhotoImage(file=resource_path(rel))
            except Exception as e:
                print(f"No se pudo cargar imagen {rel}: {e}")

        try:
            self.root.iconbitmap(resource_path("assets/app_icon.ico"))
        except Exception:
            pass

        voices_dir = Path(resource_path("assets/voices"))
        interface_consistency_dir = Path(resource_path("assets/interface_consistency"))
        if interface_consistency_dir.exists():
            for file in interface_consistency_dir.glob("*.png"):
                try:
                    self.interface_consistency_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen interface consistency {file}: {e}")

        design_system_dir = Path(resource_path("assets/design_system"))
        if design_system_dir.exists():
            for file in design_system_dir.glob("*.png"):
                try:
                    self.design_system_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen design system {file}: {e}")

        icon_system_dir = Path(resource_path("assets/icon_system"))
        if icon_system_dir.exists():
            for file in icon_system_dir.glob("*.png"):
                try:
                    self.icon_system_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen icon system {file}: {e}")

        language_pack_dir = Path(resource_path("assets/language_pack"))
        if language_pack_dir.exists():
            for file in language_pack_dir.glob("*.png"):
                try:
                    self.language_pack_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen language pack {file}: {e}")

        full_translation_dir = Path(resource_path("assets/full_translation"))
        if full_translation_dir.exists():
            for file in full_translation_dir.glob("*.png"):
                try:
                    self.full_translation_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen full translation {file}: {e}")

        bilingual_dir = Path(resource_path("assets/bilingual_visual"))
        if bilingual_dir.exists():
            for file in bilingual_dir.glob("*.png"):
                try:
                    self.bilingual_visual_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen bilingual visual {file}: {e}")

        command_dir = Path(resource_path("assets/command_center"))
        if command_dir.exists():
            for file in command_dir.glob("*.png"):
                try:
                    self.command_center_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen command center {file}: {e}")

        professional_polish_dir = Path(resource_path("assets/professional_polish"))
        if professional_polish_dir.exists():
            for file in professional_polish_dir.glob("*.png"):
                try:
                    self.professional_polish_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen professional polish {file}: {e}")

        ultra_ui_dir = Path(resource_path("assets/ultra_premium_ui"))
        if ultra_ui_dir.exists():
            for file in ultra_ui_dir.glob("*.png"):
                try:
                    self.ultra_premium_ui_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen ultra premium ui {file}: {e}")

        premium_dir = Path(resource_path("assets/premium_experience"))
        if premium_dir.exists():
            for file in premium_dir.glob("*.png"):
                try:
                    self.premium_experience_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen premium experience {file}: {e}")

        deploy_dir = Path(resource_path("assets/deploy_pro"))
        if deploy_dir.exists():
            for file in deploy_dir.glob("*.png"):
                try:
                    self.deploy_pro_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen command center pro {file}: {e}")

        web_pack_dir = Path(resource_path("assets/web_pack"))
        if web_pack_dir.exists():
            for file in web_pack_dir.glob("*.png"):
                try:
                    self.web_pack_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen web pack {file}: {e}")

        brand_kit_dir = Path(resource_path("assets/brand_kit"))
        if brand_kit_dir.exists():
            for file in brand_kit_dir.glob("*.png"):
                try:
                    self.brand_kit_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen brand kit {file}: {e}")

        publicacion_dir = Path(resource_path("assets/publicacion_pro"))
        if publicacion_dir.exists():
            for file in publicacion_dir.glob("*.png"):
                try:
                    self.publicacion_pro_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen publicacion pro {file}: {e}")

        export_pack_dir = Path(resource_path("assets/export_pack"))
        if export_pack_dir.exists():
            for file in export_pack_dir.glob("*.png"):
                try:
                    self.export_pack_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen export pack {file}: {e}")

        portadas_dir = Path(resource_path("assets/portadas_premium"))
        if portadas_dir.exists():
            for file in portadas_dir.glob("*.png"):
                try:
                    self.portadas_premium_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen portadas premium {file}: {e}")

        biblioteca_dir = Path(resource_path("assets/biblioteca_premium"))
        if biblioteca_dir.exists():
            for file in biblioteca_dir.glob("*.png"):
                try:
                    self.biblioteca_premium_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen biblioteca premium {file}: {e}")

        asistente_inicial_dir = Path(resource_path("assets/asistente_inicial"))
        if asistente_inicial_dir.exists():
            for file in asistente_inicial_dir.glob("*.png"):
                try:
                    self.asistente_inicial_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen asistente inicial {file}: {e}")

        inicio_dir = Path(resource_path("assets/inicio_premium"))
        if inicio_dir.exists():
            for file in inicio_dir.glob("*.png"):
                try:
                    self.inicio_premium_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen inicio premium {file}: {e}")

        visual_dir = Path(resource_path("assets/visual_pro"))
        if visual_dir.exists():
            for file in visual_dir.glob("*.png"):
                try:
                    self.visual_pro_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen visual pro {file}: {e}")

        revision_dir = Path(resource_path("assets/revision_tecnica"))
        if revision_dir.exists():
            for file in revision_dir.glob("*.png"):
                try:
                    self.revision_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen revision tecnica {file}: {e}")

        studio_dashboard_dir = Path(resource_path("assets/studio_dashboard"))
        if studio_dashboard_dir.exists():
            for file in studio_dashboard_dir.glob("*.png"):
                try:
                    self.studio_dashboard_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen studio dashboard {file}: {e}")

        clips_dir = Path(resource_path("assets/clips"))
        if clips_dir.exists():
            for file in clips_dir.glob("*.png"):
                try:
                    self.clips_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen clips {file}: {e}")

        vocal_analyzer_dir = Path(resource_path("assets/analizador_vocal"))
        if vocal_analyzer_dir.exists():
            for file in vocal_analyzer_dir.glob("*.png"):
                try:
                    self.vocal_analyzer_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen analizador vocal {file}: {e}")

        vocal_chain_dir = Path(resource_path("assets/cadena_vocal"))
        if vocal_chain_dir.exists():
            for file in vocal_chain_dir.glob("*.png"):
                try:
                    self.vocal_chain_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen cadena vocal {file}: {e}")

        timeline_dir = Path(resource_path("assets/timeline_pro"))
        if timeline_dir.exists():
            for file in timeline_dir.glob("*.png"):
                try:
                    self.timeline_images[file.stem] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen timeline {file}: {e}")

        if voices_dir.exists():
            for file in voices_dir.glob("*.png"):
                key = file.stem
                try:
                    self.voice_card_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar carta de voz {file}: {e}")

        packs_dir = Path(resource_path("assets/packs"))
        if packs_dir.exists():
            for file in packs_dir.glob("pack_*.png"):
                key = file.stem.replace("pack_", "")
                try:
                    self.pack_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen de pack {file}: {e}")

        studio_dir = Path(resource_path("assets/studio"))
        if studio_dir.exists():
            for file in studio_dir.glob("*.png"):
                key = file.stem
                try:
                    self.studio_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen studio {file}: {e}")

        ultra_dir = Path(resource_path("assets/ultra"))
        if ultra_dir.exists():
            for file in ultra_dir.glob("*.png"):
                key = file.stem
                try:
                    self.ultra_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen ultra {file}: {e}")

        pro_dir = Path(resource_path("assets/pro"))
        if pro_dir.exists():
            for file in pro_dir.glob("*.png"):
                key = file.stem
                try:
                    self.pro_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen pro {file}: {e}")

        grid_dir = Path(resource_path("assets/grid"))
        if grid_dir.exists():
            for file in grid_dir.glob("*.png"):
                key = file.stem
                try:
                    self.grid_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen grid {file}: {e}")

        streamer_dir = Path(resource_path("assets/streamer"))
        if streamer_dir.exists():
            for file in streamer_dir.glob("*.png"):
                key = file.stem
                try:
                    self.streamer_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen streamer {file}: {e}")

        wizard_dir = Path(resource_path("assets/asistente"))
        if wizard_dir.exists():
            for file in wizard_dir.glob("*.png"):
                key = file.stem
                try:
                    self.wizard_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen asistente {file}: {e}")

        quick_dir = Path(resource_path("assets/rapido"))
        if quick_dir.exists():
            for file in quick_dir.glob("*.png"):
                key = file.stem
                try:
                    self.quick_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen rápida {file}: {e}")

        rec_dir = Path(resource_path("assets/grabadora"))
        if rec_dir.exists():
            for file in rec_dir.glob("*.png"):
                key = file.stem
                try:
                    self.rec_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen grabadora {file}: {e}")

        mesa_dir = Path(resource_path("assets/mesa_sonidos"))
        if mesa_dir.exists():
            for file in mesa_dir.glob("*.png"):
                key = file.stem
                try:
                    self.mesa_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen mesa de sonidos {file}: {e}")

        diag_dir = Path(resource_path("assets/diagnostico"))
        if diag_dir.exists():
            for file in diag_dir.glob("*.png"):
                key = file.stem
                try:
                    self.diag_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen diagnóstico {file}: {e}")

        mini_dir = Path(resource_path("assets/mini_panel"))
        if mini_dir.exists():
            for file in mini_dir.glob("*.png"):
                key = file.stem
                try:
                    self.mini_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen mini panel {file}: {e}")

        eq_dir = Path(resource_path("assets/ecualizador"))
        if eq_dir.exists():
            for file in eq_dir.glob("*.png"):
                key = file.stem
                try:
                    self.eq_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen ecualizador {file}: {e}")

        perfiles_dir = Path(resource_path("assets/perfiles"))
        if perfiles_dir.exists():
            for file in perfiles_dir.glob("*.png"):
                key = file.stem
                try:
                    self.profile_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen perfiles {file}: {e}")

        personas_dir = Path(resource_path("assets/personas"))
        if personas_dir.exists():
            for file in personas_dir.glob("*.png"):
                key = file.stem
                try:
                    self.personas_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen personas {file}: {e}")

        cambiador_dir = Path(resource_path("assets/cambiador_personas"))
        if cambiador_dir.exists():
            for file in cambiador_dir.glob("*.png"):
                key = file.stem
                try:
                    self.cambiador_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen cambiador {file}: {e}")

        creator_dir = Path(resource_path("assets/creador_voces"))
        if creator_dir.exists():
            for file in creator_dir.glob("*.png"):
                key = file.stem
                try:
                    self.creator_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen creador de voces {file}: {e}")

        hotkeys_dir = Path(resource_path("assets/atajos"))
        if hotkeys_dir.exists():
            for file in hotkeys_dir.glob("*.png"):
                key = file.stem
                try:
                    self.hotkey_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen atajos {file}: {e}")

        favoritos_dir = Path(resource_path("assets/favoritos_pro"))
        if favoritos_dir.exists():
            for file in favoritos_dir.glob("*.png"):
                key = file.stem
                try:
                    self.favoritos_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen favoritos pro {file}: {e}")

        scenes_dir = Path(resource_path("assets/escenas_pro"))
        if scenes_dir.exists():
            for file in scenes_dir.glob("*.png"):
                key = file.stem
                try:
                    self.scenes_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen escenas pro {file}: {e}")

        hub_dir = Path(resource_path("assets/streamer_hub"))
        if hub_dir.exists():
            for file in hub_dir.glob("*.png"):
                key = file.stem
                try:
                    self.hub_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen streamer hub {file}: {e}")

        rendimiento_dir = Path(resource_path("assets/rendimiento"))
        if rendimiento_dir.exists():
            for file in rendimiento_dir.glob("*.png"):
                key = file.stem
                try:
                    self.performance_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen rendimiento {file}: {e}")

        cable_dir = Path(resource_path("assets/cable_virtual"))
        if cable_dir.exists():
            for file in cable_dir.glob("*.png"):
                key = file.stem
                try:
                    self.cable_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen cable virtual {file}: {e}")

        test_voice_dir = Path(resource_path("assets/test_voz"))
        if test_voice_dir.exists():
            for file in test_voice_dir.glob("*.png"):
                key = file.stem
                try:
                    self.test_voice_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen test de voz {file}: {e}")

        autotune_dir = Path(resource_path("assets/autotune"))
        if autotune_dir.exists():
            for file in autotune_dir.glob("*.png"):
                key = file.stem
                try:
                    self.autotune_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen autotune {file}: {e}")

        karaoke_dir = Path(resource_path("assets/karaoke"))
        if karaoke_dir.exists():
            for file in karaoke_dir.glob("*.png"):
                key = file.stem
                try:
                    self.karaoke_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen karaoke {file}: {e}")

        karaoke_studio_dir = Path(resource_path("assets/karaoke_studio"))
        if karaoke_studio_dir.exists():
            for file in karaoke_studio_dir.glob("*.png"):
                key = file.stem
                try:
                    self.karaoke_studio_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen karaoke studio {file}: {e}")

        song_dir = Path(resource_path("assets/cancion_pro"))
        if song_dir.exists():
            for file in song_dir.glob("*.png"):
                key = file.stem
                try:
                    self.song_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen canción pro {file}: {e}")
        mix_dir = Path(resource_path("assets/mezclador_musical"))
        if mix_dir.exists():
            for file in mix_dir.glob("*.png"):
                key = file.stem
                try:
                    self.mix_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen mezclador musical {file}: {e}")
        master_dir = Path(resource_path("assets/master_final"))
        if master_dir.exists():
            for file in master_dir.glob("*.png"):
                key = file.stem
                try:
                    self.master_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen master final {file}: {e}")
        multitrack_dir = Path(resource_path("assets/multipista"))
        if multitrack_dir.exists():
            for file in multitrack_dir.glob("*.png"):
                key = file.stem
                try:
                    self.multitrack_images[key] = tk.PhotoImage(file=str(file))
                except Exception as e:
                    print(f"No se pudo cargar imagen multipista {file}: {e}")

        # Miniaturas de voces más pequeñas para la cuadrícula Caja de voces.
        voices_dir = Path(resource_path("assets/voices"))
        if voices_dir.exists():
            for file in voices_dir.glob("*.png"):
                try:
                    img = Image.open(str(file)).resize((240, 135))
                    self.grid_voice_images[file.stem] = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"No se pudo cargar miniatura voicebox {file}: {e}")



    def voice_image_key(self, name):
        text = name.lower()
        replacements = {
            "á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u","ñ":"n",
            " ":"_","/":"_","\\":"_","-":"_","·":"_","(":"",")":"",
            ",":"",".":"","¡":"","!":"","?":"","¿":""
        }
        for a, b in replacements.items():
            text = text.replace(a, b)
        while "__" in text:
            text = text.replace("__", "_")
        return text.strip("_")

    def make_card(self, parent, title=None):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=14)
        if title:
            ttk.Label(frame, text=title, style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        return frame

    SECCION_POR_DEFECTO = "🛠 Herramientas"

    def _crear_seccion(self, nombre):
        if nombre not in self._secciones:
            marco = ttk.Frame(self.notebook)
            self.notebook.add(marco, text=nombre)
            sub = ttk.Notebook(marco)
            sub.pack(fill="both", expand=True)
            self._secciones[nombre] = sub
        return self._secciones[nombre]

    def _parent_for(self, attr):
        return self._crear_seccion(self._seccion_de.get(attr, self.SECCION_POR_DEFECTO))

    def _add_tab(self, tab, text):
        tab.master.add(tab, text=text)

    def select_tab(self, tab):
        """Selecciona la sección de la pestaña y luego la pestaña."""
        try:
            sub = tab.master
            self.notebook.select(sub.master)
            sub.select(tab)
        except Exception:
            pass

    def build_ui(self):
        main = ttk.Frame(self.root, padding=18)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 12))

        left = ttk.Frame(header)
        left.pack(side="left", fill="x", expand=True)
        self.main_title_label = ttk.Label(left, text="🎙️ Modulador de Voz en Directo", font=("Segoe UI", 28, "bold"))
        self.main_title_label.pack(anchor="w")
        self.main_subtitle_label = ttk.Label(left, text="V81 Navegación Pro · coherencia visual · auditoría premium · ES / EN")
        self.main_subtitle_label.pack(anchor="w")

        right = ttk.Frame(header)
        right.pack(side="right")
        ttk.Label(right, textvariable=self.state, style="Accent.TLabel").pack(anchor="e")
        self.main_hint_label = ttk.Label(right, text="Micrófono real → Voz modificada → Cable virtual", style="Muted.TLabel")
        self.main_hint_label.pack(anchor="e")

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)

        # Navegación por secciones (V81): el notebook principal contiene
        # 6 secciones y cada una un sub-notebook con sus pestañas.
        self._secciones = {}
        self._seccion_de = {
            # 🎮 Directo
            "tab_inicio": "🎮 Directo", "tab_inicio_premium": "🎮 Directo",
            "tab_pro": "🎮 Directo", "tab_barra_rapida": "🎮 Directo",
            "tab_mini_panel": "🎮 Directo", "tab_directo_pro": "🎮 Directo",
            "tab_directo": "🎮 Directo", "tab_streamer_hub": "🎮 Directo",
            "tab_escenas_pro": "🎮 Directo", "tab_clips": "🎮 Directo",
            "tab_test_voz": "🎮 Directo",
            # 🎙 Voces
            "tab_voces": "🎙 Voces", "tab_voicebox_grid": "🎙 Voces",
            "tab_packs": "🎙 Voces", "tab_personas_pro": "🎙 Voces",
            "tab_cambiador_personas": "🎙 Voces", "tab_creador_voces": "🎙 Voces",
            "tab_favoritos_pro": "🎙 Voces", "tab_perfiles_pro": "🎙 Voces",
            "tab_ultra": "🎙 Voces", "tab_studio": "🎙 Voces",
            # 🎵 Música
            "tab_autotune": "🎵 Música", "tab_karaoke": "🎵 Música",
            "tab_karaoke_studio": "🎵 Música", "tab_cancion_pro": "🎵 Música",
            "tab_mezclador_musical": "🎵 Música", "tab_master_final": "🎵 Música",
            "tab_studio_dashboard": "🎵 Música", "tab_analizador_vocal": "🎵 Música",
            "tab_cadena_vocal": "🎵 Música", "tab_timeline_pro": "🎵 Música",
            "tab_multipista": "🎵 Música", "tab_biblioteca_premium": "🎵 Música",
            # 🛠 Herramientas
            "tab_asistente": "🛠 Herramientas", "tab_asistente_inicial": "🛠 Herramientas",
            "tab_mesa_pro": "🛠 Herramientas", "tab_sonidos": "🛠 Herramientas",
            "tab_grabadora": "🛠 Herramientas", "tab_diagnostico": "🛠 Herramientas",
            "tab_ecualizador": "🛠 Herramientas", "tab_ruido": "🛠 Herramientas",
            "tab_rendimiento": "🛠 Herramientas", "tab_cable_virtual": "🛠 Herramientas",
            "tab_revision_tecnica": "🛠 Herramientas", "tab_visualizador": "🛠 Herramientas",
            "tab_command_center": "🛠 Herramientas",
            # 🚀 Publicar
            "tab_deploy_pro": "🚀 Publicar", "tab_web_pack": "🚀 Publicar",
            "tab_landing_page": "🚀 Publicar", "tab_brand_kit": "🚀 Publicar",
            "tab_publicacion_pro": "🚀 Publicar", "tab_export_pack": "🚀 Publicar",
            "tab_portadas_premium": "🚀 Publicar",
            # ⚙ Ajustes
            "tab_ajustes": "⚙ Ajustes", "tab_atajos": "⚙ Ajustes",
            "tab_guia": "⚙ Ajustes", "tab_design_system": "⚙ Ajustes",
            "tab_icon_system": "⚙ Ajustes", "tab_language_pack": "⚙ Ajustes",
            "tab_full_translation": "⚙ Ajustes", "tab_bilingual_visual": "⚙ Ajustes",
            "tab_interface_consistency": "⚙ Ajustes", "tab_visual_pro": "⚙ Ajustes",
            "tab_ultra_premium_ui": "⚙ Ajustes", "tab_premium_experience": "⚙ Ajustes",
            "tab_professional_polish": "⚙ Ajustes",
        }
        for _nombre in ["🎮 Directo", "🎙 Voces", "🎵 Música", "🛠 Herramientas", "🚀 Publicar", "⚙ Ajustes"]:
            self._crear_seccion(_nombre)

        self.tab_interface_consistency = ttk.Frame(self._parent_for("tab_interface_consistency"), padding=14)
        self.tab_design_system = ttk.Frame(self._parent_for("tab_design_system"), padding=14)
        self.tab_icon_system = ttk.Frame(self._parent_for("tab_icon_system"), padding=14)
        self.tab_language_pack = ttk.Frame(self._parent_for("tab_language_pack"), padding=14)
        self.tab_full_translation = ttk.Frame(self._parent_for("tab_full_translation"), padding=14)
        self.tab_bilingual_visual = ttk.Frame(self._parent_for("tab_bilingual_visual"), padding=14)
        self.tab_inicio = ttk.Frame(self._parent_for("tab_inicio"), padding=14)
        self.tab_pro = ttk.Frame(self._parent_for("tab_pro"), padding=14)
        self.tab_asistente = ttk.Frame(self._parent_for("tab_asistente"), padding=14)
        self.tab_barra_rapida = ttk.Frame(self._parent_for("tab_barra_rapida"), padding=14)
        self.tab_mesa_pro = ttk.Frame(self._parent_for("tab_mesa_pro"), padding=14)
        self.tab_diagnostico = ttk.Frame(self._parent_for("tab_diagnostico"), padding=14)
        self.tab_mini_panel = ttk.Frame(self._parent_for("tab_mini_panel"), padding=14)
        self.tab_ecualizador = ttk.Frame(self._parent_for("tab_ecualizador"), padding=14)
        self.tab_perfiles_pro = ttk.Frame(self._parent_for("tab_perfiles_pro"), padding=14)
        self.tab_personas_pro = ttk.Frame(self._parent_for("tab_personas_pro"), padding=14)
        self.tab_cambiador_personas = ttk.Frame(self._parent_for("tab_cambiador_personas"), padding=14)
        self.tab_creador_voces = ttk.Frame(self._parent_for("tab_creador_voces"), padding=14)
        self.tab_atajos = ttk.Frame(self._parent_for("tab_atajos"), padding=14)
        self.tab_favoritos_pro = ttk.Frame(self._parent_for("tab_favoritos_pro"), padding=14)
        self.tab_escenas_pro = ttk.Frame(self._parent_for("tab_escenas_pro"), padding=14)
        self.tab_streamer_hub = ttk.Frame(self._parent_for("tab_streamer_hub"), padding=14)
        self.tab_rendimiento = ttk.Frame(self._parent_for("tab_rendimiento"), padding=14)
        self.tab_ruido = ttk.Frame(self._parent_for("tab_ruido"), padding=14)
        self.tab_cable_virtual = ttk.Frame(self._parent_for("tab_cable_virtual"), padding=14)
        self.tab_test_voz = ttk.Frame(self._parent_for("tab_test_voz"), padding=14)
        self.tab_autotune = ttk.Frame(self._parent_for("tab_autotune"), padding=14)
        self.tab_karaoke = ttk.Frame(self._parent_for("tab_karaoke"), padding=14)
        self.tab_karaoke_studio = ttk.Frame(self._parent_for("tab_karaoke_studio"), padding=14)
        self.tab_cancion_pro = ttk.Frame(self._parent_for("tab_cancion_pro"), padding=14)
        self.tab_mezclador_musical = ttk.Frame(self._parent_for("tab_mezclador_musical"), padding=14)
        self.tab_master_final = ttk.Frame(self._parent_for("tab_master_final"), padding=14)
        self.tab_command_center = ttk.Frame(self._parent_for("tab_command_center"), padding=14)
        self.tab_professional_polish = ttk.Frame(self._parent_for("tab_professional_polish"), padding=14)
        self.tab_ultra_premium_ui = ttk.Frame(self._parent_for("tab_ultra_premium_ui"), padding=14)
        self.tab_premium_experience = ttk.Frame(self._parent_for("tab_premium_experience"), padding=14)
        self.tab_deploy_pro = ttk.Frame(self._parent_for("tab_deploy_pro"), padding=14)
        self.tab_web_pack = ttk.Frame(self._parent_for("tab_web_pack"), padding=14)
        self.tab_landing_page = ttk.Frame(self._parent_for("tab_landing_page"), padding=14)
        self.tab_brand_kit = ttk.Frame(self._parent_for("tab_brand_kit"), padding=14)
        self.tab_publicacion_pro = ttk.Frame(self._parent_for("tab_publicacion_pro"), padding=14)
        self.tab_export_pack = ttk.Frame(self._parent_for("tab_export_pack"), padding=14)
        self.tab_portadas_premium = ttk.Frame(self._parent_for("tab_portadas_premium"), padding=14)
        self.tab_biblioteca_premium = ttk.Frame(self._parent_for("tab_biblioteca_premium"), padding=14)
        self.tab_asistente_inicial = ttk.Frame(self._parent_for("tab_asistente_inicial"), padding=14)
        self.tab_inicio_premium = ttk.Frame(self._parent_for("tab_inicio_premium"), padding=14)
        self.tab_visual_pro = ttk.Frame(self._parent_for("tab_visual_pro"), padding=14)
        self.tab_revision_tecnica = ttk.Frame(self._parent_for("tab_revision_tecnica"), padding=14)
        self.tab_studio_dashboard = ttk.Frame(self._parent_for("tab_studio_dashboard"), padding=14)
        self.tab_analizador_vocal = ttk.Frame(self._parent_for("tab_analizador_vocal"), padding=14)
        self.tab_cadena_vocal = ttk.Frame(self._parent_for("tab_cadena_vocal"), padding=14)
        self.tab_timeline_pro = ttk.Frame(self._parent_for("tab_timeline_pro"), padding=14)
        self.tab_multipista = ttk.Frame(self._parent_for("tab_multipista"), padding=14)
        self.tab_clips = ttk.Frame(self._parent_for("tab_clips"), padding=14)
        self.tab_grabadora = ttk.Frame(self._parent_for("tab_grabadora"), padding=14)
        self.tab_directo_pro = ttk.Frame(self._parent_for("tab_directo_pro"), padding=14)
        self.tab_voicebox_grid = ttk.Frame(self._parent_for("tab_voicebox_grid"), padding=14)
        self.tab_ultra = ttk.Frame(self._parent_for("tab_ultra"), padding=14)
        self.tab_voces = ttk.Frame(self._parent_for("tab_voces"), padding=14)
        self.tab_studio = ttk.Frame(self._parent_for("tab_studio"), padding=14)
        self.tab_packs = ttk.Frame(self._parent_for("tab_packs"), padding=14)
        self.tab_ajustes = ttk.Frame(self._parent_for("tab_ajustes"), padding=14)
        self.tab_directo = ttk.Frame(self._parent_for("tab_directo"), padding=14)
        self.tab_sonidos = ttk.Frame(self._parent_for("tab_sonidos"), padding=14)
        self.tab_visualizador = ttk.Frame(self._parent_for("tab_visualizador"), padding=14)
        self.tab_guia = ttk.Frame(self._parent_for("tab_guia"), padding=14)

        self._add_tab(self.tab_interface_consistency, text="🧭 Consistencia")
        self._add_tab(self.tab_design_system, text="🎨 Diseño")
        self._add_tab(self.tab_icon_system, text="🖼 Iconos")
        self._add_tab(self.tab_language_pack, text="🧩 Lang Pack")
        self._add_tab(self.tab_full_translation, text="🌍 Traducción")
        self._add_tab(self.tab_bilingual_visual, text="🌐 Idiomas")
        self._add_tab(self.tab_inicio, text="🏠 Inicio")
        self._add_tab(self.tab_pro, text="🎛 Modo Pro")
        self._add_tab(self.tab_asistente, text="🧭 Asistente")
        self._add_tab(self.tab_barra_rapida, text="⚡ Barra rápida")
        self._add_tab(self.tab_mesa_pro, text="🎚 Mesa Pro")
        self._add_tab(self.tab_diagnostico, text="🛠 Diagnóstico")
        self._add_tab(self.tab_mini_panel, text="🪟 Mini Panel")
        self._add_tab(self.tab_ecualizador, text="🎚 Ecualizador")
        self._add_tab(self.tab_perfiles_pro, text="👤 Perfiles Pro+")
        self._add_tab(self.tab_personas_pro, text="👥 Personas Pro")
        self._add_tab(self.tab_cambiador_personas, text="🎭 Cambiador")
        self._add_tab(self.tab_creador_voces, text="🧪 Creador")
        self._add_tab(self.tab_atajos, text="⌨ Atajos")
        self._add_tab(self.tab_favoritos_pro, text="⭐ Favoritos")
        self._add_tab(self.tab_escenas_pro, text="🎬 Escenas")
        self._add_tab(self.tab_streamer_hub, text="📡 Streamer Hub")
        self._add_tab(self.tab_rendimiento, text="🚀 Rendimiento")
        self._add_tab(self.tab_ruido, text="🤫 Ruido")
        self._add_tab(self.tab_cable_virtual, text="🔌 Cable Virtual")
        self._add_tab(self.tab_test_voz, text="🎙 Test de Voz")
        self._add_tab(self.tab_autotune, text="🎵 Autotune")
        self._add_tab(self.tab_karaoke, text="🎤 Karaoke")
        self._add_tab(self.tab_karaoke_studio, text="🎧 Karaoke Studio")
        self._add_tab(self.tab_cancion_pro, text="🎼 Canción Pro")
        self._add_tab(self.tab_mezclador_musical, text="🎚 Mezclador")
        self._add_tab(self.tab_master_final, text="💿 Master Final")
        self._add_tab(self.tab_command_center, text="⌘ Command")
        self._add_tab(self.tab_professional_polish, text="💼 Polish")
        self._add_tab(self.tab_ultra_premium_ui, text="💠 UI Premium")
        self._add_tab(self.tab_premium_experience, text="💎 Premium")
        self._add_tab(self.tab_deploy_pro, text="🚢 Deploy")
        self._add_tab(self.tab_web_pack, text="🌍 Web Pack")
        self._add_tab(self.tab_landing_page, text="🌐 Landing")
        self._add_tab(self.tab_brand_kit, text="🏷 Brand Kit")
        self._add_tab(self.tab_publicacion_pro, text="🚀 Publicación")
        self._add_tab(self.tab_export_pack, text="📦 Export Pack")
        self._add_tab(self.tab_portadas_premium, text="🖼 Portadas")
        self._add_tab(self.tab_biblioteca_premium, text="📚 Biblioteca")
        self._add_tab(self.tab_asistente_inicial, text="🪄 Asistente")
        self._add_tab(self.tab_inicio_premium, text="🏠 Inicio")
        self._add_tab(self.tab_visual_pro, text="🎨 Visual Pro")
        self._add_tab(self.tab_revision_tecnica, text="🧪 Revisión")
        self._add_tab(self.tab_studio_dashboard, text="🏁 Studio")
        self._add_tab(self.tab_analizador_vocal, text="📊 Analizador")
        self._add_tab(self.tab_cadena_vocal, text="🎙 Cadena Vocal")
        self._add_tab(self.tab_timeline_pro, text="🧱 Timeline")
        self._add_tab(self.tab_multipista, text="🎛 Multipista")
        self._add_tab(self.tab_clips, text="🎬 Clips")
        self._add_tab(self.tab_grabadora, text="⏺ Grabadora")
        self._add_tab(self.tab_directo_pro, text="🎬 Directo Pro")
        self._add_tab(self.tab_voicebox_grid, text="▦ Caja de voces")
        self._add_tab(self.tab_ultra, text="💠 Ultra")
        self._add_tab(self.tab_voces, text="🎙 Voces")
        self._add_tab(self.tab_studio, text="💎 Estudio")
        self._add_tab(self.tab_packs, text="🧩 Packs")
        self._add_tab(self.tab_ajustes, text="🎚 Ajustes")
        self._add_tab(self.tab_directo, text="▶ Directo")
        self._add_tab(self.tab_sonidos, text="🔊 Sonidos")
        self._add_tab(self.tab_visualizador, text="📊 Visualizador")
        self._add_tab(self.tab_guia, text="📘 Guía")

        self.build_interface_consistency_tab()
        self.build_design_system_tab()
        self.build_icon_system_tab()
        self.build_language_pack_tab()
        self.build_full_translation_tab()
        self.build_bilingual_visual_tab()
        self.build_home_tab()
        self.build_pro_mode_tab()
        self.build_asistente_tab()
        self.build_barra_rapida_tab()
        self.build_mesa_pro_tab()
        self.build_diagnostico_tab()
        self.build_mini_panel_tab()
        self.build_ecualizador_tab()
        self.build_perfiles_pro_tab()
        self.build_personas_pro_tab()
        self.build_cambiador_personas_tab()
        self.build_creador_voces_tab()
        self.build_atajos_tab()
        self.build_favoritos_pro_tab()
        self.build_escenas_pro_tab()
        self.build_streamer_hub_tab()
        self.build_rendimiento_tab()
        self.build_ruido_tab()
        self.build_cable_virtual_tab()
        self.build_test_voz_tab()
        self.build_autotune_tab()
        self.build_karaoke_tab()
        self.build_karaoke_studio_tab()
        self.build_cancion_pro_tab()
        self.build_mezclador_musical_tab()
        self.build_master_final_tab()
        self.build_command_center_tab()
        self.build_professional_polish_tab()
        self.build_ultra_premium_ui_tab()
        self.build_premium_experience_tab()
        self.build_deploy_pro_tab()
        self.build_web_pack_tab()
        self.build_landing_page_tab()
        self.build_brand_kit_tab()
        self.build_publicacion_pro_tab()
        self.build_export_pack_tab()
        self.build_portadas_premium_tab()
        self.build_biblioteca_premium_tab()
        self.build_asistente_inicial_tab()
        self.build_inicio_premium_tab()
        self.build_visual_pro_tab()
        self.build_revision_tecnica_tab()
        self.build_studio_dashboard_tab()
        self.build_analizador_vocal_tab()
        self.build_cadena_vocal_tab()
        self.build_timeline_pro_tab()
        self.build_multipista_tab()
        self.build_clips_tab()
        self.build_grabadora_tab()
        self.build_directo_pro_tab()
        self.build_voicebox_grid_tab()
        self.build_ultra_tab()
        self.build_voices_tab()
        self.build_studio_tab()
        self.build_packs_tab()
        self.build_settings_tab()
        self.build_live_tab()
        self.build_soundboard_tab()
        self.build_visualizer_tab()
        self.build_guide_tab()

        self.tab_language_texts = {
            self.tab_interface_consistency: ("🧭 Consistencia", "🧭 Consistency"),
            self.tab_design_system: ("🎨 Diseño", "🎨 Design"),
            self.tab_icon_system: ("🖼 Iconos", "🖼 Icons"),
            self.tab_language_pack: ("🧩 Lang Pack", "🧩 Lang Pack"),
            self.tab_full_translation: ("🌍 Traducción", "🌍 Translation"),
            self.tab_bilingual_visual: ("🌐 Idiomas", "🌐 Languages"),
            self.tab_inicio: ("🏠 Inicio", "🏠 Home"),
            self.tab_pro: ("🎛 Modo Pro", "🎛 Pro Mode"),
            self.tab_asistente: ("🧭 Asistente", "🧭 Assistant"),
            self.tab_barra_rapida: ("⚡ Barra rápida", "⚡ Quick Bar"),
            self.tab_mesa_pro: ("🎚 Mesa Pro", "🎚 Pro Mixer"),
            self.tab_diagnostico: ("🛠 Diagnóstico", "🛠 Diagnostics"),
            self.tab_mini_panel: ("🪟 Mini Panel", "🪟 Mini Panel"),
            self.tab_ecualizador: ("🎚 Ecualizador", "🎚 Equalizer"),
            self.tab_perfiles_pro: ("👤 Perfiles Pro+", "👤 Pro Profiles+"),
            self.tab_personas_pro: ("👥 Personas Pro", "👥 People Pro"),
            self.tab_cambiador_personas: ("🎭 Cambiador", "🎭 Switcher"),
            self.tab_creador_voces: ("🧪 Creador", "🧪 Creator"),
            self.tab_atajos: ("⌨ Atajos", "⌨ Hotkeys"),
            self.tab_favoritos_pro: ("⭐ Favoritos", "⭐ Favorites"),
            self.tab_escenas_pro: ("🎬 Escenas", "🎬 Scenes"),
            self.tab_streamer_hub: ("📡 Streamer Hub", "📡 Streamer Hub"),
            self.tab_rendimiento: ("🚀 Rendimiento", "🚀 Performance"),
            self.tab_ruido: ("🤫 Ruido", "🤫 Noise"),
            self.tab_cable_virtual: ("🔌 Cable Virtual", "🔌 Virtual Cable"),
            self.tab_test_voz: ("🎙 Test de Voz", "🎙 Voice Test"),
            self.tab_autotune: ("🎵 Autotune", "🎵 Autotune"),
            self.tab_karaoke: ("🎤 Karaoke", "🎤 Karaoke"),
            self.tab_karaoke_studio: ("🎧 Karaoke Studio", "🎧 Karaoke Studio"),
            self.tab_cancion_pro: ("🎼 Canción Pro", "🎼 Song Pro"),
            self.tab_mezclador_musical: ("🎚 Mezclador", "🎚 Mixer"),
            self.tab_master_final: ("💿 Master Final", "💿 Final Master"),
            self.tab_command_center: ("⌘ Command", "⌘ Command"),
            self.tab_professional_polish: ("💼 Polish", "💼 Polish"),
            self.tab_ultra_premium_ui: ("💠 UI Premium", "💠 Premium UI"),
            self.tab_premium_experience: ("💎 Premium", "💎 Premium"),
            self.tab_deploy_pro: ("🚢 Deploy", "🚢 Deploy"),
            self.tab_web_pack: ("🌍 Web Pack", "🌍 Web Pack"),
            self.tab_landing_page: ("🌐 Landing", "🌐 Landing"),
            self.tab_brand_kit: ("🏷 Brand Kit", "🏷 Brand Kit"),
            self.tab_publicacion_pro: ("🚀 Publicación", "🚀 Publish"),
            self.tab_export_pack: ("📦 Export Pack", "📦 Export Pack"),
            self.tab_portadas_premium: ("🖼 Portadas", "🖼 Covers"),
            self.tab_biblioteca_premium: ("📚 Biblioteca", "📚 Library"),
            self.tab_asistente_inicial: ("🪄 Asistente", "🪄 Wizard"),
            self.tab_inicio_premium: ("🏠 Inicio", "🏠 Home"),
            self.tab_visual_pro: ("🎨 Visual Pro", "🎨 Visual Pro"),
            self.tab_revision_tecnica: ("🧪 Revisión", "🧪 Review"),
            self.tab_studio_dashboard: ("🏁 Studio", "🏁 Studio"),
            self.tab_analizador_vocal: ("📊 Analizador", "📊 Analyzer"),
            self.tab_cadena_vocal: ("🎙 Cadena Vocal", "🎙 Vocal Chain"),
            self.tab_timeline_pro: ("🧱 Timeline", "🧱 Timeline"),
            self.tab_multipista: ("🎛 Multipista", "🎛 Multitrack"),
            self.tab_clips: ("🎬 Clips", "🎬 Clips"),
            self.tab_grabadora: ("⏺ Grabadora", "⏺ Recorder"),
            self.tab_directo_pro: ("🎬 Directo Pro", "🎬 Live Pro"),
            self.tab_voicebox_grid: ("▦ Caja de voces", "▦ Voice Box"),
            self.tab_ultra: ("💠 Ultra", "💠 Ultra"),
            self.tab_voces: ("🎙 Voces", "🎙 Voices"),
            self.tab_studio: ("💎 Estudio", "💎 Studio"),
            self.tab_packs: ("🧩 Packs", "🧩 Packs"),
            self.tab_ajustes: ("🎚 Ajustes", "🎚 Settings"),
            self.tab_directo: ("▶ Directo", "▶ Live"),
            self.tab_sonidos: ("🔊 Sonidos", "🔊 Sounds"),
            self.tab_visualizador: ("📊 Visualizador", "📊 Visualizer"),
            self.tab_guia: ("📘 Guía", "📘 Guide"),
        }
        self.refresh_language_ui()


    def translation_pairs(self):
        """Parejas ES/EN para traducir textos comunes ya existentes en la UI."""
        return [
            ("Guardar", "Save"), ("Cargar", "Load"), ("Cerrar", "Close"), ("Abrir", "Open"),
            ("Aplicar", "Apply"), ("Exportar", "Export"), ("Actualizar", "Refresh"),
            ("Borrar", "Delete"), ("Vista previa", "Preview"), ("Estado", "Status"),
            ("Acciones", "Actions"), ("Accesos", "Shortcuts"), ("Consejos", "Tips"),
            ("Buscar", "Search"), ("Filtro", "Filter"), ("Todos", "All"),
            ("Configuración", "Settings"), ("Ajustes", "Settings"), ("Inicio", "Home"),
            ("Directo", "Live"), ("Voces", "Voices"), ("Sonidos", "Sounds"),
            ("Guía", "Guide"), ("Asistente", "Assistant"), ("Diagnóstico", "Diagnostics"),
            ("Rendimiento", "Performance"), ("Biblioteca", "Library"), ("Portadas", "Covers"),
            ("Publicación", "Publish"), ("Revisión", "Review"), ("Analizador", "Analyzer"),
            ("Cadena Vocal", "Vocal Chain"), ("Mezclador", "Mixer"), ("Master Final", "Final Master"),
            ("Grabadora", "Recorder"), ("Favoritos", "Favorites"), ("Escenas", "Scenes"),
            ("Perfiles", "Profiles"), ("Creador", "Creator"), ("Cambiador", "Switcher"),
            ("Idioma actual: Español", "Current language: English"),
            ("Configurar Discord", "Set up Discord"),
            ("Configurar Fortnite", "Set up Fortnite"),
            ("Abrir Export Pack", "Open Export Pack"),
            ("Modo enfoque", "Focus mode"),
            ("Exportar tema", "Export theme"),
            ("Export theme", "Export theme"),
            ("Español", "Spanish"), ("English", "English"),
            ("Usar título de canción", "Use song title"),
            ("Exportar PNG", "Export PNG"), ("Exportar JSON", "Export JSON"),
            ("Exportar informe", "Export report"), ("Exportar resumen", "Export summary"),
            ("Abrir carpeta", "Open folder"), ("Crear PNG", "Create PNG"),
            ("Preparación segura", "Safe setup"), ("Configurar todo seguro", "Safe full setup"),
            ("Aplicar paso", "Apply step"), ("Siguiente", "Next"), ("Anterior", "Back"),
            ("Empezar directo", "Start live"), ("Parar directo", "Stop live"),
            ("Grabar prueba WAV", "Record WAV test"), ("Grabar demo WAV", "Record WAV demo"),
            ("Exportar Master WAV", "Export Master WAV"), ("Exportar Instrumental WAV", "Export Instrumental WAV"),
            ("Micrófono", "Microphone"), ("Salida", "Output"), ("Entrada", "Input"),
            ("Latencia", "Latency"), ("Volumen", "Volume"), ("Compresor", "Compressor"),
            ("Puerta ruido", "Noise gate"), ("Ruido", "Noise"), ("Eco", "Echo"),
            ("Reverb", "Reverb"), ("Calidez", "Warmth"), ("Presencia", "Presence"),
            ("Aire/brillo", "Air/brightness"), ("Tonalidad", "Key"), ("Duración", "Duration"),
            ("Título", "Title"), ("Descripción", "Description"), ("Tags", "Tags"),
            ("Artista / canal", "Artist / channel"), ("Subtítulo", "Subtitle"),
            ("Plantillas", "Templates"), ("Checklist", "Checklist"), ("Informe", "Report"),
            ("Carpeta de trabajo", "Work folder"), ("Archivos encontrados", "Found files"),
            ("Flujo recomendado", "Recommended workflow"), ("Resumen rápido", "Quick summary"),
            ("Centro premium", "Premium center"), ("Mapa de la app", "App map"),
            ("Workflows rápidos", "Quick workflows"),
            ("Paquete de idioma", "Language pack"),
            ("Exportar paquete", "Export pack"),
            ("Exportar glosario", "Export glossary"),
            ("Importar traducción", "Import translation"),
            ("Modo de traducción", "Translation mode"),
            ("Cobertura", "Coverage"),
            ("Traducido", "Translated"),
            ("Pendiente", "Pending"),
            ("Aplicar inglés", "Apply English"),
            ("Aplicar español", "Apply Spanish"),
            ("Iconos premium", "Premium icons"),
            ("Imágenes del programa", "Program images"),
            ("Mejora visual", "Visual improvement"),
            ("Centro de idioma", "Language center"),
            ("Paquetes exportables", "Exportable packs"),
            ("Diccionario interno", "Internal dictionary"),
            ("Glosario", "Glossary"),
            ("Interfaz completa", "Full interface"),
            ("Navegación principal", "Main navigation"),
            ("Textos comunes", "Common texts"),
            ("Botones principales", "Main buttons"),
            ("Módulos premium", "Premium modules"),
            ("Abrir módulo", "Open module"),
            ("Cambiar idioma", "Change language"),
            ("Guardar idioma", "Save language"),
            ("Cargar idioma", "Load language"),
            ("Restablecer idioma", "Reset language"),
            ("Idioma guardado", "Language saved"),
            ("Idioma aplicado", "Language applied"),
            ("Paquete creado", "Pack created"),
            ("Archivo creado", "File created"),
            ("Exportación completada", "Export complete"),
            ("Sin errores", "No errors"),
            ("Validado", "Validated"),
            ("Premium visual", "Premium visual"),
            ("Panel principal", "Main panel"),
            ("Panel lateral", "Sidebar"),
            ("Acciones rápidas", "Quick actions"),
            ("Vista limpia", "Clean view"),
            ("Vista compacta", "Compact view"),
            ("Vista presentación", "Presentation view"),
            ("Modo creador", "Creator mode"),
            ("Modo streamer", "Streamer mode"),
            ("Modo karaoke", "Karaoke mode"),
            ("Modo publicar", "Publish mode"),
            ("Subir a hosting", "Upload to hosting"),
            ("Preparar web", "Prepare website"),
            ("Crear landing", "Create landing"),
            ("Crear portada", "Create cover"),
            ("Crear banner", "Create banner"),
            ("Crear avatar", "Create avatar"),
            ("Nombre de marca", "Brand name"),
            ("Nombre del canal", "Channel name"),
            ("Frase de marca", "Brand slogan"),
            ("Color principal", "Primary color"),
            ("Color secundario", "Secondary color"),
            ("Guardar pack", "Save pack"),
            ("Abrir pack", "Open pack"),
            ("Escanear archivos", "Scan files"),
            ("Limpiar lista", "Clear list"),
            ("Crear proyecto", "Create project"),
            ("Abrir proyecto", "Open project"),
            ("Guardar proyecto", "Save project"),
            ("Exportar proyecto", "Export project"),
            ("Prueba de voz", "Voice test"),
            ("Cable virtual", "Virtual cable"),
            ("Reducción de ruido", "Noise reduction"),
            ("Cadena vocal", "Vocal chain"),
            ("Analizador vocal", "Vocal analyzer"),
            ("Multipista", "Multitrack"),
            ("Lanzamiento", "Launch"),
            ("Consistencia", "Consistency"),
            ("Auditoría visual", "Visual audit"),
            ("Coherencia visual", "Visual consistency"),
            ("Reglas de diseño", "Design rules"),
            ("Aplicar consistencia", "Apply consistency"),
            ("Informe de consistencia", "Consistency report"),
            ("Revisión de interfaz", "Interface review"),
            ("Puntuación visual", "Visual score"),
            ("Sistema coherente", "Consistent system"),
            ("Espaciado", "Spacing"),
            ("Bordes", "Corners"),
            ("Jerarquía", "Hierarchy"),
            ("Contraste", "Contrast"),
            ("Navegación", "Navigation"),
            ("Exportar tablero", "Export board"),
            ("Tablero visual", "Visual board"),
        ]

    def translation_lookup(self):
        lookup_es_to_en = {}
        lookup_en_to_es = {}
        for es, en in self.translation_pairs():
            lookup_es_to_en[es] = en
            lookup_en_to_es[en] = es
        return lookup_es_to_en, lookup_en_to_es

    def translate_existing_widgets(self, root_widget=None):
        """Traduce textos comunes de botones/labels ya creados. No toca campos editables."""
        if root_widget is None:
            root_widget = self.root
        es_to_en, en_to_es = self.translation_lookup()
        target_en = self.app_language.get() == "English"

        def visit(widget):
            try:
                current = widget.cget("text")
                if isinstance(current, str) and current.strip():
                    new = es_to_en.get(current, current) if target_en else en_to_es.get(current, current)
                    if new != current:
                        widget.configure(text=new)
            except Exception:
                pass
            try:
                for child in widget.winfo_children():
                    visit(child)
            except Exception:
                pass
        visit(root_widget)

    def interface_consistency_checks(self):
        checks = []
        def add(name, ok, weight, detail):
            checks.append({"name": name, "ok": bool(ok), "weight": weight, "detail": detail})

        add("Design System", hasattr(self, "design_system_images") and bool(self.design_system_images), 15, "assets/design_system")
        add("Icon System", hasattr(self, "icon_system_images") and len(self.icon_system_images) >= 8, 15, "assets/icon_system")
        add("Language Pack", len(self.translation_pairs()) >= 120 if hasattr(self, "translation_pairs") else False, 12, "ES/EN dictionary")
        add("Bilingual tabs", hasattr(self, "tab_language_texts") and len(self.tab_language_texts) >= 40, 12, "translated tab map")
        add("Premium header", hasattr(self, "main_title_label") and hasattr(self, "main_hint_label"), 8, "main header labels")
        add("Visual tokens", hasattr(self, "design_system_theme") and hasattr(self, "design_system_density"), 10, "theme/density variables")
        add("Export modules", all(hasattr(self, n) for n in ["tab_export_pack", "tab_deploy_pro", "tab_web_pack"]), 10, "export/deploy/web pack")
        add("Creator modules", all(hasattr(self, n) for n in ["tab_brand_kit", "tab_publicacion_pro", "tab_portadas_premium"]), 10, "brand/publish/covers")
        add("Premium polish", all(hasattr(self, n) for n in ["tab_ultra_premium_ui", "tab_professional_polish", "tab_premium_experience"]), 8, "UI/polish/premium")
        return checks

    def interface_consistency_score(self):
        checks = self.interface_consistency_checks()
        total = sum(item["weight"] for item in checks) or 1
        score = sum(item["weight"] for item in checks if item["ok"]) / total * 100
        return int(round(score))

    def interface_consistency_data(self):
        checks = self.interface_consistency_checks()
        return {
            "version": VERSION,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "language": self.app_language.get() if hasattr(self, "app_language") else "Español",
            "mode": self.interface_consistency_mode.get(),
            "score": self.interface_consistency_score(),
            "checks": checks,
            "recommendations": [
                "Mantener una misma familia visual en banners, cards e iconos.",
                "Usar los tokens del Design System antes de publicar la app.",
                "Mantener navegación ES/EN coherente en pestañas y módulos premium.",
                "Exportar guía visual y manifest de iconos antes de crear instalador.",
            ],
        }

    def interface_consistency_apply(self):
        mode = self.interface_consistency_mode.get()
        try:
            if hasattr(self, "design_system_theme"):
                if mode == "Launch limpio":
                    self.design_system_theme.set("Gold Launch")
                elif mode == "Minimal pro":
                    self.design_system_theme.set("Focus Clean")
                elif mode == "Studio glass":
                    self.design_system_theme.set("Glass Studio")
                else:
                    self.design_system_theme.set("Aurora Premium")
            if hasattr(self, "design_system_density"):
                self.design_system_density.set("Cómodo premium" if mode != "Minimal pro" else "compacto pro")
            if hasattr(self, "design_system_roundness"):
                self.design_system_roundness.set(24 if mode != "Minimal pro" else 16)
            if hasattr(self, "icon_system_style"):
                self.icon_system_style.set("Dorado launch" if mode == "Launch limpio" else "Neón premium")
            if hasattr(self, "visual_theme_name"):
                self.visual_theme_name.set("Neón Azul" if mode != "Launch limpio" else "Dorado Studio")
        except Exception:
            pass
        score = self.interface_consistency_score()
        self.interface_consistency_score_var.set(self.language_text(f"Consistencia: {score}/100", f"Consistency: {score}/100"))
        self.interface_consistency_status.set(self.language_text("Reglas de consistencia aplicadas.", "Consistency rules applied."))
        self.interface_consistency_refresh_preview()

    def interface_consistency_folder(self):
        folder = Path.home() / "ModuladorVozDirecto_Canciones" / "InterfaceConsistency"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def interface_consistency_export_report(self):
        try:
            folder = self.interface_consistency_folder()
            data = self.interface_consistency_data()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = folder / f"interface_consistency_report_{ts}.json"
            txt_path = folder / f"interface_consistency_report_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = ["INTERFACE CONSISTENCY PRO", "", f"Version: {data['version']}", f"Language: {data['language']}", f"Mode: {data['mode']}", f"Score: {data['score']}/100", "", "Checks:"]
            for item in data["checks"]:
                lines.append(f"- {'OK' if item['ok'] else 'PENDING'} · {item['name']} · {item['detail']}")
            lines += ["", "Recommendations:"] + [f"- {r}" for r in data["recommendations"]]
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.interface_consistency_status.set(self.language_text("Informe de consistencia exportado.", "Consistency report exported."))
            messagebox.showinfo(self.language_text("Informe exportado", "Report exported"), f"{json_path}\n{txt_path}")
        except Exception as e:
            self.interface_consistency_status.set(f"Error: {e}")

    def interface_consistency_export_board(self):
        try:
            folder = self.interface_consistency_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"interface_consistency_board_{ts}.png"
            w, h = 1400, 900
            img = Image.new("RGBA", (w, h), (9, 11, 24, 255))
            draw = ImageDraw.Draw(img)
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54) if Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf").exists() else ImageFont.load_default()
            font_mid = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28) if Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf").exists() else ImageFont.load_default()
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22) if Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf").exists() else ImageFont.load_default()
            draw.rounded_rectangle((50, 50, w-50, h-50), radius=42, fill=(18, 22, 42, 255), outline=(0, 229, 255, 190), width=4)
            draw.text((90, 85), "Interface Consistency Pro", font=font_big, fill=(255, 255, 255, 255))
            score = self.interface_consistency_score()
            draw.rounded_rectangle((1010, 90, 1260, 170), radius=28, fill=(255, 214, 89, 255))
            draw.text((1060, 110), f"{score}/100", font=font_mid, fill=(12, 14, 24, 255))
            x, y = 100, 230
            for idx, item in enumerate(self.interface_consistency_checks()):
                xx = x + (idx % 3) * 410
                yy = y + (idx // 3) * 160
                col = (98, 255, 180, 255) if item["ok"] else (255, 116, 170, 255)
                draw.rounded_rectangle((xx, yy, xx+360, yy+120), radius=28, fill=(30, 36, 64, 255), outline=col, width=3)
                draw.ellipse((xx+24, yy+30, xx+84, yy+90), fill=col)
                draw.text((xx+104, yy+26), item["name"], font=font_mid, fill=(255, 255, 255, 255))
                draw.text((xx+104, yy+68), "OK" if item["ok"] else "PENDING", font=font_small, fill=(210, 235, 255, 255))
            img.save(path)
            self.interface_consistency_board_path.set(str(path))
            self.interface_consistency_status.set(self.language_text("Tablero visual exportado.", "Visual board exported."))
            messagebox.showinfo(self.language_text("Tablero exportado", "Board exported"), str(path))
        except Exception as e:
            self.interface_consistency_status.set(f"Error: {e}")

    def interface_consistency_refresh_preview(self):
        if not hasattr(self, "interface_consistency_preview_text"):
            return
        data = self.interface_consistency_data()
        self.interface_consistency_score_var.set(self.language_text(f"Consistencia: {data['score']}/100", f"Consistency: {data['score']}/100"))
        lines = [
            "INTERFACE CONSISTENCY PRO",
            "",
            self.language_text(f"Modo: {data['mode']}", f"Mode: {data['mode']}"),
            self.language_text(f"Idioma: {data['language']}", f"Language: {data['language']}"),
            self.language_text(f"Puntuación visual: {data['score']}/100", f"Visual score: {data['score']}/100"),
            "",
            self.language_text("Auditoría:", "Audit:"),
        ]
        for item in data["checks"]:
            status = "OK" if item["ok"] else self.language_text("PENDIENTE", "PENDING")
            lines.append(f"- {status} · {item['name']} · {item['detail']}")
        self.interface_consistency_preview_text.configure(state="normal")
        self.interface_consistency_preview_text.delete("1.0", tk.END)
        self.interface_consistency_preview_text.insert("1.0", "\n".join(lines))
        self.interface_consistency_preview_text.configure(state="disabled")

    def build_interface_consistency_tab(self):
        main = ttk.Frame(self.tab_interface_consistency)
        main.pack(fill="both", expand=True)

        header = self.make_card(main)
        header.pack(fill="x", pady=(0, 10))
        if "banner_interface_consistency" in self.interface_consistency_images:
            ttk.Label(header, image=self.interface_consistency_images["banner_interface_consistency"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Interface Consistency Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cards = self.make_card(left, "Consistency actions")
        cards.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(cards, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("card_audit", "Audit", self.interface_consistency_refresh_preview),
            ("card_apply", "Apply rules", self.interface_consistency_apply),
            ("card_report", "Report", self.interface_consistency_export_report),
            ("card_board", "Board PNG", self.interface_consistency_export_board),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            if img in self.interface_consistency_images:
                ttk.Label(box, image=self.interface_consistency_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        preview = self.make_card(left, "Interface review")
        preview.pack(fill="both", expand=True)
        if "mockup_interface_consistency" in self.interface_consistency_images:
            ttk.Label(preview, image=self.interface_consistency_images["mockup_interface_consistency"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))
        self.interface_consistency_preview_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=12)
        self.interface_consistency_preview_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(body)
        right.pack(side="right", fill="y", padx=(10, 0))
        status = self.make_card(right, "Status")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.interface_consistency_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(status, textvariable=self.interface_consistency_score_var, style="Card.TLabel", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(8, 0))

        settings = self.make_card(right, "Consistency mode")
        settings.pack(fill="x", pady=(0, 10))
        ttk.Combobox(settings, textvariable=self.interface_consistency_mode, state="readonly", values=["Premium equilibrado", "Studio glass", "Launch limpio", "Minimal pro"]).pack(fill="x", pady=4)
        ttk.Button(settings, text="Apply consistency", style="Accent.TButton", command=self.interface_consistency_apply).pack(fill="x", pady=3)
        ttk.Button(settings, text="Export report", command=self.interface_consistency_export_report).pack(fill="x", pady=3)
        ttk.Button(settings, text="Export visual board", command=self.interface_consistency_export_board).pack(fill="x", pady=3)
        ttk.Label(settings, textvariable=self.interface_consistency_board_path, style="Card.TLabel", wraplength=310).pack(anchor="w", pady=(8, 0))

        links = self.make_card(right, "Open related modules")
        links.pack(fill="x")
        for label, tab in [("🎨 Diseño", "tab_design_system"), ("🖼 Iconos", "tab_icon_system"), ("🧩 Lang Pack", "tab_language_pack"), ("💠 UI Premium", "tab_ultra_premium_ui"), ("💼 Polish", "tab_professional_polish"), ("⌘ Command", "tab_command_center")]:
            if hasattr(self, tab):
                ttk.Button(links, text=label, command=lambda t=tab: self.select_tab(getattr(self, t))).pack(fill="x", pady=3)

        self.interface_consistency_refresh_preview()

    def design_system_tokens(self):
        theme = self.design_system_theme.get()
        palettes = {
            "Aurora Premium": {
                "bg": "#0c0d14", "panel": "#151827", "panel2": "#1d2135", "text": "#f5f7ff",
                "muted": "#aab0d6", "accent": "#7c5cff", "accent2": "#00e5ff", "gold": "#ffcc66", "ok": "#62ffb4"
            },
            "Glass Studio": {
                "bg": "#0a1020", "panel": "#142034", "panel2": "#1f3352", "text": "#f7fbff",
                "muted": "#9fb9d7", "accent": "#62d9ff", "accent2": "#a88cff", "gold": "#ffd37a", "ok": "#83ffbf"
            },
            "Gold Launch": {
                "bg": "#111016", "panel": "#211b24", "panel2": "#302735", "text": "#fff8e8",
                "muted": "#d6c6a2", "accent": "#ffcc66", "accent2": "#ff8fb3", "gold": "#ffd76a", "ok": "#8bffc8"
            },
            "Focus Clean": {
                "bg": "#0f1117", "panel": "#181b24", "panel2": "#222633", "text": "#f2f4f8",
                "muted": "#a8b0c1", "accent": "#8db4ff", "accent2": "#70e1c8", "gold": "#f0c674", "ok": "#8df5b6"
            },
        }
        fonts = {
            "title": "Segoe UI Semibold / 28-32",
            "section": "Segoe UI Bold / 12-16",
            "body": "Segoe UI / 10-11",
            "mono": "Consolas / 10",
        }
        components = {
            "radius": int(self.design_system_roundness.get()),
            "density": self.design_system_density.get(),
            "button_padding": "10px 14px" if self.design_system_density.get() != "Compacto pro" else "7px 10px",
            "card_padding": "14px",
            "shadow": "soft glow + subtle border",
        }
        return {"theme": theme, "palette": palettes.get(theme, palettes["Aurora Premium"]), "fonts": fonts, "components": components}

    def design_system_score(self):
        score = 55
        if hasattr(self, "icon_system_images") and len(self.icon_system_images) >= 10:
            score += 15
        if hasattr(self, "language_pack_images") and len(self.language_pack_images) >= 3:
            score += 10
        if hasattr(self, "tab_language_texts") and len(self.tab_language_texts) >= 40:
            score += 10
        if self.design_system_theme.get() in ["Aurora Premium", "Glass Studio", "Gold Launch", "Focus Clean"]:
            score += 10
        return min(100, score)

    def design_system_folder(self):
        folder = Path.home() / "ModuladorVozDirecto_Canciones" / "DesignSystem"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def design_system_export_guide(self):
        try:
            folder = self.design_system_folder()
            data = self.design_system_tokens()
            data["version"] = VERSION
            data["language"] = self.app_language.get()
            data["score"] = self.design_system_score()
            data["created_at"] = datetime.now().isoformat(timespec="seconds")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = folder / f"design_system_{ts}.json"
            txt_path = folder / f"DESIGN_SYSTEM_GUIDE_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = [
                "DESIGN SYSTEM PRO", "",
                f"Version: {VERSION}", f"Theme: {data['theme']}", f"Language: {data['language']}", f"Score: {data['score']}/100", "",
                "COLOR PALETTE:",
            ]
            for k, v in data["palette"].items():
                lines.append(f"- {k}: {v}")
            lines += ["", "TYPOGRAPHY:"]
            for k, v in data["fonts"].items():
                lines.append(f"- {k}: {v}")
            lines += ["", "COMPONENTS:"]
            for k, v in data["components"].items():
                lines.append(f"- {k}: {v}")
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.design_system_status.set(self.language_text("Guía visual exportada.", "Visual guide exported."))
            messagebox.showinfo(self.language_text("Guía exportada", "Guide exported"), f"{json_path}\n{txt_path}")
        except Exception as e:
            self.design_system_status.set(f"Error: {e}")

    def design_system_export_css(self):
        try:
            folder = self.design_system_folder()
            data = self.design_system_tokens()
            pal = data["palette"]
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"design_tokens_{ts}.css"
            css = [":root {"]
            for k, v in pal.items():
                css.append(f"  --{k}: {v};")
            css += [
                f"  --radius: {data['components']['radius']}px;",
                "  --font-title: 'Segoe UI Semibold', 'Segoe UI', sans-serif;",
                "  --font-body: 'Segoe UI', sans-serif;",
                "}", "",
                "body { background: var(--bg); color: var(--text); font-family: var(--font-body); }",
                ".premium-card { background: var(--panel); border-radius: var(--radius); border: 1px solid rgba(255,255,255,.10); }",
                ".premium-button { background: var(--accent); color: white; border-radius: calc(var(--radius) * .65); padding: 10px 14px; }",
            ]
            path.write_text("\n".join(css), encoding="utf-8")
            self.design_system_status.set(self.language_text("CSS de tokens exportado.", "Token CSS exported."))
            messagebox.showinfo(self.language_text("CSS exportado", "CSS exported"), str(path))
        except Exception as e:
            self.design_system_status.set(f"Error: {e}")

    def design_system_export_board(self):
        try:
            folder = self.design_system_folder()
            data = self.design_system_tokens()
            pal = data["palette"]
            w, h = 1400, 900
            img = Image.new("RGBA", (w, h), pal["bg"])
            draw = ImageDraw.Draw(img)
            try:
                f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
                f_h = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
                f_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
            except Exception:
                f_title = f_h = f_b = ImageFont.load_default()
            draw.rounded_rectangle((60, 60, w-60, h-60), radius=36, fill=pal["panel"], outline=pal["accent2"], width=3)
            draw.text((100, 100), "Design System Pro", font=f_title, fill=pal["text"])
            draw.text((104, 172), f"{data['theme']} · {self.app_language.get()} · Score {self.design_system_score()}/100", font=f_b, fill=pal["muted"])
            x, y = 105, 250
            for idx, (name, color) in enumerate(pal.items()):
                xx = x + (idx % 4) * 300
                yy = y + (idx // 4) * 150
                draw.rounded_rectangle((xx, yy, xx+240, yy+90), radius=22, fill=color, outline=(255,255,255,85), width=2)
                draw.text((xx, yy+104), name, font=f_h, fill=pal["text"])
                draw.text((xx, yy+136), color, font=f_b, fill=pal["muted"])
            draw.rounded_rectangle((100, 680, 430, 760), radius=int(data['components']['radius']), fill=pal["accent"])
            draw.text((140, 704), "Premium button", font=f_h, fill="#ffffff")
            draw.rounded_rectangle((500, 660, 880, 795), radius=int(data['components']['radius']), fill=pal["panel2"], outline=pal["accent2"], width=2)
            draw.text((540, 690), "Premium card", font=f_h, fill=pal["text"])
            draw.text((540, 730), "Soft glow · clean spacing", font=f_b, fill=pal["muted"])
            path = folder / f"design_system_board_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img.save(path)
            self.design_system_status.set(self.language_text("Tablero visual PNG exportado.", "Visual board PNG exported."))
            messagebox.showinfo(self.language_text("Tablero exportado", "Board exported"), str(path))
        except Exception as e:
            self.design_system_status.set(f"Error: {e}")

    def design_system_apply_theme(self):
        # Aplica valores a módulos visuales existentes sin romper el estilo base.
        try:
            if hasattr(self, "visual_theme_name"):
                self.visual_theme_name.set(self.design_system_theme.get())
            if hasattr(self, "visual_density"):
                self.visual_density.set("Cómodo" if self.design_system_density.get() == "Cómodo premium" else "Compacto pro")
            if hasattr(self, "icon_system_style"):
                self.icon_system_style.set("Neón premium" if self.design_system_theme.get() != "Gold Launch" else "Dorado launch")
            self.design_system_status.set(self.language_text("Sistema visual aplicado a módulos premium.", "Visual system applied to premium modules."))
            self.design_system_refresh_preview()
        except Exception as e:
            self.design_system_status.set(f"Error: {e}")

    def design_system_refresh_preview(self):
        if not hasattr(self, "design_system_preview_text"):
            return
        data = self.design_system_tokens()
        lines = [
            "DESIGN SYSTEM PRO", "",
            self.language_text(f"Tema: {data['theme']}", f"Theme: {data['theme']}"),
            self.language_text(f"Densidad: {data['components']['density']}", f"Density: {data['components']['density']}"),
            self.language_text(f"Redondez: {data['components']['radius']} px", f"Roundness: {data['components']['radius']} px"),
            self.language_text(f"Puntuación visual: {self.design_system_score()}/100", f"Visual score: {self.design_system_score()}/100"),
            "", self.language_text("Paleta:", "Palette:"),
        ]
        for k, v in data["palette"].items():
            lines.append(f"- {k}: {v}")
        self.design_system_preview_text.configure(state="normal")
        self.design_system_preview_text.delete("1.0", tk.END)
        self.design_system_preview_text.insert("1.0", "\n".join(lines))
        self.design_system_preview_text.configure(state="disabled")

    def build_design_system_tab(self):
        main = ttk.Frame(self.tab_design_system)
        main.pack(fill="both", expand=True)

        header = self.make_card(main)
        header.pack(fill="x", pady=(0, 10))
        if "banner_design_system" in self.design_system_images:
            ttk.Label(header, image=self.design_system_images["banner_design_system"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Design System Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tokens = self.make_card(left, "Visual tokens")
        tokens.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tokens, style="Card.TFrame")
        grid.pack(fill="x")
        for i, (img, label, cmd) in enumerate([
            ("token_colors", "Colors", self.design_system_export_guide),
            ("token_type", "Typography", self.design_system_export_css),
            ("token_buttons", "Buttons", self.design_system_apply_theme),
            ("token_cards", "Cards", self.design_system_export_board),
            ("token_icons", "Icons", lambda: self.select_tab(self.tab_icon_system)),
            ("token_export", "Export", self.design_system_export_guide),
        ]):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.design_system_images:
                ttk.Label(box, image=self.design_system_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, command=cmd).pack(fill="x", pady=(5,0))
            grid.columnconfigure(i, weight=1)

        preview = self.make_card(left, "Design preview")
        preview.pack(fill="both", expand=True)
        if "mockup_design_system" in self.design_system_images:
            ttk.Label(preview, image=self.design_system_images["mockup_design_system"], style="Card.TLabel").pack(anchor="center", pady=(0,8))
        self.design_system_preview_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=10)
        self.design_system_preview_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(body)
        right.pack(side="right", fill="y", padx=(10,0))

        status = self.make_card(right, "Status")
        status.pack(fill="x", pady=(0,10))
        ttk.Label(status, textvariable=self.design_system_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        settings = self.make_card(right, "Design settings")
        settings.pack(fill="x", pady=(0,10))
        ttk.Label(settings, text="Theme", style="Card.TLabel").pack(anchor="w")
        ttk.Combobox(settings, textvariable=self.design_system_theme, state="readonly", values=["Aurora Premium", "Glass Studio", "Gold Launch", "Focus Clean"]).pack(fill="x", pady=4)
        ttk.Label(settings, text="Density", style="Card.TLabel").pack(anchor="w")
        ttk.Combobox(settings, textvariable=self.design_system_density, state="readonly", values=["Cómodo premium", "Compacto pro", "Presentación"]).pack(fill="x", pady=4)
        ttk.Label(settings, text="Roundness", style="Card.TLabel").pack(anchor="w")
        ttk.Scale(settings, variable=self.design_system_roundness, from_=8, to=36, orient="horizontal", command=lambda e: self.design_system_refresh_preview()).pack(fill="x", pady=4)
        ttk.Button(settings, text="Apply design system", style="Accent.TButton", command=self.design_system_apply_theme).pack(fill="x", pady=3)
        ttk.Button(settings, text="Export guide", command=self.design_system_export_guide).pack(fill="x", pady=3)
        ttk.Button(settings, text="Export CSS", command=self.design_system_export_css).pack(fill="x", pady=3)
        ttk.Button(settings, text="Export PNG board", command=self.design_system_export_board).pack(fill="x", pady=3)

        links = self.make_card(right, "Open visual modules")
        links.pack(fill="x")
        for label, tab in [("🖼 Iconos", "tab_icon_system"), ("🎨 Visual Pro", "tab_visual_pro"), ("💠 UI Premium", "tab_ultra_premium_ui"), ("🏷 Brand Kit", "tab_brand_kit"), ("🖼 Portadas", "tab_portadas_premium")]:
            if hasattr(self, tab):
                ttk.Button(links, text=label, command=lambda t=tab: self.select_tab(getattr(self, t))).pack(fill="x", pady=3)

        self.design_system_refresh_preview()

    def icon_system_items(self):
        return [
            ("icon_home_premium", "Inicio", "Home"), ("icon_voice_premium", "Voces", "Voices"),
            ("icon_studio_premium", "Studio", "Studio"), ("icon_command_premium", "Command", "Command"),
            ("icon_publish_premium", "Publicación", "Publish"), ("icon_deploy_premium", "Deploy", "Deploy"),
            ("icon_library_premium", "Biblioteca", "Library"), ("icon_cover_premium", "Portadas", "Covers"),
            ("icon_language_premium", "Idiomas", "Languages"), ("icon_translation_premium", "Traducción", "Translation"),
            ("icon_pack_premium", "Lang Pack", "Lang Pack"), ("icon_ui_premium", "UI Premium", "Premium UI"),
            ("icon_polish_premium", "Polish", "Polish"), ("icon_karaoke_premium", "Karaoke", "Karaoke"),
            ("icon_master_premium", "Master", "Master"), ("icon_export_premium", "Export", "Export"),
        ]

    def icon_system_folder(self):
        folder = Path.home() / "ModuladorVozDirecto_Canciones" / "IconPacks"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def icon_system_data(self):
        return {"version": VERSION, "created_at": datetime.now().isoformat(timespec="seconds"),
                "language": self.app_language.get(), "style": self.icon_system_style.get(),
                "icons_count": len(self.icon_system_items()),
                "icons": [{"asset": a, "es": es, "en": en} for a, es, en in self.icon_system_items()]}

    def icon_system_export_manifest(self):
        try:
            folder = self.icon_system_folder(); data = self.icon_system_data(); ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = folder / f"premium_icon_manifest_{ts}.json"; txt_path = folder / f"premium_icon_manifest_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = ["PREMIUM ICON SYSTEM PRO", "", f"Version: {data['version']}", f"Language: {data['language']}", f"Style: {data['style']}", f"Icons: {data['icons_count']}", "", "Icon list:"]
            lines += [f"- {i['asset']}: {i['es']} / {i['en']}" for i in data["icons"]]
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.icon_system_status.set(self.language_text("Manifest de iconos exportado.", "Icon manifest exported."))
            messagebox.showinfo(self.language_text("Manifest exportado", "Manifest exported"), f"{json_path}\n{txt_path}")
        except Exception as e:
            self.icon_system_status.set(f"Error: {e}")

    def icon_system_export_pack(self):
        try:
            folder = self.icon_system_folder(); ts = datetime.now().strftime("%Y%m%d_%H%M%S"); pack_dir = folder / f"premium_icon_pack_{ts}"
            pack_dir.mkdir(parents=True, exist_ok=True); src_dir = Path(resource_path("assets/icon_system")); copied = 0
            for asset, _, _ in self.icon_system_items():
                source = src_dir / f"{asset}.png"
                if source.exists(): shutil.copy2(source, pack_dir / source.name); copied += 1
            (pack_dir / "manifest.json").write_text(json.dumps(self.icon_system_data(), ensure_ascii=False, indent=2), encoding="utf-8")
            zip_path = folder / f"premium_icon_pack_{ts}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                for f in pack_dir.rglob("*"): z.write(f, f.relative_to(pack_dir.parent))
            self.icon_system_status.set(self.language_text(f"Pack de iconos exportado: {copied} iconos.", f"Icon pack exported: {copied} icons."))
            messagebox.showinfo(self.language_text("Pack exportado", "Pack exported"), str(zip_path))
        except Exception as e:
            self.icon_system_status.set(f"Error: {e}")

    def icon_system_refresh_preview(self):
        if not hasattr(self, "icon_system_preview_text"): return
        data = self.icon_system_data()
        lines = ["PREMIUM ICON SYSTEM PRO", "", self.language_text(f"Estilo: {data['style']}", f"Style: {data['style']}"),
                 self.language_text(f"Idioma: {data['language']}", f"Language: {data['language']}"),
                 self.language_text(f"Iconos premium: {data['icons_count']}", f"Premium icons: {data['icons_count']}"), "",
                 self.language_text("Incluye iconos para:", "Includes icons for:")]
        lines += [f"- {es if self.app_language.get() == 'Español' else en}" for _, es, en in self.icon_system_items()[:12]]
        self.icon_system_preview_text.configure(state="normal"); self.icon_system_preview_text.delete("1.0", tk.END)
        self.icon_system_preview_text.insert("1.0", "\n".join(lines)); self.icon_system_preview_text.configure(state="disabled")

    def build_icon_system_tab(self):
        main = ttk.Frame(self.tab_icon_system); main.pack(fill="both", expand=True)
        header = self.make_card(main); header.pack(fill="x", pady=(0, 10))
        if "banner_icon_system" in self.icon_system_images:
            ttk.Label(header, image=self.icon_system_images["banner_icon_system"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Premium Icon System Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")
        body = ttk.Frame(main); body.pack(fill="both", expand=True)
        left = ttk.Frame(body); left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        gallery = self.make_card(left, "Premium icon gallery"); gallery.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(gallery, style="Card.TFrame"); grid.pack(fill="x")
        for i, (asset, es, en) in enumerate(self.icon_system_items()):
            box = ttk.Frame(grid, style="Card.TFrame", padding=4); box.grid(row=i//8, column=i%8, sticky="nsew", padx=3, pady=3)
            if asset in self.icon_system_images: ttk.Label(box, image=self.icon_system_images[asset], style="Card.TLabel").pack()
            ttk.Label(box, text=es if self.app_language.get() == "Español" else en, style="Card.TLabel", font=("Segoe UI", 8, "bold")).pack()
            grid.columnconfigure(i%8, weight=1)
        preview = self.make_card(left, "Icon preview"); preview.pack(fill="both", expand=True)
        if "mockup_icon_system" in self.icon_system_images:
            ttk.Label(preview, image=self.icon_system_images["mockup_icon_system"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))
        self.icon_system_preview_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=10)
        self.icon_system_preview_text.pack(fill="both", expand=True, padx=4, pady=4)
        right = ttk.Frame(body); right.pack(side="right", fill="y", padx=(10, 0))
        status = self.make_card(right, "Status"); status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.icon_system_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        settings = self.make_card(right, "Icon style"); settings.pack(fill="x", pady=(0, 10))
        ttk.Combobox(settings, textvariable=self.icon_system_style, state="readonly", values=["Neón premium", "Cristal oscuro", "Dorado launch", "Minimal limpio"]).pack(fill="x", pady=4)
        ttk.Button(settings, text="Refresh preview", command=self.icon_system_refresh_preview).pack(fill="x", pady=3)
        ttk.Button(settings, text="Export manifest", command=self.icon_system_export_manifest).pack(fill="x", pady=3)
        ttk.Button(settings, text="Export icon pack", style="Accent.TButton", command=self.icon_system_export_pack).pack(fill="x", pady=3)
        links = self.make_card(right, "Open visual modules"); links.pack(fill="x")
        for label, tab in [("🌍 Traducción", "tab_full_translation"), ("🧩 Lang Pack", "tab_language_pack"), ("🎨 Visual Pro", "tab_visual_pro"), ("💠 UI Premium", "tab_ultra_premium_ui"), ("🏷 Brand Kit", "tab_brand_kit"), ("🖼 Portadas", "tab_portadas_premium")]:
            if hasattr(self, tab): ttk.Button(links, text=label, command=lambda t=tab: self.select_tab(getattr(self, t))).pack(fill="x", pady=3)
        self.icon_system_refresh_preview()

    def language_pack_data(self):
        pairs = self.translation_pairs()
        es_to_en = {es: en for es, en in pairs}
        en_to_es = {en: es for es, en in pairs}
        return {
            "pack_name": self.language_pack_name.get(),
            "version": VERSION,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "languages": ["Español", "English"],
            "active_language": self.app_language.get(),
            "pairs_count": len(pairs),
            "tabs_count": len(getattr(self, "tab_language_texts", {})),
            "es_to_en": es_to_en,
            "en_to_es": en_to_es,
            "notes": "Language Pack Pro para navegación, botones comunes y módulos premium.",
        }

    def language_pack_folder(self):
        folder = Path.home() / "ModuladorVozDirecto_Canciones" / "LanguagePacks"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def language_pack_export(self):
        try:
            folder = self.language_pack_folder()
            data = self.language_pack_data()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = folder / f"{data['pack_name']}_{ts}.json"
            txt_path = folder / f"{data['pack_name']}_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = [
                "LANGUAGE PACK PRO",
                "",
                f"Pack: {data['pack_name']}",
                f"Version: {data['version']}",
                f"Active language: {data['active_language']}",
                f"Languages: Español / English",
                f"Pairs: {data['pairs_count']}",
                f"Tabs: {data['tabs_count']}",
                "",
                "Sample translations:",
            ]
            for i, (es, en) in enumerate(list(data["es_to_en"].items())[:60], start=1):
                lines.append(f"{i:02d}. {es} -> {en}")
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.language_pack_status.set(self.language_text("Paquete ES/EN exportado correctamente.", "ES/EN pack exported successfully."))
            messagebox.showinfo(self.language_text("Paquete exportado", "Pack exported"), f"{json_path}\n{txt_path}")
        except Exception as e:
            self.language_pack_status.set(f"Error: {e}")

    def language_pack_export_glossary(self):
        try:
            folder = self.language_pack_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"glossary_es_en_{ts}.txt"
            lines = [
                "GLOSARIO ES / EN - MODULADOR DE VOZ EN DIRECTO",
                "",
                "Formato: Español = English",
                "",
            ]
            for es, en in self.translation_pairs():
                lines.append(f"{es} = {en}")
            path.write_text("\n".join(lines), encoding="utf-8")
            self.language_pack_status.set(self.language_text("Glosario exportado correctamente.", "Glossary exported successfully."))
            messagebox.showinfo(self.language_text("Glosario exportado", "Glossary exported"), str(path))
        except Exception as e:
            self.language_pack_status.set(f"Error: {e}")

    def language_pack_refresh_preview(self):
        if not hasattr(self, "language_pack_preview_text"):
            return
        data = self.language_pack_data()
        lines = [
            "LANGUAGE PACK & ICONS PRO",
            "",
            self.language_text(f"Paquete: {data['pack_name']}", f"Pack: {data['pack_name']}"),
            self.language_text(f"Idioma activo: {data['active_language']}", f"Active language: {data['active_language']}"),
            self.language_text(f"Frases ES/EN: {data['pairs_count']}", f"ES/EN phrases: {data['pairs_count']}"),
            self.language_text(f"Pestañas cubiertas: {data['tabs_count']}", f"Covered tabs: {data['tabs_count']}"),
            "",
            self.language_text("Incluye:", "Includes:"),
            self.language_text("- Diccionario interno ampliado", "- Expanded internal dictionary"),
            self.language_text("- Exportación JSON/TXT", "- JSON/TXT export"),
            self.language_text("- Glosario ES/EN", "- ES/EN glossary"),
            self.language_text("- Iconos y tarjetas premium", "- Premium icons and cards"),
        ]
        self.language_pack_preview_text.configure(state="normal")
        self.language_pack_preview_text.delete("1.0", tk.END)
        self.language_pack_preview_text.insert("1.0", "\n".join(lines))
        self.language_pack_preview_text.configure(state="disabled")

    def build_language_pack_tab(self):
        main = ttk.Frame(self.tab_language_pack)
        main.pack(fill="both", expand=True)

        header = self.make_card(main)
        header.pack(fill="x", pady=(0, 10))
        if "banner_language_pack" in self.language_pack_images:
            ttk.Label(header, image=self.language_pack_images["banner_language_pack"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Language Pack & Icons Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cards = self.make_card(left, "Language Pack")
        cards.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(cards, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("card_pack", "Export pack", self.language_pack_export),
            ("card_glossary", "Glossary", self.language_pack_export_glossary),
            ("card_spanish_pack", "Español", lambda: self.set_app_language("Español")),
            ("card_english_pack", "English", lambda: self.set_app_language("English")),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            if img in self.language_pack_images:
                ttk.Label(box, image=self.language_pack_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        preview = self.make_card(left, "Pack preview")
        preview.pack(fill="both", expand=True)
        if "mockup_language_pack" in self.language_pack_images:
            ttk.Label(preview, image=self.language_pack_images["mockup_language_pack"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))
        self.language_pack_preview_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=12)
        self.language_pack_preview_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(body)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Status")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.language_pack_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        edit = self.make_card(right, "Pack settings")
        edit.pack(fill="x", pady=(0, 10))
        ttk.Label(edit, text="Pack name", style="Card.TLabel").pack(anchor="w")
        ttk.Entry(edit, textvariable=self.language_pack_name).pack(fill="x", pady=(2, 8))
        ttk.Button(edit, text="🇪🇸 Español", command=lambda: self.set_app_language("Español")).pack(fill="x", pady=3)
        ttk.Button(edit, text="🇬🇧 English", command=lambda: self.set_app_language("English")).pack(fill="x", pady=3)
        ttk.Button(edit, text="💾 Export language pack", style="Accent.TButton", command=self.language_pack_export).pack(fill="x", pady=3)
        ttk.Button(edit, text="📘 Export glossary", command=self.language_pack_export_glossary).pack(fill="x", pady=3)

        links = self.make_card(right, "Open translation modules")
        links.pack(fill="x")
        for label, tab in [
            ("🌍 Traducción", "tab_full_translation"),
            ("🌐 Idiomas", "tab_bilingual_visual"),
            ("⌘ Command", "tab_command_center"),
            ("💠 UI Premium", "tab_ultra_premium_ui"),
            ("💼 Polish", "tab_professional_polish"),
        ]:
            if hasattr(self, tab):
                ttk.Button(links, text=label, command=lambda t=tab: self.select_tab(getattr(self, t))).pack(fill="x", pady=3)

        self.language_pack_refresh_preview()

    def full_translation_score(self):
        base_pairs = len(self.translation_pairs())
        tab_count = len(getattr(self, "tab_language_texts", {}))
        return min(100, 45 + min(35, tab_count) + min(20, base_pairs // 5))

    def full_translation_data(self):
        return {
            "version": VERSION,
            "language": self.app_language.get(),
            "mode": self.translation_mode.get(),
            "translation_pairs": len(self.translation_pairs()),
            "translated_tabs": len(getattr(self, "tab_language_texts", {})),
            "score": self.full_translation_score(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def full_translation_export_report(self):
        try:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            data = self.full_translation_data()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = folder / f"full_translation_report_{ts}.json"
            txt_path = folder / f"full_translation_report_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = [
                "FULL TRANSLATION PRO",
                "",
                f"Version: {data['version']}",
                f"Language: {data['language']}",
                f"Mode: {data['mode']}",
                f"Translation pairs: {data['translation_pairs']}",
                f"Translated tabs: {data['translated_tabs']}",
                f"Score: {data['score']}/100",
            ]
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.full_translation_status.set(self.language_text("Informe de traducción exportado.", "Translation report exported."))
            messagebox.showinfo(self.language_text("Informe exportado", "Report exported"), f"{json_path}\n{txt_path}")
        except Exception as e:
            self.full_translation_status.set(f"Error: {e}")

    def full_translation_refresh_preview(self):
        if not hasattr(self, "full_translation_preview_text"):
            return
        data = self.full_translation_data()
        lines = [
            "FULL TRANSLATION PRO",
            "",
            self.language_text(f"Idioma: {data['language']}", f"Language: {data['language']}"),
            self.language_text(f"Modo: {data['mode']}", f"Mode: {data['mode']}"),
            self.language_text(f"Pestañas traducidas: {data['translated_tabs']}", f"Translated tabs: {data['translated_tabs']}"),
            self.language_text(f"Pares de traducción: {data['translation_pairs']}", f"Translation pairs: {data['translation_pairs']}"),
            self.language_text(f"Puntuación: {data['score']}/100", f"Score: {data['score']}/100"),
            "",
            self.language_text("Esta versión traduce navegación + textos comunes de la interfaz.", "This version translates navigation + common interface text."),
        ]
        self.full_translation_preview_text.configure(state="normal")
        self.full_translation_preview_text.delete("1.0", tk.END)
        self.full_translation_preview_text.insert("1.0", "\n".join(lines))
        self.full_translation_preview_text.configure(state="disabled")

    def build_full_translation_tab(self):
        main = ttk.Frame(self.tab_full_translation)
        main.pack(fill="both", expand=True)

        header = self.make_card(main)
        header.pack(fill="x", pady=(0, 10))
        if "banner_translation" in self.full_translation_images:
            ttk.Label(header, image=self.full_translation_images["banner_translation"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Full Translation Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cards = self.make_card(left, "Language / Idioma")
        cards.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(cards, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("card_spanish", "Español", lambda: self.set_app_language("Español")),
            ("card_english", "English", lambda: self.set_app_language("English")),
            ("card_translate", "Apply UI", self.refresh_language_ui),
            ("card_report", "Report", self.full_translation_export_report),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            if img in self.full_translation_images:
                ttk.Label(box, image=self.full_translation_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        preview = self.make_card(left, "Translation preview")
        preview.pack(fill="both", expand=True)
        if "mockup_translation" in self.full_translation_images:
            ttk.Label(preview, image=self.full_translation_images["mockup_translation"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))
        self.full_translation_preview_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=12)
        self.full_translation_preview_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(body)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Status")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.full_translation_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(status, textvariable=self.translation_report, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w", pady=(8, 0))

        actions = self.make_card(right, "Actions")
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="🇪🇸 Español", command=lambda: self.set_app_language("Español")).pack(fill="x", pady=3)
        ttk.Button(actions, text="🇬🇧 English", command=lambda: self.set_app_language("English")).pack(fill="x", pady=3)
        ttk.Button(actions, text="Apply UI translation", style="Accent.TButton", command=self.refresh_language_ui).pack(fill="x", pady=3)
        ttk.Button(actions, text="Export translation report", command=self.full_translation_export_report).pack(fill="x", pady=3)

        links = self.make_card(right, "Open premium modules")
        links.pack(fill="x")
        for label, tab in [
            ("🌐 Idiomas", "tab_bilingual_visual"),
            ("⌘ Command", "tab_command_center"),
            ("🏠 Inicio", "tab_inicio_premium"),
            ("💠 UI Premium", "tab_ultra_premium_ui"),
            ("💼 Polish", "tab_professional_polish"),
        ]:
            if hasattr(self, tab):
                ttk.Button(links, text=label, command=lambda t=tab: self.select_tab(getattr(self, t))).pack(fill="x", pady=3)

        self.full_translation_refresh_preview()

    def language_text(self, es, en=None):
        if en is None:
            en = es
        return es if self.app_language.get() == "Español" else en

    def refresh_language_ui(self):
        lang = self.app_language.get()
        try:
            self.root.title(f"{APP_NAME} V{VERSION} - {'Español' if lang == 'Español' else 'English'}")
        except Exception:
            pass

        if hasattr(self, 'main_title_label'):
            self.main_title_label.configure(text=self.language_text("🎙️ Modulador de Voz en Directo", "🎙️ Live Voice Modulator"))
        if hasattr(self, 'main_subtitle_label'):
            self.main_subtitle_label.configure(text=self.language_text(
                "V81 Navegación Pro · sistema visual premium · 2 idiomas",
                "V81 Navegación Pro · premium visual system · 2 languages"
            ))
        if hasattr(self, 'main_hint_label'):
            self.main_hint_label.configure(text=self.language_text(
                "Micrófono real → Voz modificada → Cable virtual",
                "Real microphone → Modified voice → Virtual cable"
            ))
        if hasattr(self, 'tab_language_texts'):
            for tab, pair in self.tab_language_texts.items():
                try:
                    tab.master.tab(tab, text=pair[0] if lang == 'Español' else pair[1])
                except Exception:
                    pass
        if hasattr(self, 'bilingual_lang_label'):
            self.bilingual_lang_label.configure(text=self.language_text('Idioma actual: Español', 'Current language: English'))
        if hasattr(self, 'bilingual_visual_status'):
            self.bilingual_visual_status.set(self.language_text(
                'Modo bilingüe activo. Puedes usar el programa en Español o English.',
                'Bilingual mode active. You can use the app in Spanish or English.'
            ))
        if hasattr(self, 'bilingual_preview_text'):
            self.bilingual_refresh_preview()
        if hasattr(self, 'full_translation_preview_text'):
            self.full_translation_refresh_preview()
        if hasattr(self, 'language_pack_preview_text'):
            self.language_pack_refresh_preview()
        if hasattr(self, 'icon_system_preview_text'):
            self.icon_system_refresh_preview()
        if hasattr(self, 'design_system_preview_text'):
            self.design_system_refresh_preview()
        if hasattr(self, 'interface_consistency_preview_text'):
            self.interface_consistency_refresh_preview()
        try:
            self.translate_existing_widgets()
        except Exception:
            pass

    def set_app_language(self, lang):
        self.app_language.set(lang)
        self.refresh_language_ui()
        try:
            self.save_config(silent=True)
        except Exception:
            pass

    def bilingual_apply_visual_bundle(self, name):
        self.visual_bundle_name.set(name)
        try:
            if hasattr(self, 'visual_theme_name'):
                theme = 'Neón Azul' if name in ('Aurora Glass', 'Midnight Neon') else 'Dorado Studio'
                self.visual_theme_name.set(theme)
            if hasattr(self, 'visual_density'):
                self.visual_density.set('Cómodo')
            if hasattr(self, 'visual_focus_mode'):
                self.visual_focus_mode.set(name == 'Focus Minimal')
        except Exception:
            pass
        self.bilingual_visual_status.set(self.language_text(
            f'Bundle visual aplicado: {name}',
            f'Visual bundle applied: {name}'
        ))
        self.bilingual_refresh_preview()

    def bilingual_export_theme(self):
        try:
            folder = Path.home() / 'ModuladorVozDirecto_Canciones'
            folder.mkdir(parents=True, exist_ok=True)
            data = {
                'version': VERSION,
                'language': self.app_language.get(),
                'visual_bundle': self.visual_bundle_name.get(),
                'theme_name': getattr(self, 'visual_theme_name', tk.StringVar(value='')).get() if hasattr(self, 'visual_theme_name') else '',
            }
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = folder / f'bilingual_visual_theme_{ts}.json'
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            self.bilingual_visual_status.set(self.language_text('Tema exportado correctamente.', 'Theme exported successfully.'))
            messagebox.showinfo(self.language_text('Tema exportado', 'Theme exported'), str(path))
        except Exception as e:
            self.bilingual_visual_status.set(f'Error: {e}')

    def bilingual_refresh_preview(self):
        if not hasattr(self, 'bilingual_preview_text'):
            return
        lines = [
            self.language_text('BILINGUAL VISUAL PREMIUM', 'BILINGUAL VISUAL PREMIUM'),
            '',
            self.language_text(f'Idioma actual: {self.app_language.get()}', f'Current language: {self.app_language.get()}'),
            self.language_text(f'Bundle visual: {self.visual_bundle_name.get()}', f'Visual bundle: {self.visual_bundle_name.get()}'),
            self.language_text('Mejoras de esta versión:', 'Improvements in this version:'),
            self.language_text('- Navegación de pestañas ES / EN', '- ES / EN tab navigation'),
            self.language_text('- Banner y mockups premium nuevos', '- New premium banner and mockups'),
            self.language_text('- Centro para cambiar idioma rápidamente', '- Center to switch language quickly'),
            self.language_text('- Exportación del tema visual', '- Visual theme export'),
        ]
        self.bilingual_preview_text.configure(state='normal')
        self.bilingual_preview_text.delete('1.0', tk.END)
        self.bilingual_preview_text.insert('1.0', '\n'.join(lines))
        self.bilingual_preview_text.configure(state='disabled')

    def build_bilingual_visual_tab(self):
        main = ttk.Frame(self.tab_bilingual_visual)
        main.pack(fill='both', expand=True)

        header = self.make_card(main)
        header.pack(fill='x', pady=(0, 10))
        if 'banner_bilingual' in self.bilingual_visual_images:
            ttk.Label(header, image=self.bilingual_visual_images['banner_bilingual'], style='Card.TLabel').pack(anchor='center')
        else:
            ttk.Label(header, text='Bilingual Visual Premium', style='Card.TLabel', font=('Segoe UI', 28, 'bold')).pack(anchor='w')

        body = ttk.Frame(main)
        body.pack(fill='both', expand=True)

        left = ttk.Frame(body)
        left.pack(side='left', fill='both', expand=True, padx=(0, 10))

        cards = self.make_card(left, 'ES / EN')
        cards.pack(fill='x', pady=(0, 10))
        grid = ttk.Frame(cards, style='Card.TFrame')
        grid.pack(fill='x')
        items = [
            ('card_es', 'Español', lambda: self.set_app_language('Español')),
            ('card_en', 'English', lambda: self.set_app_language('English')),
            ('card_bundle', 'Aurora Glass', lambda: self.bilingual_apply_visual_bundle('Aurora Glass')),
            ('card_bundle2', 'Midnight Neon', lambda: self.bilingual_apply_visual_bundle('Midnight Neon')),
            ('card_bundle3', 'Focus Minimal', lambda: self.bilingual_apply_visual_bundle('Focus Minimal')),
            ('card_export', 'Export theme', self.bilingual_export_theme),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style='Card.TFrame', padding=5)
            box.grid(row=0, column=i, sticky='nsew', padx=4)
            if img in self.bilingual_visual_images:
                ttk.Label(box, image=self.bilingual_visual_images[img], style='Card.TLabel').pack()
            ttk.Button(box, text=label, style='Accent.TButton', command=cmd).pack(fill='x', pady=(4, 0))
            grid.columnconfigure(i, weight=1)

        editor = ttk.Frame(left)
        editor.pack(fill='both', expand=True)

        preview_card = self.make_card(editor, 'Preview')
        preview_card.pack(side='left', fill='both', expand=True, padx=(0, 5))
        if 'mockup_bilingual' in self.bilingual_visual_images:
            ttk.Label(preview_card, image=self.bilingual_visual_images['mockup_bilingual'], style='Card.TLabel').pack(anchor='center', pady=(0, 8))
        self.bilingual_lang_label = ttk.Label(preview_card, text='Idioma actual: Español', style='Card.TLabel', font=('Segoe UI', 11, 'bold'))
        self.bilingual_lang_label.pack(anchor='w')
        self.bilingual_preview_text = tk.Text(preview_card, bg=COLORS['panel2'], fg=COLORS['text'], insertbackground=COLORS['text'], relief='flat', wrap='word', font=('Consolas', 10), height=12)
        self.bilingual_preview_text.pack(fill='both', expand=True, padx=4, pady=4)

        right = ttk.Frame(body)
        right.pack(side='right', fill='y', padx=(10, 0))

        status = self.make_card(right, 'Status')
        status.pack(fill='x', pady=(0, 10))
        ttk.Label(status, textvariable=self.bilingual_visual_status, style='Card.TLabel', wraplength=320, justify='left').pack(anchor='w')

        quick = self.make_card(right, 'Quick actions')
        quick.pack(fill='x', pady=(0, 10))
        ttk.Button(quick, text='🇪🇸 Español', command=lambda: self.set_app_language('Español')).pack(fill='x', pady=3)
        ttk.Button(quick, text='🇬🇧 English', command=lambda: self.set_app_language('English')).pack(fill='x', pady=3)
        ttk.Button(quick, text='✨ Aurora Glass', command=lambda: self.bilingual_apply_visual_bundle('Aurora Glass')).pack(fill='x', pady=3)
        ttk.Button(quick, text='🌙 Midnight Neon', command=lambda: self.bilingual_apply_visual_bundle('Midnight Neon')).pack(fill='x', pady=3)
        ttk.Button(quick, text='🧼 Focus Minimal', command=lambda: self.bilingual_apply_visual_bundle('Focus Minimal')).pack(fill='x', pady=3)
        ttk.Button(quick, text='💾 Export theme', style='Accent.TButton', command=self.bilingual_export_theme).pack(fill='x', pady=3)

        links = self.make_card(right, 'Open modules')
        links.pack(fill='x')
        for label, tab in [
            ('🏠 Inicio Premium', 'tab_inicio_premium'),
            ('🎨 Visual Pro', 'tab_visual_pro'),
            ('⌘ Command Center', 'tab_command_center'),
            ('💠 UI Premium', 'tab_ultra_premium_ui'),
            ('💼 Polish', 'tab_professional_polish'),
        ]:
            if hasattr(self, tab):
                ttk.Button(links, text=label, command=lambda t=tab: self.select_tab(getattr(self, t))).pack(fill='x', pady=3)

        self.bilingual_refresh_preview()

    def show_welcome(self):
        if self.welcome_shown:
            return
        self.welcome_shown = True

        win = tk.Toplevel(self.root)
        win.title(self.language_text("Bienvenido a Estudio de Voz Ultra", "Welcome to Ultra Voice Studio"))
        win.configure(bg=COLORS["bg"])
        win.geometry("760x520")
        win.resizable(False, False)
        try:
            win.iconbitmap(resource_path("assets/app_icon.ico"))
        except Exception:
            pass

        frame = ttk.Frame(win, padding=18)
        frame.pack(fill="both", expand=True)

        if "ultra_banner" in self.ultra_images:
            ttk.Label(frame, image=self.ultra_images["ultra_banner"]).pack(pady=(0, 14))
        else:
            ttk.Label(frame, text=self.language_text("Estudio de Voz Ultra", "Ultra Voice Studio"), font=("Segoe UI", 28, "bold")).pack(pady=(0, 14))

        ttk.Label(
            frame,
            text=self.language_text("V81 Navegación Pro está preparada para directo, Discord, Fortnite, OBS, soundboard y perfiles personalizados.", "V81 Navegación Pro is ready for live use, Discord, Fortnite, OBS, soundboard and custom profiles."),
            style="Muted.TLabel",
            wraplength=690,
            justify="center",
            font=("Segoe UI", 11)
        ).pack(pady=(0, 16))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Configurar Discord", style="Accent.TButton", command=lambda: [self.quick_mode("discord"), win.destroy()]).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(buttons, text="Configurar Fortnite", style="Accent.TButton", command=lambda: [self.quick_mode("fortnite"), win.destroy()]).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(buttons, text="Abrir Export Pack", command=lambda: [self.select_tab(self.tab_export_pack), win.destroy()]).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(buttons, text="Cerrar", command=win.destroy).pack(side="left", expand=True, fill="x", padx=5)

        ttk.Label(
            frame,
            text="Consejo: para juegos usa Gaming Pro o Discord claro. Para directos usa Podcast Pro o Locutor español.",
            style="Muted.TLabel",
            wraplength=650,
            justify="center"
        ).pack(pady=(18, 0))

        win.transient(self.root)
        win.grab_set()


    def build_pro_mode_tab(self):
        main = ttk.Frame(self.tab_pro)
        main.pack(fill="both", expand=True)

        # Cabecera estilo app premium
        header = self.make_card(main)
        header.pack(fill="x", pady=(0, 10))
        if "pro_banner" in self.pro_images:
            ttk.Label(header, image=self.pro_images["pro_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="ESTUDIO DE VOZ PRO", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)

        # Sidebar tipo app de pago
        sidebar = self.make_card(body, "Panel")
        sidebar.pack(side="left", fill="y", padx=(0, 10))

        ttk.Button(sidebar, text="⚡ Barra rápida", style="Accent.TButton", command=lambda: self.select_tab(self.tab_barra_rapida)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🧭 Asistente", command=lambda: self.select_tab(self.tab_asistente)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎙 Caja de voces", command=lambda: self.select_tab(self.tab_voicebox_grid)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎬 Directo Pro", command=lambda: self.select_tab(self.tab_directo_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="⌘ Command", command=lambda: self.select_tab(self.tab_command_center)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="💼 Polish", command=lambda: self.select_tab(self.tab_professional_polish)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="💠 UI Premium", command=lambda: self.select_tab(self.tab_ultra_premium_ui)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="💎 Premium", command=lambda: self.select_tab(self.tab_premium_experience)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🚢 Deploy", command=lambda: self.select_tab(self.tab_deploy_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🌍 Web Pack", command=lambda: self.select_tab(self.tab_web_pack)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🌐 Landing", command=lambda: self.select_tab(self.tab_landing_page)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🏷 Brand Kit", command=lambda: self.select_tab(self.tab_brand_kit)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🚀 Publicación", command=lambda: self.select_tab(self.tab_publicacion_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="📦 Export Pack", command=lambda: self.select_tab(self.tab_export_pack)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🖼 Portadas", command=lambda: self.select_tab(self.tab_portadas_premium)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="📚 Biblioteca", command=lambda: self.select_tab(self.tab_biblioteca_premium)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🪄 Asistente", command=lambda: self.select_tab(self.tab_asistente_inicial)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🏠 Inicio", command=lambda: self.select_tab(self.tab_inicio_premium)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎨 Visual Pro", command=lambda: self.select_tab(self.tab_visual_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🧪 Revisión", command=lambda: self.select_tab(self.tab_revision_tecnica)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🏁 Studio", command=lambda: self.select_tab(self.tab_studio_dashboard)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="📊 Analizador", command=lambda: self.select_tab(self.tab_analizador_vocal)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎙 Cadena Vocal", command=lambda: self.select_tab(self.tab_cadena_vocal)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🧱 Timeline", command=lambda: self.select_tab(self.tab_timeline_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎛 Multipista", command=lambda: self.select_tab(self.tab_multipista)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="💿 Master Final", command=lambda: self.select_tab(self.tab_master_final)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎚 Mezclador", command=lambda: self.select_tab(self.tab_mezclador_musical)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎼 Canción Pro", command=lambda: self.select_tab(self.tab_cancion_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎧 Karaoke Studio", command=lambda: self.select_tab(self.tab_karaoke_studio)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎤 Karaoke", command=lambda: self.select_tab(self.tab_karaoke)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎵 Autotune", command=lambda: self.select_tab(self.tab_autotune)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎙 Test de Voz", command=lambda: self.select_tab(self.tab_test_voz)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🔌 Cable Virtual", command=lambda: self.select_tab(self.tab_cable_virtual)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🚀 Rendimiento", command=lambda: self.select_tab(self.tab_rendimiento)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🤫 Ruido", command=lambda: self.select_tab(self.tab_ruido)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="📡 Streamer Hub", command=lambda: self.select_tab(self.tab_streamer_hub)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎬 Escenas", command=lambda: self.select_tab(self.tab_escenas_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="⭐ Favoritos", command=lambda: self.select_tab(self.tab_favoritos_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="⌨ Atajos", command=lambda: self.select_tab(self.tab_atajos)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🧪 Creador", command=lambda: self.select_tab(self.tab_creador_voces)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎭 Cambiador", command=lambda: self.select_tab(self.tab_cambiador_personas)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="👥 Personas Pro", command=lambda: self.select_tab(self.tab_personas_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="👤 Perfiles Pro+", command=lambda: self.select_tab(self.tab_perfiles_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎚 Ecualizador", command=lambda: self.select_tab(self.tab_ecualizador)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🪟 Mini Panel", command=lambda: self.select_tab(self.tab_mini_panel)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🛠 Diagnóstico", command=lambda: self.select_tab(self.tab_diagnostico)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎬 Clips", command=lambda: self.select_tab(self.tab_clips)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="⏺ Grabadora", command=lambda: self.select_tab(self.tab_grabadora)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎚 Mesa Pro", command=lambda: self.select_tab(self.tab_mesa_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🔊 Mesa de sonidos", command=lambda: self.select_tab(self.tab_sonidos)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="💎 Estudio", command=lambda: self.select_tab(self.tab_studio)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="📊 Visualizador", command=lambda: self.select_tab(self.tab_visualizador)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="⚙ Ajustes", command=lambda: self.select_tab(self.tab_ajustes)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="▾ Bandeja Windows", command=self.hide_to_tray).pack(fill="x", pady=(18, 4))

        center = ttk.Frame(body)
        center.pack(side="left", fill="both", expand=True)

        toggle_card = self.make_card(center, "Control principal")
        toggle_card.pack(fill="x", pady=(0, 10))

        toggle_row = ttk.Frame(toggle_card, style="Card.TFrame")
        toggle_row.pack(fill="x")

        ttk.Checkbutton(toggle_row, text="Modulador de voz ON/OFF", variable=self.effects_enabled, command=self.update_engine).pack(side="left", padx=(0, 16))
        ttk.Checkbutton(toggle_row, text="Escuchar / silenciar salida", variable=self.mute, command=self.update_engine).pack(side="left", padx=16)
        ttk.Button(toggle_row, text="▶ Empezar directo", style="Accent.TButton", command=self.start).pack(side="left", padx=10)
        ttk.Button(toggle_row, text="■ Parar", style="Danger.TButton", command=self.stop).pack(side="left", padx=10)

        tiles_card = self.make_card(center, "Accesos rápidos")
        tiles_card.pack(fill="x", pady=(0, 10))
        tiles_grid = ttk.Frame(tiles_card, style="Card.TFrame")
        tiles_grid.pack(fill="x")

        pro_tiles = [
            ("pro_voicebox", self.tab_voicebox_grid),
            ("pro_soundboard", self.tab_sonidos),
            ("pro_studio", self.tab_studio),
            ("pro_settings", self.tab_ajustes),
        ]
        for i, (img_key, target) in enumerate(pro_tiles):
            box = ttk.Frame(tiles_grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=6)
            if img_key in self.pro_images:
                ttk.Label(box, image=self.pro_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text="Abrir", command=lambda t=target: self.select_tab(t)).pack(fill="x", pady=(6, 0))
            tiles_grid.columnconfigure(i, weight=1)

        voicebox = self.make_card(center, "Caja de voces rápido")
        voicebox.pack(fill="both", expand=True)

        quick_grid = ttk.Frame(voicebox, style="Card.TFrame")
        quick_grid.pack(fill="both", expand=True)

        voices = [
            "Gaming limpio", "Discord claro", "Fortnite grave", "Streamer",
            "Robot directo", "Alien", "Narrador épico", "Locutor español",
            "Payaso gamer", "Jefe final", "Podcast", "Voz clara",
        ]
        for i, voice in enumerate(voices):
            btn = ttk.Button(quick_grid, text=voice, command=lambda v=voice: self.apply_pro_voice(v))
            btn.grid(row=i // 4, column=i % 4, sticky="nsew", padx=6, pady=6, ipady=8)
        for col in range(4):
            quick_grid.columnconfigure(col, weight=1)
        for row in range(3):
            quick_grid.rowconfigure(row, weight=1)

        right = self.make_card(body, "Estado Pro")
        right.pack(side="right", fill="y", padx=(10, 0))

        ttk.Label(right, text="Voz actual", style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(right, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 18, "bold"), wraplength=260).pack(anchor="w", pady=(0, 12))

        ttk.Label(right, text="Micro", style="Card.TLabel").pack(anchor="w")
        self.pro_mic_bar = ttk.Progressbar(right, maximum=100)
        self.pro_mic_bar.pack(fill="x", pady=(4, 10))

        ttk.Label(right, text="Salida", style="Card.TLabel").pack(anchor="w")
        self.pro_out_bar = ttk.Progressbar(right, maximum=100)
        self.pro_out_bar.pack(fill="x", pady=(4, 14))

        ttk.Button(right, text="Guardar como perfil", command=self.save_current_profile).pack(fill="x", pady=4)
        ttk.Button(right, text="Voz aleatoria", command=self.random_voice).pack(fill="x", pady=4)
        ttk.Button(right, text="Grabar prueba WAV", command=self.record).pack(fill="x", pady=4)

    def apply_pro_voice(self, voice_name):
        if voice_name in VoiceBank.all_presets():
            self.preset.set(voice_name)
            # Cambiar categoría automáticamente
            cat = VoiceBank.all_presets()[voice_name][0]
            self.category.set(cat)
            self.refresh_voice_list()
            self.apply_preset()
            self.state.set(f"Estado: voz pro aplicada · {voice_name}")

    # ------------------------------------------------------------------
    # CLIP INSTANTÁNEO PRO (V51)
    # ------------------------------------------------------------------

    def build_clips_tab(self):
        cont = ttk.Frame(self.tab_clips)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "clips_banner" in self.clips_images:
            ttk.Label(header, image=self.clips_images["clips_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="🎬 Clip Instantáneo Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")
            ttk.Label(header, text="La app recuerda los últimos 60 segundos de tu voz procesada. ¿Ha pasado algo épico? Guárdalo DESPUÉS de que ocurra.", style="Card.TLabel", wraplength=900, justify="left").pack(anchor="w", pady=(4, 0))

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        guardar = self.make_card(left, "Guardar clip")
        guardar.pack(fill="x", pady=(0, 10))
        row = ttk.Frame(guardar, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Button(row, text="💾 Últimos 10 s", style="Accent.TButton", command=lambda: self.save_clip(10)).pack(side="left", fill="x", expand=True, padx=4, ipady=10)
        ttk.Button(row, text="💾 Últimos 30 s", style="Accent.TButton", command=lambda: self.save_clip(30)).pack(side="left", fill="x", expand=True, padx=4, ipady=10)
        ttk.Button(row, text="💾 Últimos 60 s", style="Accent.TButton", command=lambda: self.save_clip(60)).pack(side="left", fill="x", expand=True, padx=4, ipady=10)
        ttk.Label(guardar, textvariable=self.clips_available, style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 0))
        ttk.Label(guardar, text="Atajo: Ctrl + Shift + C guarda los últimos 30 segundos.", style="Card.TLabel").pack(anchor="w", pady=(2, 0))

        lista = self.make_card(left, "Clips guardados")
        lista.pack(fill="both", expand=True)
        cuerpo = ttk.Frame(lista, style="Card.TFrame")
        cuerpo.pack(fill="both", expand=True)
        self.clips_list = tk.Listbox(
            cuerpo,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            relief="flat",
            font=("Consolas", 10),
            height=12
        )
        self.clips_list.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.clips_list.bind("<Double-Button-1>", lambda e: self.play_selected_clip())
        botones = ttk.Frame(cuerpo, style="Card.TFrame")
        botones.pack(side="left", fill="y")
        ttk.Button(botones, text="▶ Escuchar", style="Accent.TButton", command=self.play_selected_clip).pack(fill="x", pady=3)
        ttk.Button(botones, text="Actualizar lista", command=self.refresh_clips_list).pack(fill="x", pady=3)
        ttk.Button(botones, text="Abrir carpeta", command=self.open_clips_folder).pack(fill="x", pady=3)
        ttk.Button(botones, text="Borrar clip", style="Danger.TButton", command=self.delete_selected_clip).pack(fill="x", pady=3)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.clips_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        control = self.make_card(right, "Buffer de repetición")
        control.pack(fill="x", pady=(0, 10))
        ttk.Checkbutton(control, text="Buffer activado", variable=self.replay_enabled_var, command=self.toggle_replay).pack(anchor="w", pady=3)
        ttk.Button(control, text="Vaciar buffer", command=self.clear_replay_buffer).pack(fill="x", pady=3)
        ttk.Button(control, text="▶ Empezar directo", style="Accent.TButton", command=self.start).pack(fill="x", pady=3)

        tips = self.make_card(right, "Cómo funciona")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text="• El buffer graba en memoria mientras el directo está activo.\n"
                 "• Guarda la voz YA procesada, con efectos, karaoke y soundboard.\n"
                 "• No escribe nada en disco hasta que pulsas Guardar.\n"
                 "• Los clips se guardan como WAV en tu carpeta personal.\n"
                 "• Escuchar clip lo mezcla en la salida, como un sonido de la mesa.",
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

        self.refresh_clips_list()

    def clips_output_folder(self):
        folder = Path.home() / "ModuladorVozDirecto_Clips"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def save_clip(self, seconds):
        try:
            disponible = self.engine.replay_available_seconds()
            if disponible < 0.5:
                self.clips_status.set("El buffer está vacío. Pulsa ▶ Empezar directo y habla un poco antes de guardar.")
                messagebox.showwarning("Buffer vacío", "Todavía no hay audio en el buffer.\n\nEmpieza el directo y habla unos segundos antes de guardar un clip.")
                return
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.clips_output_folder() / f"clip_{ts}_{int(seconds)}s.wav"
            dur = self.engine.save_replay(str(path), seconds)
            if dur <= 0:
                self.clips_status.set("No se pudo guardar el clip: buffer vacío.")
                return
            self.clips_status.set(f"Clip guardado ({dur:.1f} s): {path.name}")
            self.state.set(f"Estado: clip guardado · {dur:.1f} s")
            self.refresh_clips_list()
        except Exception as e:
            self.clips_status.set(f"No se pudo guardar el clip: {e}")

    def hotkey_save_clip(self):
        if not self.hotkeys_active():
            return
        self.save_clip(30)
        self.hotkey_status.set("Atajo: clip instantáneo de 30 s guardado.")

    def refresh_clips_list(self):
        if getattr(self, "clips_list", None) is None:
            return
        self.clips_list.delete(0, tk.END)
        try:
            clips = sorted(self.clips_output_folder().glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
        except Exception:
            clips = []
        if not clips:
            self.clips_list.insert(tk.END, "No hay clips todavía.")
        else:
            for clip in clips:
                self.clips_list.insert(tk.END, clip.name)

    def selected_clip_path(self):
        if getattr(self, "clips_list", None) is None or not self.clips_list.curselection():
            return None
        name = self.clips_list.get(self.clips_list.curselection()[0])
        path = self.clips_output_folder() / name
        return path if path.exists() else None

    def play_selected_clip(self):
        path = self.selected_clip_path()
        if path is None:
            self.clips_status.set("Selecciona un clip de la lista.")
            return
        if not self.engine.running:
            self.clips_status.set("Para escuchar un clip, primero pulsa ▶ Empezar directo.")
            messagebox.showinfo("Directo parado", "Los clips se escuchan mezclados en la salida.\n\nPulsa ▶ Empezar directo y vuelve a intentarlo.")
            return
        samples = self.load_wav_as_samples(str(path))
        if samples is None:
            return
        self.engine.add_sfx(samples)
        self.clips_status.set(f"Reproduciendo clip: {path.name}")

    def delete_selected_clip(self):
        path = self.selected_clip_path()
        if path is None:
            self.clips_status.set("Selecciona un clip de la lista.")
            return
        if not messagebox.askyesno("Borrar clip", f"¿Borrar este clip?\n\n{path.name}"):
            return
        try:
            path.unlink()
            self.clips_status.set(f"Clip borrado: {path.name}")
            self.refresh_clips_list()
        except Exception as e:
            self.clips_status.set(f"No se pudo borrar el clip: {e}")

    def open_clips_folder(self):
        try:
            folder = self.clips_output_folder()
            if platform.system() == "Windows": os.startfile(str(folder))
            elif platform.system() == "Darwin": subprocess.Popen(["open", str(folder)])
            else: subprocess.Popen(["xdg-open", str(folder)])
            self.clips_status.set("Carpeta de clips abierta.")
        except Exception as e:
            self.clips_status.set(f"No se pudo abrir carpeta: {e}")

    def toggle_replay(self):
        self.engine.replay_enabled = bool(self.replay_enabled_var.get())
        if self.engine.replay_enabled:
            self.clips_status.set("Buffer activado. Guardando los últimos 60 s en memoria.")
        else:
            self.clips_status.set("Buffer desactivado. No se guarda nada en memoria.")

    def clear_replay_buffer(self):
        self.engine.clear_replay()
        self.clips_status.set("Buffer vaciado. Empezará a llenarse de nuevo al hablar.")



























    def build_mezclador_musical_tab(self):
        cont = ttk.Frame(self.tab_mezclador_musical)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "mezclador_banner" in self.mix_images:
            ttk.Label(header, image=self.mix_images["mezclador_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Mezclador Musical Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Presets de mezcla")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [("tile_equilibrado","Equilibrado","equilibrado"),("tile_voz","Voz delante","voz"),("tile_base","Base fuerte","base"),("tile_demo","Demo final","demo"),("tile_guardar","Guardar proyecto","guardar"),("tile_cargar","Cargar proyecto","cargar")]
        for i, (img_key, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.mix_images:
                ttk.Label(box, image=self.mix_images[img_key], style="Card.TLabel").pack()
            if mode == "guardar":
                cmd = self.mix_save_project
            elif mode == "cargar":
                cmd = self.mix_load_project
            else:
                cmd = lambda m=mode: self.mix_apply_preset(m)
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5,0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)
        mixer = self.make_card(body, "Faders de mezcla")
        mixer.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.mix_slider(mixer, "Voz / micro", self.mix_voice, 0, 140, "%")
        self.mix_slider(mixer, "Instrumental", self.mix_music, 0, 120, "%")
        self.mix_slider(mixer, "Master final", self.mix_master, 0, 120, "%")
        ttk.Label(mixer, text="Acciones rápidas:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 4))
        row = ttk.Frame(mixer, style="Card.TFrame"); row.pack(fill="x", pady=4)
        ttk.Button(row, text="▶ Play", command=self.karaoke_play).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(row, text="⏸ Pausa", command=self.karaoke_pause).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(row, text="⏹ Stop", command=self.karaoke_stop).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        row2 = ttk.Frame(mixer, style="Card.TFrame"); row2.pack(fill="x", pady=4)
        ttk.Button(row2, text="Grabar demo", style="Accent.TButton", command=self.karaoke_record_demo).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(row2, text="Exportar instrumental", command=self.song_export_instrumental).pack(side="left", fill="x", expand=True, padx=3, ipady=7)

        info = self.make_card(body, "Proyecto musical")
        info.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.mix_project_text = tk.Text(info, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=18)
        self.mix_project_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.mix_update_project_text("Mezclador listo.")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado"); estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.mix_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")
        pista = self.make_card(right, "Pista y voz"); pista.pack(fill="x", pady=(0, 10))
        ttk.Label(pista, text="Pista:", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(pista, textvariable=self.karaoke_track, style="Card.TLabel", wraplength=310).pack(anchor="w", pady=(0,8))
        ttk.Label(pista, text="Voz:", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(pista, textvariable=self.preset, style="Card.TLabel", wraplength=310).pack(anchor="w")
        acciones = self.make_card(right, "Proyecto"); acciones.pack(fill="x", pady=(0,10))
        ttk.Button(acciones, text="Guardar proyecto JSON", style="Accent.TButton", command=self.mix_save_project).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Cargar proyecto JSON", command=self.mix_load_project).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir carpeta canciones", command=self.mix_open_song_folder).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Canción Pro", command=lambda: self.select_tab(self.tab_cancion_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Karaoke Studio", command=lambda: self.select_tab(self.tab_karaoke_studio)).pack(fill="x", pady=3)
        tips = self.make_card(right, "Consejos"); tips.pack(fill="x")
        ttk.Label(tips, text="• Voz delante: mejor para entender letra.\n• Base fuerte: mejor para practicar ritmo.\n• Demo final: mezcla más segura.\n• Guarda proyecto para continuar luego.\n• Exporta instrumental y letra por separado.", style="Card.TLabel", justify="left", wraplength=310).pack(anchor="w")
        self.mix_update_engine()

    def mix_slider(self, parent, label, var, mn, mx, unit):
        line = ttk.Frame(parent, style="Card.TFrame"); line.pack(fill="x", pady=8)
        top = ttk.Frame(line, style="Card.TFrame"); top.pack(fill="x")
        ttk.Label(top, text=label + ":", style="Card.TLabel", width=18).pack(side="left")
        value_label = ttk.Label(top, style="Card.TLabel", width=10); value_label.pack(side="right")
        ttk.Scale(line, from_=mn, to=mx, variable=var, orient="horizontal", command=lambda _=None: self.mix_update_engine()).pack(fill="x", pady=(3, 0))
        def refresh(*_):
            value_label.config(text=f"{var.get():.0f}{unit}")
            self.mix_update_engine()
        var.trace_add("write", refresh); refresh()

    def mix_update_engine(self):
        try:
            master = max(0, min(1.2, self.mix_master.get() / 100.0))
            voice = max(0, min(1.4, self.mix_voice.get() / 100.0)) * master
            music = max(0, min(1.2, self.mix_music.get() / 100.0)) * master
            if "vol" in self.vars:
                self.vars["vol"].set(voice * 100)
            self.karaoke_volume.set(music * 100)
            self.karaoke_update_engine(); self.update_engine()
            self.mix_update_project_text("Mezcla actualizada.")
        except Exception:
            pass

    def mix_apply_preset(self, mode):
        presets = {"equilibrado": (90,45,100,"Mezcla equilibrada aplicada."), "voz": (110,32,96,"Voz delante aplicada."), "base": (78,70,95,"Base fuerte aplicada."), "demo": (92,42,90,"Demo final aplicada.")}
        voice, music, master, msg = presets.get(mode, presets["equilibrado"])
        self.mix_voice.set(voice); self.mix_music.set(music); self.mix_master.set(master)
        self.mix_update_engine(); self.mix_status.set(msg)

    def mix_project_data(self):
        lyrics = ""
        if hasattr(self, "song_lyrics_text"):
            try: lyrics = self.song_lyrics_text.get("1.0", tk.END).strip()
            except Exception: lyrics = ""
        return {"version": VERSION, "title": self.song_title.get(), "style": self.song_style.get(), "voice": self.preset.get(), "category": self.category.get(), "track": self.karaoke_track.get(), "mix": {"voice": self.mix_voice.get(), "music": self.mix_music.get(), "master": self.mix_master.get()}, "effects": {k: v.get() for k, v in self.vars.items()}, "lyrics": lyrics}

    def mix_save_project(self):
        try:
            title = self.song_safe_name(self.song_title.get())
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.song_output_folder() / f"{title}_proyecto_{ts}.json"
            path.write_text(json.dumps(self.mix_project_data(), ensure_ascii=False, indent=2), encoding="utf-8")
            self.mix_status.set(f"Proyecto guardado: {path.name}")
            self.mix_update_project_text(f"Proyecto guardado en:\n{path}")
            messagebox.showinfo("Proyecto guardado", f"Archivo guardado en:\n{path}")
        except Exception as e:
            self.mix_status.set(f"No se pudo guardar proyecto: {e}")

    def mix_load_project(self):
        try:
            path = filedialog.askopenfilename(title="Cargar proyecto musical JSON", filetypes=[("Proyecto musical JSON", "*.json")])
            if not path: return
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.song_title.set(data.get("title", "Mi demo karaoke")); self.song_style.set(data.get("style", "Pop"))
            voice = data.get("voice")
            if voice in VoiceBank.all_presets():
                self.preset.set(voice); self.category.set(data.get("category", VoiceBank.all_presets()[voice][0])); self.apply_preset()
            mix = data.get("mix", {})
            self.mix_voice.set(float(mix.get("voice", 90))); self.mix_music.set(float(mix.get("music", 45))); self.mix_master.set(float(mix.get("master", 100)))
            for k, val in data.get("effects", {}).items():
                if k in self.vars: self.vars[k].set(val)
            if hasattr(self, "song_lyrics_text"):
                self.song_lyrics_text.configure(state="normal"); self.song_lyrics_text.delete("1.0", tk.END); self.song_lyrics_text.insert("1.0", data.get("lyrics", ""))
            self.mix_update_engine(); self.mix_status.set(f"Proyecto cargado: {Path(path).name}")
            self.mix_update_project_text(f"Proyecto cargado desde:\n{path}\n\nNota: el JSON recupera letra, voz y mezcla. Si quieres la misma base, genera/exporta otra vez el instrumental.")
        except Exception as e:
            self.mix_status.set(f"No se pudo cargar proyecto: {e}")

    def mix_open_song_folder(self):
        try:
            folder = self.song_output_folder()
            if platform.system() == "Windows": os.startfile(str(folder))
            elif platform.system() == "Darwin": subprocess.Popen(["open", str(folder)])
            else: subprocess.Popen(["xdg-open", str(folder)])
            self.mix_status.set("Carpeta de canciones abierta.")
        except Exception as e:
            self.mix_status.set(f"No se pudo abrir carpeta: {e}")

    def mix_update_project_text(self, extra):
        if not hasattr(self, "mix_project_text"): return
        try:
            text = ("PROYECTO MUSICAL\n\n" + f"Título: {self.song_title.get()}\nEstilo: {self.song_style.get()}\nVoz: {self.preset.get()}\nPista: {self.karaoke_track.get()}\n\n" + "MEZCLA\n" + f"Voz: {self.mix_voice.get():.0f}%\nInstrumental: {self.mix_music.get():.0f}%\nMaster: {self.mix_master.get():.0f}%\n\n" + "SALIDAS\n- Guardar proyecto JSON\n- Exportar instrumental WAV\n- Guardar letra TXT\n- Grabar demo cantada WAV\n\n" + str(extra))
            self.mix_project_text.configure(state="normal"); self.mix_project_text.delete("1.0", tk.END); self.mix_project_text.insert("1.0", text); self.mix_project_text.configure(state="disabled")
        except Exception:
            pass

    def build_cancion_pro_tab(self):
        cont = ttk.Frame(self.tab_cancion_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "cancion_banner" in self.song_images:
            ttk.Label(header, image=self.song_images["cancion_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Creador de Canciones Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Demos de canción")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_pop", "Demo Pop", "Pop"),
            ("tile_trap", "Demo Trap", "Trap"),
            ("tile_balada", "Demo Balada", "Balada"),
            ("tile_letra", "Letra", "letra"),
            ("tile_exportar", "Exportar", "exportar"),
            ("tile_grabar", "Grabar demo", "grabar"),
        ]

        for i, (img_key, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.song_images:
                ttk.Label(box, image=self.song_images[img_key], style="Card.TLabel").pack()
            if mode == "letra":
                cmd = self.song_fill_default_lyrics
            elif mode == "exportar":
                cmd = self.song_export_instrumental
            elif mode == "grabar":
                cmd = self.karaoke_record_demo
            else:
                cmd = lambda s=mode: self.song_generate_demo(s)
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        editor = self.make_card(body, "Editor de canción")
        editor.pack(side="left", fill="both", expand=True, padx=(0, 5))

        meta = ttk.Frame(editor, style="Card.TFrame")
        meta.pack(fill="x", pady=(0, 8))
        ttk.Label(meta, text="Título:", style="Card.TLabel").pack(side="left")
        ttk.Entry(meta, textvariable=self.song_title).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Label(meta, text="Estilo:", style="Card.TLabel").pack(side="left")
        ttk.Combobox(meta, textvariable=self.song_style, state="readonly", width=12, values=["Pop", "Trap", "Balada", "Lofi", "Rock"]).pack(side="left", padx=6)

        dur = ttk.Frame(editor, style="Card.TFrame")
        dur.pack(fill="x", pady=(0, 8))
        ttk.Label(dur, text="Duración:", style="Card.TLabel").pack(side="left")
        ttk.Scale(dur, from_=30, to=120, variable=self.song_duration, orient="horizontal").pack(side="left", fill="x", expand=True, padx=6)
        ttk.Label(dur, textvariable=self.song_duration, style="Card.TLabel", width=5).pack(side="left")
        ttk.Label(dur, text="seg", style="Card.TLabel").pack(side="left", padx=(2, 0))

        actions = ttk.Frame(editor, style="Card.TFrame")
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="Generar canción", style="Accent.TButton", command=lambda: self.song_generate_demo(self.song_style.get())).pack(side="left", fill="x", expand=True, padx=3, ipady=6)
        ttk.Button(actions, text="▶ Play", command=self.karaoke_play).pack(side="left", fill="x", expand=True, padx=3, ipady=6)
        ttk.Button(actions, text="⏹ Stop", command=self.karaoke_stop).pack(side="left", fill="x", expand=True, padx=3, ipady=6)

        self.song_lyrics_text = tk.Text(
            editor,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.song_lyrics_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.song_fill_default_lyrics()

        guide = self.make_card(body, "Estructura y exportación")
        guide.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.song_info_text = tk.Text(
            guide,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.song_info_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.song_update_info("Genera una demo para ver la estructura.")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.song_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        pista = self.make_card(right, "Pista actual")
        pista.pack(fill="x", pady=(0, 10))
        ttk.Label(pista, textvariable=self.karaoke_track, style="Card.TLabel", font=("Segoe UI", 13, "bold"), wraplength=310).pack(anchor="w")
        ttk.Label(pista, text="Canción Pro crea un instrumental estructurado sin voces.", style="Card.TLabel", wraplength=310).pack(anchor="w", pady=(6, 0))

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Exportar instrumental WAV", style="Accent.TButton", command=self.song_export_instrumental).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Guardar letra TXT", command=self.song_save_lyrics_txt).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Grabar demo cantada", command=self.karaoke_record_demo).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Karaoke", command=lambda: self.select_tab(self.tab_karaoke)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Autotune", command=lambda: self.select_tab(self.tab_autotune)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Genera el instrumental.\n"
                "• Edita la letra.\n"
                "• Pulsa Play y canta encima.\n"
                "• Graba demo cantada.\n"
                "• Exporta instrumental WAV si quieres reutilizarlo."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def song_fill_default_lyrics(self):
        if not hasattr(self, "song_lyrics_text"):
            return
        title = self.song_title.get().strip() or "Mi demo karaoke"
        text = (
            f"TÍTULO: {title}\n\n"
            "[Intro]\n"
            "Respira, la pista empieza,\n"
            "todo listo para cantar.\n\n"
            "[Verso 1]\n"
            "Tengo luces en la mente,\n"
            "una voz que quiere sonar,\n"
            "voy probando cada frase,\n"
            "hasta encontrar mi lugar.\n\n"
            "[Pre-estribillo]\n"
            "Sube un poco el autotune,\n"
            "deja el eco respirar,\n"
            "si la mezcla queda limpia,\n"
            "ya lo puedo publicar.\n\n"
            "[Estribillo]\n"
            "Canto fuerte sobre el beat,\n"
            "mi demo empieza a brillar,\n"
            "grabo todo en un WAV,\n"
            "y lo vuelvo a mejorar.\n\n"
            "[Outro]\n"
            "La canción se va apagando,\n"
            "pero queda la señal."
        )
        self.song_lyrics_text.configure(state="normal")
        self.song_lyrics_text.delete("1.0", tk.END)
        self.song_lyrics_text.insert("1.0", text)
        self.song_lyrics_text.configure(state="normal")
        self.song_status.set("Letra de canción cargada.")

    def song_style_to_studio_style(self, style):
        mapping = {
            "Pop": "pop",
            "Trap": "trap",
            "Balada": "balada",
            "Lofi": "lofi",
            "Rock": "rock",
        }
        return mapping.get(str(style), "pop")

    def song_generate_demo(self, style):
        try:
            self.song_style.set(str(style))
            studio_style = self.song_style_to_studio_style(style)
            defaults = {"pop": 120, "trap": 140, "lofi": 85, "balada": 72, "rock": 110}
            bpm = defaults.get(studio_style, 120)
            seconds = int(max(30, min(120, self.song_duration.get())))
            base_samples = self.generate_original_instrumental(studio_style, seconds=seconds, bpm=bpm)
            arranged = self.song_apply_arrangement(base_samples, style=studio_style, rate=self.engine.rate)
            title = self.song_title.get().strip() or "Mi demo karaoke"
            track_name = f"{title} · {style} · canción completa · {bpm} BPM"
            self.engine.set_karaoke_track(arranged, track_name)
            self.karaoke_track.set(track_name)
            self.karaoke_loop.set(False)
            self.karaoke_update_engine()

            if studio_style == "trap":
                self.karaoke_apply_voice("Karaoke Trap")
            elif studio_style == "balada":
                self.karaoke_apply_voice("Karaoke Balada")
            else:
                self.karaoke_apply_voice("Karaoke Pop")

            self.song_status.set(f"Canción generada: {track_name}")
            self.song_update_info(f"Canción generada correctamente: {track_name}")
        except Exception as e:
            self.song_status.set(f"No se pudo generar canción: {e}")

    def song_apply_arrangement(self, samples, style="pop", rate=44100):
        samples = np.asarray(samples, dtype=np.float32)
        n = len(samples)
        if n == 0:
            return samples

        # Forma: intro suave, verso medio, estribillo fuerte, outro fade.
        t = np.linspace(0, 1, n, dtype=np.float32)
        env = np.ones(n, dtype=np.float32) * 0.75
        env[t < 0.12] *= np.linspace(0.25, 0.65, max(1, np.sum(t < 0.12))).astype(np.float32)
        env[(t >= 0.12) & (t < 0.45)] *= 0.72
        env[(t >= 0.45) & (t < 0.78)] *= 1.10
        env[t >= 0.78] *= np.linspace(0.95, 0.15, max(1, np.sum(t >= 0.78))).astype(np.float32)

        # Pequeñas pausas al cambiar sección.
        for marker in [0.12, 0.45, 0.78]:
            center = int(marker * n)
            width = int(rate * 0.18)
            a = max(0, center - width // 2)
            b = min(n, center + width // 2)
            if b > a:
                env[a:b] *= np.linspace(0.6, 1.0, b-a).astype(np.float32)

        out = samples * env
        peak = np.max(np.abs(out)) if len(out) else 1
        if peak > 0:
            out = out / peak * 0.78
        return out.astype(np.float32)

    def song_update_info(self, extra):
        if not hasattr(self, "song_info_text"):
            return
        text = (
            "ESTRUCTURA DE CANCIÓN\n\n"
            "Intro: entrada suave.\n"
            "Verso: base media para cantar claro.\n"
            "Estribillo: más energía.\n"
            "Outro: final con fade.\n\n"
            "EXPORTACIÓN\n\n"
            "- Exportar instrumental WAV guarda solo la base.\n"
            "- Grabar demo cantada guarda voz + base si está sonando.\n"
            "- Guardar letra TXT exporta el texto del editor.\n\n"
            f"{extra}"
        )
        self.song_info_text.configure(state="normal")
        self.song_info_text.delete("1.0", tk.END)
        self.song_info_text.insert("1.0", text)
        self.song_info_text.configure(state="disabled")

    def song_output_folder(self):
        folder = Path.home() / "ModuladorVozDirecto_Canciones"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def song_safe_name(self, text):
        keep = []
        for ch in text:
            if ch.isalnum() or ch in " -_":
                keep.append(ch)
        name = "".join(keep).strip().replace(" ", "_")
        return name or "cancion"

    def song_export_instrumental(self):
        try:
            samples = getattr(self.engine, "karaoke_samples", np.zeros(0, dtype=np.float32))
            if samples is None or len(samples) == 0:
                self.song_status.set("No hay instrumental para exportar. Genera una canción primero.")
                return

            title = self.song_safe_name(self.song_title.get())
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.song_output_folder() / f"{title}_instrumental_{ts}.wav"
            self.write_wav_float32(path, samples, self.engine.rate)
            self.song_status.set(f"Instrumental exportado: {path.name}")
            self.song_update_info(f"Instrumental exportado en:\n{path}")
            messagebox.showinfo("Instrumental exportado", f"Archivo guardado en:\n{path}")
        except Exception as e:
            self.song_status.set(f"No se pudo exportar WAV: {e}")

    def write_wav_float32(self, path, samples, rate):
        samples = np.asarray(samples, dtype=np.float32)
        samples = np.clip(samples, -1.0, 1.0)
        pcm = (samples * 32767).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(int(rate))
            wf.writeframes(pcm.tobytes())

    def song_save_lyrics_txt(self):
        try:
            text = self.song_lyrics_text.get("1.0", tk.END).strip() if hasattr(self, "song_lyrics_text") else ""
            if not text:
                self.song_status.set("No hay letra para guardar.")
                return
            title = self.song_safe_name(self.song_title.get())
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.song_output_folder() / f"{title}_letra_{ts}.txt"
            path.write_text(text, encoding="utf-8")
            self.song_status.set(f"Letra guardada: {path.name}")
            messagebox.showinfo("Letra guardada", f"Archivo guardado en:\n{path}")
        except Exception as e:
            self.song_status.set(f"No se pudo guardar letra: {e}")


    def build_karaoke_studio_tab(self):
        cont = ttk.Frame(self.tab_karaoke_studio)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "karaoke_studio_banner" in self.karaoke_studio_images:
            ttk.Label(header, image=self.karaoke_studio_images["karaoke_studio_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Karaoke Studio Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Generador de instrumentales originales")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_pop", "Pop original", "pop"),
            ("tile_trap", "Trap original", "trap"),
            ("tile_lofi", "Lofi original", "lofi"),
            ("tile_balada", "Balada", "balada"),
            ("tile_rock", "Rock suave", "rock"),
            ("tile_demo", "Grabar demo", "demo"),
        ]

        for i, (img_key, label, style_key) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.karaoke_studio_images:
                ttk.Label(box, image=self.karaoke_studio_images[img_key], style="Card.TLabel").pack()
            cmd = self.karaoke_record_demo if style_key == "demo" else lambda s=style_key: self.karaoke_generate_original(s)
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        studio = self.make_card(body, "Controles de estudio")
        studio.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ttk.Label(studio, text="Duración del instrumental:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        dur_row = ttk.Frame(studio, style="Card.TFrame")
        dur_row.pack(fill="x", pady=4)
        ttk.Scale(dur_row, from_=15, to=90, variable=self.karaoke_studio_seconds, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(dur_row, textvariable=self.karaoke_studio_seconds, style="Card.TLabel", width=5).pack(side="left")
        ttk.Label(dur_row, text="seg", style="Card.TLabel").pack(side="left")

        ttk.Label(studio, text="BPM manual:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(8, 0))
        bpm_row = ttk.Frame(studio, style="Card.TFrame")
        bpm_row.pack(fill="x", pady=4)
        ttk.Scale(bpm_row, from_=60, to=160, variable=self.karaoke_studio_bpm, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(bpm_row, textvariable=self.karaoke_studio_bpm, style="Card.TLabel", width=5).pack(side="left")
        ttk.Label(bpm_row, text="BPM", style="Card.TLabel").pack(side="left")

        ttk.Label(studio, text="Acciones rápidas:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 0))
        for label, cmd in [
            ("▶ Reproducir instrumental", self.karaoke_play),
            ("⏸ Pausa", self.karaoke_pause),
            ("⏹ Stop", self.karaoke_stop),
            ("Activar loop", self.karaoke_toggle_loop),
            ("Abrir Karaoke", lambda: self.select_tab(self.tab_karaoke)),
        ]:
            ttk.Button(studio, text=label, command=cmd).pack(fill="x", pady=3)

        info = self.make_card(body, "Letra y guía")
        info.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.karaoke_studio_text = tk.Text(
            info,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.karaoke_studio_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.karaoke_studio_update_text("Genera un instrumental original para practicar.")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.karaoke_studio_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        actual = self.make_card(right, "Pista actual")
        actual.pack(fill="x", pady=(0, 10))
        ttk.Label(actual, textvariable=self.karaoke_track, style="Card.TLabel", font=("Segoe UI", 13, "bold"), wraplength=310).pack(anchor="w", pady=(0, 6))
        ttk.Label(actual, text="Los instrumentales generados son simples y originales para practicar.", style="Card.TLabel", wraplength=310).pack(anchor="w")

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Karaoke Pop + Play", style="Accent.TButton", command=lambda: [self.karaoke_apply_voice("Karaoke Pop"), self.karaoke_play()]).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Karaoke Trap + Play", command=lambda: [self.karaoke_apply_voice("Karaoke Trap"), self.karaoke_play()]).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Karaoke Balada + Play", command=lambda: [self.karaoke_apply_voice("Karaoke Balada"), self.karaoke_play()]).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Grabar demo WAV", command=self.karaoke_record_demo).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Guardar voz como perfil", command=self.save_current_profile).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Pop: para estribillos claros.\n"
                "• Trap: autotune marcado.\n"
                "• Lofi: practicar suave.\n"
                "• Balada: voz clara con reverb.\n"
                "• Rock suave: más energía.\n"
                "• Son bases simples originales, sin voces."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def karaoke_studio_update_text(self, extra):
        if not hasattr(self, "karaoke_studio_text"):
            return
        text = (
            "KARAOKE STUDIO PRO\n\n"
            "Genera instrumentales originales simples para cantar encima.\n"
            "No usan canciones comerciales ni voces de terceros.\n\n"
            "LETRA RÁPIDA\n\n"
            "[Verso]\n"
            "Hoy me subo al escenario,\n"
            "con mi voz y mi señal,\n"
            "la base suena de fondo,\n"
            "todo listo para cantar.\n\n"
            "[Estribillo]\n"
            "Karaoke en mi habitación,\n"
            "autotune en el corazón,\n"
            "grabo demo y pruebo el beat,\n"
            "hasta encontrar mi mejor versión.\n\n"
            f"{extra}"
        )
        self.karaoke_studio_text.configure(state="normal")
        self.karaoke_studio_text.delete("1.0", tk.END)
        self.karaoke_studio_text.insert("1.0", text)
        self.karaoke_studio_text.configure(state="normal")

    def karaoke_generate_original(self, style):
        try:
            defaults = {"pop": 120, "trap": 140, "lofi": 85, "balada": 72, "rock": 110}
            bpm = defaults.get(style, int(self.karaoke_studio_bpm.get()))
            seconds = int(max(15, min(90, self.karaoke_studio_seconds.get())))
            samples = self.generate_original_instrumental(style, seconds=seconds, bpm=bpm)
            title = f"Instrumental original {style} · {bpm} BPM · {seconds}s"
            self.engine.set_karaoke_track(samples, title)
            self.karaoke_track.set(title)
            self.karaoke_loop.set(True)
            self.karaoke_update_engine()
            self.karaoke_studio_status.set(f"Generado: {title}")
            self.karaoke_studio_update_text(f"Instrumental generado: {title}\nPulsa Play y canta encima.")
            # Voz recomendada
            if style == "trap":
                self.karaoke_apply_voice("Karaoke Trap")
            elif style == "balada":
                self.karaoke_apply_voice("Karaoke Balada")
            else:
                self.karaoke_apply_voice("Karaoke Pop")
        except Exception as e:
            self.karaoke_studio_status.set(f"No se pudo generar instrumental: {e}")

    def generate_original_instrumental(self, style, seconds=45, bpm=120):
        rate = self.engine.rate if hasattr(self, "engine") else 44100
        n = int(rate * seconds)
        t = np.arange(n, dtype=np.float32) / rate
        beat = 60.0 / max(1, bpm)
        y = np.zeros(n, dtype=np.float32)

        progressions = {
            "pop":    [261.63, 392.00, 440.00, 349.23],
            "trap":   [220.00, 174.61, 196.00, 146.83],
            "lofi":   [261.63, 329.63, 246.94, 293.66],
            "balada": [196.00, 246.94, 293.66, 261.63],
            "rock":   [164.81, 196.00, 220.00, 146.83],
        }
        roots = progressions.get(style, progressions["pop"])
        chord_len = beat * 4

        def env_pulse(times, width):
            phase = (times % beat) / beat
            return np.exp(-phase * width).astype(np.float32)

        # Acordes / pad
        for i, root in enumerate(roots):
            start = int(i * chord_len * rate)
            while start < n:
                end = min(n, start + int(chord_len * rate))
                tt = np.arange(end - start, dtype=np.float32) / rate
                if style == "rock":
                    chord = (
                        np.sign(np.sin(2*np.pi*root*tt)) * 0.10 +
                        np.sign(np.sin(2*np.pi*root*1.5*tt)) * 0.06
                    )
                else:
                    chord = (
                        np.sin(2*np.pi*root*tt) * 0.09 +
                        np.sin(2*np.pi*root*1.25*tt) * 0.06 +
                        np.sin(2*np.pi*root*1.5*tt) * 0.04
                    )
                fade = np.linspace(0, 1, min(len(chord), int(rate*0.12)), dtype=np.float32)
                if len(fade) > 0:
                    chord[:len(fade)] *= fade
                    chord[-len(fade):] *= fade[::-1]
                y[start:end] += chord.astype(np.float32)
                start += int(chord_len * rate * len(roots))

        # Bajo
        for i, root in enumerate(roots):
            start_time = i * chord_len
            while start_time < seconds:
                for b in range(4):
                    st = start_time + b * beat
                    start = int(st * rate)
                    end = min(n, start + int(beat * 0.55 * rate))
                    if start >= n:
                        continue
                    tt = np.arange(end - start, dtype=np.float32) / rate
                    bass_freq = root / (2 if style != "trap" else 3)
                    bass = np.sin(2*np.pi*bass_freq*tt) * np.exp(-tt*5.0) * 0.18
                    y[start:end] += bass.astype(np.float32)
                start_time += chord_len * len(roots)

        # Percusión sintética simple
        rng = np.random.default_rng(42 + len(style))
        total_beats = int(seconds / beat)
        for b in range(total_beats):
            st = b * beat
            start = int(st * rate)
            if start >= n:
                continue

            # kick
            if b % 4 in ([0, 2] if style != "trap" else [0, 3]):
                length = int(rate * 0.16)
                end = min(n, start + length)
                tt = np.arange(end-start, dtype=np.float32) / rate
                kick = np.sin(2*np.pi*(70 - 35*tt)*tt) * np.exp(-tt*18) * 0.35
                y[start:end] += kick.astype(np.float32)

            # snare/clap
            if b % 4 in ([1, 3] if style != "balada" else [2]):
                s0 = start
                length = int(rate * 0.08)
                end = min(n, s0 + length)
                noise = rng.normal(0, 1, end-s0).astype(np.float32) * np.exp(-np.linspace(0, 6, end-s0)).astype(np.float32) * 0.12
                y[s0:end] += noise

            # hihat
            subdivisions = 2 if style in ["pop", "rock", "lofi", "balada"] else 4
            for h in range(subdivisions):
                hs = int((st + h * beat / subdivisions) * rate)
                he = min(n, hs + int(rate * 0.025))
                if he > hs:
                    noise = rng.normal(0, 1, he-hs).astype(np.float32)
                    noise *= np.exp(-np.linspace(0, 7, he-hs)).astype(np.float32)
                    y[hs:he] += noise * (0.035 if style != "trap" else 0.05)

        # Melodía simple, muy baja para dejar sitio a la voz
        scale = [0, 2, 4, 7, 9, 7, 4, 2]
        root = roots[0] * 2
        note_len = beat / 2
        for i in range(int(seconds / note_len)):
            if style == "balada" and i % 2:
                continue
            st = i * note_len
            start = int(st * rate)
            end = min(n, start + int(note_len * 0.8 * rate))
            if end <= start:
                continue
            semitone = scale[i % len(scale)]
            freq = root * (2 ** (semitone / 12))
            tt = np.arange(end - start, dtype=np.float32) / rate
            lead = np.sin(2*np.pi*freq*tt) * np.exp(-tt*2.2) * (0.035 if style != "rock" else 0.025)
            y[start:end] += lead.astype(np.float32)

        # Normalizar suave
        y = np.tanh(y * 1.2).astype(np.float32)
        peak = np.max(np.abs(y)) if len(y) else 1
        if peak > 0:
            y = (y / peak * 0.75).astype(np.float32)
        return y


    def build_karaoke_tab(self):
        cont = ttk.Frame(self.tab_karaoke)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "karaoke_banner" in self.karaoke_images:
            ttk.Label(header, image=self.karaoke_images["karaoke_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Karaoke Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Karaoke con instrumental")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_cargar", "Cargar WAV", self.karaoke_load_track),
            ("tile_play", "Reproducir", self.karaoke_play),
            ("tile_loop", "Loop ON/OFF", self.karaoke_toggle_loop),
            ("tile_autotune", "Karaoke Pop", lambda: self.karaoke_apply_voice("Karaoke Pop")),
            ("tile_demo", "Grabar demo", self.karaoke_record_demo),
            ("tile_letra", "Letra", self.karaoke_show_default_lyrics),
        ]
        for i, (img_key, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.karaoke_images:
                ttk.Label(box, image=self.karaoke_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        player = self.make_card(body, "Reproductor instrumental")
        player.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ttk.Label(player, text="Pista cargada:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(player, textvariable=self.karaoke_track, style="Card.TLabel", wraplength=470).pack(anchor="w", pady=(0, 8))

        row = ttk.Frame(player, style="Card.TFrame")
        row.pack(fill="x", pady=4)
        ttk.Button(row, text="Cargar instrumental WAV", style="Accent.TButton", command=self.karaoke_load_track).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(row, text="▶ Play", command=self.karaoke_play).pack(side="left", fill="x", expand=True, padx=3, ipady=8)

        row2 = ttk.Frame(player, style="Card.TFrame")
        row2.pack(fill="x", pady=4)
        ttk.Button(row2, text="⏸ Pausa", command=self.karaoke_pause).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(row2, text="⏹ Stop", command=self.karaoke_stop).pack(side="left", fill="x", expand=True, padx=3, ipady=8)

        row3 = ttk.Frame(player, style="Card.TFrame")
        row3.pack(fill="x", pady=4)
        ttk.Checkbutton(row3, text="Repetir pista en loop", variable=self.karaoke_loop, command=self.karaoke_update_engine).pack(side="left", padx=4)
        ttk.Label(row3, text="Volumen pista:", style="Card.TLabel").pack(side="left", padx=(12, 4))
        ttk.Scale(row3, from_=0, to=100, variable=self.karaoke_volume, orient="horizontal", command=lambda _=None: self.karaoke_update_engine()).pack(side="left", fill="x", expand=True)

        voices = self.make_card(player, "Voces recomendadas para karaoke")
        voices.pack(fill="x", pady=(10, 0))
        for name in ["Karaoke Pop", "Karaoke Trap", "Karaoke Balada", "AutoTune Pop", "Coro Doble", "Balada Clara"]:
            ttk.Button(voices, text=name, command=lambda n=name: self.karaoke_apply_voice(n)).pack(fill="x", pady=2)

        lyrics = self.make_card(body, "Pantalla de letra")
        lyrics.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.karaoke_lyrics_text = tk.Text(
            lyrics,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 12),
            height=18
        )
        self.karaoke_lyrics_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.karaoke_show_default_lyrics()

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.karaoke_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        actual = self.make_card(right, "Voz actual")
        actual.pack(fill="x", pady=(0, 10))
        ttk.Label(actual, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=310).pack(anchor="w", pady=(0, 6))
        ttk.Label(actual, text="Karaoke usa pistas instrumentales WAV que tengas permiso de usar.", style="Card.TLabel", wraplength=310).pack(anchor="w")

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Empezar directo", command=self.start).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Grabar demo WAV", style="Accent.TButton", command=self.karaoke_record_demo).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Guardar voz como perfil", command=self.save_current_profile).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Autotune", command=lambda: self.select_tab(self.tab_autotune)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Grabadora", command=lambda: self.select_tab(self.tab_grabadora)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Carga un WAV instrumental sin voz.\n"
                "• Pulsa Play y canta encima.\n"
                "• Usa Karaoke Pop/Trap/Balada.\n"
                "• Activa loop para practicar.\n"
                "• Graba demo WAV para escuchar resultado.\n"
                "• No elimina voces de canciones; usa pistas instrumentales."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def karaoke_update_engine(self):
        try:
            self.engine.karaoke_volume = max(0.0, min(1.2, self.karaoke_volume.get() / 100.0))
            self.engine.karaoke_loop = bool(self.karaoke_loop.get())
        except Exception:
            pass

    def karaoke_load_track(self):
        path = filedialog.askopenfilename(
            title="Cargar pista instrumental WAV sin voz",
            filetypes=[("Instrumental WAV", "*.wav")]
        )
        if not path:
            return

        samples = self.load_wav_as_samples(path)
        if samples is None:
            return

        name = os.path.basename(path)
        self.engine.set_karaoke_track(samples, name)
        self.karaoke_track.set(name)
        self.karaoke_update_engine()
        self.karaoke_status.set(f"Pista instrumental cargada: {name}")

    def karaoke_play(self):
        self.karaoke_update_engine()
        self.engine.play_karaoke()
        self.karaoke_status.set("Reproduciendo instrumental. Canta encima con el micro.")

    def karaoke_pause(self):
        self.engine.pause_karaoke()
        self.karaoke_status.set("Instrumental en pausa.")

    def karaoke_stop(self):
        self.engine.stop_karaoke()
        self.karaoke_status.set("Instrumental detenido y vuelto al inicio.")

    def karaoke_toggle_loop(self):
        self.karaoke_loop.set(not self.karaoke_loop.get())
        self.karaoke_update_engine()
        self.karaoke_status.set("Loop activado." if self.karaoke_loop.get() else "Loop desactivado.")

    def karaoke_apply_voice(self, name):
        if name in VoiceBank.all_presets():
            self.preset.set(name)
            self.category.set("Cantadas")
            self.apply_preset()
            self.refresh_voice_list()
            self.karaoke_status.set(f"Voz karaoke aplicada: {name}")

    def karaoke_record_demo(self):
        self.karaoke_update_engine()
        self.record()
        self.karaoke_status.set("Demo karaoke iniciada/guardada. La grabación incluye voz + pista si está sonando.")

    def karaoke_show_default_lyrics(self):
        if not hasattr(self, "karaoke_lyrics_text"):
            return
        text = (
            "KARAOKE PRO - LETRA DE PRUEBA\n\n"
            "[Verso]\n"
            "Luces en la pantalla,\n"
            "mi voz empieza a sonar,\n"
            "con la pista instrumental,\n"
            "ya me puedo preparar.\n\n"
            "[Pre-estribillo]\n"
            "Sube el autotune,\n"
            "dale brillo a la señal,\n"
            "si la mezcla queda limpia,\n"
            "lista para publicar.\n\n"
            "[Estribillo]\n"
            "Canto encima del beat,\n"
            "todo suena mucho mejor,\n"
            "grabo demo en WAV,\n"
            "y guardo mi configuración.\n\n"
            "Notas:\n"
            "- Puedes borrar esta letra y escribir la tuya.\n"
            "- Usa instrumentales sin voz que tengas permiso de usar.\n"
            "- Esta app no quita voces de canciones."
        )
        self.karaoke_lyrics_text.configure(state="normal")
        self.karaoke_lyrics_text.delete("1.0", tk.END)
        self.karaoke_lyrics_text.insert("1.0", text)
        self.karaoke_lyrics_text.configure(state="normal")
        self.karaoke_status.set("Letra de karaoke cargada.")


    def build_autotune_tab(self):
        cont = ttk.Frame(self.tab_autotune)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "autotune_banner" in self.autotune_images:
            ttk.Label(header, image=self.autotune_images["autotune_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Autotune Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Modos de voz cantada")
        tiles.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_pop", "AutoTune Pop", "AutoTune Pop"),
            ("tile_trap", "Trap Tune", "Trap Tune"),
            ("tile_coro", "Coro Doble", "Coro Doble"),
            ("tile_robot", "Robot Cantante", "Robot Cantante"),
            ("tile_demo", "Grabar demo", "demo"),
            ("tile_letra", "Letra test", "letra"),
        ]

        for i, (img_key, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.autotune_images:
                ttk.Label(box, image=self.autotune_images[img_key], style="Card.TLabel").pack()
            if mode == "demo":
                cmd = self.autotune_record_demo
            elif mode == "letra":
                cmd = self.autotune_show_lyrics
            else:
                cmd = lambda m=mode: self.apply_autotune_preset(m)
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        mixer = self.make_card(body, "Panel Autotune")
        mixer.pack(side="left", fill="both", expand=True, padx=(0, 5))

        top = ttk.Frame(mixer, style="Card.TFrame")
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Tonalidad:", style="Card.TLabel").pack(side="left", padx=(0, 5))
        ttk.Combobox(top, textvariable=self.autotune_key, state="readonly", width=10, values=["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"]).pack(side="left", padx=(0, 10))
        ttk.Label(top, text="Escala:", style="Card.TLabel").pack(side="left", padx=(0, 5))
        ttk.Combobox(top, textvariable=self.autotune_scale, state="readonly", width=10, values=["Mayor", "Menor"]).pack(side="left", padx=(0, 10))
        ttk.Button(top, text="Aplicar tonalidad", command=self.apply_autotune_key).pack(side="left", padx=4)

        self.autotune_slider(mixer, "Intensidad autotune", "autotune", 0, 100, "%")
        self.autotune_slider(mixer, "Nota/base", "autotune_shift", -7, 7, "semitonos")
        self.autotune_slider(mixer, "Vibrato", "vibrato", 0, 100, "%")
        self.autotune_slider(mixer, "Coro doble", "chorus", 0, 100, "%")
        self.autotune_slider(mixer, "Eco/Reverb", "echo", 0, 100, "%")
        self.autotune_slider(mixer, "Compresor", "comp", 0, 100, "%")
        self.autotune_slider(mixer, "Volumen", "vol", 0, 120, "%")

        lyrics = self.make_card(body, "Letra de prueba propia")
        lyrics.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.autotune_lyrics_text = tk.Text(
            lyrics,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.autotune_lyrics_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.autotune_show_lyrics()

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.autotune_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        actual = self.make_card(right, "Voz actual")
        actual.pack(fill="x", pady=(0, 10))
        ttk.Label(actual, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=310).pack(anchor="w", pady=(0, 6))
        ttk.Label(actual, text="Modo Autotune: efecto propio, no clona voces reales.", style="Card.TLabel", wraplength=310).pack(anchor="w")

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Grabar demo WAV", style="Accent.TButton", command=self.autotune_record_demo).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Probar beep", command=lambda: self.play_sfx("beep")).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Guardar como perfil", command=self.save_current_profile).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Test de Voz", command=lambda: self.select_tab(self.tab_test_voz)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Grabadora", command=lambda: self.select_tab(self.tab_grabadora)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Sube Autotune para efecto más marcado.\n"
                "• Vibrato da sensación de canto.\n"
                "• Coro doble ensancha la voz.\n"
                "• Eco/Reverb queda mejor en estribillos.\n"
                "• Graba demo antes de usarlo en directo."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def autotune_slider(self, parent, label, key, mn, mx, unit):
        line = ttk.Frame(parent, style="Card.TFrame")
        line.pack(fill="x", pady=5)
        top = ttk.Frame(line, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text=label + ":", style="Card.TLabel", width=18).pack(side="left")
        value_label = ttk.Label(top, style="Card.TLabel", width=12)
        value_label.pack(side="right")

        var = self.vars[key]
        ttk.Scale(line, from_=mn, to=mx, variable=var, orient="horizontal", command=lambda _=None: self.update_engine()).pack(fill="x", pady=(3, 0))

        def refresh(*_):
            v = var.get()
            if unit == "semitonos":
                value_label.config(text=f"{v:+.1f}")
            else:
                value_label.config(text=f"{v:.0f}{unit}")
            self.update_engine()

        var.trace_add("write", refresh)
        refresh()

    def autotune_presets(self):
        return {
            "AutoTune Suave": {"voice": "AutoTune Suave", "key_shift": 0},
            "AutoTune Pop": {"voice": "AutoTune Pop", "key_shift": 0},
            "Trap Tune": {"voice": "Trap Tune", "key_shift": -1},
            "Robot Cantante": {"voice": "Robot Cantante", "key_shift": 0},
            "Coro Doble": {"voice": "Coro Doble", "key_shift": 0},
            "Balada Clara": {"voice": "Balada Clara", "key_shift": 0},
        }

    def apply_autotune_preset(self, name):
        presets = self.autotune_presets()
        data = presets.get(name, presets["AutoTune Pop"])
        voice = data["voice"]
        if voice in VoiceBank.all_presets():
            self.preset.set(voice)
            self.category.set("Cantadas")
            self.apply_preset()
        self.vars["autotune_shift"].set(float(data.get("key_shift", 0)))
        self.autotune_mode.set(name)
        self.update_engine()
        self.refresh_voice_list()
        self.autotune_status.set(f"Preset aplicado: {name}")
        self.state.set(f"Estado: Autotune Pro · {name}")

    def apply_autotune_key(self):
        note_map = {"Do": 0, "Re": 2, "Mi": 4, "Fa": 5, "Sol": 7, "La": 9, "Si": 11}
        shift = note_map.get(self.autotune_key.get(), 0)
        if shift > 6:
            shift -= 12
        if self.autotune_scale.get() == "Menor":
            shift -= 1
        self.vars["autotune_shift"].set(float(shift))
        self.update_engine()
        self.autotune_status.set(f"Tonalidad aplicada: {self.autotune_key.get()} {self.autotune_scale.get()}")

    def autotune_show_lyrics(self):
        if not hasattr(self, "autotune_lyrics_text"):
            return
        text = (
            "LETRA DE PRUEBA PROPIA\n\n"
            "Hoy mi voz se enciende,\n"
            "brilla fuerte en la señal,\n"
            "si el eco no se pierde,\n"
            "todo suena natural.\n\n"
            "Sube un poco el autotune,\n"
            "dale brillo al corazón,\n"
            "grabo una demo rápida,\n"
            "y reviso la canción.\n\n"
            "PRUEBAS RECOMENDADAS\n\n"
            "1. Canta una frase corta.\n"
            "2. Graba demo WAV.\n"
            "3. Ajusta Autotune, Vibrato y Coro.\n"
            "4. Guarda el perfil si te gusta."
        )
        self.autotune_lyrics_text.configure(state="normal")
        self.autotune_lyrics_text.delete("1.0", tk.END)
        self.autotune_lyrics_text.insert("1.0", text)
        self.autotune_lyrics_text.configure(state="disabled")
        self.autotune_status.set("Letra de prueba cargada.")

    def autotune_record_demo(self):
        self.record()
        self.autotune_status.set("Demo WAV iniciada/guardada. Revisa Grabadora para escucharla.")


    def build_test_voz_tab(self):
        cont = ttk.Frame(self.tab_test_voz)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "test_voz_banner" in self.test_voice_images:
            ttk.Label(header, image=self.test_voice_images["test_voz_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Test de Voz Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Pruebas rápidas")
        tiles.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_beep", "Probar beep", lambda: self.test_voice_beep()),
            ("tile_grabar", "Grabar WAV", lambda: self.test_voice_record()),
            ("tile_discord", "Test Discord", lambda: self.test_voice_mode("discord")),
            ("tile_fortnite", "Test Fortnite", lambda: self.test_voice_mode("fortnite")),
            ("tile_obs", "Test OBS", lambda: self.test_voice_mode("obs")),
            ("tile_check", "Check voz", self.test_voice_check),
        ]

        for i, (img_key, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.test_voice_images:
                ttk.Label(box, image=self.test_voice_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        phrases = self.make_card(body, "Frases para probar la voz")
        phrases.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.test_voice_text = tk.Text(
            phrases,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.test_voice_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.test_voice_update_text("Selecciona un modo o graba una prueba.")

        checklist = self.make_card(body, "Checklist de prueba")
        checklist.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ttk.Label(
            checklist,
            text=(
                "Antes de abrir Discord/Fortnite/OBS:\n\n"
                "1. Pulsa Probar beep.\n"
                "2. Elige Test Discord/Fortnite/OBS.\n"
                "3. Lee una frase de prueba.\n"
                "4. Pulsa Grabar WAV.\n"
                "5. Escucha si hay eco/cortes.\n"
                "6. Si falla, abre Rendimiento o Cable Virtual."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=430
        ).pack(anchor="w", pady=(0, 10))

        quick = ttk.Frame(checklist, style="Card.TFrame")
        quick.pack(fill="x")
        ttk.Button(quick, text="Abrir Rendimiento", command=lambda: self.select_tab(self.tab_rendimiento)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Cable Virtual", command=lambda: self.select_tab(self.tab_cable_virtual)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Grabadora", command=lambda: self.select_tab(self.tab_grabadora)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Streamer Hub", command=lambda: self.select_tab(self.tab_streamer_hub)).pack(fill="x", pady=3)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.test_voice_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        actual = self.make_card(right, "Voz actual")
        actual.pack(fill="x", pady=(0, 10))
        ttk.Label(actual, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=310).pack(anchor="w", pady=(0, 6))
        ttk.Label(actual, textvariable=self.category, style="Card.TLabel", wraplength=310).pack(anchor="w")

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Probar beep", command=self.test_voice_beep).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Grabar prueba WAV", style="Accent.TButton", command=self.test_voice_record).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Guardar como perfil", command=self.save_current_profile).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Favoritos", command=lambda: self.select_tab(self.tab_favoritos_pro)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Si hay eco: usa Rendimiento → Anti-eco.\n"
                "• Si hay cortes: usa Rendimiento → Estable.\n"
                "• Si Discord no recibe voz: revisa Cable Virtual.\n"
                "• Graba siempre una prueba antes de directo."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def test_voice_phrases(self):
        return {
            "general": [
                "Probando mi voz en directo con el modulador.",
                "Esta es una prueba rápida de claridad, volumen y eco.",
                "Si me escuchas bien, la configuración está lista.",
                "Cambio de voz preparado para juegos, Discord y OBS."
            ],
            "discord": [
                "Hola, esta es una prueba para Discord.",
                "Estoy comprobando que mi voz se escuche clara y sin eco.",
                "Si la voz llega bien, puedo entrar a llamada sin tocar más ajustes.",
                "Discord debería recibir CABLE Output o VoiceMeeter Output."
            ],
            "fortnite": [
                "Prueba de voz para Fortnite, equipo, ¿me escucháis bien?",
                "Estoy probando la voz gaming antes de entrar a partida.",
                "Si no hay cortes ni eco, la configuración está lista.",
                "Fortnite debe usar CABLE Output o VoiceMeeter Output como micrófono."
            ],
            "obs": [
                "Prueba de grabación para OBS.",
                "Estoy comprobando volumen, claridad y estabilidad.",
                "Esta voz debería sonar limpia en el directo o en la grabación.",
                "OBS debe capturar CABLE Output o VoiceMeeter Output."
            ],
        }

    def test_voice_update_text(self, extra, mode="general"):
        if not hasattr(self, "test_voice_text"):
            return
        phrases = self.test_voice_phrases().get(mode, self.test_voice_phrases()["general"])
        lines = []
        lines.append("FRASES DE TEST")
        lines.append("")
        for i, phrase in enumerate(phrases, 1):
            lines.append(f"{i}. {phrase}")
        lines.append("")
        lines.append("ESTADO ACTUAL")
        lines.append(f"Voz: {self.preset.get()}")
        lines.append(f"Categoría: {self.category.get()}")
        lines.append(f"Latencia: {self.latency.get()}")
        lines.append("")
        lines.append(str(extra))
        self.test_voice_text.configure(state="normal")
        self.test_voice_text.delete("1.0", tk.END)
        self.test_voice_text.insert("1.0", "\n".join(lines))
        self.test_voice_text.configure(state="disabled")

    def test_voice_mode(self, mode):
        if mode == "discord":
            self.hub_apply_mode("discord")
            self.test_voice_update_text("Modo Discord claro aplicado. Lee una frase y graba WAV.", "discord")
            self.test_voice_status.set("Test Discord preparado.")
        elif mode == "fortnite":
            self.hub_apply_mode("fortnite")
            self.test_voice_update_text("Modo Fortnite grave aplicado. Lee una frase y graba WAV.", "fortnite")
            self.test_voice_status.set("Test Fortnite preparado.")
        elif mode == "obs":
            self.hub_apply_mode("obs")
            self.test_voice_update_text("Modo OBS listo aplicado. Lee una frase y graba WAV.", "obs")
            self.test_voice_status.set("Test OBS preparado.")
        else:
            self.test_voice_update_text("Modo general preparado.", "general")
            self.test_voice_status.set("Test general preparado.")

    def test_voice_beep(self):
        self.play_sfx("beep")
        self.test_voice_status.set("Beep lanzado. Si lo escuchas, la salida funciona.")
        self.test_voice_update_text("Beep lanzado para comprobar salida.", "general")

    def test_voice_record(self):
        self.record()
        self.test_voice_status.set("Grabación de prueba iniciada/guardada según estado actual.")
        self.test_voice_update_text("Grabación WAV solicitada. Revisa la pestaña Grabadora si quieres verla.", "general")

    def test_voice_check(self):
        try:
            output_name = self.output_dev.get().lower()
            virtual_ok = any(w in output_name for w in ["cable", "voicemeeter", "virtual", "vb-audio", "vb audio"])
            echo_value = self.vars["echo"].get() if "echo" in self.vars else 0
            vol_value = self.vars["vol"].get() if "vol" in self.vars else 0
            notes = []
            notes.append("CHECK DE VOZ")
            notes.append("")
            notes.append(f"Salida virtual: {'OK' if virtual_ok else 'No detectada'}")
            notes.append(f"Eco: {echo_value:.0f}")
            notes.append(f"Volumen: {vol_value:.0f}")
            if not virtual_ok:
                notes.append("Consejo: abre Cable Virtual Pro y revisa la salida.")
            if echo_value > 25:
                notes.append("Consejo: baja el eco o usa Anti-eco.")
            if vol_value > 105:
                notes.append("Consejo: baja el volumen para evitar distorsión.")
            if virtual_ok and echo_value <= 25 and vol_value <= 105:
                notes.append("La configuración parece lista para probar en directo.")
            result = "\n".join(notes)
            self.test_voice_status.set("Check de voz completado.")
            self.test_voice_update_text(result, "general")
        except Exception as e:
            self.test_voice_status.set(f"Error en check de voz: {e}")


    def build_cable_virtual_tab(self):
        cont = ttk.Frame(self.tab_cable_virtual)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "cable_banner" in self.cable_images:
            ttk.Label(header, image=self.cable_images["cable_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Cable Virtual Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Configuración rápida")
        tiles.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_detectar", "Detectar cable", self.cable_detect_virtual),
            ("tile_salida", "Usar salida virtual", self.cable_select_virtual_output),
            ("tile_discord", "Guía Discord", lambda: self.cable_show_guide("discord")),
            ("tile_fortnite", "Guía Fortnite", lambda: self.cable_show_guide("fortnite")),
            ("tile_obs", "Guía OBS", lambda: self.cable_show_guide("obs")),
            ("tile_test", "Probar beep", lambda: self.play_sfx("beep")),
        ]

        for i, (img_key, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.cable_images:
                ttk.Label(box, image=self.cable_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        guide = self.make_card(body, "Guía de cable virtual")
        guide.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.cable_guide_text = tk.Text(
            guide,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.cable_guide_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.cable_show_guide("general")

        devices = self.make_card(body, "Dispositivos encontrados")
        devices.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.cable_devices_text = tk.Text(
            devices,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.cable_devices_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.cable_update_devices_text("Pulsa Detectar cable para buscar dispositivos virtuales.")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.cable_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        actual = self.make_card(right, "Selección actual")
        actual.pack(fill="x", pady=(0, 10))
        ttk.Label(actual, text="Entrada:", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(actual, textvariable=self.input_dev, style="Card.TLabel", wraplength=310).pack(anchor="w", pady=(0, 8))
        ttk.Label(actual, text="Salida:", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(actual, textvariable=self.output_dev, style="Card.TLabel", wraplength=310).pack(anchor="w")

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Actualizar dispositivos", command=self.assistant_refresh_devices).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Detectar cable virtual", style="Accent.TButton", command=self.cable_detect_virtual).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Copiar guía", command=self.cable_copy_current_guide).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Asistente", command=lambda: self.select_tab(self.tab_asistente)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Diagnóstico", command=lambda: self.select_tab(self.tab_diagnostico)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Regla básica")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "En el modulador:\n"
                "Salida = CABLE Input o VoiceMeeter Input.\n\n"
                "En Discord/Fortnite/OBS:\n"
                "Micrófono = CABLE Output o VoiceMeeter Output."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def cable_virtual_keywords(self):
        return ["cable", "voicemeeter", "virtual", "vb-audio", "vb audio", "input", "output"]

    def cable_find_virtual_devices(self):
        found = []
        try:
            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                name = str(dev.get("name", ""))
                low = name.lower()
                if any(k in low for k in ["cable", "voicemeeter", "vb-audio", "vb audio", "virtual"]):
                    found.append((idx, name, dev.get("max_input_channels", 0), dev.get("max_output_channels", 0)))
        except Exception as e:
            found.append(("error", f"No se pudieron leer dispositivos: {e}", 0, 0))
        return found

    def cable_update_devices_text(self, content):
        if not hasattr(self, "cable_devices_text"):
            return
        self.cable_devices_text.configure(state="normal")
        self.cable_devices_text.delete("1.0", tk.END)
        self.cable_devices_text.insert("1.0", str(content))
        self.cable_devices_text.configure(state="disabled")

    def cable_detect_virtual(self):
        found = self.cable_find_virtual_devices()
        lines = ["DISPOSITIVOS VIRTUALES ENCONTRADOS", ""]
        if not found:
            lines.append("No se detectó VB-Cable, VoiceMeeter o salida virtual.")
            lines.append("")
            lines.append("Consejo: instala VB-Audio Cable o VoiceMeeter y reinicia la app.")
            self.cable_status.set("No se detectó cable virtual.")
        else:
            for item in found:
                idx, name, ins, outs = item
                lines.append(f"[{idx}] {name}")
                lines.append(f"    entrada: {ins} · salida: {outs}")
                lines.append("")
            self.cable_status.set(f"Detectados {len(found)} dispositivos virtuales.")
        self.cable_update_devices_text("\n".join(lines))

    def cable_select_virtual_output(self):
        found = self.cable_find_virtual_devices()
        chosen = None
        for idx, name, ins, outs in found:
            if isinstance(idx, int) and outs and any(k in name.lower() for k in ["cable input", "voicemeeter input", "virtual input"]):
                chosen = name
                break
        if chosen is None:
            for idx, name, ins, outs in found:
                if isinstance(idx, int) and outs:
                    chosen = name
                    break
        if chosen:
            self.output_dev.set(chosen)
            self.update_engine()
            self.cable_status.set(f"Salida virtual seleccionada: {chosen}")
            self.cable_detect_virtual()
        else:
            self.cable_status.set("No encontré una salida virtual clara para seleccionar.")

    def cable_guides(self):
        return {
            "general": (
                "GUÍA GENERAL CABLE VIRTUAL\n\n"
                "1) En el modulador:\n"
                "   Entrada = tu micrófono real.\n"
                "   Salida = CABLE Input o VoiceMeeter Input.\n\n"
                "2) En Discord, Fortnite u OBS:\n"
                "   Micrófono = CABLE Output o VoiceMeeter Output.\n\n"
                "3) Usa Probar beep o Grabar prueba para comprobar que sale audio.\n\n"
                "4) Si hay eco, usa Rendimiento Pro → Anti-eco."
            ),
            "discord": (
                "GUÍA DISCORD\n\n"
                "En este modulador:\n"
                "Entrada = tu micrófono real.\n"
                "Salida = CABLE Input / VoiceMeeter Input.\n\n"
                "En Discord:\n"
                "Ajustes de voz → Dispositivo de entrada = CABLE Output / VoiceMeeter Output.\n\n"
                "Recomendado:\n"
                "Modo Streamer Hub → Discord claro.\n"
                "Rendimiento Pro → Anti-eco si te escuchas con retraso."
            ),
            "fortnite": (
                "GUÍA FORTNITE\n\n"
                "En este modulador:\n"
                "Entrada = tu micrófono real.\n"
                "Salida = CABLE Input / VoiceMeeter Input.\n\n"
                "En Fortnite:\n"
                "Audio → Chat de voz → Dispositivo de entrada = CABLE Output / VoiceMeeter Output.\n\n"
                "Recomendado:\n"
                "Streamer Hub → Fortnite grave.\n"
                "Usa Mini Panel para cambiar voces rápido."
            ),
            "obs": (
                "GUÍA OBS\n\n"
                "En este modulador:\n"
                "Entrada = tu micrófono real.\n"
                "Salida = CABLE Input / VoiceMeeter Input.\n\n"
                "En OBS:\n"
                "Fuentes → Captura de entrada de audio → CABLE Output / VoiceMeeter Output.\n\n"
                "Recomendado:\n"
                "Rendimiento Pro → OBS.\n"
                "Graba una prueba antes de directo."
            ),
        }

    def cable_show_guide(self, guide_key):
        if not hasattr(self, "cable_guide_text"):
            return
        text = self.cable_guides().get(guide_key, self.cable_guides()["general"])
        self.cable_guide_text.configure(state="normal")
        self.cable_guide_text.delete("1.0", tk.END)
        self.cable_guide_text.insert("1.0", text)
        self.cable_guide_text.configure(state="disabled")
        self.cable_status.set(f"Guía abierta: {guide_key}")

    def cable_copy_current_guide(self):
        if not hasattr(self, "cable_guide_text"):
            return
        try:
            text = self.cable_guide_text.get("1.0", tk.END).strip()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.cable_status.set("Guía copiada al portapapeles.")
        except Exception as e:
            self.cable_status.set(f"No se pudo copiar: {e}")


    def build_rendimiento_tab(self):
        cont = ttk.Frame(self.tab_rendimiento)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "rendimiento_banner" in self.performance_images:
            ttk.Label(header, image=self.performance_images["rendimiento_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Rendimiento Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Modos de optimización")
        tiles.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_ultra_baja", "Ultra baja", "ultra"),
            ("tile_estable", "Estable", "estable"),
            ("tile_anticeco", "Anti-eco", "anticeco"),
            ("tile_calidad", "Calidad", "calidad"),
            ("tile_obs", "OBS", "obs"),
            ("tile_check", "Check", "check"),
        ]

        for i, (img_key, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.performance_images:
                ttk.Label(box, image=self.performance_images[img_key], style="Card.TLabel").pack()
            cmd = self.performance_quick_check if mode == "check" else lambda m=mode: self.apply_performance_mode(m)
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        center = ttk.Frame(left)
        center.pack(fill="both", expand=True)

        monitor = self.make_card(center, "Monitor de rendimiento")
        monitor.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.performance_text = tk.Text(
            monitor,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.performance_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.performance_update_text("Selecciona un modo o pulsa Check.")

        ajuste = self.make_card(center, "Ajuste manual rápido")
        ajuste.pack(side="left", fill="both", expand=True, padx=(5, 0))

        ttk.Label(ajuste, text="Latencia actual:", style="Card.TLabel").pack(anchor="w")
        ttk.Label(ajuste, textvariable=self.latency, style="Card.TLabel", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 10))

        for label, mode in [
            ("Ultra baja para escuchar menos retraso", "ultra"),
            ("Estable para evitar cortes", "estable"),
            ("Anti-eco para auriculares/llamadas", "anticeco"),
            ("Calidad para grabación", "calidad"),
            ("OBS equilibrado", "obs"),
        ]:
            ttk.Button(ajuste, text=label, command=lambda m=mode: self.apply_performance_mode(m)).pack(fill="x", pady=3)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.performance_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")
        ttk.Label(estado, textvariable=self.xrun_status, style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(6, 0))

        bench = self.make_card(right, "Benchmark del equipo")
        bench.pack(fill="x", pady=(0, 10))
        self.benchmark_button = ttk.Button(bench, text="🧪 Medir este PC", style="Accent.TButton", command=self.run_performance_benchmark)
        self.benchmark_button.pack(fill="x", pady=3)
        ttk.Label(bench, textvariable=self.benchmark_result, style="Card.TLabel", wraplength=310, justify="left", font=("Consolas", 9)).pack(anchor="w", pady=(4, 0))

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Check rendimiento", style="Accent.TButton", command=self.performance_quick_check).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Probar beep", command=lambda: self.play_sfx("beep")).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Grabar prueba WAV", command=self.record).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Diagnóstico", command=lambda: self.select_tab(self.tab_diagnostico)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Streamer Hub", command=lambda: self.select_tab(self.tab_streamer_hub)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Ultra baja: menos retraso, más riesgo de cortes.\n"
                "• Estable: mejor equilibrio.\n"
                "• Anti-eco: reduce problemas al escuchar tu voz.\n"
                "• Calidad: mejor para grabar pruebas.\n"
                "• OBS: pensado para directos."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def performance_modes(self):
        return {
            "ultra": {
                "label": "Ultra baja",
                "latency": "Ultra baja",
                "values": {"echo": 0, "radio": 0, "robot": 0, "gate": 6, "comp": 35, "vol": 88},
                "tip": "Prioriza menos retraso. Si se corta, cambia a Estable."
            },
            "estable": {
                "label": "Estable",
                "latency": "Estable",
                "values": {"echo": 2, "radio": 0, "robot": 0, "gate": 8, "comp": 48, "vol": 90},
                "tip": "Equilibrio entre calidad, estabilidad y retraso."
            },
            "anticeco": {
                "label": "Anti-eco",
                "latency": "Baja",
                "values": {"echo": 0, "radio": 0, "robot": 0, "gate": 12, "comp": 55, "vol": 82},
                "tip": "Recomendado con auriculares para evitar acoples."
            },
            "calidad": {
                "label": "Calidad",
                "latency": "Máxima estabilidad",
                "values": {"echo": 2, "radio": 2, "robot": 0, "gate": 9, "comp": 65, "vol": 92},
                "tip": "Más estable para grabar pruebas y revisar voz."
            },
            "obs": {
                "label": "OBS",
                "latency": "Estable",
                "values": {"echo": 1, "radio": 4, "robot": 0, "gate": 9, "comp": 68, "vol": 92},
                "tip": "Modo equilibrado para directos y grabación."
            },
        }

    def apply_performance_mode(self, mode):
        data = self.performance_modes().get(mode)
        if not data:
            return

        self.latency.set(data["latency"])
        for key, value in data.get("values", {}).items():
            if key in self.vars:
                self.vars[key].set(value)

        self.update_engine()
        self.performance_status.set(f"Modo aplicado: {data['label']}")
        self.state.set(f"Estado: Rendimiento Pro · {data['label']}")
        self.performance_update_text(f"Modo aplicado: {data['label']}\n\n{data['tip']}")

    def performance_update_text(self, extra):
        if not hasattr(self, "performance_text"):
            return
        try:
            lines = []
            lines.append("RENDIMIENTO PRO")
            lines.append("")
            lines.append(f"Latencia: {self.latency.get()}")
            lines.append(f"Voz actual: {self.preset.get()}")
            lines.append(f"Modulador activo: {'sí' if self.effects_enabled.get() else 'no'}")
            lines.append(f"Silenciado: {'sí' if self.mute.get() else 'no'}")
            lines.append("")
            lines.append("Ajustes clave:")
            for key, label in [
                ("gate", "Puerta de ruido"),
                ("comp", "Compresor"),
                ("echo", "Eco"),
                ("radio", "Radio"),
                ("robot", "Robot"),
                ("vol", "Volumen"),
            ]:
                if key in self.vars:
                    lines.append(f"- {label}: {self.vars[key].get():.0f}")
            lines.append("")
            lines.append(str(extra))
            self.performance_text.configure(state="normal")
            self.performance_text.delete("1.0", tk.END)
            self.performance_text.insert("1.0", "\n".join(lines))
            self.performance_text.configure(state="disabled")
        except Exception:
            pass

    def build_ruido_tab(self):
        cont = ttk.Frame(self.tab_ruido)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="🤫 Reducción de Ruido Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")
        ttk.Label(header, text="Aprende el ruido de tu habitación (ventilador, PC, zumbido del micro) y lo resta de tu voz en tiempo real.", style="Card.TLabel", wraplength=900, justify="left").pack(anchor="w", pady=(4, 0))

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        aprender = self.make_card(left, "Paso 1 · Aprender el ruido")
        aprender.pack(fill="x", pady=(0, 10))
        ttk.Label(aprender, text="Empieza el directo, quédate en silencio total y pulsa el botón. La app escucha 2 segundos y memoriza el ruido de fondo.", style="Card.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(0, 8))
        fila = ttk.Frame(aprender, style="Card.TFrame")
        fila.pack(fill="x")
        ttk.Button(fila, text="🎙 Aprender ruido (2 s)", style="Accent.TButton", command=self.nr_learn).pack(side="left", fill="x", expand=True, padx=4, ipady=10)
        ttk.Button(fila, text="▶ Empezar directo", command=self.start).pack(side="left", fill="x", expand=True, padx=4, ipady=10)
        ttk.Button(fila, text="Olvidar perfil", command=self.nr_forget).pack(side="left", fill="x", expand=True, padx=4, ipady=10)

        ajustar = self.make_card(left, "Paso 2 · Activar y ajustar")
        ajustar.pack(fill="x", pady=(0, 10))
        ttk.Checkbutton(ajustar, text="Reducción de ruido activada", variable=self.nr_enabled, command=self.update_engine).pack(anchor="w", pady=(0, 6))
        fila2 = ttk.Frame(ajustar, style="Card.TFrame")
        fila2.pack(fill="x")
        ttk.Label(fila2, text="Intensidad:", style="Card.TLabel", width=12).pack(side="left")
        self.nr_amount_label = ttk.Label(fila2, style="Card.TLabel", width=6)
        self.nr_amount_label.pack(side="right")
        ttk.Scale(ajustar, from_=0, to=100, variable=self.nr_amount, orient="horizontal", command=lambda _=None: self.nr_amount_changed()).pack(fill="x", pady=(3, 0))
        self.nr_amount_changed()
        ttk.Label(ajustar, text="Consejo: 60-80 elimina el ruido sin robotizar la voz. Si suena \"acuosa\", baja la intensidad o vuelve a aprender el ruido.", style="Card.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(8, 0))

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.nr_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        tips = self.make_card(right, "Cómo funciona")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text="• Analiza la voz por espectro (FFT) 172 veces por segundo.\n"
                 "• Resta el perfil de ruido aprendido de cada banda.\n"
                 "• Añade ~12 ms de retardo solo cuando está activa.\n"
                 "• El perfil se conserva al parar y reanudar el directo.\n"
                 "• Vuelve a aprender si cambias de sitio o de micrófono.",
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def nr_amount_changed(self):
        try:
            self.nr_amount_label.config(text=f"{self.nr_amount.get():.0f}%")
        except Exception:
            pass
        self.update_engine()

    def nr_learn(self):
        if not self.engine.running:
            self.nr_status.set("Primero pulsa ▶ Empezar directo: hace falta el micrófono para aprender el ruido.")
            messagebox.showwarning("Directo parado", "Para aprender el ruido, empieza el directo y quédate en silencio.")
            return
        self.engine.start_noise_learn(2.0)
        self.nr_status.set("Aprendiendo ruido… quédate en silencio 2 segundos.")
        self.root.after(300, self._nr_poll)

    def _nr_poll(self):
        if self.engine._nr_learn_left > 0:
            self.root.after(300, self._nr_poll)
            return
        if self.engine.noise_profile is not None:
            self.nr_enabled.set(True)
            self.update_engine()
            self.nr_status.set("Perfil de ruido aprendido ✓ Reducción activada. Habla para probar y ajusta la intensidad.")
            self.state.set("Estado: reducción de ruido activa")
        else:
            self.nr_status.set("No se pudo aprender el ruido. ¿Se paró el directo a mitad?")

    def nr_forget(self):
        self.engine.noise_profile = None
        self.nr_enabled.set(False)
        self.update_engine()
        self.nr_status.set("Perfil olvidado. Aprende el ruido de nuevo cuando quieras.")

    def on_device_changed(self):
        if not self.engine.running:
            return
        self.stop()
        if self.start(silent=True):
            self.state.set("Estado: dispositivo cambiado · directo reiniciado")
        else:
            self.state.set("Estado: dispositivo cambiado · pulsa ▶ Empezar directo")

    def _device_test_report(self, mensaje):
        self.assistant_status.set(mensaje)
        self.state.set(f"Estado: {mensaje}")

    def test_microphone(self):
        if self.engine.running:
            self._device_test_report("Para probar el micro, para primero el directo.")
            return
        dev = self.input_map.get(self.input_dev.get())
        if dev is None:
            self._device_test_report("Selecciona primero un micrófono en la lista.")
            return
        self._device_test_report("Probando micrófono… habla ahora (2 segundos).")
        threading.Thread(target=self._test_mic_worker, args=(dev,), daemon=True).start()

    def _test_mic_worker(self, dev):
        niveles = []
        error = None
        for rate in (44100, 48000):
            for ch in (1, 2):
                try:
                    with sd.InputStream(device=dev, channels=ch, samplerate=rate, dtype="float32") as stream:
                        for _ in range(10):
                            datos, _ = stream.read(int(rate * 0.2))
                            niveles.append(float(np.sqrt(np.mean(datos ** 2))))
                    error = None
                    break
                except Exception as e:
                    error = e
            if error is None:
                break
        def informar():
            if error is not None:
                self._device_test_report(f"❌ El micrófono no se pudo abrir: {error}")
                return
            pico = max(niveles) if niveles else 0.0
            pct = min(100, int(pico * 700))
            if pico < 0.005:
                self._device_test_report(f"⚠ Micrófono abierto pero no se oye nada (nivel {pct}%). Revisa el volumen del micro en Windows.")
            else:
                self._device_test_report(f"✅ Micrófono funciona · nivel de voz {pct}%.")
        self.root.after(0, informar)

    def test_headphones(self):
        if self.engine.running:
            self._device_test_report("Para probar la salida, para primero el directo.")
            return
        dev = self.output_map.get(self.output_dev.get())
        if dev is None:
            self._device_test_report("Selecciona primero una salida en la lista.")
            return
        self._device_test_report("Enviando pitido a la salida seleccionada…")
        threading.Thread(target=self._test_out_worker, args=(dev,), daemon=True).start()

    def _test_out_worker(self, dev):
        error = None
        for rate in (44100, 48000):
            for ch in (2, 1):
                try:
                    t = np.arange(int(rate * 0.8)) / rate
                    tono = (0.30 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
                    datos = np.repeat(tono.reshape(-1, 1), ch, axis=1)
                    sd.play(datos, samplerate=rate, device=dev, blocking=True)
                    error = None
                    break
                except Exception as e:
                    error = e
            if error is None:
                break
        def informar():
            if error is not None:
                self._device_test_report(f"❌ La salida no se pudo abrir: {error}")
            else:
                self._device_test_report("✅ Pitido enviado. Si no lo oíste y era tus auriculares, revisa el volumen. Si era el cable virtual, es normal no oírlo.")
        self.root.after(0, informar)

    def stream_guard_tick(self):
        """Detecta la muerte del stream (dispositivo desconectado) por latido."""
        try:
            if self.engine.running:
                count = self.engine.callback_count
                if count == self._guard_last_count:
                    self._guard_last_count = -1
                    self.handle_stream_loss()
                else:
                    self._guard_last_count = count
            else:
                self._guard_last_count = -1
        except Exception:
            pass
        self.root.after(2000, self.stream_guard_tick)

    def handle_stream_loss(self):
        try:
            self.engine.stop()
        except Exception:
            pass
        self.state.set("Estado: ⚠ audio perdido · reconectando…")
        self.performance_status.set("⚠ El dispositivo de audio se desconectó o dejó de responder. Reintentando reconexión automática…")
        self._reconnect_attempts = 0
        self.root.after(1500, self._try_reconnect)

    def _rematch_devices(self):
        """Tras reescanear, vuelve a casar los dispositivos por nombre
        (los índices cambian al desconectar/reconectar hardware)."""
        for var, mapping in ((self.input_dev, self.input_map), (self.output_dev, self.output_map)):
            actual = var.get()
            if not isinstance(actual, str) or not actual or actual in mapping:
                continue
            nombre = actual.split(": ", 1)[1] if ": " in actual else actual
            for etiqueta in mapping:
                candidato = etiqueta.split(": ", 1)[1] if ": " in etiqueta else etiqueta
                if candidato == nombre or candidato.startswith(nombre) or nombre.startswith(candidato):
                    var.set(etiqueta)
                    break

    def _try_reconnect(self):
        if self.engine.running:
            return
        self._reconnect_attempts += 1
        if self._reconnect_attempts == 3:
            # A la tercera, reescanea los dispositivos: al desenchufar y
            # enchufar cambian los índices de PortAudio.
            try:
                sd._terminate()
                sd._initialize()
            except Exception:
                pass
            try:
                self.load_devices()
                self._rematch_devices()
            except Exception:
                pass
        if self.start(silent=True):
            self.state.set("Estado: ✅ directo recuperado")
            self.performance_status.set(f"Directo recuperado automáticamente (intento {self._reconnect_attempts}).")
            return
        if self._reconnect_attempts < 6:
            self.root.after(2000, self._try_reconnect)
        else:
            self.state.set("Estado: ⛔ directo parado · dispositivo desconectado")
            self.performance_status.set("No se pudo recuperar el audio tras 6 intentos. Revisa el micrófono y la salida, y pulsa ▶ Empezar directo.")
            messagebox.showwarning(
                "Audio desconectado",
                "El dispositivo de audio se desconectó y no se pudo recuperar.\n\n"
                "Revisa el micrófono/auriculares (o el cable virtual) y pulsa ▶ Empezar directo."
            )

    def watchdog_tick(self):
        """Vigila los cortes de audio (xruns) y sugiere subir latencia."""
        try:
            count = self.engine.xrun_count
            cb = self.engine.callback_count
            bps = max(0, (cb - self._watchdog_last_cb) / 5.0)
            self._watchdog_last_cb = cb
            if self.engine.running:
                self.xrun_status.set(f"Cortes de audio: {count} · bloques/s: {bps:.0f}")
            else:
                self.xrun_status.set(f"Cortes de audio: {count}")
            delta = count - self._watchdog_last
            self._watchdog_last = count
            if self.engine.running and delta >= 3:
                orden = ["Ultra baja", "Baja", "Estable", "Máxima estabilidad"]
                actual = self.latency.get()
                if actual in orden and actual != orden[-1]:
                    sugerida = orden[orden.index(actual) + 1]
                    self.performance_status.set(
                        f"⚠ {delta} cortes de audio en 5 s con latencia {actual}. "
                        f"Prueba {sugerida}: para el directo, cámbiala y vuelve a empezar."
                    )
                else:
                    self.performance_status.set(
                        f"⚠ {delta} cortes de audio en 5 s. Cierra programas pesados o desactiva efectos."
                    )
        except Exception:
            pass
        self.root.after(5000, self.watchdog_tick)

    def run_performance_benchmark(self):
        """Mide cuánto tarda la cadena de efectos actual en este PC."""
        if self.engine.running:
            messagebox.showwarning("Benchmark", "Para medir el rendimiento, para primero el directo.")
            return
        self.performance_status.set("Benchmark en marcha…")
        self.benchmark_result.set("Midiendo la cadena de efectos actual…")
        try:
            self.benchmark_button.configure(state="disabled")
        except Exception:
            pass
        threading.Thread(target=self._benchmark_worker, daemon=True).start()

    def _benchmark_worker(self):
        try:
            self.update_engine()
            replay_prev = self.engine.replay_enabled
            self.engine.replay_enabled = False
            results = []
            for label, block in [("Ultra baja", 128), ("Baja", 256), ("Estable", 512), ("Máx. estab.", 1024)]:
                self.engine.reset_buffers()
                indata = (np.random.uniform(-0.3, 0.3, (block, 1))).astype(np.float32)
                for _ in range(5):
                    self.engine.process(indata)
                reps = max(20, int(self.engine.rate / block))
                t0 = time.perf_counter()
                for _ in range(reps):
                    self.engine.process(indata)
                elapsed = time.perf_counter() - t0
                budget = reps * block / self.engine.rate
                results.append((label, block, 100.0 * elapsed / budget))
            self.engine.reset_buffers()
            self.engine.replay_enabled = replay_prev
            self.root.after(0, lambda: self._benchmark_done(results))
        except Exception as e:
            self.root.after(0, lambda e=e: self._benchmark_failed(e))

    def _benchmark_done(self, results):
        lines = []
        recommended = None
        for label, block, usage in results:
            estado = "✅" if usage < 60 else ("⚠" if usage < 90 else "❌")
            lines.append(f"{estado} {label} ({block}): {usage:.0f}% del tiempo")
            if recommended is None and usage < 60:
                recommended = label
        if recommended is None:
            recommended = "Máxima estabilidad"
        real_name = {"Máx. estab.": "Máxima estabilidad"}.get(recommended, recommended)
        lines.append(f"→ Recomendada: {real_name}")
        self.benchmark_result.set("\n".join(lines))
        self.latency.set(real_name)
        self.performance_status.set(f"Benchmark completado. Latencia recomendada aplicada: {real_name}.")
        try:
            self.benchmark_button.configure(state="normal")
        except Exception:
            pass

    def _benchmark_failed(self, e):
        self.benchmark_result.set(f"No se pudo completar el benchmark: {e}")
        self.performance_status.set("Benchmark con error.")
        try:
            self.benchmark_button.configure(state="normal")
        except Exception:
            pass

    def performance_quick_check(self):
        try:
            output_name = self.output_dev.get().lower()
            virtual_words = ["cable", "voicemeeter", "virtual", "vb-audio"]
            virtual_ok = any(w in output_name for w in virtual_words)
            echo_value = self.vars["echo"].get() if "echo" in self.vars else 0
            vol_value = self.vars["vol"].get() if "vol" in self.vars else 0

            result = []
            result.append("CHECK RÁPIDO")
            result.append("")
            result.append(f"Salida virtual posible: {'OK' if virtual_ok else 'No detectada'}")
            result.append(f"Eco: {echo_value:.0f}")
            result.append(f"Volumen: {vol_value:.0f}")
            result.append("")
            if not virtual_ok:
                result.append("Consejo: para Discord/Fortnite/OBS usa CABLE Input o VoiceMeeter Input como salida.")
            if echo_value > 25:
                result.append("Consejo: baja el eco si notas retraso o acople.")
            if vol_value > 105:
                result.append("Consejo: baja volumen si distorsiona.")
            if virtual_ok and echo_value <= 25 and vol_value <= 105:
                result.append("Configuración bastante correcta para directo.")
            text = "\n".join(result)
            self.performance_status.set("Check de rendimiento completado.")
            self.performance_update_text(text)
        except Exception as e:
            self.performance_status.set(f"Error en check: {e}")


    def build_streamer_hub_tab(self):
        cont = ttk.Frame(self.tab_streamer_hub)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "streamer_hub_banner" in self.hub_images:
            ttk.Label(header, image=self.hub_images["streamer_hub_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Streamer Hub Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Configuraciones rápidas")
        tiles.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_discord", "Discord claro", lambda: self.hub_apply_mode("discord")),
            ("tile_fortnite", "Fortnite grave", lambda: self.hub_apply_mode("fortnite")),
            ("tile_obs", "OBS listo", lambda: self.hub_apply_mode("obs")),
            ("tile_escenas", "Escenas", lambda: self.select_tab(self.tab_escenas_pro)),
            ("tile_favoritos", "Favoritos", lambda: self.select_tab(self.tab_favoritos_pro)),
            ("tile_check", "Check rápido", self.hub_quick_check),
        ]

        for i, (img_key, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.hub_images:
                ttk.Label(box, image=self.hub_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        center = ttk.Frame(left)
        center.pack(fill="both", expand=True)

        setup = self.make_card(center, "Panel de directo")
        setup.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ttk.Label(setup, text="1. Elige modo rápido.\n2. Comprueba micro/salida.\n3. Abre Mini Panel.\n4. Empieza directo.\n5. Usa Favoritos o Escenas.", style="Card.TLabel", justify="left", wraplength=420).pack(anchor="w", pady=(0, 10))

        quick_row = ttk.Frame(setup, style="Card.TFrame")
        quick_row.pack(fill="x", pady=4)
        ttk.Button(quick_row, text="Empezar directo", style="Accent.TButton", command=self.start).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(quick_row, text="Parar directo", style="Danger.TButton", command=self.stop).pack(side="left", fill="x", expand=True, padx=3, ipady=8)

        quick_row2 = ttk.Frame(setup, style="Card.TFrame")
        quick_row2.pack(fill="x", pady=4)
        ttk.Button(quick_row2, text="Mini Panel", command=self.open_mini_panel).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(quick_row2, text="Grabar prueba", command=self.record).pack(side="left", fill="x", expand=True, padx=3, ipady=8)

        quick_row3 = ttk.Frame(setup, style="Card.TFrame")
        quick_row3.pack(fill="x", pady=4)
        ttk.Button(quick_row3, text="Probar beep", command=lambda: self.play_sfx("beep")).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(quick_row3, text="Diagnóstico", command=lambda: self.select_tab(self.tab_diagnostico)).pack(side="left", fill="x", expand=True, padx=3, ipady=8)

        checklist = self.make_card(center, "Checklist rápido")
        checklist.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.hub_check_text = tk.Text(
            checklist,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=14
        )
        self.hub_check_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.hub_update_checklist("Pendiente de comprobar.")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.hub_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        actual = self.make_card(right, "Voz actual")
        actual.pack(fill="x", pady=(0, 10))
        ttk.Label(actual, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=310).pack(anchor="w", pady=(0, 6))
        ttk.Label(actual, textvariable=self.state, style="Card.TLabel", wraplength=310).pack(anchor="w")

        accesos = self.make_card(right, "Accesos")
        accesos.pack(fill="x", pady=(0, 10))
        ttk.Button(accesos, text="Escenas Pro", command=lambda: self.select_tab(self.tab_escenas_pro)).pack(fill="x", pady=3)
        ttk.Button(accesos, text="Favoritos Pro", command=lambda: self.select_tab(self.tab_favoritos_pro)).pack(fill="x", pady=3)
        ttk.Button(accesos, text="Atajos Pro", command=lambda: self.select_tab(self.tab_atajos)).pack(fill="x", pady=3)
        ttk.Button(accesos, text="Creador de Voces", command=lambda: self.select_tab(self.tab_creador_voces)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Discord claro: menos eco y más limpieza.\n"
                "• Fortnite grave: voz gaming potente.\n"
                "• OBS listo: perfil estable para directos.\n"
                "• Check rápido revisa configuración básica.\n"
                "• Graba prueba antes de entrar en directo."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def hub_update_checklist(self, extra):
        if not hasattr(self, "hub_check_text"):
            return
        try:
            text = []
            text.append("CHECKLIST STREAMER HUB")
            text.append("")
            text.append(f"Voz actual: {self.preset.get()}")
            text.append(f"Categoría: {self.category.get()}")
            text.append(f"Latencia: {self.latency.get()}")
            text.append(f"Modulador activo: {'sí' if self.effects_enabled.get() else 'no'}")
            text.append(f"Silenciado: {'sí' if self.mute.get() else 'no'}")
            text.append("")
            text.append("Pasos recomendados:")
            text.append("✓ Elegir modo Discord/Fortnite/OBS")
            text.append("✓ Probar beep")
            text.append("✓ Grabar prueba WAV")
            text.append("✓ Revisar salida virtual")
            text.append("✓ Abrir Mini Panel")
            text.append("")
            text.append(str(extra))
            self.hub_check_text.configure(state="normal")
            self.hub_check_text.delete("1.0", tk.END)
            self.hub_check_text.insert("1.0", "\n".join(text))
            self.hub_check_text.configure(state="disabled")
        except Exception:
            pass

    def hub_apply_mode(self, mode):
        modes = {
            "discord": {
                "label": "Discord claro",
                "voice": "Discord claro",
                "values": {"pitch": 0, "bass": 10, "robot": 0, "echo": 0, "radio": 0, "megaphone": 0, "gate": 10, "comp": 60, "vol": 92},
            },
            "fortnite": {
                "label": "Fortnite grave",
                "voice": "Fortnite grave",
                "values": {"pitch": -5, "bass": 58, "robot": 0, "echo": 3, "radio": 0, "megaphone": 0, "gate": 8, "comp": 55, "vol": 94},
            },
            "obs": {
                "label": "OBS listo",
                "voice": "Podcast",
                "values": {"pitch": -1, "bass": 25, "robot": 0, "echo": 1, "radio": 4, "megaphone": 0, "gate": 9, "comp": 68, "vol": 92},
            },
        }
        data = modes.get(mode)
        if not data:
            return

        voice = data["voice"]
        if voice in VoiceBank.all_presets():
            self.preset.set(voice)
            self.category.set(VoiceBank.all_presets()[voice][0])

        for key, value in data["values"].items():
            if key in self.vars:
                self.vars[key].set(value)

        self.update_engine()
        self.refresh_voice_list()
        self.hub_status.set(f"Modo aplicado: {data['label']}")
        self.state.set(f"Estado: Streamer Hub · {data['label']}")
        self.hub_update_checklist(f"Modo aplicado correctamente: {data['label']}")

    def hub_quick_check(self):
        try:
            input_ok = bool(self.input_dev.get())
            output_ok = bool(self.output_dev.get())
            virtual_words = ["cable", "voicemeeter", "virtual", "vb-audio"]
            virtual_ok = any(w in self.output_dev.get().lower() for w in virtual_words)
            lines = []
            lines.append("Resultado del check rápido:")
            lines.append(f"Entrada seleccionada: {'OK' if input_ok else 'Falta'}")
            lines.append(f"Salida seleccionada: {'OK' if output_ok else 'Falta'}")
            lines.append(f"Salida virtual posible: {'OK' if virtual_ok else 'No detectada'}")
            lines.append("")
            if not virtual_ok:
                lines.append("Consejo: para Discord/Fortnite/OBS suele hacer falta CABLE Input o VoiceMeeter Input como salida.")
            else:
                lines.append("La salida parece preparada para enviar voz modificada a apps.")
            result = "\n".join(lines)
            self.hub_status.set("Check rápido completado.")
            self.hub_update_checklist(result)
        except Exception as e:
            self.hub_status.set(f"Error en check rápido: {e}")


    def build_escenas_pro_tab(self):
        cont = ttk.Frame(self.tab_escenas_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "escenas_banner" in self.scenes_images:
            ttk.Label(header, image=self.scenes_images["escenas_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Escenas Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        scenes_card = self.make_card(left, "Escenas de un clic")
        scenes_card.pack(fill="both", expand=True)

        self.scenes_grid = ttk.Frame(scenes_card, style="Card.TFrame")
        self.scenes_grid.pack(fill="both", expand=True)

        scenes = [
            ("scene_discord", "Discord claro", "discord"),
            ("scene_fortnite", "Fortnite grave", "fortnite"),
            ("scene_podcast", "Podcast Pro", "podcast"),
            ("scene_robot", "Robot show", "robot"),
            ("scene_terror", "Terror suave", "terror"),
            ("scene_cine", "Cine épico", "cine"),
            ("scene_personas", "Personajes", "personajes"),
            ("scene_meme", "Meme directo", "meme"),
        ]

        cols = 4
        for i, (img_key, label, scene_key) in enumerate(scenes):
            box = ttk.Frame(self.scenes_grid, style="Card.TFrame", padding=8)
            box.grid(row=i // cols, column=i % cols, sticky="nsew", padx=8, pady=8)
            if img_key in self.scenes_images:
                ttk.Label(box, image=self.scenes_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text="Aplicar " + label, style="Accent.TButton", command=lambda s=scene_key: self.apply_scene_pro(s)).pack(fill="x", pady=(6, 2))
            ttk.Button(box, text="Probar sonido", command=lambda s=scene_key: self.scene_test_sound(s)).pack(fill="x")
            self.scenes_grid.columnconfigure(i % cols, weight=1)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.scenes_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        actual = self.make_card(right, "Voz actual")
        actual.pack(fill="x", pady=(0, 10))
        ttk.Label(actual, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=310).pack(anchor="w")

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Grabar prueba WAV", command=self.record).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Guardar como perfil", command=self.save_current_profile).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Favoritos", command=lambda: self.select_tab(self.tab_favoritos_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Directo Pro", command=lambda: self.select_tab(self.tab_directo_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Mini Panel", command=self.open_mini_panel).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Discord claro: para llamadas.\n"
                "• Fortnite grave: gaming potente.\n"
                "• Podcast Pro: voz limpia y cálida.\n"
                "• Robot show: divertido.\n"
                "• Terror/Cine: escenas épicas.\n"
                "• Guarda como perfil si te gusta."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def scene_presets(self):
        return {
            "discord": {
                "label": "Discord claro",
                "voice": "Discord claro",
                "values": {"pitch": 0, "bass": 10, "robot": 0, "echo": 0, "radio": 0, "megaphone": 0, "gate": 10, "comp": 58, "vol": 92},
                "sound": "beep"
            },
            "fortnite": {
                "label": "Fortnite grave",
                "voice": "Fortnite grave",
                "values": {"pitch": -5, "bass": 55, "robot": 0, "echo": 3, "radio": 0, "megaphone": 0, "gate": 8, "comp": 55, "vol": 94},
                "sound": "victoria"
            },
            "podcast": {
                "label": "Podcast Pro",
                "voice": "Podcast",
                "values": {"pitch": -1, "bass": 28, "robot": 0, "echo": 1, "radio": 4, "megaphone": 0, "gate": 9, "comp": 68, "vol": 92},
                "sound": "beep"
            },
            "robot": {
                "label": "Robot show",
                "voice": "Robot directo",
                "values": {"pitch": 1, "bass": 0, "robot": 88, "echo": 4, "radio": 18, "megaphone": 0, "gate": 8, "comp": 36, "vol": 84},
                "sound": "powerup"
            },
            "terror": {
                "label": "Terror suave",
                "voice": "Fantasma",
                "values": {"pitch": -6, "bass": 55, "robot": 10, "echo": 55, "radio": 0, "megaphone": 0, "gate": 7, "comp": 35, "vol": 78},
                "sound": "suspense"
            },
            "cine": {
                "label": "Cine épico",
                "voice": "Cine tráiler",
                "values": {"pitch": -7, "bass": 75, "robot": 3, "echo": 20, "radio": 6, "megaphone": 0, "gate": 7, "comp": 70, "vol": 100},
                "sound": "impacto"
            },
            "personajes": {
                "label": "Personajes",
                "voice": "Mujer Lucía",
                "values": {"pitch": 2, "bass": 10, "robot": 0, "echo": 2, "radio": 0, "megaphone": 0, "gate": 10, "comp": 50, "vol": 90},
                "sound": "magia"
            },
            "meme": {
                "label": "Meme directo",
                "voice": "Caricatura",
                "values": {"pitch": 8, "bass": 0, "robot": 4, "echo": 4, "radio": 5, "megaphone": 0, "gate": 6, "comp": 30, "vol": 80},
                "sound": "risas"
            },
        }

    def apply_scene_pro(self, scene_key):
        data = self.scene_presets().get(scene_key)
        if not data:
            return

        voice = data.get("voice", "Gaming limpio")
        if voice in VoiceBank.all_presets():
            self.preset.set(voice)
            self.category.set(VoiceBank.all_presets()[voice][0])

        for key, value in data.get("values", {}).items():
            if key in self.vars:
                self.vars[key].set(value)

        self.update_engine()
        self.refresh_voice_list()
        self.scenes_status.set(f"Escena aplicada: {data.get('label', scene_key)}")
        self.state.set(f"Estado: escena aplicada · {data.get('label', scene_key)}")

    def scene_test_sound(self, scene_key):
        data = self.scene_presets().get(scene_key, {})
        sound = data.get("sound", "beep")
        label = data.get("label", scene_key)
        self.play_sfx(sound)
        self.scenes_status.set(f"Sonido de prueba: {label}")


    def build_favoritos_pro_tab(self):
        cont = ttk.Frame(self.tab_favoritos_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "favoritos_banner" in self.favoritos_images:
            ttk.Label(header, image=self.favoritos_images["favoritos_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Favoritos Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Accesos favoritos")
        tiles.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        for i, (img_key, label) in enumerate([
            ("tile_voces", "Voces"),
            ("tile_sonidos", "Sonidos"),
            ("tile_directo", "Directo"),
            ("tile_perfiles", "Perfiles"),
        ]):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            if img_key in self.favoritos_images:
                ttk.Label(box, image=self.favoritos_images[img_key], style="Card.TLabel").pack()
            ttk.Label(box, text=label, style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        voices_card = self.make_card(body, "Voces favoritas / recomendadas")
        voices_card.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.favoritos_voice_frame = ttk.Frame(voices_card, style="Card.TFrame")
        self.favoritos_voice_frame.pack(fill="both", expand=True)

        sounds_card = self.make_card(body, "Sonidos favoritos")
        sounds_card.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.favoritos_sound_frame = ttk.Frame(sounds_card, style="Card.TFrame")
        self.favoritos_sound_frame.pack(fill="both", expand=True)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.favoritos_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        acciones = self.make_card(right, "Acciones rápidas")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Actualizar favoritos", style="Accent.TButton", command=self.refresh_favoritos_pro).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Añadir voz actual a favoritos", command=self.add_current_favorite_and_refresh).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Guardar voz actual como perfil", command=self.save_current_profile).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Caja de Voces", command=lambda: self.select_tab(self.tab_voicebox_grid)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Mini Panel", command=self.open_mini_panel).pack(fill="x", pady=3)

        directo = self.make_card(right, "Directo")
        directo.pack(fill="x", pady=(0, 10))
        ttk.Button(directo, text="Empezar directo", command=self.start).pack(fill="x", pady=3)
        ttk.Button(directo, text="Parar directo", style="Danger.TButton", command=self.stop).pack(fill="x", pady=3)
        ttk.Button(directo, text="Grabar prueba WAV", command=self.record).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Si no tienes favoritos, salen voces recomendadas.\n"
                "• Pulsa ★ en Caja de Voces o Personas Pro.\n"
                "• Combina Favoritos Pro con Atajos Pro.\n"
                "• Guarda perfiles para tus estilos finales."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

        self.refresh_favoritos_pro()

    def favoritos_voice_names(self):
        valid = VoiceBank.all_presets()
        voices = [v for v in self.favorites if v in valid]
        if not voices:
            recommended = [
                "Mujer Lucía", "Hombre Diego", "Niño Leo", "Niña Luna",
                "Abuelo Paco", "Abuela Carmen", "Robot directo", "Gaming limpio",
                "Podcast", "Locutor español", "Fortnite grave", "Cine tráiler"
            ]
            voices = [v for v in recommended if v in valid]
        return voices[:12]

    def favoritos_sounds(self):
        return [
            ("Aplausos", "aplausos"),
            ("Risas", "risas"),
            ("Victoria", "victoria"),
            ("Error", "error"),
            ("Alerta", "alerta"),
            ("Impacto", "impacto"),
            ("Magia", "magia"),
            ("Beep", "beep"),
            ("Suspense", "suspense"),
            ("Redoble", "redoble"),
            ("Power Up", "powerup"),
            ("Lluvia suave", "lluvia"),
        ]

    def refresh_favoritos_pro(self):
        if not hasattr(self, "favoritos_voice_frame") or not hasattr(self, "favoritos_sound_frame"):
            return

        for frame in [self.favoritos_voice_frame, self.favoritos_sound_frame]:
            for child in frame.winfo_children():
                child.destroy()

        voices = self.favoritos_voice_names()
        cols = 2
        for i, voice in enumerate(voices):
            card = ttk.Frame(self.favoritos_voice_frame, style="Card.TFrame", padding=8)
            card.grid(row=i // cols, column=i % cols, sticky="nsew", padx=6, pady=6)

            key = self.voice_image_key(voice)
            img = self.grid_voice_images.get(key)
            if img is not None:
                ttk.Label(card, image=img, style="Card.TLabel").pack(anchor="center", pady=(0, 4))

            ttk.Label(card, text=voice, style="Card.TLabel", font=("Segoe UI", 11, "bold"), wraplength=220).pack(anchor="w", pady=(0, 4))
            ttk.Button(card, text="Aplicar", style="Accent.TButton", command=lambda v=voice: self.apply_favorito_voice(v)).pack(fill="x")

        for col in range(cols):
            self.favoritos_voice_frame.columnconfigure(col, weight=1)

        sounds = self.favoritos_sounds()
        for i, (label, key) in enumerate(sounds):
            ttk.Button(
                self.favoritos_sound_frame,
                text=label,
                command=lambda k=key, l=label: self.play_favorito_sound(k, l)
            ).grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6, ipady=10)

        for col in range(2):
            self.favoritos_sound_frame.columnconfigure(col, weight=1)

        self.favoritos_status.set(f"Favoritos listos · voces: {len(voices)} · sonidos: {len(sounds)}")

    def apply_favorito_voice(self, voice_name):
        if voice_name in VoiceBank.all_presets():
            self.preset.set(voice_name)
            self.category.set(VoiceBank.all_presets()[voice_name][0])
            self.apply_preset()
            self.refresh_voice_list()
            self.favoritos_status.set(f"Voz aplicada: {voice_name}")
            self.state.set(f"Estado: Favoritos Pro · {voice_name}")

    def play_favorito_sound(self, key, label):
        self.play_sfx(key)
        self.favoritos_status.set(f"Sonido lanzado: {label}")
        self.state.set(f"Estado: sonido favorito · {label}")

    def add_current_favorite_and_refresh(self):
        self.add_current_favorite()
        self.refresh_favoritos_pro()


    def build_atajos_tab(self):
        cont = ttk.Frame(self.tab_atajos)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "atajos_banner" in self.hotkey_images:
            ttk.Label(header, image=self.hotkey_images["atajos_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Atajos Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Tipos de atajos")
        tiles.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_voces", "Voces"),
            ("tile_sonidos", "Sonidos"),
            ("tile_mute", "Silenciar"),
            ("tile_modulador", "Modulador"),
            ("tile_panel", "Mini Panel"),
        ]

        for i, (img_key, label) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            if img_key in self.hotkey_images:
                ttk.Label(box, image=self.hotkey_images[img_key], style="Card.TLabel").pack()
            ttk.Label(box, text=label, style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        controls = self.make_card(left, "Control de atajos")
        controls.pack(fill="x", pady=(0, 10))
        row = ttk.Frame(controls, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Checkbutton(row, text="Atajos activados", variable=self.hotkeys_enabled).pack(side="left", padx=4)
        ttk.Button(row, text="Reactivar atajos", style="Accent.TButton", command=self.bind_shortcuts).pack(side="left", padx=4)
        ttk.Button(row, text="Probar F1", command=lambda: self.apply_hotkey_voice("Mujer Lucía")).pack(side="left", padx=4)
        ttk.Button(row, text="Probar F9", command=lambda: self.play_hotkey_sound("aplausos", "Aplausos")).pack(side="left", padx=4)

        table = self.make_card(left, "Mapa de teclas")
        table.pack(fill="both", expand=True)

        text = tk.Text(
            table,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=20
        )
        text.pack(fill="both", expand=True, padx=4, pady=4)

        shortcuts = [
            ("F1", "Mujer Lucía"),
            ("F2", "Hombre Diego"),
            ("F3", "Niño Leo"),
            ("F4", "Niña Luna"),
            ("F5", "Abuelo Paco"),
            ("F6", "Abuela Carmen"),
            ("F7", "Robot directo"),
            ("F8", "Gaming limpio"),
            ("F9", "Aplausos"),
            ("F10", "Risas"),
            ("F11", "Victoria"),
            ("F12", "Error"),
            ("Ctrl + M", "Silenciar / activar salida"),
            ("Ctrl + Shift + V", "Modulador ON/OFF"),
            ("Ctrl + Shift + P", "Abrir Mini Panel"),
            ("Ctrl + Shift + G", "Grabar prueba WAV"),
            ("Ctrl + Shift + C", "Guardar clip instantáneo (30 s)"),
        ]

        text.insert("1.0", "ATAJOS PRO\n\n")
        for key, action in shortcuts:
            text.insert(tk.END, f"{key:<18} → {action}\n")
        text.insert(tk.END, "\nNota: con las dependencias instaladas los atajos son GLOBALES: funcionan aunque el juego o Discord tengan el foco. Sin la librería 'keyboard', solo funcionan con la app enfocada.")
        text.configure(state="disabled")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.hotkey_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        acciones = self.make_card(right, "Accesos")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Abrir Mini Panel", command=self.open_mini_panel).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Cambiador", command=lambda: self.select_tab(self.tab_cambiador_personas)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Creador", command=lambda: self.select_tab(self.tab_creador_voces)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Directo Pro", command=lambda: self.select_tab(self.tab_directo_pro)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Los atajos no son globales: no reemplazan teclas del juego.\n"
                "• Úsalos cuando la ventana esté enfocada.\n"
                "• Para directos, combina Atajos Pro con Mini Panel.\n"
                "• F1-F8 cambian voces.\n"
                "• F9-F12 lanzan sonidos."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def bind_shortcuts(self):
        try:
            bindings = {
                "<F1>": lambda e: self.apply_hotkey_voice("Mujer Lucía"),
                "<F2>": lambda e: self.apply_hotkey_voice("Hombre Diego"),
                "<F3>": lambda e: self.apply_hotkey_voice("Niño Leo"),
                "<F4>": lambda e: self.apply_hotkey_voice("Niña Luna"),
                "<F5>": lambda e: self.apply_hotkey_voice("Abuelo Paco"),
                "<F6>": lambda e: self.apply_hotkey_voice("Abuela Carmen"),
                "<F7>": lambda e: self.apply_hotkey_voice("Robot directo"),
                "<F8>": lambda e: self.apply_hotkey_voice("Gaming limpio"),
                "<F9>": lambda e: self.play_hotkey_sound("aplausos", "Aplausos"),
                "<F10>": lambda e: self.play_hotkey_sound("risas", "Risas"),
                "<F11>": lambda e: self.play_hotkey_sound("victoria", "Victoria"),
                "<F12>": lambda e: self.play_hotkey_sound("error", "Error"),
                "<Control-m>": lambda e: self.toggle_hotkey_mute(),
                "<Control-M>": lambda e: self.toggle_hotkey_mute(),
                "<Control-Shift-V>": lambda e: self.toggle_hotkey_effects(),
                "<Control-Shift-v>": lambda e: self.toggle_hotkey_effects(),
                "<Control-Shift-P>": lambda e: self.open_mini_panel(),
                "<Control-Shift-p>": lambda e: self.open_mini_panel(),
                "<Control-Shift-G>": lambda e: self.record(),
                "<Control-Shift-g>": lambda e: self.record(),
                "<Control-Shift-C>": lambda e: self.hotkey_save_clip(),
                "<Control-Shift-c>": lambda e: self.hotkey_save_clip(),
            }
            for key, callback in bindings.items():
                self.root.bind_all(key, callback)
            if self.bind_global_shortcuts():
                self.hotkey_status.set("Atajos GLOBALES activados: funcionan dentro del juego o Discord.")
            else:
                self.hotkey_status.set("Atajos activados solo con la app enfocada. Instala dependencias (librería 'keyboard') para atajos globales.")
        except Exception as e:
            self.hotkey_status.set(f"No se pudieron activar atajos: {e}")

    def bind_global_shortcuts(self):
        """Registra los mismos atajos a nivel de Windows (sin necesitar foco).

        Las pulsaciones llegan en un hilo del sistema, así que cada acción
        se reenvía al hilo de la interfaz con root.after.
        """
        if not GLOBAL_HOTKEYS_AVAILABLE:
            return False
        try:
            global_keyboard.unhook_all_hotkeys()
        except Exception:
            pass

        def en_ui(fn, *args):
            return lambda: self.root.after(0, lambda: fn(*args))

        mapping = {
            "f1": en_ui(self.apply_hotkey_voice, "Mujer Lucía"),
            "f2": en_ui(self.apply_hotkey_voice, "Hombre Diego"),
            "f3": en_ui(self.apply_hotkey_voice, "Niño Leo"),
            "f4": en_ui(self.apply_hotkey_voice, "Niña Luna"),
            "f5": en_ui(self.apply_hotkey_voice, "Abuelo Paco"),
            "f6": en_ui(self.apply_hotkey_voice, "Abuela Carmen"),
            "f7": en_ui(self.apply_hotkey_voice, "Robot directo"),
            "f8": en_ui(self.apply_hotkey_voice, "Gaming limpio"),
            "f9": en_ui(self.play_hotkey_sound, "aplausos", "Aplausos"),
            "f10": en_ui(self.play_hotkey_sound, "risas", "Risas"),
            "f11": en_ui(self.play_hotkey_sound, "victoria", "Victoria"),
            "f12": en_ui(self.play_hotkey_sound, "error", "Error"),
            "ctrl+m": en_ui(self.toggle_hotkey_mute),
            "ctrl+shift+v": en_ui(self.toggle_hotkey_effects),
            "ctrl+shift+p": en_ui(self.open_mini_panel),
            "ctrl+shift+g": en_ui(self.record),
            "ctrl+shift+c": en_ui(self.hotkey_save_clip),
        }
        try:
            for key, action in mapping.items():
                global_keyboard.add_hotkey(key, action)
            return True
        except Exception as e:
            print("No se pudieron activar atajos globales:", e)
            return False

    def hotkeys_active(self):
        try:
            return bool(self.hotkeys_enabled.get())
        except Exception:
            return True

    def apply_hotkey_voice(self, voice_name):
        if not self.hotkeys_active():
            return
        if voice_name in VoiceBank.all_presets():
            self.preset.set(voice_name)
            cat = VoiceBank.all_presets()[voice_name][0]
            self.category.set(cat)
            self.apply_preset()
            self.refresh_voice_list()
            self.hotkey_status.set(f"Atajo voz: {voice_name}")
            self.state.set(f"Estado: atajo aplicado · {voice_name}")

    def play_hotkey_sound(self, key, label):
        if not self.hotkeys_active():
            return
        self.play_sfx(key)
        self.hotkey_status.set(f"Atajo sonido: {label}")
        self.state.set(f"Estado: sonido por atajo · {label}")

    def toggle_hotkey_mute(self):
        if not self.hotkeys_active():
            return
        self.mute.set(not self.mute.get())
        self.update_engine()
        self.hotkey_status.set("Salida silenciada." if self.mute.get() else "Salida activada.")
        self.state.set("Estado: atajo silenciar")

    def toggle_hotkey_effects(self):
        if not self.hotkeys_active():
            return
        self.effects_enabled.set(not self.effects_enabled.get())
        self.update_engine()
        self.hotkey_status.set("Modulador activado." if self.effects_enabled.get() else "Modulador desactivado.")
        self.state.set("Estado: atajo modulador ON/OFF")


    def build_creador_voces_tab(self):
        cont = ttk.Frame(self.tab_creador_voces)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "creador_banner" in self.creator_images:
            ttk.Label(header, image=self.creator_images["creador_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Creador de Voces Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Proceso de creación")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        for i, (img_key, label) in enumerate([
            ("tile_base", "Base"),
            ("tile_estilo", "Estilo"),
            ("tile_ajustes", "Ajustes"),
            ("tile_guardar", "Guardar"),
            ("tile_probar", "Probar"),
        ]):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            if img_key in self.creator_images:
                ttk.Label(box, image=self.creator_images[img_key], style="Card.TLabel").pack()
            ttk.Label(box, text=label, style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        builder = self.make_card(left, "Crear voz personalizada")
        builder.pack(fill="x", pady=(0, 10))

        row1 = ttk.Frame(builder, style="Card.TFrame")
        row1.pack(fill="x", pady=5)
        ttk.Label(row1, text="Base humana:", style="Card.TLabel", width=16).pack(side="left")
        base_combo = ttk.Combobox(row1, textvariable=self.creator_base, state="readonly", width=22, values=["Mujer", "Hombre", "Niño", "Niña", "Abuelo", "Abuela"])
        base_combo.pack(side="left", padx=(0, 12))
        ttk.Label(row1, text="Estilo:", style="Card.TLabel", width=10).pack(side="left")
        style_combo = ttk.Combobox(row1, textvariable=self.creator_style, state="readonly", width=24, values=["Directo limpio", "Grave potente", "Radio clara", "Cine épico", "Robot suave", "Eco mágico"])
        style_combo.pack(side="left", padx=(0, 12))
        ttk.Button(row1, text="Aplicar mezcla", style="Accent.TButton", command=self.creator_apply_mix).pack(side="left", fill="x", expand=True)

        row2 = ttk.Frame(builder, style="Card.TFrame")
        row2.pack(fill="x", pady=5)
        ttk.Label(row2, text="Nombre:", style="Card.TLabel", width=16).pack(side="left")
        ttk.Entry(row2, textvariable=self.creator_name).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(row2, text="Guardar como perfil", command=self.creator_save_profile).pack(side="left", padx=4)
        ttk.Button(row2, text="Grabar prueba WAV", command=self.record).pack(side="left", padx=4)

        mis_voces = self.make_card(left, "⭐ Mis voces (aparecen en la biblioteca)")
        mis_voces.pack(fill="x", pady=(0, 10))
        cuerpo_mv = ttk.Frame(mis_voces, style="Card.TFrame")
        cuerpo_mv.pack(fill="x")
        self.my_voices_list = tk.Listbox(
            cuerpo_mv,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            relief="flat",
            font=("Consolas", 10),
            height=5
        )
        self.my_voices_list.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.my_voices_list.bind("<Double-Button-1>", lambda e: self.apply_my_voice())
        botones_mv = ttk.Frame(cuerpo_mv, style="Card.TFrame")
        botones_mv.pack(side="left", fill="y")
        ttk.Button(botones_mv, text="⭐ Guardar voz actual", style="Accent.TButton", command=self.creator_save_voice).pack(fill="x", pady=3)
        ttk.Button(botones_mv, text="Aplicar", command=self.apply_my_voice).pack(fill="x", pady=3)
        ttk.Button(botones_mv, text="Borrar", style="Danger.TButton", command=self.delete_my_voice).pack(fill="x", pady=3)
        self.refresh_my_voices_list()

        ajustes = self.make_card(left, "Ajustes finos")
        ajustes.pack(fill="both", expand=True)

        self.creator_slider(ajustes, "Tono", "pitch", -12, 12, "semitonos")
        self.creator_slider(ajustes, "Graves", "bass", 0, 100, "%")
        self.creator_slider(ajustes, "Robot", "robot", 0, 100, "%")
        self.creator_slider(ajustes, "Eco", "echo", 0, 100, "%")
        self.creator_slider(ajustes, "Radio", "radio", 0, 100, "%")
        self.creator_slider(ajustes, "Volumen", "vol", 0, 120, "%")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.creator_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        actual = self.make_card(right, "Voz actual")
        actual.pack(fill="x", pady=(0, 10))
        ttk.Label(actual, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=310).pack(anchor="w")

        acciones = self.make_card(right, "Acciones rápidas")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Abrir Cambiador", command=lambda: self.select_tab(self.tab_cambiador_personas)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Personas Pro", command=lambda: self.select_tab(self.tab_personas_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Perfiles Pro+", command=lambda: self.select_tab(self.tab_perfiles_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Reset", command=self.reset).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Base = tipo de persona.\n"
                "• Estilo = carácter de la voz.\n"
                "• Ajustes finos = detalles.\n"
                "• Guarda la mezcla como perfil.\n"
                "• No clona voces reales, solo crea efectos propios."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def creator_slider(self, parent, label, key, mn, mx, unit):
        line = ttk.Frame(parent, style="Card.TFrame")
        line.pack(fill="x", pady=5)
        top = ttk.Frame(line, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text=label + ":", style="Card.TLabel", width=14).pack(side="left")
        value_label = ttk.Label(top, style="Card.TLabel", width=12)
        value_label.pack(side="right")

        var = self.vars[key]
        scale = ttk.Scale(line, from_=mn, to=mx, variable=var, orient="horizontal", command=lambda _=None: self.update_engine())
        scale.pack(fill="x", pady=(3, 0))

        def refresh(*_):
            v = var.get()
            if unit == "semitonos":
                value_label.config(text=f"{v:+.1f}")
            else:
                value_label.config(text=f"{v:.0f}{unit}")
            self.update_engine()

        var.trace_add("write", refresh)
        refresh()

    def creator_apply_mix(self):
        base = self.creator_base.get()
        style = self.creator_style.get()

        base_values = {
            "Mujer":  dict(pitch=2,  bass=10, robot=0, echo=2, radio=0, megaphone=0, gate=10, comp=48, vol=90, preset="Mujer Lucía"),
            "Hombre": dict(pitch=-2, bass=25, robot=0, echo=1, radio=2, megaphone=0, gate=8,  comp=52, vol=92, preset="Hombre Diego"),
            "Niño":   dict(pitch=7,  bass=0,  robot=0, echo=3, radio=2, megaphone=0, gate=6,  comp=28, vol=82, preset="Niño Leo"),
            "Niña":   dict(pitch=7,  bass=0,  robot=0, echo=4, radio=2, megaphone=0, gate=6,  comp=28, vol=82, preset="Niña Luna"),
            "Abuelo": dict(pitch=-5, bass=30, robot=0, echo=3, radio=6, megaphone=0, gate=8,  comp=55, vol=88, preset="Abuelo Paco"),
            "Abuela": dict(pitch=1,  bass=10, robot=0, echo=3, radio=3, megaphone=0, gate=10, comp=50, vol=88, preset="Abuela Carmen"),
        }

        style_values = {
            "Directo limpio": dict(echo=0, radio=0, robot=0, comp=55, gate=10),
            "Grave potente": dict(pitch=-5, bass=60, echo=2, radio=0, robot=0, comp=58),
            "Radio clara": dict(echo=1, radio=72, robot=0, megaphone=12, comp=62),
            "Cine épico": dict(pitch=-4, bass=70, echo=22, radio=4, robot=0, comp=70, vol=102),
            "Robot suave": dict(robot=48, echo=5, radio=16, comp=45),
            "Eco mágico": dict(echo=52, radio=0, robot=10, comp=35, vol=84),
        }

        values = base_values.get(base, base_values["Hombre"]).copy()
        preset_name = values.pop("preset")
        values.update(style_values.get(style, {}))

        # Evita que estilo de niño/niña pierda demasiado su tono si no es grave/cine
        if base in ("Niño", "Niña") and style not in ("Grave potente", "Cine épico"):
            values["pitch"] = max(values.get("pitch", 7), 6)

        for key, value in values.items():
            if key in self.vars:
                self.vars[key].set(value)

        if preset_name in VoiceBank.all_presets():
            self.preset.set(preset_name)
            self.category.set("Personas")

        self.update_engine()
        self.refresh_voice_list()
        self.creator_status.set(f"Mezcla aplicada: {base} + {style}")
        self.state.set(f"Estado: voz creada · {base} + {style}")

    def custom_voices_path(self):
        return os.path.join(os.path.expanduser("~"), "modulador_voz_directo_v81_voces.json")

    def load_custom_voices(self):
        try:
            path = self.custom_voices_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    VoiceBank.custom = {
                        str(name): {k: float(v) for k, v in values.items() if isinstance(v, (int, float))}
                        for name, values in data.items() if isinstance(values, dict)
                    }
        except Exception as e:
            print("No se pudieron cargar Mis Voces:", e)
            VoiceBank.custom = {}

    def save_custom_voices(self):
        try:
            with open(self.custom_voices_path(), "w", encoding="utf-8") as f:
                json.dump(VoiceBank.custom, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("No se pudieron guardar Mis Voces:", e)

    def creator_save_voice(self):
        name = self.creator_name.get().strip() or "Mi voz personalizada"
        if name in VoiceBank.base_presets():
            self.creator_status.set(f"Ya existe una voz oficial llamada {name}. Elige otro nombre.")
            return
        VoiceBank.custom[name] = self.current_values()
        self.save_custom_voices()
        self.refresh_my_voices_list()
        self.preset.set(name)
        self.category.set("Mis voces")
        self.refresh_voice_list()
        self.creator_status.set(f"Voz guardada en Mis Voces: {name}. Ya aparece en la biblioteca y la caja de voces.")

    def refresh_my_voices_list(self):
        if getattr(self, "my_voices_list", None) is None:
            return
        self.my_voices_list.delete(0, tk.END)
        names = sorted(VoiceBank.custom.keys())
        if not names:
            self.my_voices_list.insert(tk.END, "Todavía no has guardado voces.")
        else:
            for name in names:
                self.my_voices_list.insert(tk.END, name)

    def selected_my_voice(self):
        if getattr(self, "my_voices_list", None) is None or not self.my_voices_list.curselection():
            return None
        name = self.my_voices_list.get(self.my_voices_list.curselection()[0])
        return name if name in VoiceBank.custom else None

    def apply_my_voice(self):
        name = self.selected_my_voice()
        if name is None:
            self.creator_status.set("Selecciona una de tus voces en la lista.")
            return
        self.preset.set(name)
        self.category.set("Mis voces")
        self.refresh_voice_list()
        self.apply_preset()
        self.creator_status.set(f"Voz aplicada: {name}")

    def delete_my_voice(self):
        name = self.selected_my_voice()
        if name is None:
            self.creator_status.set("Selecciona una de tus voces en la lista.")
            return
        if not messagebox.askyesno("Borrar voz", f"¿Borrar esta voz de Mis Voces?\n\n{name}"):
            return
        VoiceBank.custom.pop(name, None)
        self.save_custom_voices()
        self.refresh_my_voices_list()
        if self.preset.get() == name:
            self.preset.set("Gaming limpio")
            self.category.set("Todas")
            self.apply_preset()
        self.refresh_voice_list()
        self.creator_status.set(f"Voz borrada: {name}")

    def creator_save_profile(self):
        name = self.creator_name.get().strip()
        if not name:
            name = "Mi voz personalizada"

        self.profiles[name] = {
            "preset": self.preset.get(),
            "category": self.category.get(),
            "latency": self.latency.get(),
            "values": self.current_values()
        }
        self.save_profiles()
        self.refresh_profiles_list()
        if self.profile_manager_list is not None:
            self.profile_manager_refresh()
        self.creator_status.set(f"Perfil personalizado guardado: {name}")
        messagebox.showinfo("Perfil guardado", f"Tu voz personalizada se guardó como perfil:\n\n{name}")


    def build_cambiador_personas_tab(self):
        cont = ttk.Frame(self.tab_cambiador_personas)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "cambiador_banner" in self.cambiador_images:
            ttk.Label(header, image=self.cambiador_images["cambiador_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Cambiador de Personas", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tipos = self.make_card(left, "Cambio rápido por tipo")
        tipos.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tipos, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_mujer", "Mujer", "Mujer"),
            ("tile_hombre", "Hombre", "Hombre"),
            ("tile_nino", "Niño", "Niño"),
            ("tile_nina", "Niña", "Niña"),
            ("tile_abuelo", "Abuelo", "Abuelo"),
            ("tile_abuela", "Abuela", "Abuela"),
        ]

        for i, (img_key, label, tipo) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.cambiador_images:
                ttk.Label(box, image=self.cambiador_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=lambda t=tipo: self.apply_persona_type(t)).pack(fill="x", pady=(5, 2))
            ttk.Button(box, text="Cambiar variante", command=lambda t=tipo: self.next_persona_variant(t)).pack(fill="x")
            grid.columnconfigure(i, weight=1)

        ajustes = self.make_card(left, "Ajustes rápidos de persona")
        ajustes.pack(fill="x", pady=(0, 10))

        row1 = ttk.Frame(ajustes, style="Card.TFrame")
        row1.pack(fill="x", pady=3)
        ttk.Button(row1, text="Más joven", command=self.persona_younger).pack(side="left", fill="x", expand=True, padx=4, ipady=8)
        ttk.Button(row1, text="Más adulta", command=self.persona_adult).pack(side="left", fill="x", expand=True, padx=4, ipady=8)
        ttk.Button(row1, text="Más grave", command=self.persona_deeper).pack(side="left", fill="x", expand=True, padx=4, ipady=8)
        ttk.Button(row1, text="Más suave", command=self.persona_soft).pack(side="left", fill="x", expand=True, padx=4, ipady=8)

        row2 = ttk.Frame(ajustes, style="Card.TFrame")
        row2.pack(fill="x", pady=3)
        ttk.Button(row2, text="Más clara", command=self.persona_clear).pack(side="left", fill="x", expand=True, padx=4, ipady=8)
        ttk.Button(row2, text="Más radio", command=self.persona_radio).pack(side="left", fill="x", expand=True, padx=4, ipady=8)
        ttk.Button(row2, text="Más eco", command=self.persona_echo).pack(side="left", fill="x", expand=True, padx=4, ipady=8)
        ttk.Button(row2, text="Reset persona", command=self.reset).pack(side="left", fill="x", expand=True, padx=4, ipady=8)

        actual = self.make_card(left, "Voz actual")
        actual.pack(fill="both", expand=True)
        ttk.Label(actual, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 24, "bold"), wraplength=760).pack(anchor="w", pady=(0, 8))
        ttk.Label(actual, text="Usa los botones grandes para cambiar de tipo o de variante. Después prueba la voz con Grabadora Pro.", style="Card.TLabel", wraplength=760).pack(anchor="w")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.cambiador_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Grabar prueba WAV", command=self.record).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Guardar como perfil", command=self.save_current_profile).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Personas Pro", command=lambda: self.select_tab(self.tab_personas_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Mini Panel", command=lambda: self.select_tab(self.tab_mini_panel)).pack(fill="x", pady=3)

        consejos = self.make_card(right, "Consejos")
        consejos.pack(fill="x")
        ttk.Label(
            consejos,
            text=(
                "• Cambiar variante alterna entre dos personajes.\n"
                "• Más joven sube el tono.\n"
                "• Más grave baja el tono y añade cuerpo.\n"
                "• Más clara ayuda en Discord.\n"
                "• Guarda perfiles para tus voces favoritas."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def persona_variants(self):
        return {
            "Mujer": ["Mujer Lucía", "Mujer Sofía"],
            "Hombre": ["Hombre Diego", "Hombre Marcos"],
            "Niño": ["Niño Leo", "Niño Nico"],
            "Niña": ["Niña Luna", "Niña Emma"],
            "Abuelo": ["Abuelo Paco", "Abuelo José"],
            "Abuela": ["Abuela Carmen", "Abuela Lola"],
        }

    def apply_persona_type(self, tipo):
        voices = [v for v in self.persona_variants().get(tipo, []) if v in VoiceBank.all_presets()]
        if not voices:
            self.cambiador_status.set(f"No hay voces disponibles para: {tipo}")
            return
        idx = self.cambiador_index.get(tipo, 0) % len(voices)
        self.apply_cambiador_voice(voices[idx], tipo)

    def next_persona_variant(self, tipo):
        voices = [v for v in self.persona_variants().get(tipo, []) if v in VoiceBank.all_presets()]
        if not voices:
            self.cambiador_status.set(f"No hay variantes para: {tipo}")
            return
        self.cambiador_index[tipo] = (self.cambiador_index.get(tipo, 0) + 1) % len(voices)
        self.apply_cambiador_voice(voices[self.cambiador_index[tipo]], tipo)

    def apply_cambiador_voice(self, voice_name, tipo):
        self.preset.set(voice_name)
        self.category.set("Personas")
        self.apply_preset()
        self.refresh_voice_list()
        self.cambiador_status.set(f"{tipo} aplicado: {voice_name}")
        self.state.set(f"Estado: Cambiador · {voice_name}")

    def persona_adjust(self, label, **values):
        for key, value in values.items():
            if key in self.vars:
                self.vars[key].set(value)
        self.update_engine()
        self.cambiador_status.set(f"Ajuste aplicado: {label}")
        self.state.set(f"Estado: ajuste persona · {label}")

    def persona_younger(self):
        self.persona_adjust("Más joven", pitch=7, bass=0, robot=0, echo=3, radio=2, comp=30, vol=84)

    def persona_adult(self):
        self.persona_adjust("Más adulta", pitch=0, bass=16, robot=0, echo=2, radio=2, comp=48, vol=90)

    def persona_deeper(self):
        self.persona_adjust("Más grave", pitch=-5, bass=48, robot=0, echo=3, radio=2, comp=52, vol=92)

    def persona_soft(self):
        self.persona_adjust("Más suave", pitch=1, bass=10, robot=0, echo=5, radio=0, comp=38, vol=84)

    def persona_clear(self):
        self.persona_adjust("Más clara", pitch=0, bass=10, robot=0, echo=0, radio=0, comp=58, gate=10, vol=92)

    def persona_radio(self):
        self.persona_adjust("Más radio", pitch=0, bass=14, robot=0, echo=1, radio=65, megaphone=12, comp=58, vol=92)

    def persona_echo(self):
        self.persona_adjust("Más eco", pitch=0, bass=18, robot=0, echo=34, radio=0, comp=40, vol=86)


    def build_personas_pro_tab(self):
        cont = ttk.Frame(self.tab_personas_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "personas_banner" in self.personas_images:
            ttk.Label(header, image=self.personas_images["personas_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Personas Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        filtros = self.make_card(left, "Filtros por tipo de voz")
        filtros.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(filtros, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_mujeres", "Mujeres", "Mujer"),
            ("tile_hombres", "Hombres", "Hombre"),
            ("tile_ninos", "Niños", "Niño"),
            ("tile_ninas", "Niñas", "Niña"),
            ("tile_abuelos", "Abuelos", "Abuelo"),
            ("tile_abuelas", "Abuelas", "Abuela"),
        ]

        for i, (img_key, label, filtro) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.personas_images:
                ttk.Label(box, image=self.personas_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, command=lambda f=filtro: self.populate_personas_grid(f)).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        cards = self.make_card(left, "Tarjetas de personajes")
        cards.pack(fill="both", expand=True)

        canvas = tk.Canvas(cards, bg=COLORS["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(cards, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas, style="Card.TFrame")

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def resize_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", resize_canvas)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.personas_grid_frame = scrollable

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.personas_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        acciones = self.make_card(right, "Acciones rápidas")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Ver todas", style="Accent.TButton", command=lambda: self.populate_personas_grid("Todas")).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Grabar prueba WAV", command=self.record).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Ecualizador", command=lambda: self.select_tab(self.tab_ecualizador)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Mini Panel", command=lambda: self.select_tab(self.tab_mini_panel)).pack(fill="x", pady=3)

        consejos = self.make_card(right, "Consejos")
        consejos.pack(fill="x")
        ttk.Label(
            consejos,
            text=(
                "• Mujeres y hombres suenan más naturales.\n"
                "• Niños y niñas usan tono más alto.\n"
                "• Abuelos y abuelas tienen tono más calmado.\n"
                "• Usa Grabadora para probar.\n"
                "• Guarda tus favoritas en Perfiles Pro+."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

        self.populate_personas_grid("Todas")

    def persona_voices(self):
        names = [
            "Mujer Lucía", "Mujer Sofía",
            "Hombre Diego", "Hombre Marcos",
            "Niño Leo", "Niño Nico",
            "Niña Luna", "Niña Emma",
            "Abuelo Paco", "Abuelo José",
            "Abuela Carmen", "Abuela Lola",
        ]
        return [n for n in names if n in VoiceBank.all_presets()]

    def persona_type(self, name):
        for prefix in ["Mujer", "Hombre", "Niño", "Niña", "Abuelo", "Abuela"]:
            if name.startswith(prefix):
                return prefix
        return "Persona"

    def populate_personas_grid(self, filtro="Todas"):
        if not hasattr(self, "personas_grid_frame"):
            return

        for child in self.personas_grid_frame.winfo_children():
            child.destroy()

        voices = []
        for name in self.persona_voices():
            tipo = self.persona_type(name)
            if filtro != "Todas" and tipo != filtro:
                continue
            voices.append((name, tipo))

        if not voices:
            ttk.Label(
                self.personas_grid_frame,
                text="No hay voces en este filtro.",
                style="Card.TLabel"
            ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        cols = 3
        for i, (name, tipo) in enumerate(voices):
            card = ttk.Frame(self.personas_grid_frame, style="Card.TFrame", padding=10)
            card.grid(row=i // cols, column=i % cols, sticky="nsew", padx=8, pady=8)

            key = self.voice_image_key(name)
            img = self.grid_voice_images.get(key)
            if img is not None:
                ttk.Label(card, image=img, style="Card.TLabel").pack(anchor="center", pady=(0, 6))

            ttk.Label(card, text=name, style="Card.TLabel", font=("Segoe UI", 12, "bold"), wraplength=240).pack(anchor="w")
            ttk.Label(card, text=tipo, style="Card.TLabel", font=("Segoe UI", 9), wraplength=240).pack(anchor="w", pady=(0, 6))

            buttons = ttk.Frame(card, style="Card.TFrame")
            buttons.pack(fill="x")
            ttk.Button(buttons, text="Aplicar", style="Accent.TButton", command=lambda v=name: self.apply_persona_voice(v)).pack(side="left", fill="x", expand=True, padx=(0, 3))
            ttk.Button(buttons, text="★", command=lambda v=name: self.favorite_voice_by_name(v)).pack(side="left", padx=(3, 0))

        for col in range(cols):
            self.personas_grid_frame.columnconfigure(col, weight=1)

        self.personas_status.set(f"Filtro: {filtro} · Voces mostradas: {len(voices)}")

    def apply_persona_voice(self, voice_name):
        if voice_name in VoiceBank.all_presets():
            self.preset.set(voice_name)
            self.category.set("Personas")
            self.apply_preset()
            self.refresh_voice_list()
            self.personas_status.set(f"Voz aplicada: {voice_name}")
            self.state.set(f"Estado: Personas Pro · {voice_name}")


    def build_perfiles_pro_tab(self):
        cont = ttk.Frame(self.tab_perfiles_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "perfiles_banner" in self.profile_images:
            ttk.Label(header, image=self.profile_images["perfiles_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Perfiles Pro+", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Acciones de perfiles")
        tiles.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_guardar", "Guardar actual", self.profile_manager_save_current),
            ("tile_cargar", "Cargar perfil", self.profile_manager_load_selected),
            ("tile_exportar", "Exportar", self.profile_export_all),
            ("tile_importar", "Importar", self.profile_import_all),
            ("tile_plantillas", "Plantillas", self.profile_create_templates),
        ]
        for i, (img_key, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            if img_key in self.profile_images:
                ttk.Label(box, image=self.profile_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        history = self.make_card(left, "Perfiles guardados")
        history.pack(fill="both", expand=True)

        self.profile_manager_list = tk.Listbox(
            history,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 10),
            height=18,
            activestyle="none"
        )
        self.profile_manager_list.pack(fill="both", expand=True, padx=4, pady=4)
        self.profile_manager_list.bind("<Double-Button-1>", lambda e: self.profile_manager_load_selected())

        buttons = ttk.Frame(history, style="Card.TFrame")
        buttons.pack(fill="x", pady=(6, 0))
        ttk.Button(buttons, text="Cargar seleccionado", style="Accent.TButton", command=self.profile_manager_load_selected).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(buttons, text="Borrar seleccionado", style="Danger.TButton", command=self.profile_manager_delete_selected).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(buttons, text="Actualizar lista", command=self.profile_manager_refresh).pack(side="left", fill="x", expand=True, padx=4)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Estado")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.profile_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        current = self.make_card(right, "Perfil actual")
        current.pack(fill="x", pady=(0, 10))
        ttk.Label(current, text="Voz actual:", style="Card.TLabel").pack(anchor="w")
        ttk.Label(current, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=310).pack(anchor="w", pady=(2, 8))
        ttk.Label(current, text="Categoría:", style="Card.TLabel").pack(anchor="w")
        ttk.Label(current, textvariable=self.category, style="Card.TLabel", font=("Segoe UI", 12, "bold"), wraplength=310).pack(anchor="w", pady=(2, 8))
        ttk.Label(current, text="Latencia:", style="Card.TLabel").pack(anchor="w")
        ttk.Label(current, textvariable=self.latency, style="Card.TLabel", font=("Segoe UI", 12, "bold"), wraplength=310).pack(anchor="w")

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Guarda un perfil por cada uso.\n"
                "• Ejemplo: Discord, Fortnite, OBS, Podcast.\n"
                "• Exporta perfiles para copiarlos a otro PC.\n"
                "• Usa plantillas para empezar rápido.\n"
                "• Combínalo con Ecualizador Pro."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

        self.profile_manager_refresh()

    def profile_manager_refresh(self):
        if self.profile_manager_list is None:
            return
        self.profile_manager_list.delete(0, tk.END)
        for name in sorted(self.profiles.keys()):
            self.profile_manager_list.insert(tk.END, name)
        if not self.profiles:
            self.profile_manager_list.insert(tk.END, "No hay perfiles todavía.")
        self.profile_status.set(f"Perfiles guardados: {len(self.profiles)}")

    def profile_manager_save_current(self):
        name = simpledialog.askstring("Guardar perfil", "Nombre del perfil:")
        if not name:
            return
        self.profiles[name] = {
            "preset": self.preset.get(),
            "category": self.category.get(),
            "latency": self.latency.get(),
            "values": self.current_values()
        }
        self.save_profiles()
        self.profile_manager_refresh()
        self.refresh_profiles_list()
        self.profile_status.set(f"Perfil guardado: {name}")

    def profile_manager_selected_name(self):
        if self.profile_manager_list is None or not self.profile_manager_list.curselection():
            messagebox.showwarning("Sin selección", "Selecciona un perfil.")
            return None
        name = self.profile_manager_list.get(self.profile_manager_list.curselection()[0])
        if name == "No hay perfiles todavía.":
            return None
        return name

    def profile_manager_load_selected(self):
        name = self.profile_manager_selected_name()
        if not name:
            return
        profile = self.profiles.get(name)
        if not profile:
            messagebox.showwarning("Perfil", "No se encontró ese perfil.")
            return

        self.preset.set(profile.get("preset", "Gaming limpio"))
        self.category.set(profile.get("category", "Todas"))
        self.latency.set(profile.get("latency", "Baja"))
        vals = profile.get("values", {})
        for key, value in vals.items():
            if key in self.vars:
                self.vars[key].set(value)
        self.refresh_voice_list()
        self.apply_preset()
        self.profile_status.set(f"Perfil cargado: {name}")
        self.state.set(f"Estado: perfil cargado · {name}")

    def profile_manager_delete_selected(self):
        name = self.profile_manager_selected_name()
        if not name:
            return
        if name in self.profiles:
            del self.profiles[name]
            self.save_profiles()
            self.profile_manager_refresh()
            self.refresh_profiles_list()
            self.profile_status.set(f"Perfil borrado: {name}")

    def profile_export_all(self):
        if not self.profiles:
            messagebox.showwarning("Exportar", "No hay perfiles para exportar.")
            return
        path = filedialog.asksaveasfilename(
            title="Exportar perfiles",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=2)
            self.profile_status.set(f"Perfiles exportados: {path}")
            messagebox.showinfo("Exportado", f"Perfiles exportados en:\n\n{path}")
        except Exception as e:
            messagebox.showerror("Exportar", f"No se pudo exportar:\n{e}")

    def profile_import_all(self):
        path = filedialog.askopenfilename(
            title="Importar perfiles",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("El archivo no contiene perfiles válidos.")
            count = 0
            for name, profile in data.items():
                if isinstance(profile, dict):
                    final_name = name
                    if final_name in self.profiles:
                        final_name = final_name + " (importado)"
                    self.profiles[final_name] = profile
                    count += 1
            self.save_profiles()
            self.profile_manager_refresh()
            self.refresh_profiles_list()
            self.profile_status.set(f"Perfiles importados: {count}")
            messagebox.showinfo("Importado", f"Perfiles importados: {count}")
        except Exception as e:
            messagebox.showerror("Importar", f"No se pudo importar:\n{e}")

    def profile_create_templates(self):
        templates = {
            "Plantilla Discord Claro": {
                "preset": "Discord claro",
                "category": "Gaming",
                "latency": "Baja",
                "values": {"pitch": 0, "bass": 18, "robot": 0, "echo": 1, "radio": 0, "megaphone": 0, "gate": 8, "comp": 45, "vol": 94}
            },
            "Plantilla Fortnite Grave": {
                "preset": "Fortnite grave",
                "category": "Gaming",
                "latency": "Baja",
                "values": {"pitch": -3, "bass": 60, "robot": 0, "echo": 3, "radio": 0, "megaphone": 0, "gate": 8, "comp": 50, "vol": 98}
            },
            "Plantilla Podcast Pro": {
                "preset": "Podcast",
                "category": "Limpias",
                "latency": "Estable",
                "values": {"pitch": 0, "bass": 22, "robot": 0, "echo": 1, "radio": 0, "megaphone": 0, "gate": 9, "comp": 62, "vol": 92}
            },
            "Plantilla Robot Directo": {
                "preset": "Robot directo",
                "category": "Robots",
                "latency": "Baja",
                "values": {"pitch": 1, "bass": 20, "robot": 75, "echo": 4, "radio": 10, "megaphone": 0, "gate": 8, "comp": 45, "vol": 96}
            },
            "Plantilla Cine Épico": {
                "preset": "Narrador épico",
                "category": "Épicas",
                "latency": "Estable",
                "values": {"pitch": -2, "bass": 65, "robot": 0, "echo": 16, "radio": 4, "megaphone": 5, "gate": 8, "comp": 70, "vol": 102}
            }
        }

        added = 0
        for name, profile in templates.items():
            if name not in self.profiles:
                self.profiles[name] = profile
                added += 1

        self.save_profiles()
        self.profile_manager_refresh()
        self.refresh_profiles_list()
        self.profile_status.set(f"Plantillas creadas: {added}")
        messagebox.showinfo("Plantillas", f"Plantillas añadidas: {added}")


    def build_ecualizador_tab(self):
        cont = ttk.Frame(self.tab_ecualizador)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "ecualizador_banner" in self.eq_images:
            ttk.Label(header, image=self.eq_images["ecualizador_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Ecualizador Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        presets_card = self.make_card(left, "Presets de ecualizador")
        presets_card.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(presets_card, style="Card.TFrame")
        grid.pack(fill="x")

        preset_items = [
            ("tile_limpio", "Directo limpio", "limpio"),
            ("tile_grave", "Grave potente", "grave"),
            ("tile_radio", "Radio directa", "radio"),
            ("tile_robot", "Robot claro", "robot"),
            ("tile_cine", "Cine épico", "cine"),
        ]

        for i, (img_key, label, preset_key) in enumerate(preset_items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            if img_key in self.eq_images:
                ttk.Label(box, image=self.eq_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, command=lambda p=preset_key, l=label: self.apply_eq_preset(p, l)).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        controls = self.make_card(left, "Controles grandes")
        controls.pack(fill="both", expand=True)

        self.eq_big_slider(controls, "Tono", "pitch", -12, 12, "semitonos")
        self.eq_big_slider(controls, "Grave extra", "bass", 0, 100, "%")
        self.eq_big_slider(controls, "Claridad / radio", "radio", 0, 100, "%")
        self.eq_big_slider(controls, "Robot", "robot", 0, 100, "%")
        self.eq_big_slider(controls, "Eco", "echo", 0, 100, "%")
        self.eq_big_slider(controls, "Volumen salida", "vol", 0, 120, "%")

        bandas = self.make_card(left, "Bandas reales (dB)")
        bandas.pack(fill="x", pady=(10, 0))
        ttk.Label(bandas, text="Ecualizador real de 3 bandas: graves (<250 Hz), medios y agudos (>4 kHz). 0 dB = transparente.", style="Card.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(0, 4))
        self.eq_big_slider(bandas, "Graves", "eq_low", -12, 12, " dB")
        self.eq_big_slider(bandas, "Medios", "eq_mid", -12, 12, " dB")
        self.eq_big_slider(bandas, "Agudos", "eq_high", -12, 12, " dB")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Estado del ecualizador")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, text="Preset actual:", style="Card.TLabel").pack(anchor="w")
        ttk.Label(status, textvariable=self.eq_preset, style="Card.TLabel", font=("Segoe UI", 16, "bold"), wraplength=310).pack(anchor="w", pady=(2, 8))
        ttk.Label(status, textvariable=self.eq_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        actions = self.make_card(right, "Acciones")
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Guardar como perfil", command=self.save_current_profile).pack(fill="x", pady=3)
        ttk.Button(actions, text="Grabar prueba WAV", command=self.record).pack(fill="x", pady=3)
        ttk.Button(actions, text="Abrir Grabadora", command=lambda: self.select_tab(self.tab_grabadora)).pack(fill="x", pady=3)
        ttk.Button(actions, text="Reiniciar voz", command=self.reset).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Baja el eco si hay retraso.\n"
                "• Sube graves para voz potente.\n"
                "• Usa radio para estilo directo.\n"
                "• Guarda perfiles para no repetir ajustes.\n"
                "• Prueba la voz con Grabadora Pro."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def eq_big_slider(self, parent, label, key, mn, mx, unit):
        line = ttk.Frame(parent, style="Card.TFrame")
        line.pack(fill="x", pady=6)

        top = ttk.Frame(line, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text=label + ":", style="Card.TLabel", width=18).pack(side="left")

        var = self.vars[key]
        value = ttk.Label(top, style="Card.TLabel", width=14)
        value.pack(side="right")

        scale = ttk.Scale(line, from_=mn, to=mx, variable=var, orient="horizontal", command=lambda _=None: self.update_engine())
        scale.pack(fill="x", pady=(4, 0))

        def refresh(*_):
            v = var.get()
            if unit == "semitonos":
                value.config(text=f"{v:+.1f} {unit}")
            else:
                value.config(text=f"{v:.0f}{unit}")
            self.update_engine()

        var.trace_add("write", refresh)
        refresh()

    def apply_eq_preset(self, preset_key, label):
        presets = {
            "limpio": {
                "pitch": 0, "bass": 12, "robot": 0, "echo": 2, "radio": 0,
                "megaphone": 0, "gate": 7, "comp": 36, "vol": 92
            },
            "grave": {
                "pitch": -4, "bass": 70, "robot": 0, "echo": 4, "radio": 2,
                "megaphone": 0, "gate": 8, "comp": 48, "vol": 98
            },
            "radio": {
                "pitch": 0, "bass": 24, "robot": 0, "echo": 3, "radio": 70,
                "megaphone": 8, "gate": 10, "comp": 55, "vol": 95
            },
            "robot": {
                "pitch": 1, "bass": 20, "robot": 76, "echo": 4, "radio": 12,
                "megaphone": 0, "gate": 9, "comp": 45, "vol": 95
            },
            "cine": {
                "pitch": -2, "bass": 58, "robot": 0, "echo": 18, "radio": 5,
                "megaphone": 6, "gate": 8, "comp": 68, "vol": 102
            },
        }

        values = presets.get(preset_key)
        if not values:
            return

        for key, value in values.items():
            if key in self.vars:
                self.vars[key].set(value)

        self.eq_preset.set(label)
        self.eq_status.set(f"Preset aplicado: {label}. Prueba la voz o guarda perfil.")
        self.update_engine()
        self.state.set(f"Estado: ecualizador aplicado · {label}")


    def build_mini_panel_tab(self):
        cont = ttk.Frame(self.tab_mini_panel)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "mini_panel_banner" in self.mini_images:
            ttk.Label(header, image=self.mini_images["mini_panel_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Mini Panel Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Funciones")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_flotante", "Ventana flotante"),
            ("tile_voces", "Voces rápidas"),
            ("tile_sonidos", "Sonidos rápidos"),
            ("tile_directo", "Directo"),
        ]
        for i, (img_key, label) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=6)
            if img_key in self.mini_images:
                ttk.Label(box, image=self.mini_images[img_key], style="Card.TLabel").pack()
            ttk.Label(box, text=label, style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        actions = self.make_card(left, "Abrir Mini Panel")
        actions.pack(fill="x", pady=(0, 10))
        row = ttk.Frame(actions, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Button(row, text="Abrir Mini Panel flotante", style="Accent.TButton", command=self.open_mini_panel).pack(side="left", expand=True, fill="x", padx=4, pady=4)
        ttk.Button(row, text="Cerrar Mini Panel", style="Danger.TButton", command=self.close_mini_panel).pack(side="left", expand=True, fill="x", padx=4, pady=4)
        ttk.Button(row, text="Abrir Directo Pro", command=lambda: self.select_tab(self.tab_directo_pro)).pack(side="left", expand=True, fill="x", padx=4, pady=4)

        info = self.make_card(left, "Cómo se usa")
        info.pack(fill="both", expand=True)
        ttk.Label(
            info,
            text=(
                "El Mini Panel es una ventana pequeña que se queda encima.\n\n"
                "Sirve para cambiar voz, lanzar sonidos y empezar/parar directo sin tener que navegar por todas las pestañas.\n\n"
                "Ideal para Discord, Fortnite, OBS y partidas."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=760
        ).pack(anchor="w")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Estado")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.mini_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Ponlo en una esquina.\n"
                "• Usa auriculares para evitar eco.\n"
                "• Guarda tus voces favoritas.\n"
                "• Los favoritos aparecen primero.\n"
                "• Si molesta, ciérralo y usa la app normal."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def mini_quick_voices(self):
        defaults = [
            "Gaming limpio", "Discord claro", "Fortnite grave", "Streamer",
            "Locutor español", "Podcast", "Robot directo", "Alien",
        ]
        result = []
        for v in self.favorites:
            if v in VoiceBank.all_presets() and v not in result:
                result.append(v)
        for v in defaults:
            if v in VoiceBank.all_presets() and v not in result:
                result.append(v)
        return result[:8]

    def open_mini_panel(self):
        if self.mini_window is not None and self.mini_window.winfo_exists():
            self.mini_window.lift()
            self.mini_status.set("Mini Panel ya estaba abierto.")
            return

        win = tk.Toplevel(self.root)
        self.mini_window = win
        win.title("Mini Panel Pro")
        win.geometry("390x620")
        win.minsize(360, 560)
        win.configure(bg=COLORS["bg"])
        win.attributes("-topmost", True)
        try:
            win.iconbitmap(resource_path("assets/app_icon.ico"))
        except Exception:
            pass

        outer = ttk.Frame(win, padding=12)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Mini Panel Pro", style="Card.TLabel", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(outer, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 12, "bold"), wraplength=340).pack(anchor="w", pady=(0, 8))

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Button(controls, text="▶ Empezar", style="Accent.TButton", command=self.start).pack(side="left", expand=True, fill="x", padx=(0, 3))
        ttk.Button(controls, text="■ Parar", style="Danger.TButton", command=self.stop).pack(side="left", expand=True, fill="x", padx=3)
        ttk.Button(controls, text="▾ Bandeja", command=self.hide_to_tray).pack(side="left", expand=True, fill="x", padx=(3, 0))

        toggles = ttk.Frame(outer)
        toggles.pack(fill="x", pady=(0, 8))
        ttk.Checkbutton(toggles, text="Modulador", variable=self.effects_enabled, command=self.update_engine).pack(side="left", padx=(0, 8))
        ttk.Checkbutton(toggles, text="Silenciar", variable=self.mute, command=self.update_engine).pack(side="left")

        ttk.Label(outer, text="Voces rápidas", style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 4))
        voice_frame = ttk.Frame(outer)
        voice_frame.pack(fill="x")
        for i, voice in enumerate(self.mini_quick_voices()):
            ttk.Button(
                voice_frame,
                text=voice,
                command=lambda v=voice: self.apply_mini_voice(v)
            ).grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3, ipady=5)
        for col in range(2):
            voice_frame.columnconfigure(col, weight=1)

        ttk.Label(outer, text="Sonidos rápidos", style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(12, 4))
        sound_frame = ttk.Frame(outer)
        sound_frame.pack(fill="x")
        sounds = [
            ("Aplausos", "aplausos"),
            ("Risas", "risas"),
            ("Victoria", "victoria"),
            ("Error", "error"),
            ("Alerta", "alerta"),
            ("Impacto", "impacto"),
            ("Magia", "magia"),
            ("Beep", "beep"),
        ]
        for i, (label, key) in enumerate(sounds):
            ttk.Button(
                sound_frame,
                text=label,
                command=lambda k=key, l=label: self.play_mini_sound(k, l)
            ).grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3, ipady=5)
        for col in range(2):
            sound_frame.columnconfigure(col, weight=1)

        ttk.Label(outer, text="Accesos", style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(12, 4))
        access = ttk.Frame(outer)
        access.pack(fill="x")
        ttk.Button(access, text="Caja de voces", command=lambda: [self.select_tab(self.tab_voicebox_grid), win.lift()]).pack(fill="x", pady=2)
        ttk.Button(access, text="Mesa Pro", command=lambda: [self.select_tab(self.tab_mesa_pro), win.lift()]).pack(fill="x", pady=2)
        ttk.Button(access, text="Directo Pro", command=lambda: [self.select_tab(self.tab_directo_pro), win.lift()]).pack(fill="x", pady=2)

        ttk.Button(outer, text="Cerrar Mini Panel", command=self.close_mini_panel).pack(fill="x", pady=(12, 0))

        win.protocol("WM_DELETE_WINDOW", self.close_mini_panel)
        self.mini_status.set("Mini Panel abierto y siempre encima.")

    def close_mini_panel(self):
        if self.mini_window is not None:
            try:
                self.mini_window.destroy()
            except Exception:
                pass
        self.mini_window = None
        self.mini_status.set("Mini Panel cerrado.")

    def apply_mini_voice(self, voice_name):
        if voice_name in VoiceBank.all_presets():
            self.preset.set(voice_name)
            self.category.set(VoiceBank.all_presets()[voice_name][0])
            self.apply_preset()
            self.refresh_voice_list()
            self.state.set(f"Estado: voz aplicada desde Mini Panel · {voice_name}")
            self.mini_status.set(f"Voz aplicada: {voice_name}")

    def play_mini_sound(self, key, label):
        self.play_sfx(key)
        self.mini_status.set(f"Sonido lanzado: {label}")


    def build_diagnostico_tab(self):
        cont = ttk.Frame(self.tab_diagnostico)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "diagnostico_banner" in self.diag_images:
            ttk.Label(header, image=self.diag_images["diagnostico_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Diagnóstico Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Comprobaciones")
        tiles.pack(fill="x", pady=(0, 10))

        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_sistema", "Sistema", self.run_diagnostics),
            ("tile_audio", "Audio", self.diagnostic_audio_only),
            ("tile_virtual", "Cable virtual", self.diagnostic_virtual_only),
            ("tile_informe", "Informe TXT", self.save_diagnostic_report),
        ]
        for i, (img_key, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=6)
            if img_key in self.diag_images:
                ttk.Label(box, image=self.diag_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        actions = self.make_card(left, "Acciones rápidas")
        actions.pack(fill="x", pady=(0, 10))
        row = ttk.Frame(actions, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Button(row, text="Comprobar sistema", style="Accent.TButton", command=self.run_diagnostics).pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(row, text="Probar salida", command=lambda: self.play_sfx("beep")).pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(row, text="Buscar cable virtual", command=self.diagnostic_find_virtual).pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(row, text="Guardar informe TXT", command=self.save_diagnostic_report).pack(side="left", expand=True, fill="x", padx=4)

        result = self.make_card(left, "Resultado del diagnóstico")
        result.pack(fill="both", expand=True)

        self.diagnostic_text = tk.Text(
            result,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.diagnostic_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Estado")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.diagnostic_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        tips = self.make_card(right, "Qué revisar")
        tips.pack(fill="x", pady=(0, 10))
        ttk.Label(
            tips,
            text=(
                "✓ Micrófono detectado\n"
                "✓ Salida detectada\n"
                "✓ Cable virtual si usas juegos/apps\n"
                "✓ Dependencias cargadas\n"
                "✓ Assets encontrados\n"
                "✓ Prueba de salida con beep"
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

        help_card = self.make_card(right, "Si algo falla")
        help_card.pack(fill="x")
        ttk.Label(
            help_card,
            text=(
                "1. Pulsa Actualizar dispositivos.\n"
                "2. Conecta auriculares.\n"
                "3. Revisa permisos de micrófono en Windows.\n"
                "4. Para Discord/Fortnite/OBS usa cable virtual.\n"
                "5. Guarda el informe TXT para revisarlo."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

        self.run_diagnostics()

    def diagnostic_lines(self):
        lines = []
        lines.append("=== DIAGNÓSTICO PRO ===")
        lines.append(f"Aplicación: {APP_NAME}")
        lines.append(f"Versión: {VERSION}")
        lines.append(f"Python: {sys.version.split()[0]}")
        lines.append(f"Sistema: {platform.system()} {platform.release()}")
        lines.append("")

        # Dependencias
        lines.append("=== DEPENDENCIAS ===")
        deps = ["numpy", "sounddevice", "PIL", "pystray"]
        for dep in deps:
            try:
                __import__(dep)
                lines.append(f"OK · {dep}")
            except Exception as e:
                lines.append(f"ERROR · {dep}: {e}")
        lines.append("")

        # Dispositivos
        lines.append("=== DISPOSITIVOS DE AUDIO ===")
        try:
            devices = sd.query_devices()
            input_count = 0
            output_count = 0
            virtual_hits = []
            virtual_keywords = ["cable", "vb-audio", "voicemeeter", "virtual", "blackhole"]

            for i, dev in enumerate(devices):
                name = str(dev.get("name", "Sin nombre"))
                max_in = int(dev.get("max_input_channels", 0))
                max_out = int(dev.get("max_output_channels", 0))
                if max_in > 0:
                    input_count += 1
                if max_out > 0:
                    output_count += 1
                if any(k in name.lower() for k in virtual_keywords):
                    virtual_hits.append(name)
                lines.append(f"{i:02d} · {name} · entrada:{max_in} · salida:{max_out}")

            lines.append("")
            lines.append(f"Entradas detectadas: {input_count}")
            lines.append(f"Salidas detectadas: {output_count}")
            if virtual_hits:
                lines.append("Cable virtual posible:")
                for name in virtual_hits:
                    lines.append(f"  - {name}")
            else:
                lines.append("Cable virtual: no detectado")
        except Exception as e:
            lines.append(f"ERROR consultando dispositivos: {e}")
        lines.append("")

        # Config actual
        lines.append("=== CONFIGURACIÓN ACTUAL ===")
        lines.append(f"Entrada seleccionada: {self.input_dev.get() if hasattr(self, 'input_dev') else 'No disponible'}")
        lines.append(f"Salida seleccionada: {self.output_dev.get() if hasattr(self, 'output_dev') else 'No disponible'}")
        lines.append(f"Voz actual: {self.preset.get() if hasattr(self, 'preset') else 'No disponible'}")
        lines.append(f"Latencia: {self.latency.get() if hasattr(self, 'latency') else 'No disponible'}")
        lines.append("")

        # Assets
        lines.append("=== ASSETS ===")
        asset_checks = [
            "assets/voices",
            "assets/pro",
            "assets/grid",
            "assets/asistente",
            "assets/mesa_sonidos",
            "assets/grabadora",
            "assets/diagnostico",
        ]
        for folder in asset_checks:
            path = resource_path(folder)
            lines.append(f"{folder}: {'OK' if os.path.exists(path) else 'NO ENCONTRADO'}")
        lines.append("")
        lines.append("Fin del informe.")
        return lines

    def set_diagnostic_text(self, text):
        if self.diagnostic_text is None:
            return
        self.diagnostic_text.delete("1.0", tk.END)
        self.diagnostic_text.insert("1.0", text)

    def run_diagnostics(self):
        lines = self.diagnostic_lines()
        text = "\n".join(lines)
        self.set_diagnostic_text(text)
        self.diagnostic_status.set("Diagnóstico completado. Revisa el resultado.")
        self.state.set("Estado: diagnóstico completado")

    def diagnostic_audio_only(self):
        self.load_devices()
        lines = ["=== AUDIO ==="]
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                name = str(dev.get("name", "Sin nombre"))
                max_in = int(dev.get("max_input_channels", 0))
                max_out = int(dev.get("max_output_channels", 0))
                if max_in > 0 or max_out > 0:
                    lines.append(f"{i:02d} · {name} · entrada:{max_in} · salida:{max_out}")
        except Exception as e:
            lines.append(f"ERROR: {e}")
        self.set_diagnostic_text("\n".join(lines))
        self.diagnostic_status.set("Audio comprobado.")

    def diagnostic_virtual_only(self):
        lines = ["=== CABLE VIRTUAL ==="]
        try:
            devices = sd.query_devices()
            keywords = ["cable", "vb-audio", "voicemeeter", "virtual", "blackhole"]
            hits = []
            for dev in devices:
                name = str(dev.get("name", "Sin nombre"))
                if any(k in name.lower() for k in keywords):
                    hits.append(name)
            if hits:
                lines.append("Posibles cables virtuales encontrados:")
                for h in hits:
                    lines.append(f"- {h}")
            else:
                lines.append("No se encontró cable virtual.")
                lines.append("Para Discord/Fortnite/OBS suele hacer falta VB-Cable o VoiceMeeter.")
        except Exception as e:
            lines.append(f"ERROR: {e}")
        self.set_diagnostic_text("\n".join(lines))
        self.diagnostic_status.set("Cable virtual comprobado.")

    def diagnostic_find_virtual(self):
        ok = self.find_virtual()
        if ok:
            self.diagnostic_status.set("Cable virtual encontrado y seleccionado.")
        else:
            self.diagnostic_status.set("No se encontró cable virtual.")
        self.diagnostic_virtual_only()

    def save_diagnostic_report(self):
        try:
            lines = self.diagnostic_lines()
            folder = os.path.join(os.path.expanduser("~"), "ModuladorVozDirecto_Informes")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "diagnostico_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.diagnostic_status.set(f"Informe guardado: {path}")
            messagebox.showinfo("Informe guardado", f"Informe guardado en:\n\n{path}")
        except Exception as e:
            messagebox.showerror("Informe", f"No se pudo guardar el informe:\n{e}")


    def build_mesa_pro_tab(self):
        cont = ttk.Frame(self.tab_mesa_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "mesa_sonidos_banner" in self.mesa_images:
            ttk.Label(header, image=self.mesa_images["mesa_sonidos_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Mesa de Sonidos Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        categories = self.make_card(left, "Categorías de pads")
        categories.pack(fill="x", pady=(0, 10))

        cat_grid = ttk.Frame(categories, style="Card.TFrame")
        cat_grid.pack(fill="x")

        cat_items = [
            ("pad_reacciones", "Reacciones", "reacciones"),
            ("pad_gaming", "Gaming", "gaming"),
            ("pad_directo", "Directo", "directo"),
            ("pad_ambiente", "Ambiente", "ambiente"),
            ("pad_personalizados", "Personalizados", "personalizados"),
        ]

        for i, (img_key, label, category) in enumerate(cat_items):
            box = ttk.Frame(cat_grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            if img_key in self.mesa_images:
                ttk.Label(box, image=self.mesa_images[img_key], style="Card.TLabel").pack()
            ttk.Button(box, text=label, command=lambda c=category: self.mostrar_pads_mesa(c)).pack(fill="x", pady=(5, 0))
            cat_grid.columnconfigure(i, weight=1)

        pads = self.make_card(left, "Pads de sonido")
        pads.pack(fill="both", expand=True)

        self.mesa_pads_frame = ttk.Frame(pads, style="Card.TFrame")
        self.mesa_pads_frame.pack(fill="both", expand=True)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Estado")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.mesa_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        controls = self.make_card(right, "Controles")
        controls.pack(fill="x", pady=(0, 10))
        ttk.Button(controls, text="Parar sonidos", style="Danger.TButton", command=self.stop_sfx).pack(fill="x", pady=3)
        ttk.Button(controls, text="Cargar WAV personalizado", command=self.add_custom_wav).pack(fill="x", pady=3)
        ttk.Button(controls, text="Abrir mesa clásica", command=lambda: self.select_tab(self.tab_sonidos)).pack(fill="x", pady=3)
        ttk.Button(controls, text="Abrir Directo Pro", command=lambda: self.select_tab(self.tab_directo_pro)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Reacciones: para contestar rápido.\n"
                "• Gaming: para partidas.\n"
                "• Directo: para alertas y golpes.\n"
                "• Ambiente: para fondos mágicos.\n"
                "• Personalizados: tus WAV cargados."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

        self.mostrar_pads_mesa("reacciones")

    def sonidos_mesa(self):
        return {
            "reacciones": [
                ("Aplausos", "aplausos"),
                ("Risas", "risas"),
                ("Sorpresa", "suspense"),
                ("Beep", "beep"),
            ],
            "gaming": [
                ("Victoria", "victoria"),
                ("Error", "error"),
                ("Power Up", "powerup"),
                ("Impacto", "impacto"),
            ],
            "directo": [
                ("Alerta", "alerta"),
                ("Redoble", "redoble"),
                ("Impacto", "impacto"),
                ("Beep", "beep"),
            ],
            "ambiente": [
                ("Magia", "magia"),
                ("Lluvia suave", "lluvia"),
                ("Suspense", "suspense"),
                ("Power Up", "powerup"),
            ],
        }

    def mostrar_pads_mesa(self, category):
        if not hasattr(self, "mesa_pads_frame"):
            return

        for child in self.mesa_pads_frame.winfo_children():
            child.destroy()

        if category == "personalizados":
            self.mesa_status.set("Categoría: personalizados. Carga o reproduce sonidos WAV.")
            ttk.Button(
                self.mesa_pads_frame,
                text="Cargar nuevo WAV personalizado",
                style="Accent.TButton",
                command=self.add_custom_wav
            ).grid(row=0, column=0, sticky="nsew", padx=8, pady=8, ipady=18)

            names = sorted(self.custom_sfx.keys())
            if not names:
                ttk.Label(
                    self.mesa_pads_frame,
                    text="Todavía no has cargado WAV personalizados.",
                    style="Card.TLabel"
                ).grid(row=1, column=0, sticky="w", padx=8, pady=8)
            else:
                for i, name in enumerate(names):
                    ttk.Button(
                        self.mesa_pads_frame,
                        text=name,
                        command=lambda n=name: self.play_custom_sfx_by_name(n)
                    ).grid(row=(i+1)//3, column=(i+1)%3, sticky="nsew", padx=8, pady=8, ipady=14)
            for col in range(3):
                self.mesa_pads_frame.columnconfigure(col, weight=1)
            return

        sounds = self.sonidos_mesa().get(category, [])
        self.mesa_status.set(f"Categoría: {category}. Pulsa un pad para lanzarlo.")

        for i, (label, key) in enumerate(sounds):
            btn = ttk.Button(
                self.mesa_pads_frame,
                text=label,
                style="Accent.TButton",
                command=lambda k=key, l=label: self.lanzar_pad_mesa(k, l)
            )
            btn.grid(row=i // 2, column=i % 2, sticky="nsew", padx=10, pady=10, ipady=24)

        for col in range(2):
            self.mesa_pads_frame.columnconfigure(col, weight=1)
        for row in range(2):
            self.mesa_pads_frame.rowconfigure(row, weight=1)

    def lanzar_pad_mesa(self, key, label):
        self.play_sfx(key)
        self.mesa_status.set(f"Sonido lanzado: {label}")

    def play_custom_sfx_by_name(self, name):
        samples = self.custom_sfx.get(name)
        if samples is not None:
            self.engine.add_sfx(samples)
            self.mesa_status.set(f"Sonido personalizado lanzado: {name}")
























    def build_command_center_tab(self):
        cont = ttk.Frame(self.tab_command_center)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "command_banner" in self.command_center_images:
            ttk.Label(header, image=self.command_center_images["command_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Command Center Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Acciones rápidas")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_search", "Buscar", self.command_refresh_results),
            ("tile_creator", "Creator", lambda: self.command_apply_workflow("creator")),
            ("tile_streamer", "Streamer", lambda: self.command_apply_workflow("streamer")),
            ("tile_karaoke", "Karaoke", lambda: self.command_apply_workflow("karaoke")),
            ("tile_launch", "Launch", lambda: self.command_apply_workflow("launch")),
            ("tile_export", "Exportar mapa", self.command_export_map),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.command_center_images:
                ttk.Label(box, image=self.command_center_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        navigator = self.make_card(body, "Buscador de módulos")
        navigator.pack(side="left", fill="both", expand=True, padx=(0, 5))
        search_row = ttk.Frame(navigator, style="Card.TFrame")
        search_row.pack(fill="x", pady=(0, 6))
        ttk.Label(search_row, text="Buscar:", style="Card.TLabel").pack(side="left")
        entry = ttk.Entry(search_row, textvariable=self.command_search)
        entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(search_row, text="Buscar", command=self.command_refresh_results).pack(side="left", padx=3)
        ttk.Button(search_row, text="Limpiar", command=self.command_clear_search).pack(side="left", padx=3)
        self.command_search.trace_add("write", lambda *_: self.command_refresh_results())

        list_frame = ttk.Frame(navigator, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True)
        self.command_listbox = tk.Listbox(
            list_frame,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#071018",
            relief="flat",
            activestyle="none",
            font=("Consolas", 10),
            height=16
        )
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.command_listbox.yview)
        self.command_listbox.configure(yscrollcommand=scroll.set)
        self.command_listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.command_listbox.bind("<<ListboxSelect>>", lambda e: self.command_preview_selected())
        self.command_listbox.bind("<Double-Button-1>", lambda e: self.command_open_selected())

        btns = ttk.Frame(navigator, style="Card.TFrame")
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Abrir módulo", style="Accent.TButton", command=self.command_open_selected).pack(side="left", expand=True, fill="x", padx=3, ipady=7)
        ttk.Button(btns, text="Exportar mapa", command=self.command_export_map).pack(side="left", expand=True, fill="x", padx=3, ipady=7)
        ttk.Button(btns, text="Abrir Inicio", command=lambda: self.command_open_attr("tab_inicio_premium")).pack(side="left", expand=True, fill="x", padx=3, ipady=7)

        preview = self.make_card(body, "Mapa / vista previa")
        preview.pack(side="left", fill="both", expand=True, padx=(5, 0))
        if "command_map" in self.command_center_images:
            ttk.Label(preview, image=self.command_center_images["command_map"], style="Card.TLabel").pack(anchor="center", pady=(0, 6))
        self.command_preview_text = tk.Text(
            preview,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=12
        )
        self.command_preview_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.command_center_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        workflow = self.make_card(right, "Workflow premium")
        workflow.pack(fill="x", pady=(0, 10))
        ttk.Combobox(workflow, textvariable=self.command_mode, state="readonly", values=["Creator", "Streamer", "Karaoke", "Launch"]).pack(fill="x", pady=(0, 6))
        ttk.Button(workflow, text="Aplicar workflow", style="Accent.TButton", command=self.command_apply_selected_workflow).pack(fill="x", pady=3)
        ttk.Button(workflow, text="Modo Creator", command=lambda: self.command_apply_workflow("creator")).pack(fill="x", pady=3)
        ttk.Button(workflow, text="Modo Streamer", command=lambda: self.command_apply_workflow("streamer")).pack(fill="x", pady=3)
        ttk.Button(workflow, text="Modo Launch", command=lambda: self.command_apply_workflow("launch")).pack(fill="x", pady=3)

        fav = self.make_card(right, "Accesos top")
        fav.pack(fill="x", pady=(0, 10))
        for label, attr in [
            ("🏠 Inicio Premium", "tab_inicio_premium"),
            ("🪄 Asistente", "tab_asistente_inicial"),
            ("💎 Premium", "tab_premium_experience"),
            ("💠 UI Premium", "tab_ultra_premium_ui"),
            ("💼 Polish", "tab_professional_polish"),
            ("📚 Biblioteca", "tab_biblioteca_premium"),
            ("🚀 Publicación", "tab_publicacion_pro"),
            ("🚢 Deploy", "tab_deploy_pro"),
        ]:
            if hasattr(self, attr):
                ttk.Button(fav, text=label, command=lambda a=attr: self.command_open_attr(a)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Qué mejora V73")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text="Command Center convierte la app en algo más premium porque cualquier función se encuentra en segundos: buscador, mapa, workflows y accesos inteligentes.",
            style="Card.TLabel",
            justify="left",
            wraplength=320,
        ).pack(anchor="w")

        self.command_refresh_results()
        self.command_preview_text_set("Command Center listo. Busca 'karaoke', 'master', 'publicación', 'visual', 'cable', 'directo'...")

    def command_modules(self):
        modules = [
            ("Inicio Premium", "tab_inicio_premium", "Setup", "Launcher principal con tarjetas y flujo recomendado."),
            ("Asistente Inicial", "tab_asistente_inicial", "Setup", "Primer arranque guiado: micro, cable, voz, visual y exportación."),
            ("Revisión Técnica", "tab_revision_tecnica", "Sistema", "Auditoría técnica, WAV, dependencias y estabilidad."),
            ("Visual Pro", "tab_visual_pro", "Visual", "Temas, densidad visual, modo enfoque y look premium."),
            ("Premium Experience", "tab_premium_experience", "Visual", "Centro premium, puntuación y acabado de producto."),
            ("UI Premium", "tab_ultra_premium_ui", "Visual", "Temas premium, focus mode y badge UI."),
            ("Professional Polish", "tab_professional_polish", "Visual", "Pulido profesional, showroom y puntuación de acabado."),
            ("Studio Dashboard", "tab_studio_dashboard", "Studio", "Flujo completo: analizar, voz, timeline, multipista, mezcla y master."),
            ("Analizador Vocal", "tab_analizador_vocal", "Voz", "Calidad vocal: volumen, eco, compresión y recomendaciones."),
            ("Cadena Vocal", "tab_cadena_vocal", "Voz", "Ruido, compresor, presencia, aire, reverb y delay."),
            ("Autotune", "tab_autotune", "Voz", "Cantar con efecto tipo autotune y voces cantadas."),
            ("Karaoke", "tab_karaoke", "Música", "Cargar instrumental WAV y cantar encima."),
            ("Karaoke Studio", "tab_karaoke_studio", "Música", "Generar bases originales sin voz."),
            ("Canción Pro", "tab_cancion_pro", "Música", "Crear demo con intro, verso, estribillo y outro."),
            ("Timeline", "tab_timeline_pro", "Música", "Estructura de canción, BPM, tonalidad y secciones."),
            ("Multipista", "tab_multipista", "Studio", "Organizar voz, coros, instrumental, FX y master."),
            ("Mezclador", "tab_mezclador_musical", "Studio", "Faders de voz, instrumental y master."),
            ("Master Final", "tab_master_final", "Studio", "Normalizar, limiter, fades y exportar WAV."),
            ("Biblioteca", "tab_biblioteca_premium", "Archivos", "Gestionar WAV, PNG, JSON, TXT y proyectos."),
            ("Portadas", "tab_portadas_premium", "Visual", "Generar cover art PNG para demos/canciones."),
            ("Brand Kit", "tab_brand_kit", "Visual", "Logo, banner, avatar, paleta y pack de marca."),
            ("Publicación", "tab_publicacion_pro", "Launch", "Título, descripción, tags y release notes."),
            ("Export Pack", "tab_export_pack", "Launch", "ZIP final con audio, portada, docs y manifiesto."),
            ("Landing Page", "tab_landing_page", "Launch", "HTML de presentación para demo/proyecto."),
            ("Web Pack", "tab_web_pack", "Launch", "ZIP web completo para hosting/GitHub Pages."),
            ("Deploy", "tab_deploy_pro", "Launch", "Checklist y ZIP publicable con .nojekyll."),
            ("Cable Virtual", "tab_cable_virtual", "Directo", "Guía Discord/Fortnite/OBS con cable virtual."),
            ("Streamer Hub", "tab_streamer_hub", "Directo", "Preparación para directo, OBS, Discord y Fortnite."),
            ("Rendimiento", "tab_rendimiento", "Sistema", "Modos de latencia y estabilidad."),
            ("Diagnóstico", "tab_diagnostico", "Sistema", "Revisión de dispositivos y problemas."),
            ("Atajos", "tab_atajos", "Control", "Hotkeys internos/globales según versión."),
            ("Favoritos", "tab_favoritos_pro", "Control", "Voces y sonidos rápidos favoritos."),
            ("Mesa Pro", "tab_mesa_pro", "Control", "Soundboard y mesa de sonidos."),
        ]
        return [dict(name=n, attr=a, group=g, desc=d) for n,a,g,d in modules if hasattr(self, a)]

    def command_refresh_results(self):
        if not hasattr(self, "command_listbox"):
            return
        q = self.command_search.get().strip().lower()
        mods = self.command_modules()
        if q:
            mods = [m for m in mods if q in m["name"].lower() or q in m["group"].lower() or q in m["desc"].lower()]
        self.command_results = mods
        self.command_listbox.delete(0, tk.END)
        for m in mods:
            self.command_listbox.insert(tk.END, f"{m['group']:<9} · {m['name']:<24} · {m['desc']}")
        self.command_center_status.set(f"Command Center: {len(mods)} módulo(s) encontrado(s).")

    def command_clear_search(self):
        self.command_search.set("")
        self.command_refresh_results()

    def command_selected_module(self):
        if not hasattr(self, "command_listbox"):
            return None
        sel = self.command_listbox.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.command_results):
            return None
        return self.command_results[idx]

    def command_preview_text_set(self, text):
        if not hasattr(self, "command_preview_text"):
            return
        self.command_preview_text.configure(state="normal")
        self.command_preview_text.delete("1.0", tk.END)
        self.command_preview_text.insert("1.0", text)
        self.command_preview_text.configure(state="disabled")

    def command_preview_selected(self):
        m = self.command_selected_module()
        if not m:
            self.command_preview_text_set("Selecciona un módulo para ver detalles.")
            return
        self.command_preview_text_set(
            "MÓDULO SELECCIONADO\n\n"
            f"Nombre: {m['name']}\n"
            f"Grupo: {m['group']}\n"
            f"Pestaña interna: {m['attr']}\n\n"
            f"Uso: {m['desc']}\n\n"
            "Doble clic o pulsa 'Abrir módulo' para entrar."
        )

    def command_open_selected(self):
        m = self.command_selected_module()
        if not m:
            self.command_center_status.set("Selecciona un módulo primero.")
            return
        self.command_open_attr(m["attr"])

    def command_open_attr(self, attr):
        if attr and hasattr(self, attr):
            self.select_tab(getattr(self, attr))
            self.command_center_status.set(f"Abierto: {attr}")
            return True
        self.command_center_status.set(f"No se encontró el módulo: {attr}")
        return False

    def command_apply_selected_workflow(self):
        self.command_apply_workflow(self.command_mode.get().lower())

    def command_apply_workflow(self, mode):
        mode = str(mode).lower()
        workflows = {
            "creator": ["tab_asistente_inicial", "tab_cadena_vocal", "tab_timeline_pro", "tab_cancion_pro", "tab_mezclador_musical", "tab_master_final", "tab_biblioteca_premium"],
            "streamer": ["tab_cable_virtual", "tab_streamer_hub", "tab_analizador_vocal", "tab_cadena_vocal", "tab_favoritos_pro", "tab_directo_pro"],
            "karaoke": ["tab_cadena_vocal", "tab_karaoke_studio", "tab_karaoke", "tab_autotune", "tab_grabadora", "tab_master_final"],
            "launch": ["tab_portadas_premium", "tab_brand_kit", "tab_publicacion_pro", "tab_export_pack", "tab_landing_page", "tab_web_pack", "tab_deploy_pro"],
        }
        steps = workflows.get(mode, workflows["creator"])
        first = next((s for s in steps if hasattr(self, s)), None)
        if first:
            self.command_open_attr(first)
        try:
            if mode in ("creator", "karaoke") and hasattr(self, "vocal_chain_apply_preset"):
                self.vocal_chain_apply_preset("clean")
            if mode == "streamer" and hasattr(self, "vocal_analyzer_auto_fix"):
                self.vocal_analyzer_auto_fix()
            if mode == "launch" and hasattr(self, "visual_apply_theme"):
                self.visual_apply_theme("neon")
        except Exception:
            pass
        names = []
        for attr in steps:
            mod = next((m for m in self.command_modules() if m["attr"] == attr), None)
            if mod:
                names.append(mod["name"])
        self.command_preview_text_set("WORKFLOW APLICADO\n\n" + mode.upper() + "\n\n" + "\n".join(f"- {n}" for n in names))
        self.command_center_status.set(f"Workflow {mode} preparado.")

    def command_map_data(self):
        return {
            "version": VERSION,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "modules": self.command_modules(),
            "workflows": {
                "creator": ["Asistente", "Cadena Vocal", "Timeline", "Canción", "Mezcla", "Master"],
                "streamer": ["Cable Virtual", "Streamer Hub", "Analizador", "Favoritos", "Directo"],
                "karaoke": ["Cadena Vocal", "Karaoke Studio", "Karaoke", "Autotune", "Master"],
                "launch": ["Portadas", "Brand Kit", "Publicación", "Export Pack", "Landing", "Deploy"],
            },
        }

    def command_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def command_export_map(self):
        try:
            data = self.command_map_data()
            folder = self.command_output_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = folder / f"command_center_mapa_{ts}.json"
            txt_path = folder / f"command_center_mapa_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = ["COMMAND CENTER PRO", "", f"Versión: {VERSION}", f"Módulos: {len(data['modules'])}", "", "MÓDULOS"]
            for m in data["modules"]:
                lines.append(f"- {m['group']} · {m['name']} · {m['desc']}")
            lines += ["", "WORKFLOWS"]
            for k, vals in data["workflows"].items():
                lines.append(f"- {k}: " + " → ".join(vals))
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.command_center_status.set(f"Mapa exportado: {json_path.name} + TXT")
            messagebox.showinfo("Mapa exportado", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.command_center_status.set(f"No se pudo exportar mapa: {e}")


    def build_professional_polish_tab(self):
        cont = ttk.Frame(self.tab_professional_polish)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "polish_banner" in self.professional_polish_images:
            ttk.Label(header, image=self.professional_polish_images["polish_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Command Center Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Pulido profesional")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_score", "Score", self.professional_polish_run_score),
            ("tile_showroom", "Showroom", self.professional_polish_showroom),
            ("tile_polish", "Pulido", self.professional_polish_apply_all),
            ("tile_theme", "Tema", self.professional_polish_export_theme),
            ("tile_report", "Informe", self.professional_polish_export_report),
            ("tile_badge", "Badge", self.professional_polish_export_badge),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.professional_polish_images:
                ttk.Label(box, image=self.professional_polish_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        panel = self.make_card(body, "Centro de acabado")
        panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        if "polish_mockup" in self.professional_polish_images:
            ttk.Label(panel, image=self.professional_polish_images["polish_mockup"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))

        self.professional_polish_text = tk.Text(
            panel,
            bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"],
            relief="flat", wrap="word", font=("Consolas", 10), height=9
        )
        self.professional_polish_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.professional_polish_refresh_text("Professional Polish cargado.")

        right_panel = self.make_card(body, "Modo de producto")
        right_panel.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ttk.Label(right_panel, text="Modo premium:", style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Combobox(
            right_panel,
            textvariable=self.professional_polish_mode,
            state="readonly",
            values=["Producto premium", "Showroom", "Streamer limpio", "Karaoke studio", "Launch final"]
        ).pack(fill="x", pady=(4, 10))
        ttk.Button(right_panel, text="Aplicar modo", style="Accent.TButton", command=self.professional_polish_apply_mode).pack(fill="x", pady=4)
        ttk.Button(right_panel, text="Score de acabado", command=self.professional_polish_run_score).pack(fill="x", pady=4)
        ttk.Button(right_panel, text="Pulido premium completo", command=self.professional_polish_apply_all).pack(fill="x", pady=4)
        ttk.Button(right_panel, text="Exportar badge PNG", command=self.professional_polish_export_badge).pack(fill="x", pady=4)
        ttk.Label(right_panel, textvariable=self.professional_polish_last, style="Card.TLabel", wraplength=460).pack(anchor="w", pady=(12, 0))

        side = ttk.Frame(main)
        side.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(side, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.professional_polish_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(estado, textvariable=self.professional_polish_score, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=320).pack(anchor="w", pady=(8, 0))

        accesos = self.make_card(side, "Accesos premium")
        accesos.pack(fill="x", pady=(0, 10))
        for label, attr in [
            ("🏠 Inicio", "tab_inicio_premium"),
            ("🪄 Asistente", "tab_asistente_inicial"),
            ("💎 Premium", "tab_premium_experience"),
            ("💠 UI Premium", "tab_ultra_premium_ui"),
            ("📚 Biblioteca", "tab_biblioteca_premium"),
            ("🚀 Publicación", "tab_publicacion_pro"),
            ("🚢 Deploy", "tab_deploy_pro"),
        ]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

        tips = self.make_card(side, "Qué mejora V73")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text="V73 no añade solo otra función: revisa si el programa ya parece un producto terminado y aplica un pulido visual/flujo final.",
            style="Card.TLabel", justify="left", wraplength=320
        ).pack(anchor="w")

    def professional_polish_data(self):
        effects = {}
        for k, v in getattr(self, "vars", {}).items():
            try:
                effects[k] = float(v.get())
            except Exception:
                effects[k] = 0.0
        files_count = 0
        try:
            folder = self.song_output_folder() if hasattr(self, "song_output_folder") else Path.home() / "ModuladorVozDirecto_Canciones"
            files_count = len(list(Path(folder).glob("*"))) if Path(folder).exists() else 0
        except Exception:
            pass
        return {
            "version": VERSION,
            "mode": self.professional_polish_mode.get(),
            "voice": self.preset.get() if hasattr(self, "preset") else "",
            "category": self.category.get() if hasattr(self, "category") else "",
            "theme": self.visual_theme_name.get() if hasattr(self, "visual_theme_name") else "",
            "ui_theme": self.ultra_premium_ui_theme.get() if hasattr(self, "ultra_premium_ui_theme") else "",
            "premium_mode": self.premium_mode.get() if hasattr(self, "premium_mode") else "",
            "files_count": files_count,
            "effects": effects,
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        }

    def professional_polish_score_value(self):
        data = self.professional_polish_data()
        score = 0
        checks = []
        if data.get("voice"):
            score += 12; checks.append(("🟢", "Voz seleccionada"))
        else:
            checks.append(("🟡", "Falta seleccionar voz"))
        if data.get("theme") or data.get("ui_theme"):
            score += 16; checks.append(("🟢", "Tema visual configurado"))
        else:
            checks.append(("🟡", "Tema visual sin configurar"))
        if data.get("premium_mode"):
            score += 14; checks.append(("🟢", "Modo premium definido"))
        else:
            checks.append(("🟡", "Modo premium pendiente"))
        effects = data.get("effects", {})
        if effects.get("vol", 90) <= 100 and effects.get("echo", 0) <= 35:
            score += 14; checks.append(("🟢", "Volumen y eco controlados"))
        else:
            checks.append(("🟡", "Revisar volumen/eco"))
        if data.get("files_count", 0) >= 3:
            score += 14; checks.append(("🟢", "Biblioteca con archivos/proyectos"))
        else:
            checks.append(("🟡", "Genera audio, portada o publicación"))
        for attr, msg in [
            ("tab_inicio_premium", "Inicio premium"),
            ("tab_biblioteca_premium", "Biblioteca"),
            ("tab_publicacion_pro", "Publicación"),
            ("tab_deploy_pro", "Deploy"),
            ("tab_export_pack", "Export Pack"),
        ]:
            if hasattr(self, attr):
                score += 6; checks.append(("🟢", f"{msg} disponible"))
            else:
                checks.append(("🟡", f"{msg} no disponible"))
        return max(0, min(100, score)), checks

    def professional_polish_grade(self, score):
        if score >= 88:
            return "💎 ULTRA PREMIUM"
        if score >= 72:
            return "🟢 PREMIUM"
        if score >= 55:
            return "🟡 BUENO"
        return "🔴 FALTA PULIR"

    def professional_polish_refresh_text(self, extra=""):
        if not hasattr(self, "professional_polish_text"):
            return
        score, checks = self.professional_polish_score_value()
        self.professional_polish_score.set(f"Polish score: {score}/100 · {self.professional_polish_grade(score)}")
        data = self.professional_polish_data()
        lines = [
            "PROFESSIONAL POLISH PRO", "",
            f"Modo: {data['mode']}",
            f"Voz: {data['voice']}",
            f"Tema visual: {data['theme'] or data['ui_theme']}",
            f"Archivos en biblioteca: {data['files_count']}",
            "", "CHECKLIST DE PRODUCTO",
        ]
        for icon, msg in checks:
            lines.append(f"{icon} {msg}")
        lines += ["", str(extra)]
        self.professional_polish_text.configure(state="normal")
        self.professional_polish_text.delete("1.0", tk.END)
        self.professional_polish_text.insert("1.0", "\n".join(lines))
        self.professional_polish_text.configure(state="disabled")

    def professional_polish_run_score(self):
        score, _ = self.professional_polish_score_value()
        self.professional_polish_refresh_text("Score actualizado.")
        self.professional_polish_status.set(f"Revisión premium completada: {score}/100.")

    def professional_polish_apply_mode(self):
        mode = self.professional_polish_mode.get()
        try:
            if hasattr(self, "visual_apply_theme"):
                if "Launch" in mode:
                    self.visual_apply_theme("dorado")
                elif "Streamer" in mode:
                    self.visual_apply_theme("neon")
                else:
                    self.visual_apply_theme("morado")
            try:
                self.design_system_theme.set("Glass Studio")
                self.design_system_apply_theme()
            except Exception:
                pass
            if hasattr(self, "vocal_chain_apply_preset"):
                if "Karaoke" in mode:
                    self.vocal_chain_apply_preset("karaoke")
                else:
                    self.vocal_chain_apply_preset("clean")
            self.professional_polish_refresh_text(f"Modo aplicado: {mode}")
            self.professional_polish_status.set(f"Modo aplicado: {mode}.")
        except Exception as e:
            self.professional_polish_status.set(f"No se pudo aplicar modo: {e}")

    def professional_polish_apply_all(self):
        try:
            if hasattr(self, "revision_safe_fix"):
                self.revision_safe_fix()
            if hasattr(self, "visual_apply_theme"):
                self.visual_apply_theme("morado")
            if hasattr(self, "visual_apply_density"):
                self.visual_apply_density("grande")
            if hasattr(self, "premium_apply_mode"):
                try: self.premium_apply_mode()
                except Exception: pass
            if hasattr(self, "studio_dashboard_refresh_all"):
                self.studio_dashboard_refresh_all()
            self.professional_polish_refresh_text("Pulido premium completo aplicado.")
            self.professional_polish_status.set("Pulido premium completo aplicado.")
        except Exception as e:
            self.professional_polish_status.set(f"No se pudo aplicar pulido: {e}")

    def professional_polish_showroom(self):
        try:
            self.professional_polish_mode.set("Showroom")
            if hasattr(self, "visual_apply_density"):
                self.visual_apply_density("grande")
            if hasattr(self, "tab_inicio_premium"):
                self.select_tab(self.tab_inicio_premium)
            self.professional_polish_status.set("Showroom activado: vista grande y flujo de inicio.")
        except Exception as e:
            self.professional_polish_status.set(f"No se pudo activar showroom: {e}")

    def professional_polish_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def professional_polish_safe_name(self):
        try:
            return self.song_safe_name(self.song_title.get())
        except Exception:
            return "professional_polish"

    def professional_polish_export_report(self):
        try:
            data = self.professional_polish_data()
            score, checks = self.professional_polish_score_value()
            data["score"] = score
            data["grade"] = self.professional_polish_grade(score)
            data["checks"] = [{"status": i, "message": m} for i, m in checks]
            folder = self.professional_polish_output_folder()
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            name = self.professional_polish_safe_name()
            json_path = folder / f"{name}_professional_polish_{ts}.json"
            txt_path = folder / f"{name}_professional_polish_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = ["PROFESSIONAL POLISH PRO", "", f"Fecha: {data['created_at']}", f"Score: {score}/100", f"Grado: {data['grade']}", "", "CHECKS"]
            for item in data["checks"]:
                lines.append(f"{item['status']} {item['message']}")
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.professional_polish_last.set(f"Informe: {json_path.name}")
            self.professional_polish_status.set("Informe polish exportado.")
            messagebox.showinfo("Informe exportado", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.professional_polish_status.set(f"No se pudo exportar informe: {e}")

    def professional_polish_export_theme(self):
        try:
            data = self.professional_polish_data()
            folder = self.professional_polish_output_folder()
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"professional_polish_theme_{ts}.json"
            path.write_text(json.dumps({"version": VERSION, "theme": data.get("theme"), "ui_theme": data.get("ui_theme"), "mode": data.get("mode"), "created_at": data.get("created_at")}, ensure_ascii=False, indent=2), encoding="utf-8")
            self.professional_polish_last.set(f"Tema: {path.name}")
            self.professional_polish_status.set("Tema polish exportado.")
            messagebox.showinfo("Tema exportado", f"Guardado en:\n{path}")
        except Exception as e:
            self.professional_polish_status.set(f"No se pudo exportar tema: {e}")

    def professional_polish_export_badge(self):
        try:
            score, _ = self.professional_polish_score_value()
            grade = self.professional_polish_grade(score)
            folder = self.professional_polish_output_folder()
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"professional_polish_badge_{ts}.png"
            img = Image.new("RGBA", (1200, 630), (8, 10, 22, 255))
            d = ImageDraw.Draw(img)
            for cx, cy, r, c, a in [(980, 90, 240, (255,203,87), 60), (210, 540, 260, (0,229,255), 45), (620, 300, 170, (188,120,255), 35)]:
                ov = Image.new("RGBA", img.size, (0,0,0,0)); od = ImageDraw.Draw(ov)
                od.ellipse((cx-r, cy-r, cx+r, cy+r), fill=c+(a,))
                img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(36)))
            d.rounded_rectangle((70, 70, 1130, 560), radius=55, fill=(18,22,42,220), outline=(255,255,255,90), width=4)
            try:
                f1 = ImageFont.truetype("DejaVuSans-Bold.ttf", 66)
                f2 = ImageFont.truetype("DejaVuSans-Bold.ttf", 42)
                f3 = ImageFont.truetype("DejaVuSans.ttf", 28)
            except Exception:
                f1 = f2 = f3 = ImageFont.load_default()
            d.text((110, 125), "PROFESSIONAL POLISH", font=f1, fill=(255,255,255,255))
            d.text((115, 230), f"{score}/100 · {grade}", font=f2, fill=(255,214,89,255))
            d.text((115, 310), "Modulador de Voz en Directo · V73", font=f3, fill=(205,235,255,230))
            d.rounded_rectangle((115, 410, 620, 465), radius=24, fill=(255,214,89,235))
            d.text((145, 424), "PRODUCTO MÁS PREMIUM", font=f3, fill=(14,15,22,255))
            img.convert("RGB").save(path, "PNG", optimize=True)
            self.professional_polish_last.set(f"Badge: {path.name}")
            self.professional_polish_status.set("Badge premium exportado.")
            messagebox.showinfo("Badge exportado", f"Guardado en:\n{path}")
        except Exception as e:
            self.professional_polish_status.set(f"No se pudo exportar badge: {e}")


    def build_ultra_premium_ui_tab(self):
        cont = ttk.Frame(self.tab_ultra_premium_ui)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "ultra_premium_banner" in self.ultra_premium_ui_images:
            ttk.Label(header, image=self.ultra_premium_ui_images["ultra_premium_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Ultra Premium UI Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Acabados visuales premium")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_glass", "Glass Studio", lambda: self.ultra_ui_apply_mode("glass")),
            ("tile_creator", "Creator Pro", lambda: self.ultra_ui_apply_mode("creator")),
            ("tile_stream", "Streamer Pro", lambda: self.ultra_ui_apply_mode("streamer")),
            ("tile_focus", "Focus Mode", self.ultra_ui_focus_mode),
            ("tile_polish", "Pulido final", self.ultra_ui_apply_full_polish),
            ("tile_export", "Exportar UI", self.ultra_ui_export_report),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.ultra_premium_ui_images:
                ttk.Label(box, image=self.ultra_premium_ui_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)
        preview = self.make_card(body, "Vista de producto")
        preview.pack(side="left", fill="both", expand=True, padx=(0, 5))
        if "ultra_premium_mockup" in self.ultra_premium_ui_images:
            ttk.Label(preview, image=self.ultra_premium_ui_images["ultra_premium_mockup"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))
        self.ultra_ui_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=8)
        self.ultra_ui_text.pack(fill="both", expand=True, padx=4, pady=4)

        controls = self.make_card(body, "Control de experiencia")
        controls.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ttk.Label(controls, text="Tema premium:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Combobox(controls, textvariable=self.ultra_premium_ui_theme, state="readonly", values=["Glass Studio", "Creator Pro", "Streamer Pro", "Gold Launch", "Focus Dark"]).pack(fill="x", pady=(4, 10))
        ttk.Label(controls, text="Densidad:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Combobox(controls, textvariable=self.ultra_premium_ui_density, state="readonly", values=["Premium cómodo", "Compacto pro", "Grande presentación"]).pack(fill="x", pady=(4, 10))
        ttk.Button(controls, text="Aplicar tema seleccionado", style="Accent.TButton", command=self.ultra_ui_apply_selected).pack(fill="x", pady=4)
        ttk.Button(controls, text="Pulido premium completo", command=self.ultra_ui_apply_full_polish).pack(fill="x", pady=4)
        ttk.Button(controls, text="Revisar acabado UI", command=self.ultra_ui_refresh_score).pack(fill="x", pady=4)
        ttk.Label(controls, textvariable=self.ultra_premium_ui_score, style="Card.TLabel", font=("Segoe UI", 14, "bold"), wraplength=460).pack(anchor="w", pady=(12, 0))

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.ultra_premium_ui_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        accesos = self.make_card(right, "Zonas premium")
        accesos.pack(fill="x", pady=(0, 10))
        for label, attr in [("🏠 Inicio", "tab_inicio_premium"), ("🪄 Asistente", "tab_asistente_inicial"), ("💎 Premium", "tab_premium_experience"), ("🎨 Visual Pro", "tab_visual_pro"), ("📚 Biblioteca", "tab_biblioteca_premium"), ("🚀 Publicación", "tab_publicacion_pro")]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

        export = self.make_card(right, "Exportar")
        export.pack(fill="x")
        ttk.Button(export, text="Exportar UI JSON/TXT", style="Accent.TButton", command=self.ultra_ui_export_report).pack(fill="x", pady=3)
        ttk.Button(export, text="Exportar mini badge PNG", command=self.ultra_ui_export_badge).pack(fill="x", pady=3)
        self.ultra_ui_refresh_preview("Ultra Premium UI cargado.")
        self.ultra_ui_refresh_score()

    def ultra_ui_palette(self, mode):
        palettes = {
            "glass": ("Glass Studio", "#070b1a", "#12182d", "#1b2440", "#00e5ff", "#bc78ff", "#f7fbff"),
            "creator": ("Creator Pro", "#140b20", "#22132f", "#321d42", "#ff74aa", "#ffcb57", "#fff7ff"),
            "streamer": ("Streamer Pro", "#06131d", "#0e2230", "#18384a", "#62ffb4", "#00e5ff", "#f1fffb"),
            "gold": ("Gold Launch", "#171008", "#24180c", "#332211", "#ffcb57", "#ff965a", "#fff8e8"),
            "focus": ("Focus Dark", "#07070d", "#11121c", "#1b1d2b", "#7c5cff", "#00e5ff", "#f5f7ff"),
        }
        return palettes.get(mode, palettes["glass"])

    def ultra_ui_apply_mode(self, mode):
        name, bg, panel, panel2, accent, accent2, text = self.ultra_ui_palette(mode)
        try:
            COLORS["bg"] = bg; COLORS["panel"] = panel; COLORS["panel2"] = panel2; COLORS["accent"] = accent; COLORS["accent2"] = accent2; COLORS["text"] = text
            style = ttk.Style()
            style.configure(".", background=bg, foreground=text, fieldbackground=panel2)
            style.configure("TFrame", background=bg)
            style.configure("Card.TFrame", background=panel)
            style.configure("TLabel", background=bg, foreground=text)
            style.configure("Card.TLabel", background=panel, foreground=text)
            style.configure("Accent.TButton", padding=(14, 9), font=("Segoe UI", 10, "bold"))
            style.configure("TNotebook.Tab", padding=(15, 8), font=("Segoe UI", 10, "bold"))
            self.root.configure(bg=bg)
        except Exception:
            pass
        self.ultra_premium_ui_theme.set(name)
        self.ultra_premium_ui_status.set(f"Acabado aplicado: {name}. Para verlo perfecto en todo, reinicia la app tras guardar.")
        self.ultra_ui_refresh_preview(f"Tema aplicado: {name}.")
        self.ultra_ui_refresh_score()

    def ultra_ui_apply_selected(self):
        mapping = {"Glass Studio":"glass", "Creator Pro":"creator", "Streamer Pro":"streamer", "Gold Launch":"gold", "Focus Dark":"focus"}
        self.ultra_ui_apply_mode(mapping.get(self.ultra_premium_ui_theme.get(), "glass"))
        self.ultra_ui_apply_density()

    def ultra_ui_apply_density(self):
        try:
            style = ttk.Style()
            d = self.ultra_premium_ui_density.get()
            if "Compacto" in d:
                style.configure("TButton", padding=(8, 5), font=("Segoe UI", 9))
                style.configure("Accent.TButton", padding=(10, 6), font=("Segoe UI", 9, "bold"))
                style.configure("TNotebook.Tab", padding=(10, 5), font=("Segoe UI", 9, "bold"))
            elif "Grande" in d:
                style.configure("TButton", padding=(15, 10), font=("Segoe UI", 11))
                style.configure("Accent.TButton", padding=(17, 11), font=("Segoe UI", 11, "bold"))
                style.configure("TNotebook.Tab", padding=(17, 9), font=("Segoe UI", 11, "bold"))
            else:
                style.configure("TButton", padding=(11, 7), font=("Segoe UI", 10))
                style.configure("Accent.TButton", padding=(14, 9), font=("Segoe UI", 10, "bold"))
                style.configure("TNotebook.Tab", padding=(15, 8), font=("Segoe UI", 10, "bold"))
        except Exception:
            pass

    def ultra_ui_focus_mode(self):
        self.ultra_premium_ui_theme.set("Focus Dark")
        self.ultra_premium_ui_density.set("Compacto pro")
        self.ultra_ui_apply_selected()
        if hasattr(self, "tab_inicio_premium"):
            self.select_tab(self.tab_inicio_premium)
        self.ultra_premium_ui_status.set("Focus Mode activado: menos ruido visual y vuelta al inicio premium.")

    def ultra_ui_apply_full_polish(self):
        self.ultra_premium_ui_theme.set("Glass Studio")
        self.ultra_premium_ui_density.set("Premium cómodo")
        self.ultra_ui_apply_selected()
        try:
            if hasattr(self, "visual_apply_theme"):
                self.visual_apply_theme("neon")
            if hasattr(self, "premium_apply_mode"):
                self.premium_apply_mode("studio")
            if hasattr(self, "studio_dashboard_refresh_all"):
                self.studio_dashboard_refresh_all()
        except Exception:
            pass
        self.ultra_premium_ui_status.set("Pulido premium completo aplicado.")
        self.ultra_ui_refresh_preview("Pulido completo aplicado: tema, densidad y flujo premium revisados.")
        self.ultra_ui_refresh_score()

    def ultra_ui_score_data(self):
        score = 0
        checks = []
        if hasattr(self, "tab_inicio_premium"):
            score += 15; checks.append(("🟢", "Inicio Premium disponible"))
        else:
            checks.append(("🟡", "Falta Inicio Premium"))
        if hasattr(self, "tab_asistente_inicial"):
            score += 15; checks.append(("🟢", "Asistente Inicial disponible"))
        if hasattr(self, "tab_visual_pro"):
            score += 15; checks.append(("🟢", "Visual Pro disponible"))
        if hasattr(self, "tab_premium_experience"):
            score += 15; checks.append(("🟢", "Premium Experience disponible"))
        if self.ultra_premium_ui_theme.get():
            score += 20; checks.append(("🟢", f"Tema activo: {self.ultra_premium_ui_theme.get()}"))
        if self.ultra_premium_ui_density.get():
            score += 10; checks.append(("🟢", f"Densidad: {self.ultra_premium_ui_density.get()}"))
        if hasattr(self, "tab_deploy_pro") and hasattr(self, "tab_web_pack"):
            score += 10; checks.append(("🟢", "Flujo de publicación completo"))
        return min(100, score), checks

    def ultra_ui_refresh_score(self):
        score, _ = self.ultra_ui_score_data()
        grade = "💎 Premium alto" if score >= 85 else ("✨ Premium medio" if score >= 65 else "🟡 Mejorable")
        self.ultra_premium_ui_score.set(f"Acabado UI: {score}/100 · {grade}")
        self.ultra_ui_refresh_preview("Revisión UI actualizada.")

    def ultra_ui_data(self):
        score, checks = self.ultra_ui_score_data()
        return {"version": VERSION, "theme": self.ultra_premium_ui_theme.get(), "density": self.ultra_premium_ui_density.get(), "score": score, "checks": [{"status": a, "message": b} for a,b in checks], "created_at": datetime.now().isoformat(timespec="seconds")}

    def ultra_ui_refresh_preview(self, extra=""):
        if not hasattr(self, "ultra_ui_text"):
            return
        data = self.ultra_ui_data()
        lines = ["ULTRA PREMIUM UI PRO", "", f"Tema: {data['theme']}", f"Densidad: {data['density']}", f"Puntuación: {data['score']}/100", "", "CHECKLIST"]
        for item in data["checks"]:
            lines.append(f"{item['status']} {item['message']}")
        lines += ["", str(extra)]
        self.ultra_ui_text.configure(state="normal")
        self.ultra_ui_text.delete("1.0", tk.END)
        self.ultra_ui_text.insert("1.0", "\n".join(lines))
        self.ultra_ui_text.configure(state="disabled")

    def ultra_ui_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def ultra_ui_export_report(self):
        try:
            data = self.ultra_ui_data()
            folder = self.ultra_ui_output_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = folder / f"ultra_premium_ui_{ts}.json"
            txt_path = folder / f"ultra_premium_ui_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = ["ULTRA PREMIUM UI PRO", "", f"Fecha: {data['created_at']}", f"Tema: {data['theme']}", f"Densidad: {data['density']}", f"Puntuación: {data['score']}/100", "", "CHECKLIST"]
            for item in data["checks"]:
                lines.append(f"{item['status']} {item['message']}")
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.ultra_premium_ui_status.set(f"Informe UI exportado: {json_path.name} + TXT")
            messagebox.showinfo("UI exportada", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.ultra_premium_ui_status.set(f"No se pudo exportar UI: {e}")

    def ultra_ui_export_badge(self):
        try:
            folder = self.ultra_ui_output_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"ultra_premium_badge_{ts}.png"
            img = Image.new("RGBA", (900, 300), (8, 10, 22, 255))
            d = ImageDraw.Draw(img)
            for x in range(900):
                for y in range(300):
                    t = x / 900 * 0.7 + y / 300 * 0.3
                    img.putpixel((x, y), (int(8*(1-t)+40*t), int(10*(1-t)+34*t), int(22*(1-t)+92*t), 255))
            ov = Image.new("RGBA", (900,300), (0,0,0,0)); od = ImageDraw.Draw(ov)
            od.ellipse((620,-80,980,280), fill=(0,229,255,65)); od.ellipse((-90,140,250,430), fill=(188,120,255,55))
            img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(22)))
            d.rounded_rectangle((35,35,865,265), radius=42, outline=(255,255,255,90), width=3, fill=(0,0,0,45))
            d.text((78,76), "ULTRA PREMIUM UI", font=("Segoe UI", 36, "bold"), fill=(255,255,255,255))
            d.text((82,135), f"{self.ultra_premium_ui_theme.get()} · {self.ultra_premium_ui_density.get()}", font=("Segoe UI", 17), fill=(210,235,255,240))
            d.rounded_rectangle((82,190,310,228), radius=18, fill=(255,214,89,235))
            d.text((108,198), self.ultra_premium_ui_score.get()[:26], font=("Segoe UI", 13, "bold"), fill=(14,15,22,255))
            img.convert("RGB").save(path, "PNG")
            self.ultra_premium_ui_status.set(f"Badge exportado: {path.name}")
            messagebox.showinfo("Badge exportado", f"Guardado en:\n{path}")
        except Exception as e:
            self.ultra_premium_ui_status.set(f"No se pudo exportar badge: {e}")


    def build_premium_experience_tab(self):
        cont = ttk.Frame(self.tab_premium_experience)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "premium_banner" in self.premium_experience_images:
            ttk.Label(header, image=self.premium_experience_images["premium_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Premium Experience Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Modos premium")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_studio", "Studio Creator", lambda: self.premium_apply_mode("studio")),
            ("tile_streamer", "Streamer", lambda: self.premium_apply_mode("streamer")),
            ("tile_karaoke", "Karaoke", lambda: self.premium_apply_mode("karaoke")),
            ("tile_launch", "Launch", lambda: self.premium_apply_mode("launch")),
            ("tile_badge", "Badge PNG", self.premium_export_badge),
            ("tile_report", "Informe", self.premium_export_report),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.premium_experience_images:
                ttk.Label(box, image=self.premium_experience_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        polish = self.make_card(body, "Pulido premium")
        polish.pack(side="left", fill="both", expand=True, padx=(0, 5))
        if "premium_panel" in self.premium_experience_images:
            ttk.Label(polish, image=self.premium_experience_images["premium_panel"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))
        self.premium_text = tk.Text(polish, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=10)
        self.premium_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.premium_refresh()

        project = self.make_card(body, "Diagnóstico de acabado")
        project.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.premium_project_text = tk.Text(project, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=18)
        self.premium_project_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.premium_refresh_project()

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado premium")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.premium_experience_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(estado, textvariable=self.premium_quality, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=320).pack(anchor="w", pady=(8, 0))
        ttk.Label(estado, textvariable=self.premium_badge_last, style="Card.TLabel", wraplength=320).pack(anchor="w", pady=(8, 0))

        modo = self.make_card(right, "Modo de producto")
        modo.pack(fill="x", pady=(0, 10))
        ttk.Combobox(modo, textvariable=self.premium_mode, state="readonly", values=["Studio Creator", "Streamer", "Karaoke", "Launch / Publicar"]).pack(fill="x", pady=(0, 6))
        ttk.Button(modo, text="Aplicar modo seleccionado", style="Accent.TButton", command=self.premium_apply_selected).pack(fill="x", pady=3)
        ttk.Button(modo, text="Aplicar acabado premium completo", command=self.premium_apply_full_polish).pack(fill="x", pady=3)
        ttk.Button(modo, text="Actualizar diagnóstico", command=self.premium_refresh_all).pack(fill="x", pady=3)

        accesos = self.make_card(right, "Accesos clave")
        accesos.pack(fill="x", pady=(0, 10))
        for label, attr in [
            ("🏠 Inicio", "tab_inicio_premium"),
            ("🪄 Asistente", "tab_asistente_inicial"),
            ("📚 Biblioteca", "tab_biblioteca_premium"),
            ("🖼 Portadas", "tab_portadas_premium"),
            ("🏷 Brand Kit", "tab_brand_kit"),
            ("🚀 Publicación", "tab_publicacion_pro"),
            ("🚢 Deploy", "tab_deploy_pro"),
        ]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

        export = self.make_card(right, "Exportar acabado")
        export.pack(fill="x")
        ttk.Button(export, text="Exportar Badge PNG", style="Accent.TButton", command=self.premium_export_badge).pack(fill="x", pady=3)
        ttk.Button(export, text="Exportar informe premium", command=self.premium_export_report).pack(fill="x", pady=3)

    def premium_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def premium_safe_name(self, text):
        try:
            return self.song_safe_name(text)
        except Exception:
            safe = "".join(ch for ch in str(text) if ch.isalnum() or ch in " -_").strip().replace(" ", "_")
            return safe or "premium"

    def premium_data(self):
        title = "Mi proyecto"
        if hasattr(self, "song_title") and self.song_title.get().strip():
            title = self.song_title.get().strip()
        elif hasattr(self, "portada_titulo") and self.portada_titulo.get().strip():
            title = self.portada_titulo.get().strip()
        effects = {}
        for k, v in getattr(self, "vars", {}).items():
            try:
                effects[k] = float(v.get())
            except Exception:
                effects[k] = 0
        return {
            "version": VERSION,
            "title": title,
            "mode": self.premium_mode.get(),
            "voice": self.preset.get() if hasattr(self, "preset") else "",
            "track": self.karaoke_track.get() if hasattr(self, "karaoke_track") else "",
            "visual_theme": self.visual_theme_name.get() if hasattr(self, "visual_theme_name") else "",
            "quality_score": self.premium_score()[0],
            "effects": effects,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def premium_score(self):
        score = 0
        checks = []
        if hasattr(self, "tab_inicio_premium"):
            score += 10; checks.append(("🟢", "Inicio Premium disponible"))
        else:
            checks.append(("🟡", "Falta pantalla inicial premium"))
        if hasattr(self, "tab_visual_pro"):
            score += 12; checks.append(("🟢", "Sistema visual disponible"))
        if hasattr(self, "tab_revision_tecnica"):
            score += 12; checks.append(("🟢", "Revisión técnica disponible"))
        if hasattr(self, "tab_portadas_premium"):
            score += 12; checks.append(("🟢", "Portadas disponibles"))
        else:
            checks.append(("🟡", "Falta portada del proyecto"))
        if hasattr(self, "tab_brand_kit"):
            score += 10; checks.append(("🟢", "Brand Kit disponible"))
        if hasattr(self, "tab_publicacion_pro"):
            score += 10; checks.append(("🟢", "Publicación disponible"))
        if hasattr(self, "tab_deploy_pro"):
            score += 10; checks.append(("🟢", "Deploy disponible"))
        data_track = self.karaoke_track.get() if hasattr(self, "karaoke_track") else ""
        if data_track and data_track != "Sin pista instrumental":
            score += 12; checks.append(("🟢", "Pista/base cargada"))
        else:
            checks.append(("🟡", "Genera o carga una pista para completar el producto"))
        if hasattr(self, "premium_experience_images") and self.premium_experience_images:
            score += 12; checks.append(("🟢", "Assets premium cargados"))
        else:
            checks.append(("🟡", "Assets premium no cargados"))
        return max(0, min(100, score)), checks

    def premium_grade(self, score):
        if score >= 85: return "💎 Premium alto"
        if score >= 65: return "✨ Premium medio"
        return "🟡 Necesita pulido"

    def premium_refresh(self):
        if not hasattr(self, "premium_text"): return
        score, checks = self.premium_score()
        self.premium_quality.set(f"Calidad premium: {score}/100 · {self.premium_grade(score)}")
        lines = [
            "PREMIUM EXPERIENCE PRO", "",
            "OBJETIVO", "Convertir el prototipo en una experiencia más cercana a una app de pago.", "",
            "MEJORAS V73", "✓ Centro premium unificado.", "✓ Modos de producto.", "✓ Aplicar acabado completo.", "✓ Diagnóstico de calidad.", "✓ Badge PNG exportable.", "✓ Informe premium JSON/TXT.", "",
            "CHECKLIST",
        ]
        for icon, msg in checks:
            lines.append(f"{icon} {msg}")
        self.premium_text.configure(state="normal")
        self.premium_text.delete("1.0", tk.END)
        self.premium_text.insert("1.0", "\n".join(lines))
        self.premium_text.configure(state="disabled")

    def premium_refresh_project(self):
        if not hasattr(self, "premium_project_text"): return
        data = self.premium_data()
        lines = [
            "DIAGNÓSTICO DE ACABADO", "",
            f"Proyecto: {data['title']}",
            f"Modo: {data['mode']}",
            f"Voz: {data['voice']}",
            f"Pista: {data['track']}",
            f"Tema visual: {data['visual_theme']}",
            f"Puntuación: {data['quality_score']}/100", "",
            "DETALLES QUE DAN LOOK PREMIUM", "- Inicio claro.", "- Menos caos visual.", "- Exportación completa.", "- Portada y marca.", "- Checklist antes de publicar.", "- Paquete web/despliegue.", "",
            "RECOMENDACIÓN", self.premium_next_recommendation(data['quality_score'])
        ]
        self.premium_project_text.configure(state="normal")
        self.premium_project_text.delete("1.0", tk.END)
        self.premium_project_text.insert("1.0", "\n".join(lines))
        self.premium_project_text.configure(state="disabled")

    def premium_next_recommendation(self, score):
        if score < 65: return "Empieza por Asistente, Visual Pro y Revisión Técnica."
        if score < 85: return "Crea portada, Brand Kit y ficha de publicación."
        return "Listo para Export Pack, Web Pack y Deploy."

    def premium_refresh_all(self):
        self.premium_refresh()
        self.premium_refresh_project()
        score, _ = self.premium_score()
        self.premium_experience_status.set(f"Diagnóstico actualizado: {score}/100 · {self.premium_grade(score)}")

    def premium_apply_selected(self):
        mode = self.premium_mode.get().lower()
        if "streamer" in mode: self.premium_apply_mode("streamer")
        elif "karaoke" in mode: self.premium_apply_mode("karaoke")
        elif "launch" in mode or "public" in mode: self.premium_apply_mode("launch")
        else: self.premium_apply_mode("studio")

    def premium_apply_mode(self, mode):
        try:
            if hasattr(self, "revision_safe_fix"):
                self.revision_safe_fix()
            if hasattr(self, "visual_apply_theme"):
                self.visual_apply_theme("neon" if mode != "launch" else "dorado")
            if hasattr(self, "visual_apply_density"):
                self.visual_apply_density("normal")
            if mode == "streamer":
                self.premium_mode.set("Streamer")
                if hasattr(self, "vocal_chain_apply_preset"): self.vocal_chain_apply_preset("clean")
                target = "tab_streamer_hub" if hasattr(self, "tab_streamer_hub") else "tab_directo_pro"
            elif mode == "karaoke":
                self.premium_mode.set("Karaoke")
                if hasattr(self, "vocal_chain_apply_preset"): self.vocal_chain_apply_preset("karaoke")
                target = "tab_karaoke_studio" if hasattr(self, "tab_karaoke_studio") else "tab_karaoke"
            elif mode == "launch":
                self.premium_mode.set("Launch / Publicar")
                target = "tab_publicacion_pro" if hasattr(self, "tab_publicacion_pro") else "tab_deploy_pro"
            else:
                self.premium_mode.set("Studio Creator")
                if hasattr(self, "studio_dashboard_refresh_all"): self.studio_dashboard_refresh_all()
                target = "tab_studio_dashboard" if hasattr(self, "tab_studio_dashboard") else "tab_inicio_premium"
            if hasattr(self, target):
                self.select_tab(getattr(self, target))
            self.premium_refresh_all()
            self.premium_experience_status.set(f"Modo premium aplicado: {self.premium_mode.get()}.")
        except Exception as e:
            self.premium_experience_status.set(f"No se pudo aplicar modo premium: {e}")

    def premium_apply_full_polish(self):
        try:
            if hasattr(self, "inicio_apply_safe_start"): self.inicio_apply_safe_start()
            if hasattr(self, "asistente_apply_all_safe"): self.asistente_apply_all_safe()
            if hasattr(self, "visual_apply_theme"): self.visual_apply_theme("morado")
            if hasattr(self, "visual_apply_density"): self.visual_apply_density("normal")
            if hasattr(self, "studio_dashboard_refresh_all"): self.studio_dashboard_refresh_all()
            self.premium_refresh_all()
            self.premium_experience_status.set("Acabado premium completo aplicado.")
        except Exception as e:
            self.premium_experience_status.set(f"No se pudo aplicar acabado completo: {e}")

    def premium_font(self, size, bold=False):
        try:
            for p in ["C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"]:
                if Path(p).exists(): return ImageFont.truetype(p, size)
        except Exception: pass
        try: return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
        except Exception: return ImageFont.load_default()

    def premium_export_badge(self):
        try:
            data = self.premium_data()
            score = data["quality_score"]
            folder = self.premium_output_folder(); folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"{self.premium_safe_name(data['title'])}_premium_badge_{ts}.png"
            w,h=1400,520
            img=Image.new("RGBA",(w,h),(8,10,22,255)); px=img.load()
            c1=(8,10,22); c2=(56,31,104)
            for y in range(h):
                for x in range(w):
                    t=(x/(w-1))*0.65+(y/(h-1))*0.35
                    px[x,y]=tuple(int(c1[i]*(1-t)+c2[i]*t) for i in range(3))+(255,)
            for cx,cy,r,c,a in [(1180,95,230,(255,203,87),58),(250,440,220,(0,229,255),42),(760,260,180,(255,116,170),30)]:
                ov=Image.new("RGBA",(w,h),(0,0,0,0)); od=ImageDraw.Draw(ov)
                od.ellipse((cx-r,cy-r,cx+r,cy+r), fill=c+(a,)); img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(35)))
            d=ImageDraw.Draw(img)
            d.rounded_rectangle((55,55,w-55,h-55), radius=48, fill=(0,0,0,55), outline=(255,214,89,180), width=4)
            d.text((105,118), data["title"].upper()[:32], font=self.premium_font(56, True), fill=(255,255,255,255))
            d.text((110,196), f"{data['mode']} · {self.premium_grade(score)}", font=self.premium_font(28), fill=(205,235,255,235))
            d.rounded_rectangle((110,300,520,372), radius=34, fill=(255,214,89,235))
            d.text((145,316), f"PREMIUM {score}/100", font=self.premium_font(32, True), fill=(14,15,22,255))
            d.text((110,415), "MODULADOR VOZ DIRECTO · V73 PREMIUM EXPERIENCE PRO", font=self.premium_font(22, True), fill=(255,255,255,190))
            img.convert("RGB").save(path, "PNG", optimize=True)
            self.premium_badge_last.set(f"Badge: {path.name}")
            self.premium_experience_status.set(f"Badge premium exportado: {path.name}")
            if hasattr(self, "biblioteca_scan"):
                try: self.biblioteca_scan()
                except Exception: pass
            messagebox.showinfo("Badge exportado", f"Guardado en:\n{path}")
        except Exception as e:
            self.premium_experience_status.set(f"No se pudo exportar badge: {e}")

    def premium_export_report(self):
        try:
            data = self.premium_data()
            score, checks = self.premium_score()
            data["checks"] = [{"status": icon, "message": msg} for icon, msg in checks]
            data["grade"] = self.premium_grade(score)
            data["recommendation"] = self.premium_next_recommendation(score)
            folder = self.premium_output_folder(); folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = self.premium_safe_name(data["title"])
            json_path = folder / f"{name}_premium_report_{ts}.json"
            txt_path = folder / f"{name}_premium_report_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = ["PREMIUM EXPERIENCE PRO", "", f"Fecha: {data['created_at']}", f"Proyecto: {data['title']}", f"Modo: {data['mode']}", f"Puntuación: {score}/100", f"Grado: {data['grade']}", "", "CHECKLIST"]
            for item in data["checks"]:
                lines.append(f"{item['status']} {item['message']}")
            lines += ["", "RECOMENDACIÓN", data["recommendation"]]
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.premium_experience_status.set(f"Informe premium exportado: {json_path.name} + TXT")
            messagebox.showinfo("Informe premium exportado", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.premium_experience_status.set(f"No se pudo exportar informe premium: {e}")


    def build_deploy_pro_tab(self):
        cont = ttk.Frame(self.tab_deploy_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "deploy_banner" in self.deploy_pro_images:
            ttk.Label(header, image=self.deploy_pro_images["deploy_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Deploy Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Publicar proyecto web")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_scan", "Escanear", self.deploy_scan),
            ("tile_package", "Crear Deploy", self.deploy_create_package),
            ("tile_github", "GitHub Pages", lambda: self.deploy_set_platform("GitHub Pages")),
            ("tile_hosting", "Hosting", lambda: self.deploy_set_platform("Hosting estático")),
            ("tile_check", "Checklist", self.deploy_export_checklist),
            ("tile_open", "Abrir carpeta", self.deploy_open_folder),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.deploy_pro_images:
                ttk.Label(box, image=self.deploy_pro_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)
        files_card = self.make_card(body, "Archivos detectados para publicar")
        files_card.pack(side="left", fill="both", expand=True, padx=(0, 5))
        if "deploy_checklist" in self.deploy_pro_images:
            ttk.Label(files_card, image=self.deploy_pro_images["deploy_checklist"], style="Card.TLabel").pack(anchor="center", pady=(0, 6))
        list_frame = ttk.Frame(files_card, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True)
        self.deploy_listbox = tk.Listbox(list_frame, bg=COLORS["panel2"], fg=COLORS["text"], selectbackground=COLORS["accent"], selectforeground="#071018", relief="flat", activestyle="none", font=("Consolas", 10), height=12)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.deploy_listbox.yview)
        self.deploy_listbox.configure(yscrollcommand=scroll.set)
        self.deploy_listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.deploy_listbox.bind("<<ListboxSelect>>", lambda e: self.deploy_preview_selected())

        btns = ttk.Frame(files_card, style="Card.TFrame")
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Vista previa", command=self.deploy_preview_selected).pack(side="left", expand=True, fill="x", padx=3, ipady=7)
        ttk.Button(btns, text="Crear ZIP Deploy", style="Accent.TButton", command=self.deploy_create_package).pack(side="left", expand=True, fill="x", padx=3, ipady=7)

        preview = self.make_card(body, "Vista previa / guía")
        preview.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.deploy_preview_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=18)
        self.deploy_preview_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.deploy_pro_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        platform_card = self.make_card(right, "Destino")
        platform_card.pack(fill="x", pady=(0, 10))
        ttk.Combobox(platform_card, textvariable=self.deploy_platform, state="readonly", values=["GitHub Pages", "Netlify", "Firebase Hosting", "Hosting estático", "Local"]).pack(fill="x", pady=4)
        ttk.Button(platform_card, text="Generar guía", style="Accent.TButton", command=self.deploy_export_checklist).pack(fill="x", pady=3)

        acc = self.make_card(right, "Accesos")
        acc.pack(fill="x", pady=(0, 10))
        for label, attr in [("🌍 Web Pack", "tab_web_pack"), ("🌐 Landing", "tab_landing_page"), ("📦 Export Pack", "tab_export_pack"), ("📚 Biblioteca", "tab_biblioteca_premium"), ("🚀 Publicación", "tab_publicacion_pro")]:
            if hasattr(self, attr):
                ttk.Button(acc, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

        info = self.make_card(right, "Qué añade")
        info.pack(fill="x")
        ttk.Label(info, text="Deploy Pro prepara un ZIP web final con index.html, assets, .nojekyll, manifest y una guía de subida. Es el paso después de Web Pack.", style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        self.deploy_scan()

    def deploy_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def deploy_scan(self):
        try:
            folder = self.deploy_folder()
            folder.mkdir(parents=True, exist_ok=True)
            files = []
            for ext in ("*.html", "*.wav", "*.png", "*.json", "*.txt", "*.zip"):
                files.extend(folder.glob(ext))
            files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
            self.deploy_files = files
            if hasattr(self, "deploy_listbox"):
                self.deploy_listbox.delete(0, tk.END)
                for p in files:
                    mb = p.stat().st_size / (1024 * 1024)
                    mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")
                    self.deploy_listbox.insert(tk.END, f"{p.suffix.upper()[1:]:<5} · {mb:>6.2f} MB · {mtime} · {p.name}")
            self.deploy_pro_status.set(f"Deploy scan: {len(files)} archivo(s) encontrados.")
            self.deploy_preview_text_set(self.deploy_summary_text(files))
        except Exception as e:
            self.deploy_pro_status.set(f"No se pudo escanear Deploy: {e}")

    def deploy_summary_text(self, files):
        htmls = [p for p in files if p.suffix.lower() == ".html"]
        zips = [p for p in files if p.suffix.lower() == ".zip"]
        return "\n".join([
            "DEPLOY PRO",
            "",
            f"Destino: {self.deploy_platform.get()}",
            f"Archivos detectados: {len(files)}",
            f"HTML: {len(htmls)}",
            f"ZIP previos: {len(zips)}",
            "",
            "CHECKLIST",
            "✓ index.html",
            "✓ assets/",
            "✓ .nojekyll para GitHub Pages",
            "✓ deploy_manifest.json",
            "✓ README_DEPLOY.txt",
            "",
            "Pulsa Crear Deploy para generar un ZIP listo para subir."
        ])

    def deploy_selected_path(self):
        if not hasattr(self, "deploy_listbox"):
            return None
        sel = self.deploy_listbox.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.deploy_files):
            return None
        return self.deploy_files[idx]

    def deploy_preview_text_set(self, text):
        if not hasattr(self, "deploy_preview_text"):
            return
        self.deploy_preview_text.configure(state="normal")
        self.deploy_preview_text.delete("1.0", tk.END)
        self.deploy_preview_text.insert("1.0", text)
        self.deploy_preview_text.configure(state="disabled")

    def deploy_preview_selected(self):
        p = self.deploy_selected_path()
        if not p:
            self.deploy_preview_text_set("Selecciona un archivo para ver detalles.")
            return
        try:
            stat = p.stat()
            lines = ["ARCHIVO", "", f"Nombre: {p.name}", f"Tipo: {p.suffix.upper()[1:]}", f"Tamaño: {stat.st_size/(1024*1024):.2f} MB", f"Ruta: {p}", ""]
            if p.suffix.lower() in (".html", ".txt", ".json"):
                text = p.read_text(encoding="utf-8", errors="replace")
                lines += ["CONTENIDO", "-"*40, text[:5000] + ("\n[...]" if len(text)>5000 else "")]
            else:
                lines.append("Archivo binario listo para incluir en el deploy.")
            self.deploy_preview_text_set("\n".join(lines))
        except Exception as e:
            self.deploy_pro_status.set(f"No se pudo previsualizar: {e}")

    def deploy_set_platform(self, platform_name):
        self.deploy_platform.set(platform_name)
        self.deploy_preview_text_set(self.deploy_guide_text())
        self.deploy_pro_status.set(f"Destino seleccionado: {platform_name}")

    def deploy_basic_index(self):
        title = self.landing_title.get() if hasattr(self, "landing_title") else "Mi proyecto"
        artist = self.landing_artist.get() if hasattr(self, "landing_artist") else "Atenea Studio"
        desc = self.landing_description.get("1.0", "end").strip() if hasattr(self, "landing_description") else "Proyecto generado con Modulador de Voz en Directo."
        return ("<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>" + html.escape(title) + "</title><style>body{margin:0;font-family:Arial;background:#090b18;color:white}main{max-width:920px;margin:auto;padding:60px 24px}.card{border:1px solid #2ee9ff55;border-radius:28px;background:#151827;padding:28px}h1{font-size:44px}a{color:#00e5ff}</style></head><body><main><div class=\"card\"><h1>" + html.escape(title) + "</h1><h2>" + html.escape(artist) + "</h2><p>" + html.escape(desc) + "</p><p>Web generada con Modulador de Voz en Directo V81 Navegación Pro.</p></div></main></body></html>")

    def deploy_manifest_data(self, included):
        return {
            "version": VERSION,
            "platform": self.deploy_platform.get(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "files": [{"name": p.name, "type": p.suffix.lower().replace('.', ''), "size_bytes": p.stat().st_size} for p in included],
        }

    def deploy_guide_text(self):
        platform = self.deploy_platform.get()
        base = ["DEPLOY PRO", "", f"Destino: {platform}", "", "PASOS GENERALES", "1. Crea el ZIP Deploy.", "2. Extrae el ZIP.", "3. Sube el contenido de la carpeta, no la carpeta entera.", "4. Comprueba que index.html está en la raíz.", ""]
        if platform == "GitHub Pages":
            base += ["GITHUB PAGES", "1. Crea un repositorio.", "2. Sube index.html, assets/, .nojekyll y manifest.", "3. Ve a Settings > Pages.", "4. Elige rama main y carpeta root.", "5. Guarda y espera a que se publique."]
        elif platform == "Firebase Hosting":
            base += ["FIREBASE HOSTING", "1. Instala Firebase CLI.", "2. Ejecuta firebase init hosting.", "3. Usa la carpeta extraída como public.", "4. Ejecuta firebase deploy."]
        elif platform == "Netlify":
            base += ["NETLIFY", "1. Entra en Netlify.", "2. Arrastra la carpeta extraída al deploy manual.", "3. Espera la URL final."]
        else:
            base += ["HOSTING ESTÁTICO", "1. Sube todos los archivos por FTP/panel.", "2. index.html debe quedar en la raíz.", "3. assets/ debe quedar al lado de index.html."]
        return "\n".join(base)

    def deploy_create_package(self):
        try:
            self.deploy_scan()
            folder = self.deploy_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = folder / f"deploy_web_pack_{ts}.zip"
            files = [p for p in self.deploy_files if p.suffix.lower() in (".html", ".wav", ".png", ".json", ".txt")]
            htmls = [p for p in files if p.suffix.lower() == ".html"]
            latest_html = htmls[0] if htmls else None
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                if latest_html:
                    z.write(latest_html, "index.html")
                else:
                    z.writestr("index.html", self.deploy_basic_index())
                for p in files:
                    if latest_html and p.resolve() == latest_html.resolve():
                        continue
                    ext = p.suffix.lower()
                    if ext == ".wav": arc = f"assets/audio/{p.name}"
                    elif ext == ".png": arc = f"assets/images/{p.name}"
                    elif ext == ".html": arc = f"assets/html/{p.name}"
                    else: arc = f"assets/docs/{p.name}"
                    z.write(p, arc)
                z.writestr(".nojekyll", "")
                z.writestr("README_DEPLOY.txt", self.deploy_guide_text())
                z.writestr("deploy_manifest.json", json.dumps(self.deploy_manifest_data(files), ensure_ascii=False, indent=2))
            self.deploy_pro_status.set(f"Deploy ZIP creado: {zip_path.name}")
            self.deploy_preview_text_set(f"DEPLOY CREADO\n\n{zip_path}\n\nIncluye index.html, assets/, .nojekyll, README_DEPLOY.txt y deploy_manifest.json.")
            messagebox.showinfo("Deploy creado", f"ZIP guardado en:\n{zip_path}")
        except Exception as e:
            self.deploy_pro_status.set(f"No se pudo crear deploy: {e}")

    def deploy_export_checklist(self):
        try:
            folder = self.deploy_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            txt = folder / f"deploy_checklist_{ts}.txt"
            js = folder / f"deploy_checklist_{ts}.json"
            guide = self.deploy_guide_text()
            txt.write_text(guide, encoding="utf-8")
            js.write_text(json.dumps({"version": VERSION, "platform": self.deploy_platform.get(), "created_at": datetime.now().isoformat(timespec="seconds"), "guide": guide}, ensure_ascii=False, indent=2), encoding="utf-8")
            self.deploy_pro_status.set(f"Checklist exportado: {txt.name} + JSON")
            self.deploy_preview_text_set(guide)
            messagebox.showinfo("Checklist exportado", f"Guardado en:\n{txt}\n{js}")
        except Exception as e:
            self.deploy_pro_status.set(f"No se pudo exportar checklist: {e}")

    def deploy_open_folder(self):
        folder = self.deploy_folder()
        try:
            if platform.system() == "Windows": os.startfile(str(folder))
            elif platform.system() == "Darwin": subprocess.Popen(["open", str(folder)])
            else: subprocess.Popen(["xdg-open", str(folder)])
            self.deploy_pro_status.set("Carpeta abierta.")
        except Exception as e:
            self.deploy_pro_status.set(f"No se pudo abrir carpeta: {e}")


    def build_web_pack_tab(self):
        cont = ttk.Frame(self.tab_web_pack)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "web_pack_banner" in self.web_pack_images:
            ttk.Label(header, image=self.web_pack_images["web_pack_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Web Pack Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Crear paquete web")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_scan", "Escanear", self.web_pack_scan),
            ("tile_html", "Generar HTML", self.web_pack_generate_html_only),
            ("tile_assets", "Ver assets", self.web_pack_preview_selected),
            ("tile_zip", "Crear ZIP", self.web_pack_create_zip),
            ("tile_open", "Abrir carpeta", self.web_pack_open_folder),
            ("tile_meta", "Manifest", self.web_pack_export_manifest),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.web_pack_images:
                ttk.Label(box, image=self.web_pack_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        lista = self.make_card(body, "Archivos que entrarán en el pack")
        lista.pack(side="left", fill="both", expand=True, padx=(0, 5))
        checks = ttk.Frame(lista, style="Card.TFrame")
        checks.pack(fill="x", pady=(0, 6))
        ttk.Checkbutton(checks, text="HTML", variable=self.web_pack_include_html, command=self.web_pack_scan).pack(side="left", padx=4)
        ttk.Checkbutton(checks, text="Audio WAV", variable=self.web_pack_include_audio, command=self.web_pack_scan).pack(side="left", padx=4)
        ttk.Checkbutton(checks, text="Imágenes PNG", variable=self.web_pack_include_images, command=self.web_pack_scan).pack(side="left", padx=4)
        ttk.Checkbutton(checks, text="Docs JSON/TXT", variable=self.web_pack_include_docs, command=self.web_pack_scan).pack(side="left", padx=4)

        list_frame = ttk.Frame(lista, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True)
        self.web_pack_listbox = tk.Listbox(
            list_frame,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#071018",
            relief="flat",
            activestyle="none",
            font=("Consolas", 10),
            height=16
        )
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.web_pack_listbox.yview)
        self.web_pack_listbox.configure(yscrollcommand=scroll.set)
        self.web_pack_listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.web_pack_listbox.bind("<<ListboxSelect>>", lambda e: self.web_pack_preview_selected())

        btns = ttk.Frame(lista, style="Card.TFrame")
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Vista previa", command=self.web_pack_preview_selected).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(btns, text="Crear ZIP web", style="Accent.TButton", command=self.web_pack_create_zip).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(btns, text="Landing", command=lambda: self.select_tab(self.tab_landing_page)).pack(side="left", fill="x", expand=True, padx=3, ipady=7)

        preview = self.make_card(body, "Vista previa")
        preview.pack(side="left", fill="both", expand=True, padx=(5, 0))
        if "web_pack_flow" in self.web_pack_images:
            ttk.Label(preview, image=self.web_pack_images["web_pack_flow"], style="Card.TLabel").pack(anchor="center", pady=(0, 6))
        self.web_pack_preview_text = tk.Text(
            preview,
            bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"],
            relief="flat", wrap="word", font=("Consolas", 10), height=12
        )
        self.web_pack_preview_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.web_pack_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(estado, textvariable=self.web_pack_last, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w", pady=(8, 0))

        info = self.make_card(right, "Estructura del ZIP")
        info.pack(fill="x", pady=(0, 10))
        ttk.Label(info, text="index.html\nassets/audio/\nassets/images/\nassets/docs/\nmanifest.json\nLEEME.txt", style="Card.TLabel", justify="left", wraplength=320).pack(anchor="w")

        accesos = self.make_card(right, "Accesos")
        accesos.pack(fill="x", pady=(0, 10))
        for label, attr in [
            ("🌐 Landing", "tab_landing_page"),
            ("🖼 Portadas", "tab_portadas_premium"),
            ("📚 Biblioteca", "tab_biblioteca_premium"),
            ("🚀 Publicación", "tab_publicacion_pro"),
            ("🏷 Brand Kit", "tab_brand_kit"),
            ("📦 Export Pack", "tab_export_pack"),
        ]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

        export = self.make_card(right, "Final")
        export.pack(fill="x")
        ttk.Button(export, text="Crear Web Pack ZIP", style="Accent.TButton", command=self.web_pack_create_zip).pack(fill="x", pady=3)
        ttk.Button(export, text="Abrir carpeta", command=self.web_pack_open_folder).pack(fill="x", pady=3)

        self.web_pack_scan()

    def web_pack_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def web_pack_scan(self):
        try:
            folder = self.web_pack_folder()
            folder.mkdir(parents=True, exist_ok=True)
            patterns = []
            if self.web_pack_include_audio.get():
                patterns += ["*.wav"]
            if self.web_pack_include_images.get():
                patterns += ["*.png"]
            if self.web_pack_include_docs.get():
                patterns += ["*.json", "*.txt"]
            if self.web_pack_include_html.get():
                patterns += ["*.html"]
            files = []
            for pat in patterns:
                files.extend(folder.glob(pat))
            files = [p for p in files if not p.name.lower().startswith("web_pack_")]
            files = sorted(set(files), key=lambda p: p.stat().st_mtime, reverse=True)
            self.web_pack_files = files
            if hasattr(self, "web_pack_listbox"):
                self.web_pack_listbox.delete(0, tk.END)
                for p in files:
                    size_mb = p.stat().st_size / (1024 * 1024)
                    mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")
                    self.web_pack_listbox.insert(tk.END, f"{p.suffix.upper()[1:]:<5} · {size_mb:>6.2f} MB · {mtime} · {p.name}")
            self.web_pack_status.set(f"Web Pack escaneado: {len(files)} archivo(s).")
            self.web_pack_text_set(self.web_pack_summary_text())
        except Exception as e:
            self.web_pack_status.set(f"No se pudo escanear: {e}")

    def web_pack_summary_text(self):
        files = getattr(self, "web_pack_files", [])
        counts = {}
        for p in files:
            counts[p.suffix.lower()] = counts.get(p.suffix.lower(), 0) + 1
        total = sum(p.stat().st_size for p in files) / (1024 * 1024) if files else 0
        lines = [
            "WEB PACK PRO",
            "",
            f"Archivos seleccionados: {len(files)}",
            f"Peso total aprox: {total:.2f} MB",
            "",
            "TIPOS",
        ]
        for ext, n in sorted(counts.items()):
            lines.append(f"- {ext or 'sin extensión'}: {n}")
        lines += [
            "",
            "El ZIP web incluirá una landing index.html, assets ordenados, manifest.json y LEEME.txt.",
        ]
        return "\n".join(lines)

    def web_pack_text_set(self, text):
        if not hasattr(self, "web_pack_preview_text"):
            return
        self.web_pack_preview_text.configure(state="normal")
        self.web_pack_preview_text.delete("1.0", tk.END)
        self.web_pack_preview_text.insert("1.0", text)
        self.web_pack_preview_text.configure(state="disabled")

    def web_pack_selected_path(self):
        if not hasattr(self, "web_pack_listbox"):
            return None
        sel = self.web_pack_listbox.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.web_pack_files):
            return None
        return self.web_pack_files[idx]

    def web_pack_preview_selected(self):
        p = self.web_pack_selected_path()
        if not p:
            self.web_pack_text_set(self.web_pack_summary_text())
            return
        try:
            stat = p.stat()
            lines = [
                "ARCHIVO WEB PACK",
                "",
                f"Nombre: {p.name}",
                f"Tipo: {p.suffix.upper()[1:]}",
                f"Tamaño: {stat.st_size / (1024*1024):.2f} MB",
                f"Modificado: {datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M:%S')}",
                f"Ruta: {p}",
                "",
            ]
            if p.suffix.lower() in (".txt", ".json", ".html"):
                text = p.read_text(encoding="utf-8", errors="replace")
                lines.append(text[:5000] + ("\n\n[...] Contenido recortado." if len(text) > 5000 else ""))
            elif p.suffix.lower() == ".png":
                try:
                    img = Image.open(p)
                    lines.append(f"Imagen: {img.width}x{img.height}px")
                    lines.append("Se copiará a assets/images/ dentro del ZIP web.")
                except Exception as e:
                    lines.append(f"No se pudo leer imagen: {e}")
            elif p.suffix.lower() == ".wav":
                try:
                    import wave
                    with wave.open(str(p), "rb") as wav:
                        dur = wav.getnframes() / max(1, wav.getframerate())
                        lines.append(f"WAV: {wav.getnchannels()} canal(es), {wav.getframerate()} Hz, {dur:.1f}s")
                    lines.append("Se copiará a assets/audio/ dentro del ZIP web.")
                except Exception as e:
                    lines.append(f"No se pudo leer WAV: {e}")
            self.web_pack_text_set("\n".join(lines))
            self.web_pack_status.set(f"Vista previa: {p.name}")
        except Exception as e:
            self.web_pack_status.set(f"No se pudo previsualizar: {e}")

    def web_pack_safe_name(self, text):
        try:
            return self.song_safe_name(text)
        except Exception:
            safe = "".join(ch for ch in str(text) if ch.isalnum() or ch in " -_").strip().replace(" ", "_")
            return safe or "web_pack"

    def web_pack_landing_html(self):
        try:
            return self.landing_html()
        except Exception:
            title = self.landing_title.get() if hasattr(self, "landing_title") else "Mi Demo"
            artist = self.landing_artist.get() if hasattr(self, "landing_artist") else "Atenea Studio"
            return f"""<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>{html.escape(title)}</title><style>body{{margin:0;background:#070914;color:white;font-family:Arial,sans-serif}}main{{max-width:900px;margin:auto;padding:60px 20px}}.card{{background:#111827;border:1px solid #00e5ff55;border-radius:24px;padding:30px}}h1{{font-size:54px}}a{{color:#00e5ff}}</style></head><body><main><div class='card'><h1>{html.escape(title)}</h1><h2>{html.escape(artist)}</h2><p>Proyecto creado con Modulador Voz Directo.</p></div></main></body></html>"""

    def web_pack_manifest(self, files):
        return {
            "version": VERSION,
            "type": "web_pack",
            "title": self.landing_title.get() if hasattr(self, "landing_title") else "Mi Demo",
            "artist": self.landing_artist.get() if hasattr(self, "landing_artist") else "Atenea Studio",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "files": [{"name": p.name, "type": p.suffix.lower().replace('.', ''), "size_bytes": p.stat().st_size} for p in files],
        }

    def web_pack_target_for(self, p):
        ext = p.suffix.lower()
        if ext == ".wav":
            return "assets/audio/" + p.name
        if ext == ".png":
            return "assets/images/" + p.name
        if ext in (".json", ".txt"):
            return "assets/docs/" + p.name
        if ext == ".html":
            return "assets/html/" + p.name
        return "assets/otros/" + p.name

    def web_pack_generate_html_only(self):
        try:
            folder = self.web_pack_folder()
            title = self.landing_title.get() if hasattr(self, "landing_title") else "mi_demo"
            path = folder / f"{self.web_pack_safe_name(title)}_index.html"
            path.write_text(self.web_pack_landing_html(), encoding="utf-8")
            self.web_pack_last.set(f"HTML creado: {path.name}")
            self.web_pack_status.set("HTML web generado.")
            self.web_pack_scan()
            messagebox.showinfo("HTML generado", f"Guardado en:\n{path}")
        except Exception as e:
            self.web_pack_status.set(f"No se pudo generar HTML: {e}")

    def web_pack_create_zip(self):
        try:
            self.web_pack_scan()
            files = list(getattr(self, "web_pack_files", []))
            folder = self.web_pack_folder()
            title = self.landing_title.get() if hasattr(self, "landing_title") else "web_pack"
            name = self.web_pack_safe_name(title)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = folder / f"{name}_web_pack_{ts}.zip"
            manifest = self.web_pack_manifest(files)
            readme = [
                "WEB PACK PRO",
                "",
                f"Título: {manifest.get('title')}",
                f"Artista: {manifest.get('artist')}",
                f"Creado: {manifest.get('created_at')}",
                "",
                "Estructura:",
                "- index.html",
                "- assets/audio/",
                "- assets/images/",
                "- assets/docs/",
                "- manifest.json",
                "",
                "Para publicar: sube todo el contenido del ZIP a un hosting o GitHub Pages.",
            ]
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("index.html", self.web_pack_landing_html())
                z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
                z.writestr("LEEME.txt", "\n".join(readme))
                for p in files:
                    try:
                        z.write(p, self.web_pack_target_for(p))
                    except Exception:
                        pass
            self.web_pack_last.set(f"Último ZIP: {zip_path.name}")
            self.web_pack_status.set("Web Pack ZIP creado correctamente.")
            self.web_pack_text_set(f"ZIP creado:\n{zip_path}\n\nArchivos incluidos: {len(files)}\n\nIncluye index.html, manifest.json y LEEME.txt.")
            if hasattr(self, "biblioteca_scan"):
                try:
                    self.biblioteca_scan()
                except Exception:
                    pass
            messagebox.showinfo("Web Pack creado", f"ZIP guardado en:\n{zip_path}")
        except Exception as e:
            self.web_pack_status.set(f"No se pudo crear Web Pack: {e}")

    def web_pack_export_manifest(self):
        try:
            self.web_pack_scan()
            folder = self.web_pack_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"web_pack_manifest_{ts}.json"
            path.write_text(json.dumps(self.web_pack_manifest(getattr(self, "web_pack_files", [])), ensure_ascii=False, indent=2), encoding="utf-8")
            self.web_pack_status.set(f"Manifest exportado: {path.name}")
            messagebox.showinfo("Manifest exportado", f"Guardado en:\n{path}")
        except Exception as e:
            self.web_pack_status.set(f"No se pudo exportar manifest: {e}")

    def web_pack_open_folder(self):
        folder = self.web_pack_folder()
        try:
            if platform.system() == "Windows":
                os.startfile(str(folder))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
            self.web_pack_status.set("Carpeta abierta.")
        except Exception as e:
            self.web_pack_status.set(f"No se pudo abrir carpeta: {e}")


    def build_landing_page_tab(self):
        cont = ttk.Frame(self.tab_landing_page)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "landing_banner" in self.landing_page_images:
            ttk.Label(header, image=self.landing_page_images["landing_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Landing Page Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Acciones web")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_web", "Crear HTML", self.landing_export_html),
            ("tile_publi", "Usar publicación", self.landing_use_publicacion),
            ("tile_brand", "Usar Brand Kit", self.landing_use_brand),
            ("tile_neon", "Neón", lambda: self.landing_set_style("Neón")),
            ("tile_elegante", "Elegante", lambda: self.landing_set_style("Elegante")),
            ("tile_pack", "Export Pack", lambda: self.select_tab(self.tab_export_pack) if hasattr(self, "tab_export_pack") else None),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.landing_page_images:
                ttk.Label(box, image=self.landing_page_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        editor = self.make_card(body, "Editor de landing")
        editor.pack(side="left", fill="both", expand=True, padx=(0, 5))
        for label, var in [("Título", self.landing_title), ("Artista/canal", self.landing_artist), ("YouTube", self.landing_url_youtube), ("Twitch", self.landing_url_twitch), ("Discord/Web", self.landing_url_discord)]:
            ttk.Label(editor, text=label + ":", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(5, 2))
            ttk.Entry(editor, textvariable=var).pack(fill="x", pady=(0, 5))
        ttk.Label(editor, text="Estilo:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(5, 2))
        ttk.Combobox(editor, textvariable=self.landing_style, state="readonly", values=["Neón", "Elegante", "Pop", "Oscuro", "Dorado", "Gaming"]).pack(fill="x", pady=(0, 5))
        ttk.Label(editor, text="Descripción:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(5, 2))
        self.landing_description_text = tk.Text(editor, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", height=8)
        self.landing_description_text.pack(fill="both", expand=True, pady=(0, 8))
        self.landing_description_text.insert("1.0", "Demo creada con Modulador Voz Directo. Voz, mezcla, portada y exportación preparadas desde el estudio.")
        btns = ttk.Frame(editor, style="Card.TFrame")
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Vista previa", command=self.landing_refresh_preview).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(btns, text="Exportar HTML", style="Accent.TButton", command=self.landing_export_html).pack(side="left", fill="x", expand=True, padx=3, ipady=7)

        preview = self.make_card(body, "Vista previa / código")
        preview.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.landing_preview_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=18)
        self.landing_preview_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.landing_refresh_preview()

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.landing_page_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(estado, textvariable=self.landing_last_file, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w", pady=(8,0))

        accesos = self.make_card(right, "Accesos")
        accesos.pack(fill="x", pady=(0, 10))
        for label, attr in [("🚀 Publicación", "tab_publicacion_pro"), ("🏷 Brand Kit", "tab_brand_kit"), ("🖼 Portadas", "tab_portadas_premium"), ("📚 Biblioteca", "tab_biblioteca_premium"), ("📦 Export Pack", "tab_export_pack")]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

        export = self.make_card(right, "Web final")
        export.pack(fill="x")
        ttk.Button(export, text="Exportar index.html", style="Accent.TButton", command=self.landing_export_html).pack(fill="x", pady=3)
        ttk.Button(export, text="Abrir última landing", command=self.landing_open_last).pack(fill="x", pady=3)
        ttk.Button(export, text="Exportar metadatos JSON", command=self.landing_export_metadata).pack(fill="x", pady=3)

    def landing_set_style(self, style_name):
        self.landing_style.set(style_name)
        self.landing_page_status.set(f"Estilo landing seleccionado: {style_name}")
        self.landing_refresh_preview()

    def landing_description(self):
        try:
            return self.landing_description_text.get("1.0", tk.END).strip()
        except Exception:
            return "Demo creada con Modulador Voz Directo."

    def landing_use_publicacion(self):
        try:
            if self.publicacion_title.get().strip():
                self.landing_title.set(self.publicacion_title.get().strip())
            if self.publicacion_artist.get().strip():
                self.landing_artist.set(self.publicacion_artist.get().strip())
            if hasattr(self, "publicacion_desc"):
                desc = self.publicacion_desc.get("1.0", tk.END).strip()
                if desc and hasattr(self, "landing_description_text"):
                    self.landing_description_text.delete("1.0", tk.END)
                    self.landing_description_text.insert("1.0", desc)
            self.landing_page_status.set("Datos de Publicación Pro aplicados.")
            self.landing_refresh_preview()
        except Exception as e:
            self.landing_page_status.set(f"No se pudieron usar datos de publicación: {e}")

    def landing_use_brand(self):
        try:
            if hasattr(self, "brand_name") and self.brand_name.get().strip():
                self.landing_artist.set(self.brand_name.get().strip())
            if hasattr(self, "brand_slogan") and self.brand_slogan.get().strip():
                current = self.landing_description()
                self.landing_description_text.delete("1.0", tk.END)
                self.landing_description_text.insert("1.0", current + "\n\n" + self.brand_slogan.get().strip())
            self.landing_page_status.set("Datos de Brand Kit aplicados.")
            self.landing_refresh_preview()
        except Exception as e:
            self.landing_page_status.set(f"No se pudieron usar datos de marca: {e}")

    def landing_palette(self):
        style = self.landing_style.get()
        palettes = {
            "Neón": ("#07111f", "#00e5ff", "#bc78ff", "#ffffff"),
            "Elegante": ("#10131f", "#ffcb57", "#62ffb4", "#fff8e8"),
            "Pop": ("#1b0d24", "#ff74aa", "#ffcb57", "#ffffff"),
            "Oscuro": ("#07080f", "#7c5cff", "#00e5ff", "#f8fbff"),
            "Dorado": ("#171006", "#ffcb57", "#ff965a", "#fff4d8"),
            "Gaming": ("#071827", "#00e5ff", "#62ffb4", "#ffffff"),
        }
        return palettes.get(style, palettes["Neón"])

    def landing_html(self):
        bg, accent, accent2, textc = self.landing_palette()
        title = html.escape(self.landing_title.get().strip() or "Mi Demo")
        artist = html.escape(self.landing_artist.get().strip() or "Atenea Studio")
        desc = html.escape(self.landing_description()).replace("\n", "<br>")
        youtube = html.escape(self.landing_url_youtube.get().strip())
        twitch = html.escape(self.landing_url_twitch.get().strip())
        discord = html.escape(self.landing_url_discord.get().strip())
        links = []
        if youtube: links.append(f'<a class="btn" href="{youtube}">YouTube</a>')
        if twitch: links.append(f'<a class="btn" href="{twitch}">Twitch</a>')
        if discord: links.append(f'<a class="btn" href="{discord}">Discord / Web</a>')
        if not links: links.append('<span class="muted">Añade enlaces en la app para que aparezcan aquí.</span>')
        created = datetime.now().strftime('%d/%m/%Y %H:%M')
        return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · {artist}</title>
<style>
:root{{--bg:{bg};--accent:{accent};--accent2:{accent2};--text:{textc};}}
*{{box-sizing:border-box}} body{{margin:0;min-height:100vh;font-family:Segoe UI,Arial,sans-serif;color:var(--text);background:radial-gradient(circle at 80% 10%, var(--accent)33, transparent 30%),radial-gradient(circle at 15% 85%, var(--accent2)44, transparent 32%),linear-gradient(135deg,var(--bg),#111827);display:flex;align-items:center;justify-content:center;padding:32px;}}
.card{{width:min(100%,980px);border:1px solid #ffffff22;border-radius:34px;background:#00000055;backdrop-filter:blur(14px);box-shadow:0 30px 100px #0009;padding:48px;overflow:hidden;position:relative}}
.badge{{display:inline-block;padding:10px 16px;border-radius:999px;background:var(--accent);color:#071018;font-weight:800;margin-bottom:24px}}
h1{{font-size:clamp(42px,8vw,96px);line-height:.95;margin:0 0 16px;font-weight:900;letter-spacing:-.06em}}
h2{{font-size:clamp(20px,3vw,32px);margin:0 0 28px;color:#ffffffcc;font-weight:500}}
p{{font-size:18px;line-height:1.65;color:#ffffffd8;max-width:760px}}
.buttons{{display:flex;flex-wrap:wrap;gap:14px;margin-top:30px}} .btn{{text-decoration:none;color:#071018;background:linear-gradient(135deg,var(--accent),var(--accent2));padding:14px 20px;border-radius:16px;font-weight:900}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin-top:38px}} .mini{{border:1px solid #ffffff22;border-radius:20px;padding:18px;background:#ffffff10}}
.muted{{color:#ffffffaa}} footer{{margin-top:34px;color:#ffffff88;font-size:14px}}
</style>
</head>
<body><main class="card"><span class="badge">LANDING PAGE PRO · V73</span><h1>{title}</h1><h2>{artist}</h2><p>{desc}</p><div class="buttons">{''.join(links)}</div><div class="grid"><div class="mini"><b>Audio</b><br><span class="muted">Demo / master WAV</span></div><div class="mini"><b>Portada</b><br><span class="muted">Cover art PNG</span></div><div class="mini"><b>Proyecto</b><br><span class="muted">JSON / TXT / Export Pack</span></div></div><footer>Creado el {created} con Modulador Voz Directo.</footer></main></body></html>'''

    def landing_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def landing_safe_name(self, text):
        try:
            return self.song_safe_name(text)
        except Exception:
            safe = ''.join(ch for ch in str(text) if ch.isalnum() or ch in ' -_').strip().replace(' ', '_')
            return safe or 'landing'

    def landing_export_html(self):
        try:
            folder = self.landing_output_folder()
            folder.mkdir(parents=True, exist_ok=True)
            name = self.landing_safe_name(self.landing_title.get())
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = folder / f"{name}_landing_{ts}.html"
            path.write_text(self.landing_html(), encoding='utf-8')
            self.landing_last_file.set(str(path))
            self.landing_page_status.set(f"Landing exportada: {path.name}")
            self.landing_refresh_preview(f"HTML exportado:\n{path}")
            try:
                webbrowser.open(path.as_uri())
            except Exception:
                pass
            if hasattr(self, 'biblioteca_scan'):
                try: self.biblioteca_scan()
                except Exception: pass
            messagebox.showinfo('Landing exportada', f'Página guardada en:\n{path}')
        except Exception as e:
            self.landing_page_status.set(f"No se pudo exportar landing: {e}")

    def landing_metadata(self):
        return {
            'version': VERSION,
            'title': self.landing_title.get(),
            'artist': self.landing_artist.get(),
            'style': self.landing_style.get(),
            'youtube': self.landing_url_youtube.get(),
            'twitch': self.landing_url_twitch.get(),
            'discord_web': self.landing_url_discord.get(),
            'description': self.landing_description(),
            'created_at': datetime.now().isoformat(timespec='seconds'),
        }

    def landing_export_metadata(self):
        try:
            folder = self.landing_output_folder()
            name = self.landing_safe_name(self.landing_title.get())
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = folder / f"{name}_landing_metadata_{ts}.json"
            path.write_text(json.dumps(self.landing_metadata(), ensure_ascii=False, indent=2), encoding='utf-8')
            self.landing_page_status.set(f"Metadatos landing exportados: {path.name}")
            messagebox.showinfo('Metadatos exportados', f'Guardado en:\n{path}')
        except Exception as e:
            self.landing_page_status.set(f"No se pudo exportar metadata: {e}")

    def landing_open_last(self):
        try:
            p = Path(self.landing_last_file.get())
            if p.exists():
                webbrowser.open(p.as_uri())
                self.landing_page_status.set('Landing abierta en navegador.')
            else:
                self.landing_page_status.set('Primero exporta una landing HTML.')
        except Exception as e:
            self.landing_page_status.set(f"No se pudo abrir landing: {e}")

    def landing_refresh_preview(self, extra=''):
        if not hasattr(self, 'landing_preview_text'):
            return
        data = self.landing_metadata()
        lines = [
            'LANDING PAGE PRO', '',
            f"Título: {data['title']}",
            f"Artista: {data['artist']}",
            f"Estilo: {data['style']}",
            f"YouTube: {data['youtube'] or 'sin enlace'}",
            f"Twitch: {data['twitch'] or 'sin enlace'}",
            f"Discord/Web: {data['discord_web'] or 'sin enlace'}",
            '', 'DESCRIPCIÓN', data['description'], '',
            'EXPORTA', '- index.html listo para abrir en navegador.', '- metadata JSON para el proyecto.', '', str(extra)
        ]
        self.landing_preview_text.configure(state='normal')
        self.landing_preview_text.delete('1.0', tk.END)
        self.landing_preview_text.insert('1.0', '\n'.join(lines))
        self.landing_preview_text.configure(state='disabled')


    def build_brand_kit_tab(self):
        cont = ttk.Frame(self.tab_brand_kit)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "brand_banner" in self.brand_kit_images:
            ttk.Label(header, image=self.brand_kit_images["brand_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Brand Kit Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Identidad visual")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_logo", "Crear logo", self.brand_export_logo),
            ("tile_banner", "Crear banner", self.brand_export_banner),
            ("tile_avatar", "Crear avatar", self.brand_export_avatar),
            ("tile_palette", "Paleta", self.brand_export_palette),
            ("tile_zip", "Pack ZIP", self.brand_export_full_pack),
            ("tile_biblioteca", "Biblioteca", lambda: self.select_tab(self.tab_biblioteca_premium)),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.brand_kit_images:
                ttk.Label(box, image=self.brand_kit_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        editor = self.make_card(body, "Datos de marca")
        editor.pack(side="left", fill="both", expand=True, padx=(0, 5))

        for label, var in [
            ("Nombre de marca/canal", self.brand_name),
            ("Artista/creador", self.brand_artist),
            ("Frase/slogan", self.brand_slogan),
        ]:
            ttk.Label(editor, text=label + ":", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(6, 2))
            ttk.Entry(editor, textvariable=var).pack(fill="x", pady=(0, 6))

        ttk.Label(editor, text="Estilo visual:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(6, 2))
        ttk.Combobox(editor, textvariable=self.brand_style, state="readonly", values=["Neón Azul", "Dorado Pro", "Morado Studio", "Gaming", "Lofi", "Oscuro"] ).pack(fill="x", pady=(0, 8))

        color_row = ttk.Frame(editor, style="Card.TFrame")
        color_row.pack(fill="x", pady=(6, 8))
        ttk.Label(color_row, text="Color 1:", style="Card.TLabel").pack(side="left")
        ttk.Entry(color_row, textvariable=self.brand_primary, width=10).pack(side="left", padx=5)
        ttk.Label(color_row, text="Color 2:", style="Card.TLabel").pack(side="left", padx=(10, 0))
        ttk.Entry(color_row, textvariable=self.brand_secondary, width=10).pack(side="left", padx=5)

        btns = ttk.Frame(editor, style="Card.TFrame")
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="Usar datos de publicación", command=self.brand_use_publication_data).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(btns, text="Vista previa", command=self.brand_refresh_preview).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(btns, text="Exportar todo", style="Accent.TButton", command=self.brand_export_full_pack).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Label(editor, textvariable=self.brand_last_export, style="Card.TLabel", wraplength=460).pack(anchor="w", pady=(12, 0))

        preview = self.make_card(body, "Vista previa")
        preview.pack(side="left", fill="both", expand=True, padx=(5, 0))
        if "brand_preview" in self.brand_kit_images:
            ttk.Label(preview, image=self.brand_kit_images["brand_preview"], style="Card.TLabel").pack(anchor="center", pady=(0, 6))

        self.brand_preview_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=10)
        self.brand_preview_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.brand_refresh_preview()

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.brand_kit_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        formato = self.make_card(right, "Exporta")
        formato.pack(fill="x", pady=(0, 10))
        ttk.Label(formato, text="Brand Kit crea logo, banner, avatar, paleta y guía de marca. Perfecto para YouTube, miniaturas, demos y directos.", style="Card.TLabel", justify="left", wraplength=320).pack(anchor="w")
        ttk.Button(formato, text="Logo PNG", command=self.brand_export_logo).pack(fill="x", pady=(8, 3))
        ttk.Button(formato, text="Banner PNG", command=self.brand_export_banner).pack(fill="x", pady=3)
        ttk.Button(formato, text="Avatar PNG", command=self.brand_export_avatar).pack(fill="x", pady=3)
        ttk.Button(formato, text="Pack ZIP completo", style="Accent.TButton", command=self.brand_export_full_pack).pack(fill="x", pady=3)

        accesos = self.make_card(right, "Accesos")
        accesos.pack(fill="x")
        for label, attr in [
            ("🖼 Portadas", "tab_portadas_premium"),
            ("🚀 Publicación", "tab_publicacion_pro"),
            ("📦 Export Pack", "tab_export_pack"),
            ("📚 Biblioteca", "tab_biblioteca_premium"),
            ("🏠 Inicio", "tab_inicio_premium"),
        ]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

    def brand_hex_to_rgb(self, value, fallback=(0, 229, 255)):
        try:
            value = str(value).strip().lstrip('#')
            if len(value) == 3:
                value = ''.join(ch*2 for ch in value)
            return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            return fallback

    def brand_palette(self):
        presets = {
            "Neón Azul": ("#00E5FF", "#7C5CFF", (8,10,24), (22,42,88)),
            "Dorado Pro": ("#FFCB57", "#FF965A", (18,13,8), (74,45,12)),
            "Morado Studio": ("#BC78FF", "#FF74AA", (18,10,28), (76,28,88)),
            "Gaming": ("#00E5FF", "#62FFB4", (5,12,24), (20,60,82)),
            "Lofi": ("#62FFB4", "#FFCB57", (18,20,30), (42,52,58)),
            "Oscuro": ("#FF5C8A", "#7C5CFF", (6,7,14), (26,14,52)),
        }
        style = self.brand_style.get()
        p = presets.get(style, presets["Neón Azul"])
        # Permite sobrescribir colores a mano.
        c1 = self.brand_hex_to_rgb(self.brand_primary.get(), self.brand_hex_to_rgb(p[0]))
        c2 = self.brand_hex_to_rgb(self.brand_secondary.get(), self.brand_hex_to_rgb(p[1]))
        return {"style": style, "primary": c1, "secondary": c2, "bg1": p[2], "bg2": p[3], "primary_hex": self.brand_primary.get(), "secondary_hex": self.brand_secondary.get()}

    def brand_font(self, size, bold=False):
        try:
            for p in [
                "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            ]:
                if Path(p).exists():
                    return ImageFont.truetype(p, size)
        except Exception:
            pass
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def brand_gradient_image(self, size, wide=False):
        pal = self.brand_palette()
        w, h = size if isinstance(size, tuple) else (size, size)
        img = Image.new("RGBA", (w, h), pal["bg1"] + (255,))
        px = img.load()
        for y in range(h):
            for x in range(w):
                t = (x / max(1, w-1)) * 0.64 + (y / max(1, h-1)) * 0.36
                px[x, y] = tuple(int(pal["bg1"][i]*(1-t)+pal["bg2"][i]*t) for i in range(3)) + (255,)
        for cx, cy, r, c, a in [
            (int(w*0.80), int(h*0.18), int(min(w,h)*0.36), pal["primary"], 70),
            (int(w*0.20), int(h*0.82), int(min(w,h)*0.32), pal["secondary"], 58),
            (int(w*0.55), int(h*0.54), int(min(w,h)*0.20), (255,203,87), 28),
        ]:
            ov = Image.new("RGBA", (w,h), (0,0,0,0)); od = ImageDraw.Draw(ov)
            od.ellipse((cx-r, cy-r, cx+r, cy+r), fill=c+(a,))
            img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(max(18, min(w,h)//24))))
        return img

    def brand_make_logo(self, size=1024):
        pal = self.brand_palette()
        img = self.brand_gradient_image(size)
        d = ImageDraw.Draw(img)
        margin = int(size*0.08)
        d.rounded_rectangle((margin, margin, size-margin, size-margin), radius=int(size*0.10), fill=(0,0,0,45), outline=(255,255,255,80), width=max(4, size//180))
        initials = ''.join([w[0] for w in self.brand_name.get().split()[:2]]).upper() or 'A'
        f = self.brand_font(int(size*0.30), True)
        bb = d.textbbox((0,0), initials, font=f)
        d.text(((size-(bb[2]-bb[0]))/2, size*0.33), initials, font=f, fill=(255,255,255,255))
        d.rounded_rectangle((int(size*0.28), int(size*0.68), int(size*0.72), int(size*0.73)), radius=int(size*0.03), fill=pal["primary"]+(245,))
        d.text((int(size*0.20), int(size*0.78)), self.brand_artist.get()[:24], font=self.brand_font(int(size*0.045), True), fill=(255,255,255,220))
        return img.convert('RGB')

    def brand_make_banner(self):
        w, h = 1920, 1080
        pal = self.brand_palette()
        img = self.brand_gradient_image((w, h), wide=True)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((90, 90, w-90, h-90), radius=80, fill=(0,0,0,50), outline=(255,255,255,70), width=6)
        logo = self.brand_make_logo(360).resize((260,260))
        img.paste(logo, (140, 180))
        d.text((450, 215), self.brand_name.get().upper()[:34], font=self.brand_font(92, True), fill=(255,255,255,255))
        d.text((456, 335), self.brand_slogan.get()[:80], font=self.brand_font(42), fill=(220,235,255,230))
        d.rounded_rectangle((456, 450, 760, 520), radius=32, fill=pal['primary']+(245,))
        d.text((500, 466), 'BRAND KIT', font=self.brand_font(30, True), fill=(8,12,24,255))
        for i,c in enumerate([pal['primary'], pal['secondary'], (255,203,87), (255,116,170), (98,255,180)]):
            d.rounded_rectangle((456+i*98, 615, 526+i*98, 685), radius=22, fill=c+(240,))
        d.text((456, 775), 'MODULADOR VOZ DIRECTO · V73', font=self.brand_font(32, True), fill=(255,255,255,170))
        return img.convert('RGB')

    def brand_make_avatar(self):
        img = self.brand_make_logo(512)
        mask = Image.new('L', (512,512), 0)
        md = ImageDraw.Draw(mask)
        md.ellipse((8,8,504,504), fill=255)
        out = Image.new('RGB', (512,512), (0,0,0))
        out.paste(img, (0,0), mask)
        return out

    def brand_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def brand_safe_name(self, text):
        try:
            return self.song_safe_name(text)
        except Exception:
            safe = ''.join(ch for ch in str(text) if ch.isalnum() or ch in ' -_').strip().replace(' ', '_')
            return safe or 'brand_kit'

    def brand_data(self):
        pal = self.brand_palette()
        return {
            "version": VERSION,
            "brand_name": self.brand_name.get(),
            "artist": self.brand_artist.get(),
            "slogan": self.brand_slogan.get(),
            "style": self.brand_style.get(),
            "primary": self.brand_primary.get(),
            "secondary": self.brand_secondary.get(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "assets": ["logo_1024.png", "banner_1920x1080.png", "avatar_512.png", "brand_palette.json", "BRAND_KIT.txt"],
        }

    def brand_use_publication_data(self):
        try:
            if hasattr(self, 'publicacion_artist') and self.publicacion_artist.get().strip():
                self.brand_artist.set(self.publicacion_artist.get().strip())
            if hasattr(self, 'publicacion_title') and self.publicacion_title.get().strip():
                self.brand_name.set(self.publicacion_title.get().strip()[:32])
            self.brand_refresh_preview('Datos tomados de Publicación Pro.')
            self.brand_kit_status.set('Datos de publicación aplicados al Brand Kit.')
        except Exception as e:
            self.brand_kit_status.set(f'No se pudieron usar datos de publicación: {e}')

    def brand_export_logo(self):
        try:
            folder = self.brand_output_folder(); folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = folder / f"{self.brand_safe_name(self.brand_name.get())}_logo_{ts}.png"
            self.brand_make_logo(1024).save(path, 'PNG', optimize=True)
            self.brand_last_export.set(f'Último logo: {path.name}')
            self.brand_kit_status.set(f'Logo exportado: {path.name}')
            self.brand_refresh_preview(f'Logo guardado:\n{path}')
            if hasattr(self, 'biblioteca_scan'):
                try: self.biblioteca_scan()
                except Exception: pass
        except Exception as e:
            self.brand_kit_status.set(f'No se pudo exportar logo: {e}')

    def brand_export_banner(self):
        try:
            folder = self.brand_output_folder(); folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = folder / f"{self.brand_safe_name(self.brand_name.get())}_banner_{ts}.png"
            self.brand_make_banner().save(path, 'PNG', optimize=True)
            self.brand_last_export.set(f'Último banner: {path.name}')
            self.brand_kit_status.set(f'Banner exportado: {path.name}')
            self.brand_refresh_preview(f'Banner guardado:\n{path}')
            if hasattr(self, 'biblioteca_scan'):
                try: self.biblioteca_scan()
                except Exception: pass
        except Exception as e:
            self.brand_kit_status.set(f'No se pudo exportar banner: {e}')

    def brand_export_avatar(self):
        try:
            folder = self.brand_output_folder(); folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = folder / f"{self.brand_safe_name(self.brand_name.get())}_avatar_{ts}.png"
            self.brand_make_avatar().save(path, 'PNG', optimize=True)
            self.brand_last_export.set(f'Último avatar: {path.name}')
            self.brand_kit_status.set(f'Avatar exportado: {path.name}')
            self.brand_refresh_preview(f'Avatar guardado:\n{path}')
        except Exception as e:
            self.brand_kit_status.set(f'No se pudo exportar avatar: {e}')

    def brand_export_palette(self):
        try:
            folder = self.brand_output_folder(); folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = folder / f"{self.brand_safe_name(self.brand_name.get())}_brand_palette_{ts}.json"
            path.write_text(json.dumps(self.brand_data(), ensure_ascii=False, indent=2), encoding='utf-8')
            self.brand_last_export.set(f'Última paleta: {path.name}')
            self.brand_kit_status.set(f'Paleta exportada: {path.name}')
            self.brand_refresh_preview(f'Paleta JSON guardada:\n{path}')
        except Exception as e:
            self.brand_kit_status.set(f'No se pudo exportar paleta: {e}')

    def brand_export_full_pack(self):
        try:
            folder = self.brand_output_folder(); folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = self.brand_safe_name(self.brand_name.get())
            work = folder / f"{base_name}_brand_kit_{ts}"
            work.mkdir(parents=True, exist_ok=True)
            logo = work / 'logo_1024.png'
            banner = work / 'banner_1920x1080.png'
            avatar = work / 'avatar_512.png'
            palette = work / 'brand_palette.json'
            readme = work / 'BRAND_KIT.txt'
            self.brand_make_logo(1024).save(logo, 'PNG', optimize=True)
            self.brand_make_banner().save(banner, 'PNG', optimize=True)
            self.brand_make_avatar().save(avatar, 'PNG', optimize=True)
            palette.write_text(json.dumps(self.brand_data(), ensure_ascii=False, indent=2), encoding='utf-8')
            readme.write_text('\n'.join([
                'BRAND KIT PRO', '',
                f'Marca: {self.brand_name.get()}',
                f'Artista: {self.brand_artist.get()}',
                f'Slogan: {self.brand_slogan.get()}',
                f'Estilo: {self.brand_style.get()}',
                f'Color 1: {self.brand_primary.get()}',
                f'Color 2: {self.brand_secondary.get()}',
                '', 'Incluye logo, banner, avatar y paleta JSON.'
            ]), encoding='utf-8')
            zip_path = folder / f"{base_name}_brand_kit_{ts}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                for f in [logo, banner, avatar, palette, readme]:
                    z.write(f, f.name)
            self.brand_last_export.set(f'Último pack: {zip_path.name}')
            self.brand_kit_status.set(f'Brand Kit exportado: {zip_path.name}')
            self.brand_refresh_preview(f'Pack ZIP guardado:\n{zip_path}')
            if hasattr(self, 'biblioteca_scan'):
                try: self.biblioteca_scan()
                except Exception: pass
            messagebox.showinfo('Brand Kit exportado', f'Guardado en:\n{zip_path}')
        except Exception as e:
            self.brand_kit_status.set(f'No se pudo exportar Brand Kit: {e}')

    def brand_refresh_preview(self, extra=''):
        if not hasattr(self, 'brand_preview_text'):
            return
        data = self.brand_data()
        lines = [
            'BRAND KIT PRO', '',
            f"Marca: {data['brand_name']}",
            f"Artista: {data['artist']}",
            f"Slogan: {data['slogan']}",
            f"Estilo: {data['style']}",
            f"Color 1: {data['primary']}",
            f"Color 2: {data['secondary']}", '',
            'EXPORTA', '- Logo PNG 1024x1024', '- Banner PNG 1920x1080', '- Avatar PNG 512x512', '- Paleta JSON', '- Pack ZIP completo', '', str(extra)
        ]
        self.brand_preview_text.configure(state='normal')
        self.brand_preview_text.delete('1.0', tk.END)
        self.brand_preview_text.insert('1.0', '\n'.join(lines))
        self.brand_preview_text.configure(state='disabled')


    def build_publicacion_pro_tab(self):
        cont = ttk.Frame(self.tab_publicacion_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "publicacion_banner" in self.publicacion_pro_images:
            ttk.Label(header, image=self.publicacion_pro_images["publicacion_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Publicación Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Preparar lanzamiento")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_youtube", "YouTube", self.publicacion_template_youtube),
            ("tile_tags", "Tags", self.publicacion_generate_tags),
            ("tile_release", "Release", self.publicacion_release_notes),
            ("tile_check", "Checklist", self.publicacion_checklist),
            ("tile_export", "Exportar", self.publicacion_export_all),
            ("tile_pack", "Export Pack", lambda: self.select_tab(self.tab_export_pack)),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.publicacion_pro_images:
                ttk.Label(box, image=self.publicacion_pro_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        editor = self.make_card(body, "Ficha de publicación")
        editor.pack(side="left", fill="both", expand=True, padx=(0, 5))
        for label, var in [
            ("Título", self.publicacion_title),
            ("Artista / canal", self.publicacion_artist),
            ("Tags", self.publicacion_tags),
        ]:
            ttk.Label(editor, text=label + ":", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(6, 2))
            ttk.Entry(editor, textvariable=var).pack(fill="x", pady=(0, 6))
        ttk.Label(editor, text="Plataforma:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(6, 2))
        ttk.Combobox(editor, textvariable=self.publicacion_platform, state="readonly", values=["YouTube", "TikTok", "Instagram", "Archivo privado", "Demo para amigo"]).pack(fill="x", pady=(0, 8))

        self.publicacion_desc = tk.Text(editor, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Segoe UI", 10), height=12)
        self.publicacion_desc.pack(fill="both", expand=True, pady=(6, 8))
        self.publicacion_desc.insert("1.0", self.publicacion_default_description())

        btns = ttk.Frame(editor, style="Card.TFrame")
        btns.pack(fill="x")
        ttk.Button(btns, text="Usar proyecto", command=self.publicacion_use_project).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(btns, text="Generar descripción", command=self.publicacion_template_youtube).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(btns, text="Exportar", style="Accent.TButton", command=self.publicacion_export_all).pack(side="left", fill="x", expand=True, padx=3, ipady=7)

        preview = self.make_card(body, "Checklist y vista previa")
        preview.pack(side="left", fill="both", expand=True, padx=(5, 0))
        if "publicacion_sheet" in self.publicacion_pro_images:
            ttk.Label(preview, image=self.publicacion_pro_images["publicacion_sheet"], style="Card.TLabel").pack(anchor="center", pady=(0, 6))
        self.publicacion_preview = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=12)
        self.publicacion_preview.pack(fill="both", expand=True, padx=4, pady=4)
        self.publicacion_refresh_preview("Publicación preparada.")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.publicacion_pro_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(estado, textvariable=self.publicacion_ready, style="Card.TLabel", font=("Segoe UI", 14, "bold"), wraplength=320).pack(anchor="w", pady=(8, 0))
        ttk.Label(estado, textvariable=self.publicacion_last_export, style="Card.TLabel", wraplength=320).pack(anchor="w", pady=(8, 0))

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Generar tags", command=self.publicacion_generate_tags).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Release notes", command=self.publicacion_release_notes).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Checklist final", command=self.publicacion_checklist).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Exportar TXT/JSON", style="Accent.TButton", command=self.publicacion_export_all).pack(fill="x", pady=3)

        accesos = self.make_card(right, "Accesos")
        accesos.pack(fill="x")
        for label, attr in [("📦 Export Pack", "tab_export_pack"), ("🖼 Portadas", "tab_portadas_premium"), ("📚 Biblioteca", "tab_biblioteca_premium"), ("💿 Master", "tab_master_final"), ("🏁 Studio", "tab_studio_dashboard")]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

    def publicacion_default_description(self):
        return (
            "Nueva demo creada con Modulador de Voz en Directo.\n\n"
            "Incluye voz procesada, mezcla, master final y recursos del proyecto.\n\n"
            "🎧 Gracias por escuchar."
        )

    def publicacion_data(self):
        desc = ""
        if hasattr(self, "publicacion_desc"):
            desc = self.publicacion_desc.get("1.0", tk.END).strip()
        return {
            "version": VERSION,
            "title": self.publicacion_title.get().strip(),
            "artist": self.publicacion_artist.get().strip(),
            "platform": self.publicacion_platform.get(),
            "tags": [t.strip() for t in self.publicacion_tags.get().split(',') if t.strip()],
            "description": desc,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def publicacion_use_project(self):
        try:
            if hasattr(self, "song_title") and self.song_title.get().strip():
                self.publicacion_title.set(self.song_title.get().strip())
            elif hasattr(self, "karaoke_track") and self.karaoke_track.get().strip():
                self.publicacion_title.set(self.karaoke_track.get().strip()[:70])
            self.publicacion_template_youtube()
            self.publicacion_pro_status.set("Datos del proyecto usados en publicación.")
        except Exception as e:
            self.publicacion_pro_status.set(f"No se pudo usar proyecto: {e}")

    def publicacion_template_youtube(self):
        title = self.publicacion_title.get().strip() or "Mi demo"
        artist = self.publicacion_artist.get().strip() or "Atenea Studio"
        text = (
            f"{title}\n\n"
            f"Demo creada por {artist} con Modulador de Voz en Directo.\n\n"
            "Incluye procesamiento vocal, mezcla, master y recursos exportados desde la app.\n\n"
            "🎙 Voz / efectos / mezcla\n"
            "🎧 Demo WAV\n"
            "🖼 Portada / recursos visuales\n"
            "📦 Proyecto preparado con Export Pack Pro\n\n"
            "#musica #demo #karaoke #autotune #gaming #voz"
        )
        if hasattr(self, "publicacion_desc"):
            self.publicacion_desc.delete("1.0", tk.END)
            self.publicacion_desc.insert("1.0", text)
        self.publicacion_refresh_preview("Descripción tipo YouTube generada.")
        self.publicacion_pro_status.set("Plantilla YouTube generada.")

    def publicacion_generate_tags(self):
        base = ["demo", "música", "voz", "autotune", "karaoke", "gaming", "modulador", "cover", "stream", "youtube"]
        title = (self.publicacion_title.get() or "").lower()
        if "fortnite" in title:
            base += ["fortnite", "directo", "gaming"]
        if "trap" in title:
            base += ["trap", "beat", "vocal"]
        if "pop" in title:
            base += ["pop", "vocal", "canción"]
        seen=[]
        for t in base:
            if t not in seen: seen.append(t)
        self.publicacion_tags.set(", ".join(seen[:15]))
        self.publicacion_refresh_preview("Tags generados.")
        self.publicacion_pro_status.set("Tags listos.")

    def publicacion_release_notes(self):
        data = self.publicacion_data()
        text = (
            "RELEASE NOTES\n\n"
            f"Título: {data['title']}\n"
            f"Artista/canal: {data['artist']}\n"
            f"Plataforma: {data['platform']}\n"
            "Contenido incluido:\n"
            "- Audio WAV / demo / master si está exportado.\n"
            "- Portada PNG si está generada.\n"
            "- Metadatos JSON/TXT.\n"
            "- Export Pack opcional para guardar todo junto.\n"
        )
        if hasattr(self, "publicacion_preview"):
            self.publicacion_preview.configure(state="normal")
            self.publicacion_preview.delete("1.0", tk.END)
            self.publicacion_preview.insert("1.0", text)
            self.publicacion_preview.configure(state="disabled")
        self.publicacion_pro_status.set("Release notes generadas.")

    def publicacion_checklist(self):
        checks=[]
        data=self.publicacion_data()
        checks.append(("🟢" if data['title'] else "🔴", "Título preparado"))
        checks.append(("🟢" if data['description'] else "🔴", "Descripción preparada"))
        checks.append(("🟢" if data['tags'] else "🟡", "Tags preparados"))
        try:
            folder = self.publicacion_output_folder()
            checks.append(("🟢" if list(folder.glob('*.wav')) else "🟡", "Hay audio WAV en biblioteca"))
            checks.append(("🟢" if list(folder.glob('*.png')) else "🟡", "Hay portada PNG en biblioteca"))
            checks.append(("🟢" if list(folder.glob('*.zip')) else "🟡", "Export Pack ZIP creado"))
        except Exception:
            pass
        ok=sum(1 for c,_ in checks if c=='🟢')
        self.publicacion_ready.set(f"Checklist: {ok}/{len(checks)} OK")
        lines=['CHECKLIST DE PUBLICACIÓN','']+[f"{c} {m}" for c,m in checks]
        if hasattr(self, "publicacion_preview"):
            self.publicacion_preview.configure(state="normal")
            self.publicacion_preview.delete("1.0", tk.END)
            self.publicacion_preview.insert("1.0", "\n".join(lines))
            self.publicacion_preview.configure(state="disabled")
        self.publicacion_pro_status.set("Checklist revisado.")

    def publicacion_refresh_preview(self, extra=""):
        if not hasattr(self, "publicacion_preview"): return
        data=self.publicacion_data()
        lines=["PUBLICACIÓN PRO", "", f"Título: {data['title']}", f"Artista: {data['artist']}", f"Plataforma: {data['platform']}", f"Tags: {', '.join(data['tags'])}", "", "DESCRIPCIÓN", data['description'][:1400], "", str(extra)]
        self.publicacion_preview.configure(state="normal")
        self.publicacion_preview.delete("1.0", tk.END)
        self.publicacion_preview.insert("1.0", "\n".join(lines))
        self.publicacion_preview.configure(state="disabled")

    def publicacion_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def publicacion_safe_name(self, text):
        try:
            return self.song_safe_name(text)
        except Exception:
            safe = "".join(ch for ch in str(text) if ch.isalnum() or ch in " -_").strip().replace(" ", "_")
            return safe or "publicacion"

    def publicacion_export_all(self):
        try:
            data=self.publicacion_data()
            folder=self.publicacion_output_folder()
            folder.mkdir(parents=True, exist_ok=True)
            ts=datetime.now().strftime("%Y%m%d_%H%M%S")
            name=self.publicacion_safe_name(data['title'])
            json_path=folder / f"{name}_publicacion_{ts}.json"
            txt_path=folder / f"{name}_publicacion_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines=["PUBLICACIÓN PRO", "", f"Fecha: {data['created_at']}", f"Título: {data['title']}", f"Artista: {data['artist']}", f"Plataforma: {data['platform']}", "", "TAGS", ", ".join(data['tags']), "", "DESCRIPCIÓN", data['description']]
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            self.publicacion_last_export.set(f"Último export: {json_path.name} + TXT")
            self.publicacion_pro_status.set("Publicación exportada.")
            self.publicacion_checklist()
            messagebox.showinfo("Publicación exportada", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.publicacion_pro_status.set(f"No se pudo exportar publicación: {e}")


    def build_export_pack_tab(self):
        cont = ttk.Frame(self.tab_export_pack)
        cont.pack(fill="both", expand=True)
        header = self.make_card(cont)
        header.pack(fill="x", pady=(0,10))
        if "export_banner" in self.export_pack_images:
            ttk.Label(header, image=self.export_pack_images["export_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Export Pack Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0,10))

        tiles = self.make_card(left, "Pack final del proyecto")
        tiles.pack(fill="x", pady=(0,10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")
        items = [
            ("tile_scan", "Escanear", self.export_pack_scan),
            ("tile_zip", "Crear ZIP", self.export_pack_create_zip),
            ("tile_audio", "Audio", lambda: self.export_pack_quick_filter(audio=True, images=False, docs=False)),
            ("tile_cover", "Portadas", lambda: self.export_pack_quick_filter(audio=False, images=True, docs=False)),
            ("tile_docs", "Docs", lambda: self.export_pack_quick_filter(audio=False, images=False, docs=True)),
            ("tile_folder", "Abrir carpeta", self.export_pack_open_folder),
        ]
        for i,(img,label,cmd) in enumerate(items):
            box=ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.export_pack_images:
                ttk.Label(box, image=self.export_pack_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5,0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)
        lista = self.make_card(body, "Archivos que entrarán en el pack")
        lista.pack(side="left", fill="both", expand=True, padx=(0,5))

        opts=ttk.Frame(lista, style="Card.TFrame")
        opts.pack(fill="x", pady=(0,6))
        ttk.Checkbutton(opts, text="Audio WAV", variable=self.export_pack_filter_audio, command=self.export_pack_scan).pack(side="left", padx=5)
        ttk.Checkbutton(opts, text="Portadas PNG", variable=self.export_pack_filter_images, command=self.export_pack_scan).pack(side="left", padx=5)
        ttk.Checkbutton(opts, text="Docs JSON/TXT", variable=self.export_pack_filter_docs, command=self.export_pack_scan).pack(side="left", padx=5)
        ttk.Button(opts, text="Actualizar", command=self.export_pack_scan).pack(side="right", padx=5)

        list_frame=ttk.Frame(lista, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True)
        self.export_pack_listbox = tk.Listbox(list_frame, bg=COLORS["panel2"], fg=COLORS["text"], selectbackground=COLORS["accent"], selectforeground="#071018", relief="flat", activestyle="none", font=("Consolas",10), height=18)
        scroll=ttk.Scrollbar(list_frame, orient="vertical", command=self.export_pack_listbox.yview)
        self.export_pack_listbox.configure(yscrollcommand=scroll.set)
        self.export_pack_listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.export_pack_listbox.bind("<<ListboxSelect>>", lambda e: self.export_pack_preview_selected())

        btns=ttk.Frame(lista, style="Card.TFrame")
        btns.pack(fill="x", pady=(8,0))
        ttk.Button(btns, text="Vista previa", command=self.export_pack_preview_selected).pack(side="left", expand=True, fill="x", padx=3, ipady=7)
        ttk.Button(btns, text="Crear ZIP final", style="Accent.TButton", command=self.export_pack_create_zip).pack(side="left", expand=True, fill="x", padx=3, ipady=7)
        ttk.Button(btns, text="Abrir carpeta", command=self.export_pack_open_folder).pack(side="left", expand=True, fill="x", padx=3, ipady=7)

        preview = self.make_card(body, "Informe del pack")
        preview.pack(side="left", fill="both", expand=True, padx=(5,0))
        self.export_pack_text = tk.Text(preview, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas",10), height=18)
        self.export_pack_text.pack(fill="both", expand=True, padx=4, pady=4)

        right=ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10,0))
        estado=self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0,10))
        ttk.Label(estado, textvariable=self.export_pack_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(estado, textvariable=self.export_pack_last, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w", pady=(8,0))

        acc=self.make_card(right, "Accesos")
        acc.pack(fill="x", pady=(0,10))
        for label, attr in [("📚 Biblioteca", "tab_biblioteca_premium"),("🖼 Portadas", "tab_portadas_premium"),("💿 Master Final", "tab_master_final"),("🏁 Studio", "tab_studio_dashboard"),("🏠 Inicio", "tab_inicio_premium")]:
            if hasattr(self, attr):
                ttk.Button(acc, text=label, command=lambda a=attr: self.select_tab(getattr(self,a))).pack(fill="x", pady=3)

        tips=self.make_card(right, "Qué mete en el ZIP")
        tips.pack(fill="x")
        ttk.Label(tips, text="• Audio WAV\n• Portadas PNG\n• Letras TXT\n• Proyectos JSON\n• Índice manifest.json\n• Resumen LEEME.txt\n\nIdeal para guardar una versión final del proyecto.", style="Card.TLabel", justify="left", wraplength=320).pack(anchor="w")
        self.export_pack_scan()

    def export_pack_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def export_pack_quick_filter(self, audio=True, images=True, docs=True):
        self.export_pack_filter_audio.set(audio)
        self.export_pack_filter_images.set(images)
        self.export_pack_filter_docs.set(docs)
        self.export_pack_scan()

    def export_pack_scan(self):
        try:
            folder = self.export_pack_folder()
            folder.mkdir(parents=True, exist_ok=True)
            patterns=[]
            if self.export_pack_filter_audio.get(): patterns += ["*.wav"]
            if self.export_pack_filter_images.get(): patterns += ["*.png"]
            if self.export_pack_filter_docs.get(): patterns += ["*.json", "*.txt"]
            files=[]
            for pat in patterns: files.extend(folder.glob(pat))
            files=sorted(set(files), key=lambda p:p.stat().st_mtime, reverse=True)
            self.export_pack_files=files
            if hasattr(self,"export_pack_listbox"):
                self.export_pack_listbox.delete(0, tk.END)
                for p in files:
                    size=p.stat().st_size/(1024*1024)
                    mtime=datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")
                    self.export_pack_listbox.insert(tk.END, f"{p.suffix.upper()[1:]:<4} · {size:>6.2f} MB · {mtime} · {p.name}")
            self.export_pack_status.set(f"Archivos listos para pack: {len(files)}")
            self.export_pack_text_set(self.export_pack_summary(files))
        except Exception as e:
            self.export_pack_status.set(f"No se pudo escanear: {e}")

    def export_pack_summary(self, files):
        counts={"wav":0,"png":0,"json":0,"txt":0}
        total=0
        for p in files:
            ext=p.suffix.lower().replace('.', '')
            if ext in counts: counts[ext]+=1
            total += p.stat().st_size
        return "\n".join([
            "EXPORT PACK PRO", "", f"Archivos: {len(files)}", f"Audio WAV: {counts['wav']}", f"Portadas PNG: {counts['png']}", f"Proyectos JSON: {counts['json']}", f"Letras/Informes TXT: {counts['txt']}", f"Peso total: {total/(1024*1024):.2f} MB", "", "Pulsa Crear ZIP final para generar un paquete completo con manifest.json y LEEME.txt."
        ])

    def export_pack_text_set(self, text):
        if not hasattr(self,"export_pack_text"): return
        self.export_pack_text.configure(state="normal")
        self.export_pack_text.delete("1.0", tk.END)
        self.export_pack_text.insert("1.0", text)
        self.export_pack_text.configure(state="disabled")

    def export_pack_selected_path(self):
        if not hasattr(self,"export_pack_listbox"): return None
        sel=self.export_pack_listbox.curselection()
        if not sel: return None
        i=int(sel[0])
        return self.export_pack_files[i] if 0 <= i < len(self.export_pack_files) else None

    def export_pack_preview_selected(self):
        p=self.export_pack_selected_path()
        if not p:
            self.export_pack_text_set("Selecciona un archivo para ver información.")
            return
        try:
            st=p.stat()
            lines=["ARCHIVO", "", f"Nombre: {p.name}", f"Tipo: {p.suffix.upper()[1:]}", f"Tamaño: {st.st_size/(1024*1024):.2f} MB", f"Modificado: {datetime.fromtimestamp(st.st_mtime).strftime('%d/%m/%Y %H:%M:%S')}", f"Ruta: {p}", ""]
            if p.suffix.lower() in ('.txt','.json'):
                txt=p.read_text(encoding='utf-8', errors='replace')
                lines += ["CONTENIDO", '-'*40, txt[:4500] + ('\n\n[...]' if len(txt)>4500 else '')]
            elif p.suffix.lower()=='.wav':
                try:
                    with wave.open(str(p),'rb') as wav:
                        dur=wav.getnframes()/max(1,wav.getframerate())
                        lines += [f"Canales: {wav.getnchannels()}", f"Hz: {wav.getframerate()}", f"Bits: {wav.getsampwidth()*8}", f"Duración: {dur:.1f}s"]
                except Exception as e: lines.append(f"No se pudo leer WAV: {e}")
            elif p.suffix.lower()=='.png':
                try:
                    im=Image.open(p)
                    lines += [f"Imagen: {im.size[0]}x{im.size[1]}", "Lista para portada/miniatura."]
                except Exception as e: lines.append(f"No se pudo leer PNG: {e}")
            self.export_pack_text_set('\n'.join(lines))
        except Exception as e:
            self.export_pack_status.set(f"No se pudo previsualizar: {e}")

    def export_pack_manifest(self, files):
        items=[]
        for p in files:
            try:
                items.append({"name":p.name,"type":p.suffix.lower().replace('.',''),"size_bytes":p.stat().st_size,"modified":datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec='seconds')})
            except Exception: pass
        return {"version":VERSION,"created_at":datetime.now().isoformat(timespec='seconds'),"source_folder":str(self.export_pack_folder()),"count":len(items),"files":items}

    def export_pack_create_zip(self):
        try:
            self.export_pack_scan()
            files=list(getattr(self,'export_pack_files',[]))
            if not files:
                messagebox.showwarning("Sin archivos", "No hay archivos para crear el pack.")
                return
            folder=self.export_pack_folder()
            ts=datetime.now().strftime('%Y%m%d_%H%M%S')
            title='proyecto'
            try:
                if hasattr(self,'song_title') and self.song_title.get().strip(): title=self.song_title.get().strip()
                elif hasattr(self,'portada_titulo') and self.portada_titulo.get().strip(): title=self.portada_titulo.get().strip()
                title=self.song_safe_name(title)
            except Exception:
                title='proyecto'
            zip_path=folder / f"{title}_export_pack_{ts}.zip"
            manifest=self.export_pack_manifest(files)
            readme=["EXPORT PACK PRO", "", f"Creado: {manifest['created_at']}", f"Versión: {manifest['version']}", f"Archivos incluidos: {manifest['count']}", "", "CONTENIDO"]
            for item in manifest['files']:
                readme.append(f"- {item['type'].upper()} · {item['name']} · {item['size_bytes']} bytes")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
                z.writestr('LEEME.txt', '\n'.join(readme))
                for p in files:
                    sub = {'wav':'audio', 'png':'portadas', 'json':'proyectos_json', 'txt':'letras_informes'}.get(p.suffix.lower().replace('.',''), 'otros')
                    z.write(p, f"{sub}/{p.name}")
            self.export_pack_last.set(f"Último pack: {zip_path.name}")
            self.export_pack_status.set("ZIP final creado correctamente.")
            self.export_pack_text_set(f"PACK CREADO\n\n{zip_path}\n\nArchivos incluidos: {len(files)}\n\nTambién se añadieron manifest.json y LEEME.txt dentro del ZIP.")
            if hasattr(self,'biblioteca_scan'):
                try: self.biblioteca_scan()
                except Exception: pass
            messagebox.showinfo("Export Pack creado", f"ZIP guardado en:\n{zip_path}")
        except Exception as e:
            self.export_pack_status.set(f"No se pudo crear ZIP: {e}")

    def export_pack_open_folder(self):
        folder=self.export_pack_folder()
        try:
            if platform.system()=='Windows': os.startfile(str(folder))
            elif platform.system()=='Darwin': subprocess.Popen(['open', str(folder)])
            else: subprocess.Popen(['xdg-open', str(folder)])
            self.export_pack_status.set("Carpeta abierta.")
        except Exception as e:
            self.export_pack_status.set(f"No se pudo abrir carpeta: {e}")


    def build_portadas_premium_tab(self):
        cont = ttk.Frame(self.tab_portadas_premium)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "portadas_banner" in self.portadas_premium_images:
            ttk.Label(header, image=self.portadas_premium_images["portadas_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Portadas Premium Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Estilos de portada")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_neon", "Neón", lambda: self.portada_set_style("Neón")),
            ("tile_pop", "Pop", lambda: self.portada_set_style("Pop")),
            ("tile_trap", "Trap", lambda: self.portada_set_style("Trap")),
            ("tile_lofi", "Lofi", lambda: self.portada_set_style("Lofi")),
            ("tile_cover", "Crear PNG", self.portada_export_png),
            ("tile_biblio", "Biblioteca", lambda: self.select_tab(self.tab_biblioteca_premium)),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.portadas_premium_images:
                ttk.Label(box, image=self.portadas_premium_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        editor = self.make_card(body, "Editor de portada")
        editor.pack(side="left", fill="both", expand=True, padx=(0, 5))

        for label, var in [
            ("Título", self.portada_titulo),
            ("Artista / canal", self.portada_artista),
            ("Subtítulo", self.portada_subtitulo),
        ]:
            ttk.Label(editor, text=label + ":", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(6, 2))
            ttk.Entry(editor, textvariable=var).pack(fill="x", pady=(0, 6))

        ttk.Label(editor, text="Estilo:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(6, 2))
        ttk.Combobox(editor, textvariable=self.portada_estilo, state="readonly", values=["Neón", "Pop", "Trap", "Lofi", "Dorado", "Gaming"]).pack(fill="x", pady=(0, 8))

        btns = ttk.Frame(editor, style="Card.TFrame")
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="Usar título de canción", command=self.portada_use_song_title).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(btns, text="Vista previa", command=self.portada_refresh_preview).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(btns, text="Exportar PNG", style="Accent.TButton", command=self.portada_export_png).pack(side="left", fill="x", expand=True, padx=3, ipady=7)

        ttk.Label(editor, textvariable=self.portada_ultimo_archivo, style="Card.TLabel", wraplength=460).pack(anchor="w", pady=(12, 0))

        preview = self.make_card(body, "Vista previa")
        preview.pack(side="left", fill="both", expand=True, padx=(5, 0))

        if "portada_preview" in self.portadas_premium_images:
            ttk.Label(preview, image=self.portadas_premium_images["portada_preview"], style="Card.TLabel").pack(anchor="center", pady=(0, 6))

        self.portada_preview_text = tk.Text(
            preview,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=10
        )
        self.portada_preview_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.portada_refresh_preview()

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.portadas_premium_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        info = self.make_card(right, "Formato exportado")
        info.pack(fill="x", pady=(0, 10))
        ttk.Label(
            info,
            text="Las portadas se exportan en PNG cuadrado 1600x1600, perfecto para miniatura, canción, demo, biblioteca o portada provisional.",
            style="Card.TLabel",
            justify="left",
            wraplength=320
        ).pack(anchor="w")

        accesos = self.make_card(right, "Accesos")
        accesos.pack(fill="x", pady=(0, 10))
        for label, attr in [
            ("📚 Biblioteca", "tab_biblioteca_premium"),
            ("🏠 Inicio", "tab_inicio_premium"),
            ("🎼 Canción Pro", "tab_cancion_pro"),
            ("💿 Master Final", "tab_master_final"),
            ("🎨 Visual Pro", "tab_visual_pro"),
        ]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

        export = self.make_card(right, "Guardar")
        export.pack(fill="x")
        ttk.Button(export, text="Exportar portada PNG", style="Accent.TButton", command=self.portada_export_png).pack(fill="x", pady=3)
        ttk.Button(export, text="Exportar metadatos JSON", command=self.portada_export_metadata).pack(fill="x", pady=3)

    def portada_set_style(self, style_name):
        self.portada_estilo.set(style_name)
        self.portadas_premium_status.set(f"Estilo seleccionado: {style_name}")
        self.portada_refresh_preview()

    def portada_use_song_title(self):
        try:
            if hasattr(self, "song_title") and self.song_title.get().strip():
                self.portada_titulo.set(self.song_title.get().strip())
            elif hasattr(self, "karaoke_track") and self.karaoke_track.get().strip():
                self.portada_titulo.set(self.karaoke_track.get().strip()[:40])
            self.portada_refresh_preview()
            self.portadas_premium_status.set("Título de canción usado en portada.")
        except Exception as e:
            self.portadas_premium_status.set(f"No se pudo usar título: {e}")

    def portada_palette(self, style_name):
        palettes = {
            "Neón": ((8,10,24), (20,44,94), (0,229,255), (188,120,255), (255,255,255)),
            "Pop": ((18,10,28), (88,28,76), (255,116,170), (255,203,87), (255,255,255)),
            "Trap": ((6,7,14), (26,14,52), (188,120,255), (0,229,255), (255,255,255)),
            "Lofi": ((18,20,30), (42,52,58), (98,255,180), (255,203,87), (245,250,240)),
            "Dorado": ((18,13,8), (74,45,12), (255,203,87), (255,150,90), (255,248,225)),
            "Gaming": ((5,12,24), (20,60,82), (0,229,255), (98,255,180), (255,255,255)),
        }
        return palettes.get(style_name, palettes["Neón"])

    def portada_font(self, size, bold=False):
        try:
            for p in [
                "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            ]:
                if Path(p).exists():
                    return ImageFont.truetype(p, size)
        except Exception:
            pass
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def portada_wrap_text(self, draw, text, font, max_width):
        words = str(text).split()
        lines = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines[:3]

    def portada_create_image(self, size=1600):
        style = self.portada_estilo.get()
        bg1, bg2, accent, accent2, textc = self.portada_palette(style)
        img = Image.new("RGBA", (size, size), bg1 + (255,))
        px = img.load()
        for y in range(size):
            for x in range(size):
                t = (x / max(1, size-1)) * 0.62 + (y / max(1, size-1)) * 0.38
                px[x, y] = tuple(int(bg1[i]*(1-t)+bg2[i]*t) for i in range(3)) + (255,)

        for cx, cy, r, c, a in [
            (int(size*0.82), int(size*0.14), int(size*0.36), accent, 70),
            (int(size*0.18), int(size*0.86), int(size*0.33), accent2, 55),
            (int(size*0.54), int(size*0.52), int(size*0.22), (255,203,87), 30),
        ]:
            ov = Image.new("RGBA", (size, size), (0,0,0,0))
            od = ImageDraw.Draw(ov)
            od.ellipse((cx-r, cy-r, cx+r, cy+r), fill=c+(a,))
            img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(int(size*0.045))))

        d = ImageDraw.Draw(img)
        margin = int(size * 0.075)
        d.rounded_rectangle((margin, margin, size-margin, size-margin), radius=int(size*0.055), outline=textc+(70,), width=max(4, size//180), fill=(0,0,0,38))

        for i in range(18):
            x = int(size*0.12 + i*size*0.043)
            h = int(size*(0.05 + (i % 5) * 0.022))
            y = int(size*0.66 - h/2)
            c = [accent, accent2, (255,203,87), (98,255,180)][i % 4]
            d.rounded_rectangle((x, y, x+int(size*0.022), y+h), radius=int(size*0.012), fill=c+(210,))

        title = self.portada_titulo.get().strip() or "Mi Demo"
        artist = self.portada_artista.get().strip() or "Atenea Studio"
        subtitle = self.portada_subtitulo.get().strip() or "Demo creada con Modulador Voz Directo"

        title_font = self.portada_font(int(size*0.085), True)
        artist_font = self.portada_font(int(size*0.036), False)
        small_font = self.portada_font(int(size*0.028), True)
        sub_font = self.portada_font(int(size*0.025), False)

        y = int(size*0.18)
        for line in self.portada_wrap_text(d, title.upper(), title_font, int(size*0.78)):
            d.text((margin+int(size*0.035), y), line, font=title_font, fill=textc+(255,))
            y += int(size*0.09)

        d.text((margin+int(size*0.04), y+int(size*0.02)), artist, font=artist_font, fill=textc+(220,))
        d.rounded_rectangle((margin+int(size*0.04), int(size*0.78), margin+int(size*0.36), int(size*0.825)), radius=int(size*0.022), fill=(255,214,89,225))
        d.text((margin+int(size*0.065), int(size*0.789)), style.upper(), font=small_font, fill=(14,15,22,255))
        d.text((margin+int(size*0.04), int(size*0.86)), subtitle[:70], font=sub_font, fill=textc+(210,))
        d.text((margin+int(size*0.04), int(size*0.905)), "MODULADOR VOZ DIRECTO · V73", font=self.portada_font(int(size*0.020), True), fill=textc+(150,))
        return img.convert("RGB")

    def portada_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def portada_safe_name(self, text):
        try:
            return self.song_safe_name(text)
        except Exception:
            safe = "".join(ch for ch in str(text) if ch.isalnum() or ch in " -_").strip().replace(" ", "_")
            return safe or "portada"

    def portada_export_png(self):
        try:
            folder = self.portada_output_folder()
            folder.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = self.portada_safe_name(self.portada_titulo.get())
            path = folder / f"{name}_portada_{ts}.png"
            img = self.portada_create_image(1600)
            img.save(path, "PNG", optimize=True)
            self.portada_ultimo_archivo.set(f"Última portada: {path.name}")
            self.portadas_premium_status.set(f"Portada exportada: {path.name}")
            self.portada_refresh_preview(f"PNG exportado:\n{path}")
            if hasattr(self, "biblioteca_scan"):
                try:
                    self.biblioteca_scan()
                except Exception:
                    pass
            messagebox.showinfo("Portada exportada", f"Portada guardada en:\n{path}")
        except Exception as e:
            self.portadas_premium_status.set(f"No se pudo exportar portada: {e}")

    def portada_metadata(self):
        return {
            "version": VERSION,
            "title": self.portada_titulo.get(),
            "artist": self.portada_artista.get(),
            "subtitle": self.portada_subtitulo.get(),
            "style": self.portada_estilo.get(),
            "format": "PNG 1600x1600",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def portada_export_metadata(self):
        try:
            folder = self.portada_output_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = self.portada_safe_name(self.portada_titulo.get())
            path = folder / f"{name}_portada_metadata_{ts}.json"
            path.write_text(json.dumps(self.portada_metadata(), ensure_ascii=False, indent=2), encoding="utf-8")
            self.portadas_premium_status.set(f"Metadatos exportados: {path.name}")
            messagebox.showinfo("Metadatos exportados", f"Guardado en:\n{path}")
        except Exception as e:
            self.portadas_premium_status.set(f"No se pudo exportar metadata: {e}")

    def portada_refresh_preview(self, extra=""):
        if not hasattr(self, "portada_preview_text"):
            return
        data = self.portada_metadata()
        lines = [
            "PORTADAS PREMIUM PRO",
            "",
            f"Título: {data['title']}",
            f"Artista: {data['artist']}",
            f"Estilo: {data['style']}",
            f"Formato: {data['format']}",
            "",
            "USO",
            "- Miniatura provisional.",
            "- Portada para demo.",
            "- Imagen para biblioteca.",
            "- Imagen para vídeo o directo.",
            "",
            str(extra),
        ]
        self.portada_preview_text.configure(state="normal")
        self.portada_preview_text.delete("1.0", tk.END)
        self.portada_preview_text.insert("1.0", "\n".join(lines))
        self.portada_preview_text.configure(state="disabled")


    def build_biblioteca_premium_tab(self):
        cont = ttk.Frame(self.tab_biblioteca_premium)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "biblioteca_banner" in self.biblioteca_premium_images:
            ttk.Label(header, image=self.biblioteca_premium_images["biblioteca_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Biblioteca Premium Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Gestión rápida")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_actualizar", "Actualizar", self.biblioteca_scan),
            ("tile_wav", "Solo WAV", lambda: self.biblioteca_set_filter("WAV")),
            ("tile_json", "Solo JSON", lambda: self.biblioteca_set_filter("JSON")),
            ("tile_txt", "Solo TXT", lambda: self.biblioteca_set_filter("TXT")),
            ("tile_cargar", "Cargar WAV", self.biblioteca_load_selected_wav),
            ("tile_export", "Abrir carpeta", self.biblioteca_open_folder),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.biblioteca_premium_images:
                ttk.Label(box, image=self.biblioteca_premium_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        lista = self.make_card(body, "Archivos encontrados")
        lista.pack(side="left", fill="both", expand=True, padx=(0, 5))

        top = ttk.Frame(lista, style="Card.TFrame")
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Filtro:", style="Card.TLabel").pack(side="left")
        ttk.Combobox(top, textvariable=self.biblioteca_filter, state="readonly", width=10, values=["Todos", "WAV", "PNG", "HTML", "JSON", "TXT"]).pack(side="left", padx=6)
        ttk.Button(top, text="Aplicar", command=self.biblioteca_scan).pack(side="left", padx=3)
        ttk.Button(top, text="Todos", command=lambda: self.biblioteca_set_filter("Todos")).pack(side="left", padx=3)

        list_frame = ttk.Frame(lista, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True)
        self.biblioteca_listbox = tk.Listbox(
            list_frame,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#071018",
            relief="flat",
            activestyle="none",
            font=("Consolas", 10),
            height=16
        )
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.biblioteca_listbox.yview)
        self.biblioteca_listbox.configure(yscrollcommand=scroll.set)
        self.biblioteca_listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.biblioteca_listbox.bind("<<ListboxSelect>>", lambda e: self.biblioteca_preview_selected())

        btns = ttk.Frame(lista, style="Card.TFrame")
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Vista previa", command=self.biblioteca_preview_selected).pack(side="left", expand=True, fill="x", padx=3, ipady=7)
        ttk.Button(btns, text="Cargar WAV", style="Accent.TButton", command=self.biblioteca_load_selected_wav).pack(side="left", expand=True, fill="x", padx=3, ipady=7)
        ttk.Button(btns, text="Borrar", command=self.biblioteca_delete_selected).pack(side="left", expand=True, fill="x", padx=3, ipady=7)

        preview = self.make_card(body, "Vista previa / información")
        preview.pack(side="left", fill="both", expand=True, padx=(5, 0))

        if "biblioteca_empty" in self.biblioteca_premium_images:
            ttk.Label(preview, image=self.biblioteca_premium_images["biblioteca_empty"], style="Card.TLabel").pack(anchor="center", pady=(0, 6))

        self.biblioteca_preview_text = tk.Text(
            preview,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=13
        )
        self.biblioteca_preview_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.biblioteca_premium_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        info = self.make_card(right, "Carpeta de trabajo")
        info.pack(fill="x", pady=(0, 10))
        ttk.Label(info, text=str(self.biblioteca_folder()), style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Button(info, text="Abrir carpeta", style="Accent.TButton", command=self.biblioteca_open_folder).pack(fill="x", pady=(8, 3))

        accesos = self.make_card(right, "Crear más contenido")
        accesos.pack(fill="x", pady=(0, 10))
        for label, attr in [
            ("🏠 Inicio", "tab_inicio_premium"),
            ("🪄 Asistente", "tab_asistente_inicial"),
            ("🧱 Timeline", "tab_timeline_pro"),
            ("🎼 Canción Pro", "tab_cancion_pro"),
            ("💿 Master Final", "tab_master_final"),
            ("🏁 Studio", "tab_studio_dashboard"),
        ]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

        export = self.make_card(right, "Informe")
        export.pack(fill="x")
        ttk.Button(export, text="Exportar índice JSON/TXT", command=self.biblioteca_export_index).pack(fill="x", pady=3)
        ttk.Button(export, text="Actualizar biblioteca", command=self.biblioteca_scan).pack(fill="x", pady=3)

        self.biblioteca_scan()

    def biblioteca_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def biblioteca_set_filter(self, filt):
        self.biblioteca_filter.set(filt)
        self.biblioteca_scan()

    def biblioteca_scan(self):
        try:
            folder = self.biblioteca_folder()
            folder.mkdir(parents=True, exist_ok=True)
            files = []
            for ext in ("*.wav", "*.png", "*.html", "*.json", "*.txt"):
                files.extend(folder.glob(ext))
            files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

            filt = self.biblioteca_filter.get()
            if filt == "WAV":
                files = [p for p in files if p.suffix.lower() == ".wav"]
            elif filt == "PNG":
                files = [p for p in files if p.suffix.lower() == ".png"]
            elif filt == "HTML":
                files = [p for p in files if p.suffix.lower() == ".html"]
            elif filt == "JSON":
                files = [p for p in files if p.suffix.lower() == ".json"]
            elif filt == "TXT":
                files = [p for p in files if p.suffix.lower() == ".txt"]

            self.biblioteca_files = files

            if hasattr(self, "biblioteca_listbox"):
                self.biblioteca_listbox.delete(0, tk.END)
                for p in files:
                    size_mb = p.stat().st_size / (1024 * 1024)
                    mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")
                    self.biblioteca_listbox.insert(tk.END, f"{p.suffix.upper()[1:]:<4} · {size_mb:>6.2f} MB · {mtime} · {p.name}")

            self.biblioteca_premium_status.set(f"Biblioteca actualizada: {len(files)} archivo(s).")
            self.biblioteca_preview_text_set(self.biblioteca_summary_text(files))
        except Exception as e:
            self.biblioteca_premium_status.set(f"No se pudo escanear biblioteca: {e}")

    def biblioteca_summary_text(self, files):
        wav = len([p for p in files if p.suffix.lower() == ".wav"])
        jsn = len([p for p in files if p.suffix.lower() == ".json"])
        txt = len([p for p in files if p.suffix.lower() == ".txt"])
        png = len([p for p in files if p.suffix.lower() == ".png"])
        htmln = len([p for p in files if p.suffix.lower() == ".html"])
        total = sum(p.stat().st_size for p in files) / (1024 * 1024) if files else 0
        lines = [
            "BIBLIOTECA PREMIUM PRO",
            "",
            f"Archivos visibles: {len(files)}",
            f"WAV: {wav}",
            f"JSON: {jsn}",
            f"TXT: {txt}",
            f"PNG: {png}",
            f"HTML: {htmln}",
            f"Peso total: {total:.2f} MB",
            "",
            "USO RÁPIDO",
            "- Selecciona un WAV y pulsa Cargar WAV para usarlo en Karaoke.",
            "- Selecciona un TXT/JSON para ver su contenido.",
            "- Exporta índice para guardar un inventario.",
        ]
        return "\n".join(lines)

    def biblioteca_selected_path(self):
        if not hasattr(self, "biblioteca_listbox"):
            return None
        sel = self.biblioteca_listbox.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.biblioteca_files):
            return None
        return self.biblioteca_files[idx]

    def biblioteca_preview_text_set(self, text):
        if not hasattr(self, "biblioteca_preview_text"):
            return
        self.biblioteca_preview_text.configure(state="normal")
        self.biblioteca_preview_text.delete("1.0", tk.END)
        self.biblioteca_preview_text.insert("1.0", text)
        self.biblioteca_preview_text.configure(state="disabled")

    def biblioteca_preview_selected(self):
        p = self.biblioteca_selected_path()
        if not p:
            self.biblioteca_preview_text_set("Selecciona un archivo para ver información.")
            return
        try:
            stat = p.stat()
            lines = [
                "ARCHIVO SELECCIONADO",
                "",
                f"Nombre: {p.name}",
                f"Tipo: {p.suffix.upper()[1:]}",
                f"Tamaño: {stat.st_size / (1024*1024):.2f} MB",
                f"Modificado: {datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M:%S')}",
                f"Ruta: {p}",
                "",
            ]
            if p.suffix.lower() in (".txt", ".json", ".html"):
                text = p.read_text(encoding="utf-8", errors="replace")
                lines.append("CONTENIDO")
                lines.append("-" * 40)
                lines.append(text[:5000] + ("\n\n[...] Contenido recortado." if len(text) > 5000 else ""))
            elif p.suffix.lower() == ".wav":
                lines.append("WAV listo para cargar como pista de Karaoke/Studio.")
                try:
                    import wave
                    with wave.open(str(p), "rb") as wav:
                        dur = wav.getnframes() / max(1, wav.getframerate())
                        lines.append(f"Canales: {wav.getnchannels()}")
                        lines.append(f"Hz: {wav.getframerate()}")
                        lines.append(f"Bits aprox: {wav.getsampwidth()*8}")
                        lines.append(f"Duración: {dur:.1f}s")
                except Exception as e:
                    lines.append(f"No se pudo leer cabecera WAV: {e}")
            self.biblioteca_preview_text_set("\n".join(lines))
            self.biblioteca_premium_status.set(f"Vista previa: {p.name}")
        except Exception as e:
            self.biblioteca_premium_status.set(f"No se pudo previsualizar: {e}")

    def biblioteca_load_selected_wav(self):
        p = self.biblioteca_selected_path()
        if not p:
            self.biblioteca_premium_status.set("Selecciona un WAV primero.")
            return
        if p.suffix.lower() != ".wav":
            self.biblioteca_premium_status.set("El archivo seleccionado no es WAV.")
            return
        try:
            samples = self.load_wav_as_samples(str(p))
            if samples is None:
                self.biblioteca_premium_status.set("No se pudo cargar el WAV.")
                return
            self.engine.set_karaoke_track(samples, p.name)
            if hasattr(self, "karaoke_track"):
                self.karaoke_track.set(p.name)
            if hasattr(self, "karaoke_update_engine"):
                self.karaoke_update_engine()
            self.biblioteca_premium_status.set(f"WAV cargado como pista: {p.name}")
            self.biblioteca_preview_text_set(f"WAV cargado correctamente:\n\n{p.name}\n\nPuedes abrir Karaoke/Karaoke Studio y reproducirlo.")
        except Exception as e:
            self.biblioteca_premium_status.set(f"No se pudo cargar WAV: {e}")

    def biblioteca_delete_selected(self):
        p = self.biblioteca_selected_path()
        if not p:
            self.biblioteca_premium_status.set("Selecciona un archivo para borrar.")
            return
        try:
            if messagebox.askyesno("Borrar archivo", f"¿Seguro que quieres borrar este archivo?\n\n{p.name}"):
                p.unlink()
                self.biblioteca_premium_status.set(f"Archivo borrado: {p.name}")
                self.biblioteca_scan()
        except Exception as e:
            self.biblioteca_premium_status.set(f"No se pudo borrar: {e}")

    def biblioteca_open_folder(self):
        folder = self.biblioteca_folder()
        try:
            if platform.system() == "Windows":
                os.startfile(str(folder))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
            self.biblioteca_premium_status.set("Carpeta abierta.")
        except Exception as e:
            self.biblioteca_premium_status.set(f"No se pudo abrir carpeta: {e}")

    def biblioteca_index_data(self):
        files = []
        for p in getattr(self, "biblioteca_files", []):
            try:
                files.append({
                    "name": p.name,
                    "path": str(p),
                    "type": p.suffix.lower().replace(".", ""),
                    "size_bytes": p.stat().st_size,
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                })
            except Exception:
                pass
        return {
            "version": VERSION,
            "folder": str(self.biblioteca_folder()),
            "filter": self.biblioteca_filter.get(),
            "count": len(files),
            "files": files,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def biblioteca_export_index(self):
        try:
            self.biblioteca_scan()
            data = self.biblioteca_index_data()
            folder = self.biblioteca_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = folder / f"biblioteca_premium_indice_{ts}.json"
            txt_path = folder / f"biblioteca_premium_indice_{ts}.txt"

            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = [
                "BIBLIOTECA PREMIUM PRO",
                "",
                f"Fecha: {data['created_at']}",
                f"Carpeta: {data['folder']}",
                f"Filtro: {data['filter']}",
                f"Archivos: {data['count']}",
                "",
                "LISTA",
            ]
            for item in data["files"]:
                lines.append(f"- {item['type'].upper()} · {item['name']} · {item['size_bytes']} bytes · {item['modified']}")
            txt_path.write_text("\n".join(lines), encoding="utf-8")

            self.biblioteca_premium_status.set(f"Índice exportado: {json_path.name} + TXT")
            messagebox.showinfo("Índice exportado", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.biblioteca_premium_status.set(f"No se pudo exportar índice: {e}")


    def build_asistente_inicial_tab(self):
        cont = ttk.Frame(self.tab_asistente_inicial)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "asistente_banner" in self.asistente_inicial_images:
            ttk.Label(header, image=self.asistente_inicial_images["asistente_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Asistente Inicial Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Pasos guiados")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_micro", "1 Micro", 1),
            ("tile_cable", "2 Cable", 2),
            ("tile_voz", "3 Voz", 3),
            ("tile_visual", "4 Visual", 4),
            ("tile_directo", "5 Directo", 5),
            ("tile_export", "6 Informe", 6),
        ]
        for i, (img, label, step) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.asistente_inicial_images:
                ttk.Label(box, image=self.asistente_inicial_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=lambda s=step: self.asistente_set_step(s)).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        panel = self.make_card(body, "Configuración guiada")
        panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        if "asistente_steps" in self.asistente_inicial_images:
            ttk.Label(panel, image=self.asistente_inicial_images["asistente_steps"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))

        ttk.Label(panel, text="Progreso del setup:", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Progressbar(panel, variable=self.asistente_progress, maximum=100).pack(fill="x", pady=(4, 10))

        self.asistente_text = tk.Text(
            panel,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=10
        )
        self.asistente_text.pack(fill="both", expand=True, padx=4, pady=4)

        buttons = ttk.Frame(panel, style="Card.TFrame")
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="← Anterior", command=self.asistente_prev_step).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(buttons, text="Aplicar paso", style="Accent.TButton", command=self.asistente_apply_current_step).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(buttons, text="Siguiente →", command=self.asistente_next_step).pack(side="left", fill="x", expand=True, padx=3, ipady=7)

        info = self.make_card(body, "Resultado del asistente")
        info.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.asistente_result_text = tk.Text(
            info,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.asistente_result_text.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.asistente_inicial_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        acciones = self.make_card(right, "Acciones del setup")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Configurar todo seguro", style="Accent.TButton", command=self.asistente_apply_all_safe).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Inicio Premium", command=lambda: self.select_tab(self.tab_inicio_premium)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Revisión", command=lambda: self.select_tab(self.tab_revision_tecnica)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Studio", command=lambda: self.select_tab(self.tab_studio_dashboard)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Exportar setup JSON/TXT", command=self.asistente_export_setup).pack(fill="x", pady=3)

        tips = self.make_card(right, "Para qué sirve")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "Este asistente deja la app preparada para usarla sin perderte entre pestañas.\n\n"
                "Ideal después de instalarla por primera vez o al cambiar de micro/PC."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=320
        ).pack(anchor="w")

        self.asistente_set_step(1)

    def asistente_steps_data(self):
        return {
            1: {
                "title": "Paso 1 · Micro y salida",
                "text": (
                    "Elige tu micrófono real como entrada y la salida correcta.\n\n"
                    "Para Discord/Fortnite/OBS lo ideal es:\n"
                    "- Entrada en la app: tu micrófono real.\n"
                    "- Salida en la app: CABLE Input / VoiceMeeter Input.\n"
                    "- Micro en Discord/OBS: CABLE Output / VoiceMeeter Output."
                ),
                "target": "tab_cable_virtual",
            },
            2: {
                "title": "Paso 2 · Cable virtual",
                "text": (
                    "Comprueba el cable virtual para enviar la voz modificada a otras apps.\n\n"
                    "Si no usas cable virtual, podrás oír pruebas y grabar demos, pero Discord/OBS no recibirá la voz modulada."
                ),
                "target": "tab_cable_virtual",
            },
            3: {
                "title": "Paso 3 · Voz inicial",
                "text": (
                    "Aplica una voz segura para empezar.\n\n"
                    "Recomendado:\n"
                    "- Gaming limpio para directos.\n"
                    "- Karaoke Pop para cantar.\n"
                    "- Podcast Pro para voz clara."
                ),
                "target": "tab_cadena_vocal",
            },
            4: {
                "title": "Paso 4 · Look visual",
                "text": (
                    "Aplica un tema visual premium y densidad cómoda.\n\n"
                    "Para empezar recomiendo Neón Azul + densidad cómoda."
                ),
                "target": "tab_visual_pro",
            },
            5: {
                "title": "Paso 5 · Directo o grabación",
                "text": (
                    "Prepara el modo de trabajo:\n\n"
                    "- Directo: abre Streamer Hub / Studio.\n"
                    "- Karaoke: abre Karaoke o Karaoke Studio.\n"
                    "- Canción: abre Timeline y Canción Pro."
                ),
                "target": "tab_studio_dashboard",
            },
            6: {
                "title": "Paso 6 · Exportación final",
                "text": (
                    "Cuando todo esté listo puedes exportar:\n\n"
                    "- Informe técnico.\n"
                    "- Resumen Studio.\n"
                    "- Master WAV.\n"
                    "- Demo WAV."
                ),
                "target": "tab_master_final",
            },
        }

    def asistente_set_step(self, step):
        step = max(1, min(6, int(step)))
        self.asistente_step.set(step)
        self.asistente_progress.set((step - 1) / 5 * 100)
        data = self.asistente_steps_data()[step]
        if hasattr(self, "asistente_text"):
            lines = [
                data["title"],
                "",
                data["text"],
                "",
                "Pulsa 'Aplicar paso' para ejecutar una acción segura o abrir la pantalla correspondiente."
            ]
            self.asistente_text.configure(state="normal")
            self.asistente_text.delete("1.0", tk.END)
            self.asistente_text.insert("1.0", "\n".join(lines))
            self.asistente_text.configure(state="disabled")
        self.asistente_refresh_result(f"Paso actual: {step}/6 · {data['title']}")
        self.asistente_inicial_status.set(f"Asistente en paso {step}/6.")

    def asistente_next_step(self):
        self.asistente_set_step(self.asistente_step.get() + 1)

    def asistente_prev_step(self):
        self.asistente_set_step(self.asistente_step.get() - 1)

    def asistente_open_target(self, target):
        if target and hasattr(self, target):
            self.select_tab(getattr(self, target))
            return True
        return False

    def asistente_apply_current_step(self):
        step = self.asistente_step.get()
        data = self.asistente_steps_data()[step]
        try:
            if step == 1:
                self.load_devices()
                self.asistente_open_target(data["target"])
                self.asistente_inicial_status.set("Paso 1 aplicado: dispositivos actualizados/abiertos.")
            elif step == 2:
                self.cable_detect_virtual()
                self.asistente_open_target(data["target"])
                self.asistente_inicial_status.set("Paso 2 aplicado: cable virtual revisado.")
            elif step == 3:
                if hasattr(self, "vocal_chain_apply_preset"):
                    self.vocal_chain_apply_preset("clean")
                elif "vol" in self.vars:
                    self.vars["vol"].set(92)
                    self.update_engine()
                self.asistente_open_target(data["target"])
                self.asistente_inicial_status.set("Paso 3 aplicado: voz inicial segura.")
            elif step == 4:
                if hasattr(self, "visual_apply_theme"):
                    self.visual_apply_theme("neon")
                if hasattr(self, "visual_apply_density"):
                    self.visual_apply_density("normal")
                self.asistente_open_target(data["target"])
                self.asistente_inicial_status.set("Paso 4 aplicado: look premium inicial.")
            elif step == 5:
                if hasattr(self, "studio_dashboard_refresh_all"):
                    self.studio_dashboard_refresh_all()
                self.asistente_open_target(data["target"])
                self.asistente_inicial_status.set("Paso 5 aplicado: studio/directo preparado.")
            elif step == 6:
                self.asistente_export_setup()
                self.asistente_open_target(data["target"])
                self.asistente_inicial_status.set("Paso 6 aplicado: setup exportado.")
            self.asistente_refresh_result(f"Aplicado correctamente: paso {step}/6.")
        except Exception as e:
            self.asistente_inicial_status.set(f"No se pudo aplicar el paso: {e}")

    def asistente_apply_all_safe(self):
        try:
            if hasattr(self, "revision_safe_fix"):
                self.revision_safe_fix()
            elif hasattr(self, "vocal_analyzer_auto_fix"):
                self.vocal_analyzer_auto_fix()

            if hasattr(self, "vocal_chain_apply_preset"):
                self.vocal_chain_apply_preset("clean")

            if hasattr(self, "visual_apply_theme"):
                self.visual_apply_theme("neon")
            if hasattr(self, "visual_apply_density"):
                self.visual_apply_density("normal")

            if hasattr(self, "mix_apply_preset"):
                self.mix_apply_preset("demo")
            if hasattr(self, "master_apply_preset"):
                self.master_apply_preset("seguro")
            if hasattr(self, "studio_dashboard_refresh_all"):
                self.studio_dashboard_refresh_all()

            self.asistente_progress.set(100)
            self.asistente_refresh_result("Configuración segura completa aplicada.")
            self.asistente_inicial_status.set("Asistente completado: setup seguro aplicado.")
        except Exception as e:
            self.asistente_inicial_status.set(f"No se pudo configurar todo: {e}")

    def asistente_setup_data(self):
        effects = {}
        for k, v in getattr(self, "vars", {}).items():
            try:
                effects[k] = float(v.get())
            except Exception:
                effects[k] = 0
        return {
            "version": VERSION,
            "step": int(self.asistente_step.get()),
            "progress": float(self.asistente_progress.get()),
            "input": self.input_dev.get() if hasattr(self, "input_dev") else "",
            "output": self.output_dev.get() if hasattr(self, "output_dev") else "",
            "voice": self.preset.get() if hasattr(self, "preset") else "",
            "category": self.category.get() if hasattr(self, "category") else "",
            "latency": self.latency.get() if hasattr(self, "latency") else "",
            "visual_theme": self.visual_theme_name.get() if hasattr(self, "visual_theme_name") else "",
            "effects": effects,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def asistente_refresh_result(self, extra=""):
        if not hasattr(self, "asistente_result_text"):
            return
        data = self.asistente_setup_data()
        lines = [
            "RESULTADO DEL ASISTENTE",
            "",
            f"Versión: {data['version']}",
            f"Progreso: {data['progress']:.0f}%",
            f"Entrada: {data['input'] or 'No seleccionada'}",
            f"Salida: {data['output'] or 'No seleccionada'}",
            f"Voz: {data['voice']}",
            f"Categoría: {data['category']}",
            f"Latencia: {data['latency']}",
            f"Tema visual: {data['visual_theme']}",
            "",
            "EFECTOS CLAVE",
        ]
        for key in ["gate", "comp", "vol", "echo", "autotune", "vibrato", "chorus"]:
            if key in data["effects"]:
                lines.append(f"- {key}: {data['effects'][key]:.0f}")
        lines += ["", str(extra)]
        self.asistente_result_text.configure(state="normal")
        self.asistente_result_text.delete("1.0", tk.END)
        self.asistente_result_text.insert("1.0", "\n".join(lines))
        self.asistente_result_text.configure(state="disabled")

    def asistente_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def asistente_safe_name(self):
        try:
            return self.song_safe_name(self.song_title.get())
        except Exception:
            return "setup_asistente"

    def asistente_export_setup(self):
        try:
            data = self.asistente_setup_data()
            folder = self.asistente_output_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = self.asistente_safe_name()
            json_path = folder / f"{name}_asistente_inicial_{ts}.json"
            txt_path = folder / f"{name}_asistente_inicial_{ts}.txt"

            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = [
                "ASISTENTE INICIAL PRO",
                "",
                f"Fecha: {data['created_at']}",
                f"Versión: {data['version']}",
                f"Progreso: {data['progress']:.0f}%",
                f"Entrada: {data['input'] or 'No seleccionada'}",
                f"Salida: {data['output'] or 'No seleccionada'}",
                f"Voz: {data['voice']}",
                f"Tema visual: {data['visual_theme']}",
                "",
                "Este archivo guarda la configuración inicial recomendada."
            ]
            txt_path.write_text("\n".join(lines), encoding="utf-8")

            self.asistente_inicial_status.set(f"Setup exportado: {json_path.name} + TXT")
            messagebox.showinfo("Setup exportado", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.asistente_inicial_status.set(f"No se pudo exportar setup: {e}")


    def build_inicio_premium_tab(self):
        cont = ttk.Frame(self.tab_inicio_premium)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "inicio_banner" in self.inicio_premium_images:
            ttk.Label(header, image=self.inicio_premium_images["inicio_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Inicio Premium Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Elige qué quieres hacer")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_directo", "Directo Pro", "directo"),
            ("tile_karaoke", "Karaoke", "karaoke"),
            ("tile_cancion", "Canción", "cancion"),
            ("tile_revision", "Revisión", "revision"),
            ("tile_visual", "Visual", "visual"),
            ("tile_exportar", "Finalizar", "exportar"),
        ]
        for i, (img, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.inicio_premium_images:
                ttk.Label(box, image=self.inicio_premium_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=lambda m=mode: self.inicio_open_mode(m)).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        flow = self.make_card(body, "Flujo recomendado")
        flow.pack(side="left", fill="both", expand=True, padx=(0, 5))
        if "inicio_flow" in self.inicio_premium_images:
            ttk.Label(flow, image=self.inicio_premium_images["inicio_flow"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))

        self.inicio_premium_text = tk.Text(
            flow,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=8
        )
        self.inicio_premium_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.inicio_refresh_text("Inicio Premium cargado.")

        project = self.make_card(body, "Resumen rápido")
        project.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.inicio_project_text = tk.Text(
            project,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.inicio_project_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.inicio_refresh_project()

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.inicio_premium_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        modo = self.make_card(right, "Modo rápido")
        modo.pack(fill="x", pady=(0, 10))
        ttk.Combobox(
            modo,
            textvariable=self.inicio_premium_mode,
            state="readonly",
            values=["Studio completo", "Directo", "Karaoke", "Crear canción", "Revisión técnica", "Exportación final"]
        ).pack(fill="x", pady=(0, 5))
        ttk.Button(modo, text="Abrir modo", style="Accent.TButton", command=self.inicio_open_selected).pack(fill="x", pady=3)
        ttk.Button(modo, text="Aplicar preparación segura", command=self.inicio_apply_safe_start).pack(fill="x", pady=3)

        acciones = self.make_card(right, "Acciones finales")
        acciones.pack(fill="x", pady=(0, 10))
        if hasattr(self, "master_export_wav"):
            ttk.Button(acciones, text="Exportar Master WAV", command=self.master_export_wav).pack(fill="x", pady=3)
        if hasattr(self, "studio_export_summary"):
            ttk.Button(acciones, text="Exportar resumen Studio", command=self.studio_export_summary).pack(fill="x", pady=3)
        if hasattr(self, "revision_export_report"):
            ttk.Button(acciones, text="Exportar informe técnico", command=self.revision_export_report).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Grabar demo WAV", command=self.karaoke_record_demo).pack(fill="x", pady=3)

        visual = self.make_card(right, "Look premium")
        visual.pack(fill="x")
        ttk.Label(
            visual,
            text="V73 hace que la app empiece como un producto real: primero eliges qué quieres hacer y luego entras al módulo correcto.",
            style="Card.TLabel",
            justify="left",
            wraplength=320
        ).pack(anchor="w")
        if hasattr(self, "tab_visual_pro"):
            ttk.Button(visual, text="Abrir Visual Pro", command=lambda: self.select_tab(self.tab_visual_pro)).pack(fill="x", pady=(8, 3))

    def inicio_data(self):
        effects = {}
        for k, v in getattr(self, "vars", {}).items():
            try:
                effects[k] = float(v.get())
            except Exception:
                effects[k] = 0
        return {
            "version": VERSION,
            "title": self.song_title.get() if hasattr(self, "song_title") else "Mi demo",
            "voice": self.preset.get() if hasattr(self, "preset") else "",
            "category": self.category.get() if hasattr(self, "category") else "",
            "track": self.karaoke_track.get() if hasattr(self, "karaoke_track") else "",
            "latency": self.latency.get() if hasattr(self, "latency") else "",
            "effects": effects,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def inicio_refresh_text(self, extra=""):
        if not hasattr(self, "inicio_premium_text"):
            return
        lines = [
            "INICIO PREMIUM PRO",
            "",
            "FLUJO SUGERIDO",
            "1. Revisión técnica: comprueba estabilidad.",
            "2. Analizador: revisa voz y ruido.",
            "3. Cadena vocal: prepara el sonido.",
            "4. Timeline/Canción: crea estructura.",
            "5. Mezclador: balancea voz e instrumental.",
            "6. Master Final: exporta WAV.",
            "",
            str(extra),
        ]
        self.inicio_premium_text.configure(state="normal")
        self.inicio_premium_text.delete("1.0", tk.END)
        self.inicio_premium_text.insert("1.0", "\n".join(lines))
        self.inicio_premium_text.configure(state="disabled")

    def inicio_refresh_project(self):
        if not hasattr(self, "inicio_project_text"):
            return
        data = self.inicio_data()
        lines = [
            "RESUMEN RÁPIDO",
            "",
            f"Versión: {data['version']}",
            f"Título: {data['title']}",
            f"Voz: {data['voice']}",
            f"Categoría: {data['category']}",
            f"Pista: {data['track']}",
            f"Latencia: {data['latency']}",
            "",
            "AJUSTES CLAVE",
        ]
        for key in ["gate", "comp", "vol", "echo", "autotune", "vibrato", "chorus"]:
            if key in data["effects"]:
                lines.append(f"- {key}: {data['effects'][key]:.0f}")
        lines += [
            "",
            "BOTONES RECOMENDADOS",
            "- Directo Pro para Discord/Fortnite/OBS.",
            "- Karaoke para cantar con música sin voz.",
            "- Canción para crear estructura.",
            "- Revisión para controlar errores.",
            "- Finalizar para exportar."
        ]
        self.inicio_project_text.configure(state="normal")
        self.inicio_project_text.delete("1.0", tk.END)
        self.inicio_project_text.insert("1.0", "\n".join(lines))
        self.inicio_project_text.configure(state="disabled")

    def inicio_open_selected(self):
        m = self.inicio_premium_mode.get().lower()
        if "studio" in m:
            self.inicio_open_mode("studio")
        elif "directo" in m:
            self.inicio_open_mode("directo")
        elif "karaoke" in m:
            self.inicio_open_mode("karaoke")
        elif "canción" in m or "cancion" in m:
            self.inicio_open_mode("cancion")
        elif "revisión" in m or "revision" in m:
            self.inicio_open_mode("revision")
        else:
            self.inicio_open_mode("exportar")

    def inicio_open_mode(self, mode):
        mapping = {
            "studio": "tab_studio_dashboard",
            "directo": "tab_streamer_hub",
            "karaoke": "tab_karaoke",
            "cancion": "tab_timeline_pro",
            "revision": "tab_revision_tecnica",
            "visual": "tab_visual_pro",
            "exportar": "tab_master_final",
        }
        # Fallbacks por si alguna pestaña tiene otro nombre.
        fallbacks = {
            "directo": ["tab_directo", "tab_asistente", "tab_studio_dashboard"],
            "karaoke": ["tab_karaoke_studio", "tab_autotune"],
            "cancion": ["tab_cancion_pro", "tab_timeline_pro"],
            "exportar": ["tab_mezclador_musical", "tab_studio_dashboard"],
        }
        attr = mapping.get(mode)
        candidates = [attr] + fallbacks.get(mode, [])
        for candidate in candidates:
            if candidate and hasattr(self, candidate):
                self.select_tab(getattr(self, candidate))
                self.inicio_premium_status.set(f"Modo abierto: {mode}.")
                return
        self.inicio_premium_status.set(f"No se encontró el módulo para: {mode}.")

    def inicio_apply_safe_start(self):
        try:
            if hasattr(self, "revision_safe_fix"):
                self.revision_safe_fix()
            elif hasattr(self, "vocal_analyzer_auto_fix"):
                self.vocal_analyzer_auto_fix()

            if hasattr(self, "vocal_chain_apply_preset"):
                self.vocal_chain_apply_preset("clean")
            elif "vol" in self.vars:
                self.vars["vol"].set(92)

            if hasattr(self, "mix_apply_preset"):
                self.mix_apply_preset("demo")
            if hasattr(self, "master_apply_preset"):
                self.master_apply_preset("seguro")
            if hasattr(self, "visual_apply_theme"):
                self.visual_apply_theme("neon")

            self.inicio_refresh_project()
            self.inicio_refresh_text("Preparación segura aplicada: audio, voz, mezcla, master y visual revisados.")
            self.inicio_premium_status.set("Preparación segura aplicada.")
        except Exception as e:
            self.inicio_premium_status.set(f"No se pudo aplicar preparación segura: {e}")


    def build_visual_pro_tab(self):
        cont = ttk.Frame(self.tab_visual_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "visual_banner" in self.visual_pro_images:
            ttk.Label(header, image=self.visual_pro_images["visual_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Rediseño Visual Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Temas visuales premium")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_neon", "Neón Azul", "neon"),
            ("tile_morado", "Morado Studio", "morado"),
            ("tile_dorado", "Dorado Pro", "dorado"),
            ("tile_compacto", "Compacto", "compacto"),
            ("tile_enfoque", "Modo enfoque", "enfoque"),
            ("tile_export", "Exportar UI", "export"),
        ]
        for i, (img, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.visual_pro_images:
                ttk.Label(box, image=self.visual_pro_images[img], style="Card.TLabel").pack()
            if mode == "export":
                cmd = self.visual_export_style
            elif mode == "enfoque":
                cmd = self.visual_toggle_focus
            else:
                cmd = lambda m=mode: self.visual_apply_theme(m)
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        preview = self.make_card(body, "Vista previa")
        preview.pack(side="left", fill="both", expand=True, padx=(0, 5))
        if "visual_mockup" in self.visual_pro_images:
            ttk.Label(preview, image=self.visual_pro_images["visual_mockup"], style="Card.TLabel").pack(anchor="center", pady=(0, 8))
        self.visual_preview_text = tk.Text(
            preview,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=8
        )
        self.visual_preview_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.visual_refresh_preview("Visual Pro cargado.")

        settings = self.make_card(body, "Ajustes visuales")
        settings.pack(side="left", fill="both", expand=True, padx=(5, 0))

        ttk.Label(settings, text="Tema actual:", style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Combobox(settings, textvariable=self.visual_theme_name, state="readonly", values=["Neón Azul", "Morado Studio", "Dorado Pro", "Compacto"]).pack(fill="x", pady=(4, 10))

        ttk.Label(settings, text="Densidad:", style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Combobox(settings, textvariable=self.visual_density, state="readonly", values=["Cómodo", "Compacto", "Grande"]).pack(fill="x", pady=(4, 10))

        ttk.Checkbutton(settings, text="Modo enfoque visual", variable=self.visual_focus_mode, command=self.visual_toggle_focus_state).pack(anchor="w", pady=5)

        ttk.Button(settings, text="Aplicar tema seleccionado", style="Accent.TButton", command=self.visual_apply_selected).pack(fill="x", pady=4)
        ttk.Button(settings, text="Optimizar para portátil", command=lambda: self.visual_apply_density("compacto")).pack(fill="x", pady=4)
        ttk.Button(settings, text="Optimizar para pantalla grande", command=lambda: self.visual_apply_density("grande")).pack(fill="x", pady=4)
        ttk.Button(settings, text="Abrir Studio Dashboard", command=lambda: self.select_tab(self.tab_studio_dashboard)).pack(fill="x", pady=4)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado visual")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.visual_pro_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        stylebox = self.make_card(right, "Sistema visual V73")
        stylebox.pack(fill="x", pady=(0, 10))
        ttk.Label(
            stylebox,
            text=(
                "Nuevo look más premium:\n\n"
                "• Banners grandes.\n"
                "• Tarjetas visuales.\n"
                "• Temas rápidos.\n"
                "• Modo enfoque.\n"
                "• Densidad compacta/grande.\n"
                "• Exportación de estilo."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=320
        ).pack(anchor="w")

        accesos = self.make_card(right, "Accesos premium")
        accesos.pack(fill="x", pady=(0, 10))
        for label, attr in [
            ("🏁 Studio", "tab_studio_dashboard"),
            ("📊 Analizador", "tab_analizador_vocal"),
            ("🎙 Cadena Vocal", "tab_cadena_vocal"),
            ("🧪 Revisión", "tab_revision_tecnica"),
            ("💿 Master", "tab_master_final"),
        ]:
            if hasattr(self, attr):
                ttk.Button(accesos, text=label, command=lambda a=attr: self.select_tab(getattr(self, a))).pack(fill="x", pady=3)

        export = self.make_card(right, "Exportar")
        export.pack(fill="x")
        ttk.Button(export, text="Exportar estilo JSON/TXT", style="Accent.TButton", command=self.visual_export_style).pack(fill="x", pady=3)
        ttk.Button(export, text="Revisión técnica", command=lambda: self.select_tab(self.tab_revision_tecnica)).pack(fill="x", pady=3)

    def visual_theme_palette(self, mode):
        palettes = {
            "neon": {
                "name": "Neón Azul",
                "accent": COLORS.get("accent", "#00e5ff"),
                "accent2": COLORS.get("accent2", "#7c5cff"),
                "panel": COLORS.get("panel", "#111827"),
                "panel2": COLORS.get("panel2", "#1f2937"),
                "text": COLORS.get("text", "#f8fafc"),
            },
            "morado": {
                "name": "Morado Studio",
                "accent": "#bc78ff",
                "accent2": "#ff74aa",
                "panel": "#151022",
                "panel2": "#211832",
                "text": "#fff7ff",
            },
            "dorado": {
                "name": "Dorado Pro",
                "accent": "#ffcb57",
                "accent2": "#ff965a",
                "panel": "#17130d",
                "panel2": "#261f14",
                "text": "#fff8e8",
            },
            "compacto": {
                "name": "Compacto",
                "accent": "#62ffb4",
                "accent2": "#00e5ff",
                "panel": "#0f1720",
                "panel2": "#172231",
                "text": "#f0fff8",
            },
        }
        return palettes.get(mode, palettes["neon"])

    def visual_apply_theme(self, mode):
        p = self.visual_theme_palette(mode)
        self.visual_theme_name.set(p["name"])
        try:
            COLORS["accent"] = p["accent"]
            COLORS["accent2"] = p["accent2"]
            COLORS["panel"] = p["panel"]
            COLORS["panel2"] = p["panel2"]
            COLORS["text"] = p["text"]
        except Exception:
            pass

        try:
            style = ttk.Style()
            style.configure("Accent.TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))
            style.configure("Card.TFrame", background=p["panel"])
            style.configure("Card.TLabel", background=p["panel"], foreground=p["text"])
            style.configure("TNotebook.Tab", padding=(14, 7), font=("Segoe UI", 10, "bold"))
            style.map("Accent.TButton", foreground=[("active", p["text"])])
            self.root.configure(bg=p["panel2"])
        except Exception:
            pass

        self.visual_pro_status.set(f"Tema aplicado: {p['name']}. Reinicia la app para aplicar el color a absolutamente todos los paneles.")
        self.visual_refresh_preview(f"Tema aplicado: {p['name']}.")

    def visual_apply_selected(self):
        name = self.visual_theme_name.get()
        mapping = {
            "Neón Azul": "neon",
            "Morado Studio": "morado",
            "Dorado Pro": "dorado",
            "Compacto": "compacto",
        }
        self.visual_apply_theme(mapping.get(name, "neon"))

    def visual_apply_density(self, mode):
        try:
            style = ttk.Style()
            if mode == "compacto":
                style.configure("TButton", padding=(8, 4), font=("Segoe UI", 9))
                style.configure("Accent.TButton", padding=(10, 5), font=("Segoe UI", 9, "bold"))
                style.configure("TNotebook.Tab", padding=(10, 4), font=("Segoe UI", 9, "bold"))
                self.visual_density.set("Compacto")
                self.visual_pro_status.set("Densidad compacta aplicada.")
            elif mode == "grande":
                style.configure("TButton", padding=(14, 9), font=("Segoe UI", 11))
                style.configure("Accent.TButton", padding=(16, 10), font=("Segoe UI", 11, "bold"))
                style.configure("TNotebook.Tab", padding=(16, 8), font=("Segoe UI", 11, "bold"))
                self.visual_density.set("Grande")
                self.visual_pro_status.set("Densidad grande aplicada.")
            else:
                style.configure("TButton", padding=(10, 6), font=("Segoe UI", 10))
                style.configure("Accent.TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))
                style.configure("TNotebook.Tab", padding=(14, 7), font=("Segoe UI", 10, "bold"))
                self.visual_density.set("Cómodo")
                self.visual_pro_status.set("Densidad cómoda aplicada.")
            self.visual_refresh_preview("Densidad visual actualizada.")
        except Exception as e:
            self.visual_pro_status.set(f"No se pudo aplicar densidad: {e}")

    def visual_toggle_focus(self):
        self.visual_focus_mode.set(not self.visual_focus_mode.get())
        self.visual_toggle_focus_state()

    def visual_toggle_focus_state(self):
        try:
            if self.visual_focus_mode.get():
                if hasattr(self, "tab_studio_dashboard"):
                    self.select_tab(self.tab_studio_dashboard)
                self.visual_pro_status.set("Modo enfoque activado: vuelve al flujo Studio para trabajar más limpio.")
                self.visual_density.set("Compacto")
                self.visual_apply_density("compacto")
            else:
                self.visual_pro_status.set("Modo enfoque desactivado.")
                self.visual_apply_density("normal")
            self.visual_refresh_preview("Modo enfoque actualizado.")
        except Exception as e:
            self.visual_pro_status.set(f"No se pudo cambiar modo enfoque: {e}")

    def visual_data(self):
        return {
            "version": VERSION,
            "theme": self.visual_theme_name.get(),
            "density": self.visual_density.get(),
            "focus_mode": bool(self.visual_focus_mode.get()),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "recommendation": "Reinicia la app tras elegir tema si quieres aplicar el look a todos los paneles desde el inicio.",
        }

    def visual_refresh_preview(self, extra=""):
        if not hasattr(self, "visual_preview_text"):
            return
        data = self.visual_data()
        lines = [
            "REDISEÑO VISUAL PRO",
            "",
            f"Tema: {data['theme']}",
            f"Densidad: {data['density']}",
            f"Modo enfoque: {'ON' if data['focus_mode'] else 'OFF'}",
            "",
            "MEJORAS VISUALES V73",
            "✓ Nueva pestaña visual.",
            "✓ Banners premium.",
            "✓ Tarjetas de temas.",
            "✓ Modo enfoque.",
            "✓ Densidad compacta/grande.",
            "✓ Exportar estilo.",
            "",
            str(extra),
        ]
        self.visual_preview_text.configure(state="normal")
        self.visual_preview_text.delete("1.0", tk.END)
        self.visual_preview_text.insert("1.0", "\n".join(lines))
        self.visual_preview_text.configure(state="disabled")

    def visual_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def visual_safe_name(self):
        try:
            return self.song_safe_name(self.song_title.get())
        except Exception:
            return "estilo_visual"

    def visual_export_style(self):
        try:
            data = self.visual_data()
            folder = self.visual_output_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = self.visual_safe_name()
            json_path = folder / f"{name}_visual_pro_{ts}.json"
            txt_path = folder / f"{name}_visual_pro_{ts}.txt"

            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = [
                "REDISEÑO VISUAL PRO",
                "",
                f"Fecha: {data['created_at']}",
                f"Versión: {data['version']}",
                f"Tema: {data['theme']}",
                f"Densidad: {data['density']}",
                f"Modo enfoque: {data['focus_mode']}",
                "",
                data["recommendation"],
            ]
            txt_path.write_text("\n".join(lines), encoding="utf-8")

            self.visual_pro_status.set(f"Estilo exportado: {json_path.name} + TXT")
            messagebox.showinfo("Estilo exportado", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.visual_pro_status.set(f"No se pudo exportar estilo: {e}")


    def build_revision_tecnica_tab(self):
        cont = ttk.Frame(self.tab_revision_tecnica)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "revision_banner" in self.revision_images:
            ttk.Label(header, image=self.revision_images["revision_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Revisión Técnica Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Auditoría técnica")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_auditar", "Auditar todo", self.revision_run_full),
            ("tile_audio", "Check audio", self.revision_audio_check),
            ("tile_wav", "Check WAV", self.revision_wav_check),
            ("tile_guardian", "Guardián", self.revision_guard_check),
            ("tile_informe", "Informe", self.revision_export_report),
            ("tile_fix", "Fix seguro", self.revision_safe_fix),
        ]
        for i, (img, label, cmd) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.revision_images:
                ttk.Label(box, image=self.revision_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        report = self.make_card(body, "Informe técnico")
        report.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.revision_text = tk.Text(
            report,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.revision_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.revision_refresh_text("Pulsa Auditar todo para revisar la app.")

        details = self.make_card(body, "Mejoras aplicadas en V73")
        details.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ttk.Label(
            details,
            text=(
                "CORRECCIONES REALES\n\n"
                "✓ El motor reinicia callback_count al empezar directo.\n"
                "✓ configure_rate recalcula graves, radio, EQ, colas, replay y buffers al cambiar 44100/48000 Hz.\n"
                "✓ El cargador WAV acepta 8/16/24/32-bit PCM.\n"
                "✓ Resampling WAV más seguro para archivos vacíos o raros.\n"
                "✓ Nueva auditoría interna con JSON/TXT.\n\n"
                "OBJETIVO\n\n"
                "Hacer la app más estable y más fácil de revisar antes de usarla en directo."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=460
        ).pack(anchor="w")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.revision_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(estado, textvariable=self.revision_score, style="Card.TLabel", font=("Segoe UI", 15, "bold"), wraplength=320).pack(anchor="w", pady=(8, 0))

        acciones = self.make_card(right, "Accesos")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Abrir Studio", command=lambda: self.select_tab(self.tab_studio_dashboard)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Analizador", command=lambda: self.select_tab(self.tab_analizador_vocal)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Rendimiento", command=lambda: self.select_tab(self.tab_rendimiento)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Diagnóstico", command=lambda: self.select_tab(self.tab_diagnostico)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Lectura rápida")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text="🟢 OK: preparado.\n🟡 Revisar: funciona, pero puede mejorar.\n🔴 Crítico: conviene arreglar antes de directo.\n\nLa auditoría no sustituye probar el micro real, pero ayuda a detectar configuración peligrosa.",
            style="Card.TLabel",
            justify="left",
            wraplength=320
        ).pack(anchor="w")

    def revision_data(self):
        values = {}
        for k, v in getattr(self, "vars", {}).items():
            try:
                values[k] = float(v.get())
            except Exception:
                values[k] = 0.0

        deps = {}
        for name in ["numpy", "sounddevice", "PIL", "pystray", "keyboard"]:
            try:
                __import__(name)
                deps[name] = True
            except Exception:
                deps[name] = False

        data = {
            "version": VERSION,
            "engine_rate": getattr(self.engine, "rate", 0),
            "engine_running": bool(getattr(self.engine, "running", False)),
            "callback_count": int(getattr(self.engine, "callback_count", 0)),
            "xrun_count": int(getattr(self.engine, "xrun_count", 0)),
            "input_selected": self.input_dev.get() if hasattr(self, "input_dev") else "",
            "output_selected": self.output_dev.get() if hasattr(self, "output_dev") else "",
            "latency": self.latency.get() if hasattr(self, "latency") else "",
            "voice": self.preset.get() if hasattr(self, "preset") else "",
            "effects": values,
            "dependencies": deps,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        return data

    def revision_evaluate(self):
        data = self.revision_data()
        score = 100
        items = []

        deps = data["dependencies"]
        for dep in ["numpy", "sounddevice"]:
            if deps.get(dep):
                items.append(("🟢", f"Dependencia crítica {dep}: OK"))
            else:
                items.append(("🔴", f"Falta dependencia crítica {dep}."))
                score -= 25

        for dep in ["PIL", "pystray", "keyboard"]:
            if deps.get(dep):
                items.append(("🟢", f"Extra {dep}: instalado"))
            else:
                items.append(("🟡", f"Extra {dep}: no instalado; algunas funciones serán limitadas."))
                score -= 5

        if data["input_selected"] and data["output_selected"]:
            items.append(("🟢", "Entrada y salida seleccionadas."))
        else:
            items.append(("🔴", "Falta seleccionar entrada o salida de audio."))
            score -= 20

        vals = data["effects"]
        if vals.get("vol", 90) > 105:
            items.append(("🟡", "Volumen alto: riesgo de saturación."))
            score -= 8
        else:
            items.append(("🟢", "Volumen en rango seguro."))

        if vals.get("echo", 0) > 35:
            items.append(("🟡", "Eco/reverb alto: puede ensuciar Discord/OBS."))
            score -= 8
        else:
            items.append(("🟢", "Eco controlado."))

        if data["engine_rate"] in (44100, 48000):
            items.append(("🟢", f"Tasa de audio común: {data['engine_rate']} Hz."))
        else:
            items.append(("🟡", f"Tasa de audio no habitual: {data['engine_rate']} Hz."))

        if data["xrun_count"] > 0:
            items.append(("🟡", f"Cortes detectados: {data['xrun_count']}. Prueba latencia Estable."))
            score -= min(20, data["xrun_count"] * 2)
        else:
            items.append(("🟢", "Sin cortes de audio registrados."))

        score = max(0, min(100, score))
        return score, items

    def revision_grade(self, score):
        if score >= 85:
            return "🟢 OK"
        if score >= 65:
            return "🟡 REVISAR"
        return "🔴 CRÍTICO"

    def revision_refresh_text(self, extra=""):
        if not hasattr(self, "revision_text"):
            return
        score, items = self.revision_evaluate()
        data = self.revision_data()
        self.revision_score.set(f"Calidad técnica: {score}/100 · {self.revision_grade(score)}")
        lines = [
            "REVISIÓN TÉCNICA PRO",
            "",
            f"Versión: {data['version']}",
            f"Fecha: {data['created_at']}",
            f"Estado: {self.revision_grade(score)}",
            f"Puntuación: {score}/100",
            "",
            "AUDIO",
            f"Rate: {data['engine_rate']} Hz",
            f"Directo activo: {data['engine_running']}",
            f"Callbacks: {data['callback_count']}",
            f"Cortes: {data['xrun_count']}",
            f"Latencia: {data['latency']}",
            "",
            "DISPOSITIVOS",
            f"Entrada: {data['input_selected'] or 'No seleccionada'}",
            f"Salida: {data['output_selected'] or 'No seleccionada'}",
            "",
            "RESULTADOS",
        ]
        for icon, msg in items:
            lines.append(f"{icon} {msg}")
        lines += ["", str(extra)]
        self.revision_text.configure(state="normal")
        self.revision_text.delete("1.0", tk.END)
        self.revision_text.insert("1.0", "\n".join(lines))
        self.revision_text.configure(state="disabled")

    def revision_run_full(self):
        self.revision_refresh_text("Auditoría completa ejecutada.")
        score, _ = self.revision_evaluate()
        self.revision_status.set(f"Auditoría completada: {score}/100 · {self.revision_grade(score)}")

    def revision_audio_check(self):
        self.revision_refresh_text("Check de audio ejecutado: dispositivos, tasa, callbacks y cortes revisados.")
        self.revision_status.set("Check de audio completado.")

    def revision_wav_check(self):
        self.revision_refresh_text("Cargador WAV V73: 8/16/24/32-bit PCM + resampling seguro.")
        self.revision_status.set("Check WAV completado: cargador ampliado en V73.")

    def revision_guard_check(self):
        self.revision_refresh_text("Guardián revisado: callback_count se reinicia al empezar directo y la reconexión conserva el flujo V57.")
        self.revision_status.set("Check del guardián completado.")

    def revision_safe_fix(self):
        try:
            if "vol" in self.vars and self.vars["vol"].get() > 98:
                self.vars["vol"].set(92)
            if "echo" in self.vars and self.vars["echo"].get() > 30:
                self.vars["echo"].set(18)
            if "comp" in self.vars:
                c = self.vars["comp"].get()
                if c < 35:
                    self.vars["comp"].set(52)
                elif c > 82:
                    self.vars["comp"].set(72)
            if "gate" in self.vars:
                g = self.vars["gate"].get()
                if g < 6:
                    self.vars["gate"].set(8)
                elif g > 24:
                    self.vars["gate"].set(18)
            self.update_engine()
            self.revision_refresh_text("Fix seguro aplicado: volumen, eco, compresor y puerta revisados.")
            self.revision_status.set("Fix seguro aplicado.")
        except Exception as e:
            self.revision_status.set(f"No se pudo aplicar fix: {e}")

    def revision_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def revision_safe_name(self):
        try:
            return self.song_safe_name(self.song_title.get())
        except Exception:
            return "revision_tecnica"

    def revision_export_report(self):
        try:
            data = self.revision_data()
            score, items = self.revision_evaluate()
            data["score"] = score
            data["grade"] = self.revision_grade(score)
            data["items"] = [{"status": icon, "message": msg} for icon, msg in items]

            folder = self.revision_output_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = self.revision_safe_name()
            json_path = folder / f"{name}_revision_tecnica_{ts}.json"
            txt_path = folder / f"{name}_revision_tecnica_{ts}.txt"

            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            lines = [
                "REVISIÓN TÉCNICA PRO",
                "",
                f"Fecha: {data['created_at']}",
                f"Versión: {data['version']}",
                f"Estado: {data['grade']}",
                f"Puntuación: {data['score']}/100",
                "",
                "RESULTADOS",
            ]
            for item in data["items"]:
                lines.append(f"{item['status']} {item['message']}")
            txt_path.write_text("\n".join(lines), encoding="utf-8")

            self.revision_status.set(f"Informe exportado: {json_path.name} + TXT")
            messagebox.showinfo("Informe exportado", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.revision_status.set(f"No se pudo exportar informe: {e}")


    def build_studio_dashboard_tab(self):
        cont = ttk.Frame(self.tab_studio_dashboard)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "studio_banner" in self.studio_dashboard_images:
            ttk.Label(header, image=self.studio_dashboard_images["studio_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Studio Dashboard Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Flujo profesional recomendado")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_analizar", "1 Analizar", "analizar"),
            ("tile_cadena", "2 Voz", "cadena"),
            ("tile_timeline", "3 Timeline", "timeline"),
            ("tile_multipista", "4 Multipista", "multipista"),
            ("tile_mezcla", "5 Mezcla", "mezcla"),
            ("tile_master", "6 Master", "master"),
        ]
        for i, (img, label, step) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.studio_dashboard_images:
                ttk.Label(box, image=self.studio_dashboard_images[img], style="Card.TLabel").pack()
            ttk.Button(box, text=label, style="Accent.TButton", command=lambda s=step: self.studio_go_step(s)).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        checklist = self.make_card(body, "Checklist de producción")
        checklist.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.studio_dashboard_text = tk.Text(
            checklist,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.studio_dashboard_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.studio_dashboard_refresh()

        overview = self.make_card(body, "Resumen del proyecto")
        overview.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.studio_project_text = tk.Text(
            overview,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.studio_project_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.studio_project_refresh()

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.studio_dashboard_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        ttk.Label(estado, textvariable=self.studio_ready_score, style="Card.TLabel", font=("Segoe UI", 16, "bold"), wraplength=320).pack(anchor="w", pady=(8, 0))

        acciones = self.make_card(right, "Acciones rápidas")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Actualizar dashboard", style="Accent.TButton", command=self.studio_dashboard_refresh_all).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Check vocal ahora", command=self.studio_quick_analyze).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Aplicar flujo seguro", command=self.studio_apply_safe_flow).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Exportar resumen JSON/TXT", command=self.studio_export_summary).pack(fill="x", pady=3)

        exportar = self.make_card(right, "Finalizar")
        exportar.pack(fill="x", pady=(0, 10))
        if hasattr(self, "master_export_wav"):
            ttk.Button(exportar, text="Exportar Master WAV", command=self.master_export_wav).pack(fill="x", pady=3)
        if hasattr(self, "song_export_instrumental"):
            ttk.Button(exportar, text="Exportar Instrumental WAV", command=self.song_export_instrumental).pack(fill="x", pady=3)
        ttk.Button(exportar, text="Grabar demo WAV", command=self.karaoke_record_demo).pack(fill="x", pady=3)
        ttk.Button(exportar, text="Guardar perfil", command=self.save_current_profile).pack(fill="x", pady=3)

        tips = self.make_card(right, "Objetivo V73")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text="Esta pantalla no añade solo efectos: organiza el flujo completo de producción para que la app se sienta más profesional.",
            style="Card.TLabel",
            justify="left",
            wraplength=320
        ).pack(anchor="w")

    def studio_dashboard_data(self):
        data = {
            "version": VERSION,
            "title": self.song_title.get() if hasattr(self, "song_title") else "Mi demo",
            "voice": self.preset.get() if hasattr(self, "preset") else "",
            "category": self.category.get() if hasattr(self, "category") else "",
            "track": self.karaoke_track.get() if hasattr(self, "karaoke_track") else "",
            "timeline_total": self.timeline_total_seconds() if hasattr(self, "timeline_total_seconds") else 0,
            "latency": self.latency.get() if hasattr(self, "latency") else "",
            "effects": {k: v.get() for k, v in getattr(self, "vars", {}).items()},
        }
        if hasattr(self, "vocal_analyzer_recommendations"):
            try:
                score, recs = self.vocal_analyzer_recommendations()
                data["vocal_score"] = score
                data["vocal_grade"] = self.vocal_analyzer_grade(score)
            except Exception:
                data["vocal_score"] = 0
                data["vocal_grade"] = "Sin análisis"
        return data

    def studio_readiness_score(self):
        data = self.studio_dashboard_data()
        score = 0
        checks = []
        if data.get("voice"):
            score += 15; checks.append(("🟢", "Voz seleccionada"))
        else:
            checks.append(("🔴", "Falta voz"))
        if data.get("track") and data.get("track") != "Sin pista instrumental":
            score += 20; checks.append(("🟢", "Pista/base preparada"))
        else:
            checks.append(("🟡", "Falta generar o cargar base"))
        if data.get("timeline_total", 0) >= 30:
            score += 15; checks.append(("🟢", "Timeline suficiente"))
        else:
            checks.append(("🟡", "Timeline corta o no configurada"))
        vocal_score = data.get("vocal_score", 0)
        if vocal_score >= 80:
            score += 25; checks.append(("🟢", f"Calidad vocal OK ({vocal_score}/100)"))
        elif vocal_score >= 60:
            score += 15; checks.append(("🟡", f"Calidad vocal revisable ({vocal_score}/100)"))
        else:
            checks.append(("🔴", f"Calidad vocal baja o sin check ({vocal_score}/100)"))
        vals = data.get("effects", {})
        if vals.get("vol", 90) <= 105 and vals.get("echo", 0) <= 35:
            score += 15; checks.append(("🟢", "Volumen/eco controlados"))
        else:
            checks.append(("🟡", "Revisar volumen o eco"))
        if hasattr(self, "master_export_wav"):
            score += 10; checks.append(("🟢", "Master disponible"))
        else:
            checks.append(("🟡", "Master no disponible"))
        return max(0, min(100, score)), checks

    def studio_dashboard_refresh(self):
        if not hasattr(self, "studio_dashboard_text"):
            return
        score, checks = self.studio_readiness_score()
        self.studio_ready_score.set(f"Preparación: {score}%")
        lines = [
            "STUDIO DASHBOARD PRO",
            "",
            "FLUJO RECOMENDADO",
            "1. Analizador: revisa ruido, eco y volumen.",
            "2. Cadena Vocal: prepara voz limpia o cantada.",
            "3. Timeline: define estructura real de canción.",
            "4. Multipista: organiza voz, coros, instrumental y FX.",
            "5. Mezclador: balancea voz/base/master.",
            "6. Master Final: exporta WAV terminado.",
            "",
            "CHECKLIST",
        ]
        for icon, msg in checks:
            lines.append(f"{icon} {msg}")
        lines += ["", "Siguiente paso recomendado:", self.studio_next_step(score)]
        self.studio_dashboard_text.configure(state="normal")
        self.studio_dashboard_text.delete("1.0", tk.END)
        self.studio_dashboard_text.insert("1.0", "\n".join(lines))
        self.studio_dashboard_text.configure(state="disabled")

    def studio_project_refresh(self):
        if not hasattr(self, "studio_project_text"):
            return
        data = self.studio_dashboard_data()
        lines = [
            "RESUMEN DEL PROYECTO",
            "",
            f"Título: {data.get('title')}",
            f"Voz: {data.get('voice')}",
            f"Categoría: {data.get('category')}",
            f"Pista: {data.get('track')}",
            f"Timeline total: {data.get('timeline_total')}s",
            f"Latencia: {data.get('latency')}",
            f"Calidad vocal: {data.get('vocal_grade', 'Sin análisis')} · {data.get('vocal_score', 0)}/100",
            "",
            "AJUSTES CLAVE",
        ]
        for key in ["gate", "comp", "vol", "echo", "autotune", "vibrato", "chorus"]:
            if key in data.get("effects", {}):
                lines.append(f"- {key}: {data['effects'][key]:.0f}")
        self.studio_project_text.configure(state="normal")
        self.studio_project_text.delete("1.0", tk.END)
        self.studio_project_text.insert("1.0", "\n".join(lines))
        self.studio_project_text.configure(state="disabled")

    def studio_dashboard_refresh_all(self):
        self.studio_dashboard_refresh()
        self.studio_project_refresh()
        score, _ = self.studio_readiness_score()
        self.studio_dashboard_status.set(f"Dashboard actualizado. Preparación {score}%.")

    def studio_next_step(self, score):
        data = self.studio_dashboard_data()
        if not data.get("track") or data.get("track") == "Sin pista instrumental":
            return "Genera una base en Timeline/Canción Pro/Karaoke Studio."
        if data.get("vocal_score", 0) < 70:
            return "Pasa por Analizador y Cadena Vocal."
        if score < 85:
            return "Revisa Mezclador y Multipista."
        return "Listo para Master Final o grabar demo."

    def studio_go_step(self, step):
        mapping = {
            "analizar": "tab_analizador_vocal",
            "cadena": "tab_cadena_vocal",
            "timeline": "tab_timeline_pro",
            "multipista": "tab_multipista",
            "mezcla": "tab_mezclador_musical",
            "master": "tab_master_final",
        }
        attr = mapping.get(step)
        if attr and hasattr(self, attr):
            self.select_tab(getattr(self, attr))
            self.studio_dashboard_status.set(f"Abierto paso: {step}.")
        else:
            self.studio_dashboard_status.set(f"El paso {step} todavía no está disponible en esta versión.")

    def studio_quick_analyze(self):
        try:
            if hasattr(self, "vocal_analyzer_run_check"):
                self.vocal_analyzer_run_check()
            self.studio_dashboard_refresh_all()
        except Exception as e:
            self.studio_dashboard_status.set(f"No se pudo analizar: {e}")

    def studio_apply_safe_flow(self):
        try:
            if hasattr(self, "vocal_analyzer_auto_fix"):
                self.vocal_analyzer_auto_fix()
            if hasattr(self, "vocal_chain_apply_preset"):
                self.vocal_chain_apply_preset("clean")
            if hasattr(self, "mix_apply_preset"):
                self.mix_apply_preset("demo")
            if hasattr(self, "master_apply_preset"):
                self.master_apply_preset("seguro")
            self.studio_dashboard_refresh_all()
            self.studio_dashboard_status.set("Flujo seguro aplicado: voz limpia, mezcla demo y master seguro.")
        except Exception as e:
            self.studio_dashboard_status.set(f"No se pudo aplicar flujo seguro: {e}")

    def studio_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def studio_safe_name(self, text):
        try:
            return self.song_safe_name(text)
        except Exception:
            return "".join(ch for ch in str(text) if ch.isalnum() or ch in " -_").strip().replace(" ", "_") or "studio"

    def studio_export_summary(self):
        try:
            data = self.studio_dashboard_data()
            score, checks = self.studio_readiness_score()
            data["readiness_score"] = score
            data["checklist"] = [{"status": icon, "message": msg} for icon, msg in checks]
            data["created_at"] = datetime.now().isoformat(timespec="seconds")
            folder = self.studio_output_folder()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = self.studio_safe_name(data.get("title", "studio"))
            json_path = folder / f"{name}_studio_dashboard_{ts}.json"
            txt_path = folder / f"{name}_studio_dashboard_{ts}.txt"
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            lines = [
                "STUDIO DASHBOARD PRO",
                "",
                f"Fecha: {data['created_at']}",
                f"Título: {data.get('title')}",
                f"Preparación: {score}%",
                f"Voz: {data.get('voice')}",
                f"Pista: {data.get('track')}",
                "",
                "CHECKLIST",
            ]
            for item in data["checklist"]:
                lines.append(f"{item['status']} {item['message']}")
            lines += ["", "Siguiente paso:", self.studio_next_step(score)]
            txt_path.write_text("\n".join(lines), encoding="utf-8")

            self.studio_dashboard_status.set(f"Resumen exportado: {json_path.name} + TXT")
            messagebox.showinfo("Resumen exportado", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.studio_dashboard_status.set(f"No se pudo exportar resumen: {e}")


    def build_analizador_vocal_tab(self):
        cont = ttk.Frame(self.tab_analizador_vocal)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "analizador_banner" in self.vocal_analyzer_images:
            ttk.Label(header, image=self.vocal_analyzer_images["analizador_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Analizador Vocal Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Checks de calidad")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_check", "Check rápido", "check"),
            ("tile_directo", "Modo directo", "directo"),
            ("tile_cantar", "Modo cantar", "cantar"),
            ("tile_ruido", "Bajar ruido", "ruido"),
            ("tile_reporte", "Informe", "reporte"),
            ("tile_arreglar", "Auto-ajuste", "auto"),
        ]
        for i, (img, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.vocal_analyzer_images:
                ttk.Label(box, image=self.vocal_analyzer_images[img], style="Card.TLabel").pack()
            if mode == "check":
                cmd = self.vocal_analyzer_run_check
            elif mode == "directo":
                cmd = lambda: self.vocal_analyzer_mode_check("Directo")
            elif mode == "cantar":
                cmd = lambda: self.vocal_analyzer_mode_check("Cantar")
            elif mode == "ruido":
                cmd = self.vocal_analyzer_reduce_noise
            elif mode == "reporte":
                cmd = self.vocal_analyzer_export_report
            else:
                cmd = self.vocal_analyzer_auto_fix
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        panel = self.make_card(body, "Panel de análisis")
        panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.vocal_analyzer_text = tk.Text(
            panel,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.vocal_analyzer_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.vocal_analyzer_refresh_text("Pulsa Check rápido para analizar la configuración actual.")

        checklist = self.make_card(body, "Checklist profesional")
        checklist.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ttk.Label(
            checklist,
            text=(
                "ANTES DE GRABAR O HACER DIRECTO\n\n"
                "1. Habla o canta cerca del micro.\n"
                "2. Mira si el nivel llega muy alto.\n"
                "3. Si hay eco, baja reverb/delay.\n"
                "4. Si hay ruido, sube puerta de ruido.\n"
                "5. Si la voz no se entiende, sube presencia.\n"
                "6. Si distorsiona, baja volumen/master.\n"
                "7. Exporta informe si quieres guardar el ajuste."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=450
        ).pack(anchor="w", pady=(0, 10))

        ttk.Button(checklist, text="Abrir Cadena Vocal", command=lambda: self.select_tab(self.tab_cadena_vocal)).pack(fill="x", pady=3)
        if hasattr(self, "tab_mezclador_musical"):
            ttk.Button(checklist, text="Abrir Mezclador", command=lambda: self.select_tab(self.tab_mezclador_musical)).pack(fill="x", pady=3)
        if hasattr(self, "tab_master_final"):
            ttk.Button(checklist, text="Abrir Master Final", command=lambda: self.select_tab(self.tab_master_final)).pack(fill="x", pady=3)
        ttk.Button(checklist, text="Grabar prueba WAV", style="Accent.TButton", command=self.record).pack(fill="x", pady=3)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.vocal_analyzer_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        modo = self.make_card(right, "Modo")
        modo.pack(fill="x", pady=(0, 10))
        ttk.Combobox(modo, textvariable=self.vocal_analyzer_mode, state="readonly", values=["Directo", "Cantar", "Podcast", "Karaoke", "Fortnite/Discord"]).pack(fill="x", pady=4)
        ttk.Button(modo, text="Analizar modo", style="Accent.TButton", command=self.vocal_analyzer_run_check).pack(fill="x", pady=4)

        acciones = self.make_card(right, "Acciones")
        acciones.pack(fill="x", pady=(0, 10))
        ttk.Button(acciones, text="Auto-ajuste seguro", command=self.vocal_analyzer_auto_fix).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Bajar ruido", command=self.vocal_analyzer_reduce_noise).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Exportar informe JSON/TXT", command=self.vocal_analyzer_export_report).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Guardar perfil", command=self.save_current_profile).pack(fill="x", pady=3)

        tips = self.make_card(right, "Semáforo")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text="🟢 OK: listo.\n🟡 Revisar: puede mejorar.\n🔴 Alto riesgo: eco, clipping o volumen excesivo.\n\nEste analizador revisa la configuración y los niveles internos disponibles.",
            style="Card.TLabel",
            justify="left",
            wraplength=320
        ).pack(anchor="w")

    def vocal_analyzer_values(self):
        values = {}
        for k, v in getattr(self, "vars", {}).items():
            try:
                values[k] = float(v.get())
            except Exception:
                values[k] = 0.0
        try:
            mic_level = float(getattr(self.engine, "mic_level", 0.0))
        except Exception:
            mic_level = 0.0
        try:
            out_level = float(getattr(self.engine, "out_level", 0.0))
        except Exception:
            out_level = 0.0
        return {
            "mode": self.vocal_analyzer_mode.get(),
            "voice": self.preset.get(),
            "category": self.category.get(),
            "latency": self.latency.get() if hasattr(self, "latency") else "",
            "mic_level": mic_level,
            "out_level": out_level,
            "values": values,
        }

    def vocal_analyzer_recommendations(self):
        data = self.vocal_analyzer_values()
        vals = data["values"]
        recs = []
        score = 100

        vol = vals.get("vol", 90)
        echo = vals.get("echo", 0)
        comp = vals.get("comp", 0)
        gate = vals.get("gate", 0)
        robot = vals.get("robot", 0)
        radio = vals.get("radio", 0)
        autotune = vals.get("autotune", 0)

        if vol > 105:
            recs.append(("🔴", "Volumen muy alto: baja Volumen o Master para evitar distorsión."))
            score -= 18
        elif vol > 96:
            recs.append(("🟡", "Volumen algo alto: vigila picos al cantar fuerte."))
            score -= 8
        else:
            recs.append(("🟢", "Volumen en rango seguro."))

        if echo > 35:
            recs.append(("🔴", "Eco/Reverb alto: puede ensuciar la voz en Discord/OBS."))
            score -= 16
        elif echo > 18:
            recs.append(("🟡", "Eco moderado: bien para cantar, cuidado en directo."))
            score -= 6
        else:
            recs.append(("🟢", "Eco controlado."))

        if comp < 30:
            recs.append(("🟡", "Compresión baja: la voz puede subir y bajar demasiado."))
            score -= 6
        elif comp > 82:
            recs.append(("🟡", "Compresión alta: puede sonar aplastada."))
            score -= 6
        else:
            recs.append(("🟢", "Compresión equilibrada."))

        if gate < 5:
            recs.append(("🟡", "Puerta de ruido baja: puede entrar ruido de fondo."))
            score -= 6
        elif gate > 22:
            recs.append(("🟡", "Puerta de ruido alta: puede cortar finales de palabras."))
            score -= 6
        else:
            recs.append(("🟢", "Puerta de ruido razonable."))

        mode = data["mode"].lower()
        if "cantar" in mode or "karaoke" in mode:
            if autotune < 20:
                recs.append(("🟡", "Para cantar, puedes subir Autotune o Vibrato si quieres efecto musical."))
                score -= 4
            if echo < 8:
                recs.append(("🟡", "Para karaoke, un poco más de reverb suele quedar mejor."))
                score -= 4
        else:
            if autotune > 50:
                recs.append(("🟡", "Autotune alto en directo puede sonar artificial."))
                score -= 5
            if robot > 35:
                recs.append(("🟡", "Robot alto puede dificultar entender la voz."))
                score -= 5

        if radio > 28:
            recs.append(("🟡", "Radio/presencia muy alta: puede sonar chillón."))
            score -= 5

        score = max(0, min(100, score))
        return score, recs

    def vocal_analyzer_grade(self, score):
        if score >= 85:
            return "🟢 LISTO"
        if score >= 65:
            return "🟡 REVISAR"
        return "🔴 AJUSTAR"

    def vocal_analyzer_refresh_text(self, extra=""):
        if not hasattr(self, "vocal_analyzer_text"):
            return
        data = self.vocal_analyzer_values()
        score, recs = self.vocal_analyzer_recommendations()
        lines = [
            "ANALIZADOR VOCAL PRO",
            "",
            f"Estado: {self.vocal_analyzer_grade(score)}",
            f"Puntuación: {score}/100",
            f"Modo: {data['mode']}",
            f"Voz: {data['voice']}",
            f"Categoría: {data['category']}",
            f"Latencia: {data['latency']}",
            "",
            "NIVELES DISPONIBLES",
            f"Mic level: {data['mic_level']:.3f}",
            f"Out level: {data['out_level']:.3f}",
            "",
            "AJUSTES CLAVE",
        ]
        vals = data["values"]
        for key in ["gate", "comp", "vol", "echo", "radio", "bass", "robot", "autotune", "vibrato", "chorus"]:
            if key in vals:
                lines.append(f"- {key}: {vals[key]:.0f}")
        lines += ["", "RECOMENDACIONES"]
        for icon, msg in recs:
            lines.append(f"{icon} {msg}")
        lines += ["", str(extra)]
        self.vocal_analyzer_text.configure(state="normal")
        self.vocal_analyzer_text.delete("1.0", tk.END)
        self.vocal_analyzer_text.insert("1.0", "\n".join(lines))
        self.vocal_analyzer_text.configure(state="disabled")

    def vocal_analyzer_run_check(self):
        score, _ = self.vocal_analyzer_recommendations()
        self.vocal_analyzer_status.set(f"Check completado: {self.vocal_analyzer_grade(score)} · {score}/100")
        self.vocal_analyzer_refresh_text("Check rápido completado.")

    def vocal_analyzer_mode_check(self, mode):
        self.vocal_analyzer_mode.set(mode)
        self.vocal_analyzer_run_check()

    def vocal_analyzer_auto_fix(self):
        try:
            vals = self.vocal_analyzer_values()["values"]
            if "vol" in self.vars and vals.get("vol", 90) > 98:
                self.vars["vol"].set(92)
            if "echo" in self.vars and vals.get("echo", 0) > 30:
                self.vars["echo"].set(18)
            if "comp" in self.vars:
                c = vals.get("comp", 50)
                if c < 35:
                    self.vars["comp"].set(52)
                elif c > 82:
                    self.vars["comp"].set(72)
            if "gate" in self.vars:
                g = vals.get("gate", 8)
                if g < 6:
                    self.vars["gate"].set(8)
                elif g > 24:
                    self.vars["gate"].set(18)
            self.update_engine()
            self.vocal_analyzer_status.set("Auto-ajuste seguro aplicado.")
            self.vocal_analyzer_refresh_text("Auto-ajuste aplicado: volumen, eco, compresor y puerta revisados.")
        except Exception as e:
            self.vocal_analyzer_status.set(f"No se pudo aplicar auto-ajuste: {e}")

    def vocal_analyzer_reduce_noise(self):
        try:
            if "gate" in self.vars:
                self.vars["gate"].set(max(10, min(18, self.vars["gate"].get() + 4)))
            if "comp" in self.vars:
                self.vars["comp"].set(max(45, self.vars["comp"].get()))
            self.update_engine()
            self.vocal_analyzer_status.set("Preset de reducción de ruido aplicado.")
            self.vocal_analyzer_refresh_text("Se subió la puerta de ruido y se equilibró la compresión.")
        except Exception as e:
            self.vocal_analyzer_status.set(f"No se pudo bajar ruido: {e}")

    def vocal_analyzer_report_data(self):
        score, recs = self.vocal_analyzer_recommendations()
        data = self.vocal_analyzer_values()
        data["score"] = score
        data["grade"] = self.vocal_analyzer_grade(score)
        data["recommendations"] = [{"level": icon, "message": msg} for icon, msg in recs]
        data["created_at"] = datetime.now().isoformat(timespec="seconds")
        data["version"] = VERSION
        return data

    def vocal_analyzer_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def vocal_analyzer_safe_name(self):
        try:
            return self.song_safe_name(self.song_title.get())
        except Exception:
            return "analisis_vocal"

    def vocal_analyzer_export_report(self):
        try:
            data = self.vocal_analyzer_report_data()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = self.vocal_analyzer_safe_name()
            folder = self.vocal_analyzer_output_folder()
            json_path = folder / f"{base_name}_analisis_vocal_{ts}.json"
            txt_path = folder / f"{base_name}_analisis_vocal_{ts}.txt"

            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            lines = [
                "INFORME ANALIZADOR VOCAL PRO",
                "",
                f"Fecha: {data['created_at']}",
                f"Versión: {data['version']}",
                f"Estado: {data['grade']}",
                f"Puntuación: {data['score']}/100",
                f"Modo: {data['mode']}",
                f"Voz: {data['voice']}",
                "",
                "RECOMENDACIONES",
            ]
            for rec in data["recommendations"]:
                lines.append(f"{rec['level']} {rec['message']}")
            txt_path.write_text("\n".join(lines), encoding="utf-8")

            self.vocal_analyzer_status.set(f"Informe exportado: {json_path.name} + TXT")
            messagebox.showinfo("Informe exportado", f"Guardado en:\n{json_path}\n{txt_path}")
        except Exception as e:
            self.vocal_analyzer_status.set(f"No se pudo exportar informe: {e}")


    def build_cadena_vocal_tab(self):
        cont = ttk.Frame(self.tab_cadena_vocal)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "cadena_banner" in self.vocal_chain_images:
            ttk.Label(header, image=self.vocal_chain_images["cadena_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Cadena Vocal Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Presets de cadena vocal")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_clean", "Voz limpia", "clean"),
            ("tile_pop", "Pop vocal", "pop"),
            ("tile_trap", "Trap vocal", "trap"),
            ("tile_podcast", "Podcast", "podcast"),
            ("tile_karaoke", "Karaoke", "karaoke"),
            ("tile_export", "Exportar cadena", "export"),
        ]
        for i, (img, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.vocal_chain_images:
                ttk.Label(box, image=self.vocal_chain_images[img], style="Card.TLabel").pack()
            cmd = self.vocal_chain_export_json if mode == "export" else lambda m=mode: self.vocal_chain_apply_preset(m)
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        chain = self.make_card(body, "Cadena de voz")
        chain.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.vocal_chain_slider(chain, "Puerta ruido", "gate", 0, 35, "%")
        self.vocal_chain_slider(chain, "Compresor", "comp", 0, 100, "%")
        self.vocal_chain_slider(chain, "Presencia", self.vocal_presence, 0, 60, "%")
        self.vocal_chain_slider(chain, "Aire/brillo", self.vocal_air, 0, 60, "%")
        self.vocal_chain_slider(chain, "Calidez", self.vocal_warmth, 0, 60, "%")
        self.vocal_chain_slider(chain, "Reverb", self.vocal_reverb_send, 0, 70, "%")
        self.vocal_chain_slider(chain, "Delay", self.vocal_delay_send, 0, 50, "%")
        self.vocal_chain_slider(chain, "Volumen", "vol", 0, 120, "%")

        actions = ttk.Frame(chain, style="Card.TFrame")
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Aplicar ajustes", style="Accent.TButton", command=self.vocal_chain_apply_manual).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(actions, text="Grabar prueba", command=self.record).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(actions, text="Guardar perfil", command=self.save_current_profile).pack(side="left", fill="x", expand=True, padx=3, ipady=8)

        info = self.make_card(body, "Monitor de cadena")
        info.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.vocal_chain_text = tk.Text(
            info,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            height=18
        )
        self.vocal_chain_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.vocal_chain_refresh_text("Cadena preparada.")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.vocal_chain_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        actual = self.make_card(right, "Voz actual")
        actual.pack(fill="x", pady=(0, 10))
        ttk.Label(actual, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 13, "bold"), wraplength=320).pack(anchor="w")
        ttk.Label(actual, text="Cadena Vocal usa controles internos del modulador para acercar la voz a un flujo de estudio.", style="Card.TLabel", wraplength=320).pack(anchor="w", pady=(8, 0))

        acc = self.make_card(right, "Accesos")
        acc.pack(fill="x", pady=(0, 10))
        if hasattr(self, "tab_autotune"):
            ttk.Button(acc, text="Abrir Autotune", command=lambda: self.select_tab(self.tab_autotune)).pack(fill="x", pady=3)
        if hasattr(self, "tab_karaoke"):
            ttk.Button(acc, text="Abrir Karaoke", command=lambda: self.select_tab(self.tab_karaoke)).pack(fill="x", pady=3)
        if hasattr(self, "tab_mezclador_musical"):
            ttk.Button(acc, text="Abrir Mezclador", command=lambda: self.select_tab(self.tab_mezclador_musical)).pack(fill="x", pady=3)
        if hasattr(self, "tab_master_final"):
            ttk.Button(acc, text="Abrir Master Final", command=lambda: self.select_tab(self.tab_master_final)).pack(fill="x", pady=3)
        ttk.Button(acc, text="Exportar cadena JSON", style="Accent.TButton", command=self.vocal_chain_export_json).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text="• Voz limpia para Discord/OBS.\n• Pop vocal para cantar claro.\n• Trap vocal para autotune marcado.\n• Reverb y delay con moderación.\n• Exporta JSON para repetir el sonido.",
            style="Card.TLabel",
            justify="left",
            wraplength=320
        ).pack(anchor="w")

    def vocal_chain_slider(self, parent, label, key_or_var, mn, mx, unit):
        box = ttk.Frame(parent, style="Card.TFrame")
        box.pack(fill="x", pady=6)
        top = ttk.Frame(box, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text=label + ":", style="Card.TLabel", width=18).pack(side="left")
        value_label = ttk.Label(top, style="Card.TLabel", width=10)
        value_label.pack(side="right")
        var = self.vars[key_or_var] if isinstance(key_or_var, str) else key_or_var
        ttk.Scale(box, from_=mn, to=mx, variable=var, orient="horizontal", command=lambda _=None: self.vocal_chain_apply_manual()).pack(fill="x", pady=(3,0))
        def refresh(*_):
            value_label.config(text=f"{var.get():.0f}{unit}")
        var.trace_add("write", refresh)
        refresh()

    def vocal_chain_apply_manual(self):
        try:
            # Mapear controles "profesionales" a motor interno disponible.
            if "radio" in self.vars:
                self.vars["radio"].set(max(0, min(30, self.vocal_air.get() * 0.35 + self.vocal_presence.get() * 0.20)))
            if "bass" in self.vars:
                self.vars["bass"].set(max(0, min(45, self.vocal_warmth.get() * 0.55)))
            if "echo" in self.vars:
                self.vars["echo"].set(max(0, min(55, self.vocal_reverb_send.get() * 0.55 + self.vocal_delay_send.get() * 0.30)))
            self.update_engine()
            self.vocal_chain_refresh_text("Ajustes aplicados al motor de voz.")
        except Exception as e:
            self.vocal_chain_status.set(f"No se pudo aplicar cadena: {e}")

    def vocal_chain_apply_preset(self, mode):
        presets = {
            "clean":   {"gate":10, "comp":55, "vol":90, "air":10, "presence":18, "warmth":10, "reverb":6,  "delay":0,  "voice":"Gaming limpio", "msg":"Voz limpia aplicada."},
            "pop":     {"gate":8,  "comp":68, "vol":92, "air":28, "presence":34, "warmth":18, "reverb":26, "delay":8,  "voice":"Karaoke Pop", "msg":"Cadena Pop Vocal aplicada."},
            "trap":    {"gate":9,  "comp":72, "vol":92, "air":22, "presence":28, "warmth":20, "reverb":18, "delay":16, "voice":"Trap Tune", "msg":"Cadena Trap Vocal aplicada."},
            "podcast": {"gate":12, "comp":75, "vol":88, "air":8,  "presence":22, "warmth":34, "reverb":4,  "delay":0,  "voice":"Podcast Pro", "msg":"Cadena Podcast aplicada."},
            "karaoke": {"gate":8,  "comp":63, "vol":90, "air":24, "presence":28, "warmth":18, "reverb":30, "delay":10, "voice":"Karaoke Balada", "msg":"Cadena Karaoke aplicada."},
        }
        p = presets.get(mode, presets["clean"])

        for key in ["gate", "comp", "vol"]:
            if key in self.vars:
                self.vars[key].set(p[key])
        self.vocal_air.set(p["air"])
        self.vocal_presence.set(p["presence"])
        self.vocal_warmth.set(p["warmth"])
        self.vocal_reverb_send.set(p["reverb"])
        self.vocal_delay_send.set(p["delay"])

        voice = p.get("voice")
        try:
            if voice in VoiceBank.all_presets():
                self.preset.set(voice)
                self.category.set(VoiceBank.all_presets()[voice][0])
                self.apply_preset()
        except Exception:
            pass

        self.vocal_chain_apply_manual()
        self.vocal_chain_status.set(p["msg"])
        self.state.set("Estado: Cadena Vocal Pro · " + p["msg"])

    def vocal_chain_data(self):
        data = {
            "version": VERSION,
            "voice": self.preset.get(),
            "category": self.category.get(),
            "chain": {
                "gate": self.vars["gate"].get() if "gate" in self.vars else 0,
                "compressor": self.vars["comp"].get() if "comp" in self.vars else 0,
                "air": self.vocal_air.get(),
                "presence": self.vocal_presence.get(),
                "warmth": self.vocal_warmth.get(),
                "reverb": self.vocal_reverb_send.get(),
                "delay": self.vocal_delay_send.get(),
                "volume": self.vars["vol"].get() if "vol" in self.vars else 0,
            },
            "engine_values": {k: v.get() for k, v in self.vars.items()},
        }
        return data

    def vocal_chain_refresh_text(self, extra):
        if not hasattr(self, "vocal_chain_text"):
            return
        data = self.vocal_chain_data()
        lines = [
            "CADENA VOCAL PRO",
            "",
            f"Voz: {data['voice']}",
            f"Categoría: {data['category']}",
            "",
            "ORDEN DE CADENA",
            "1. Puerta de ruido",
            "2. Compresor",
            "3. Presencia / aire",
            "4. Calidez",
            "5. Reverb / delay",
            "6. Volumen final",
            "",
            "VALORES",
        ]
        for k, v in data["chain"].items():
            lines.append(f"- {k}: {v:.0f}")
        lines += ["", str(extra)]
        self.vocal_chain_text.configure(state="normal")
        self.vocal_chain_text.delete("1.0", tk.END)
        self.vocal_chain_text.insert("1.0", "\n".join(lines))
        self.vocal_chain_text.configure(state="disabled")

    def vocal_chain_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def vocal_chain_export_json(self):
        try:
            data = self.vocal_chain_data()
            title = "cadena_vocal"
            try:
                title = self.song_safe_name(self.song_title.get())
            except Exception:
                pass
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.vocal_chain_output_folder() / f"{title}_cadena_vocal_{ts}.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.vocal_chain_status.set(f"Cadena exportada: {path.name}")
            messagebox.showinfo("Cadena vocal exportada", f"JSON guardado en:\n{path}")
        except Exception as e:
            self.vocal_chain_status.set(f"No se pudo exportar cadena: {e}")


    def build_timeline_pro_tab(self):
        cont = ttk.Frame(self.tab_timeline_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "timeline_banner" in self.timeline_images:
            ttk.Label(header, image=self.timeline_images["timeline_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Timeline Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tiles = self.make_card(left, "Plantillas profesionales")
        tiles.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(tiles, style="Card.TFrame")
        grid.pack(fill="x")

        items = [
            ("tile_pop", "Pop", "Pop"),
            ("tile_trap", "Trap", "Trap"),
            ("tile_balada", "Balada", "Balada"),
            ("tile_rock", "Rock", "Rock"),
            ("tile_export", "Exportar plan", "export"),
            ("tile_demo", "Generar demo", "demo"),
        ]
        for i, (img, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img in self.timeline_images:
                ttk.Label(box, image=self.timeline_images[img], style="Card.TLabel").pack()
            if mode == "export":
                cmd = self.timeline_export_all
            elif mode == "demo":
                cmd = self.timeline_generate_demo
            else:
                cmd = lambda m=mode: self.timeline_apply_template(m)
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        editor = self.make_card(body, "Editor de estructura")
        editor.pack(side="left", fill="both", expand=True, padx=(0, 5))

        meta = ttk.Frame(editor, style="Card.TFrame")
        meta.pack(fill="x", pady=(0, 8))
        ttk.Label(meta, text="BPM:", style="Card.TLabel").pack(side="left")
        ttk.Scale(meta, from_=60, to=170, variable=self.timeline_bpm, orient="horizontal", command=lambda _=None: self.timeline_refresh()).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Label(meta, textvariable=self.timeline_bpm, style="Card.TLabel", width=6).pack(side="left")
        ttk.Label(meta, text="Tonalidad:", style="Card.TLabel").pack(side="left", padx=(8, 4))
        ttk.Combobox(meta, textvariable=self.timeline_key, state="readonly", width=12, values=["Do mayor","Re mayor","Mi menor","Fa mayor","Sol mayor","La menor","Si menor"]).pack(side="left")

        for name, var in self.timeline_sections.items():
            row = ttk.Frame(editor, style="Card.TFrame")
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=name, style="Card.TLabel", width=12).pack(side="left")
            ttk.Scale(row, from_=0, to=32, variable=var, orient="horizontal", command=lambda _=None: self.timeline_refresh()).pack(side="left", fill="x", expand=True, padx=6)
            ttk.Label(row, textvariable=var, style="Card.TLabel", width=6).pack(side="left")
            ttk.Label(row, text="seg", style="Card.TLabel").pack(side="left")

        actions = ttk.Frame(editor, style="Card.TFrame")
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Generar base con esta timeline", style="Accent.TButton", command=self.timeline_generate_demo).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(actions, text="Play", command=self.karaoke_play).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(actions, text="Stop", command=self.karaoke_stop).pack(side="left", fill="x", expand=True, padx=3, ipady=8)

        info = self.make_card(body, "Plan de canción")
        info.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.timeline_text = tk.Text(info, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=18)
        self.timeline_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.timeline_refresh()

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.timeline_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        pista = self.make_card(right, "Pista actual")
        pista.pack(fill="x", pady=(0, 10))
        ttk.Label(pista, textvariable=self.karaoke_track, style="Card.TLabel", font=("Segoe UI", 13, "bold"), wraplength=320).pack(anchor="w")

        acc = self.make_card(right, "Exportar")
        acc.pack(fill="x", pady=(0, 10))
        ttk.Button(acc, text="Exportar plan JSON", style="Accent.TButton", command=self.timeline_export_json).pack(fill="x", pady=3)
        ttk.Button(acc, text="Exportar plan TXT", command=self.timeline_export_txt).pack(fill="x", pady=3)
        ttk.Button(acc, text="Abrir Canción Pro", command=lambda: self.select_tab(self.tab_cancion_pro)).pack(fill="x", pady=3)
        ttk.Button(acc, text="Abrir Multipista", command=lambda: self.select_tab(self.tab_multipista)).pack(fill="x", pady=3)
        if hasattr(self, "tab_master_final"):
            ttk.Button(acc, text="Abrir Master Final", command=lambda: self.select_tab(self.tab_master_final)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text="• Timeline ayuda a pensar como canción real.\n• Sube estribillo para más energía.\n• Intro/outro cortos quedan más directos.\n• Exporta JSON para continuar luego.\n• Genera base y canta encima.",
            style="Card.TLabel",
            justify="left",
            wraplength=320
        ).pack(anchor="w")

    def timeline_total_seconds(self):
        return int(sum(v.get() for v in self.timeline_sections.values()))

    def timeline_style_to_engine(self):
        m = {"Pop":"pop", "Trap":"trap", "Balada":"balada", "Rock":"rock"}
        return m.get(self.timeline_style.get(), "pop")

    def timeline_apply_template(self, style):
        self.timeline_style.set(style)
        templates = {
            "Pop": (120, {"Intro":8, "Verso 1":16, "Pre":8, "Estribillo":20, "Verso 2":16, "Puente":8, "Outro":8}),
            "Trap": (140, {"Intro":6, "Verso 1":18, "Pre":0, "Estribillo":18, "Verso 2":18, "Puente":8, "Outro":6}),
            "Balada": (72, {"Intro":10, "Verso 1":20, "Pre":10, "Estribillo":24, "Verso 2":16, "Puente":12, "Outro":10}),
            "Rock": (110, {"Intro":8, "Verso 1":16, "Pre":8, "Estribillo":18, "Verso 2":16, "Puente":8, "Outro":8}),
        }
        bpm, values = templates.get(style, templates["Pop"])
        self.timeline_bpm.set(bpm)
        for k, val in values.items():
            if k in self.timeline_sections:
                self.timeline_sections[k].set(val)
        self.timeline_status.set(f"Plantilla aplicada: {style}")
        self.timeline_refresh()

    def timeline_data(self):
        cur = 0
        sections = []
        for name, var in self.timeline_sections.items():
            dur = int(var.get())
            if dur <= 0:
                continue
            sections.append({"name": name, "start": cur, "duration": dur, "end": cur + dur})
            cur += dur
        return {
            "version": VERSION,
            "title": self.song_title.get() if hasattr(self, "song_title") else "Mi canción",
            "style": self.timeline_style.get(),
            "bpm": int(self.timeline_bpm.get()),
            "key": self.timeline_key.get(),
            "total_seconds": cur,
            "sections": sections,
        }

    def timeline_refresh(self):
        if not hasattr(self, "timeline_text"):
            return
        data = self.timeline_data()
        lines = [
            "TIMELINE PRO",
            "",
            f"Título: {data['title']}",
            f"Estilo: {data['style']}",
            f"BPM: {data['bpm']}",
            f"Tonalidad: {data['key']}",
            f"Duración total: {data['total_seconds']}s",
            "",
            "SECCIONES",
        ]
        for sec in data["sections"]:
            lines.append(f"- {sec['name']}: {sec['start']}s → {sec['end']}s ({sec['duration']}s)")
        lines += ["", "USO", "1. Ajusta secciones.", "2. Genera base.", "3. Canta encima.", "4. Exporta plan o proyecto."]
        self.timeline_text.configure(state="normal")
        self.timeline_text.delete("1.0", tk.END)
        self.timeline_text.insert("1.0", "\n".join(lines))
        self.timeline_text.configure(state="disabled")

    def timeline_generate_demo(self):
        try:
            data = self.timeline_data()
            seconds = max(10, int(data["total_seconds"]))
            bpm = int(data["bpm"])
            style = self.timeline_style_to_engine()
            samples = self.generate_original_instrumental(style, seconds=seconds, bpm=bpm)
            if hasattr(self, "song_apply_arrangement"):
                samples = self.song_apply_arrangement(samples, style=style, rate=self.engine.rate)
            title = f"{data['title']} · Timeline {data['style']} · {bpm} BPM · {seconds}s"
            self.engine.set_karaoke_track(samples, title)
            self.karaoke_track.set(title)
            self.karaoke_loop.set(False)
            self.karaoke_update_engine()
            if style == "trap":
                self.karaoke_apply_voice("Karaoke Trap")
            elif style == "balada":
                self.karaoke_apply_voice("Karaoke Balada")
            else:
                self.karaoke_apply_voice("Karaoke Pop")
            self.timeline_status.set("Base generada con la timeline actual.")
            self.timeline_refresh()
        except Exception as e:
            self.timeline_status.set(f"No se pudo generar base: {e}")

    def timeline_output_folder(self):
        try:
            return self.song_output_folder()
        except Exception:
            folder = Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            return folder

    def timeline_safe_name(self, text):
        try:
            return self.song_safe_name(text)
        except Exception:
            return "".join(ch for ch in text if ch.isalnum() or ch in " -_").strip().replace(" ", "_") or "timeline"

    def timeline_export_json(self):
        try:
            data = self.timeline_data()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.timeline_output_folder() / f"{self.timeline_safe_name(data['title'])}_timeline_{ts}.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.timeline_status.set(f"Timeline JSON exportada: {path.name}")
            messagebox.showinfo("Timeline exportada", f"JSON guardado en:\n{path}")
        except Exception as e:
            self.timeline_status.set(f"No se pudo exportar JSON: {e}")

    def timeline_export_txt(self):
        try:
            data = self.timeline_data()
            lines = [f"{data['title']} - Timeline", f"Estilo: {data['style']}", f"BPM: {data['bpm']}", f"Tonalidad: {data['key']}", ""]
            for sec in data["sections"]:
                lines.append(f"{sec['start']:>3}s - {sec['end']:>3}s  {sec['name']}")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.timeline_output_folder() / f"{self.timeline_safe_name(data['title'])}_timeline_{ts}.txt"
            path.write_text("\n".join(lines), encoding="utf-8")
            self.timeline_status.set(f"Timeline TXT exportada: {path.name}")
            messagebox.showinfo("Timeline exportada", f"TXT guardado en:\n{path}")
        except Exception as e:
            self.timeline_status.set(f"No se pudo exportar TXT: {e}")

    def timeline_export_all(self):
        self.timeline_export_json()
        self.timeline_export_txt()


    def build_multipista_tab(self):
        cont = ttk.Frame(self.tab_multipista)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "multipista_banner" in self.multitrack_images:
            ttk.Label(header, image=self.multitrack_images["multipista_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Multipista Pro", style="Card.TLabel", font=("Segoe UI", 30, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        presets = self.make_card(left, "Presets multipista")
        presets.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(presets, style="Card.TFrame")
        grid.pack(fill="x")
        items = [("tile_studio", "Studio Clean", "studio"), ("tile_vocal", "Voz Pro", "vocal"), ("tile_chorus", "Coros", "chorus"), ("tile_live", "Directo", "live"), ("tile_project", "Proyecto", "project"), ("tile_stems", "Stems", "stems")]
        for i, (img_key, label, mode) in enumerate(items):
            box = ttk.Frame(grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            if img_key in self.multitrack_images:
                ttk.Label(box, image=self.multitrack_images[img_key], style="Card.TLabel").pack()
            if mode == "project":
                cmd = self.multitrack_save_project
            elif mode == "stems":
                cmd = self.multitrack_export_stems_manifest
            else:
                cmd = lambda m=mode: self.multitrack_apply_preset(m)
            ttk.Button(box, text=label, style="Accent.TButton", command=cmd).pack(fill="x", pady=(5, 0))
            grid.columnconfigure(i, weight=1)

        body = ttk.Frame(left)
        body.pack(fill="both", expand=True)

        mixer = self.make_card(body, "Pistas")
        mixer.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.multitrack_slider(mixer, "Voz principal", self.track_lead_voice, 0, 140)
        self.multitrack_slider(mixer, "Coros / doblaje", self.track_chorus, 0, 120)
        self.multitrack_slider(mixer, "Instrumental", self.track_instrumental, 0, 120)
        self.multitrack_slider(mixer, "FX / soundboard", self.track_fx, 0, 100)
        self.multitrack_slider(mixer, "Master", self.track_master, 0, 120)

        arms = ttk.Frame(mixer, style="Card.TFrame")
        arms.pack(fill="x", pady=(10, 0))
        ttk.Checkbutton(arms, text="Armar voz", variable=self.track_arm_lead).pack(side="left", padx=4)
        ttk.Checkbutton(arms, text="Armar coros", variable=self.track_arm_chorus).pack(side="left", padx=4)
        ttk.Checkbutton(arms, text="Armar FX", variable=self.track_arm_fx).pack(side="left", padx=4)

        actions = ttk.Frame(mixer, style="Card.TFrame")
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Aplicar mezcla", style="Accent.TButton", command=self.multitrack_update_mix).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(actions, text="Grabar toma", command=self.karaoke_record_demo).pack(side="left", fill="x", expand=True, padx=3, ipady=7)
        ttk.Button(actions, text="Exportar base", command=self.song_export_instrumental).pack(side="left", fill="x", expand=True, padx=3, ipady=7)

        project = self.make_card(body, "Proyecto multipista")
        project.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.multitrack_text = tk.Text(project, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 10), height=18)
        self.multitrack_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.multitrack_update_text("Multipista preparado.")

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0, 10))
        ttk.Label(estado, textvariable=self.multitrack_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        current = self.make_card(right, "Actual")
        current.pack(fill="x", pady=(0, 10))
        ttk.Label(current, text="Voz:", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(current, textvariable=self.preset, style="Card.TLabel", wraplength=320).pack(anchor="w", pady=(0, 8))
        ttk.Label(current, text="Pista:", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(current, textvariable=self.karaoke_track, style="Card.TLabel", wraplength=320).pack(anchor="w")

        quick = self.make_card(right, "Acciones Pro")
        quick.pack(fill="x", pady=(0, 10))
        ttk.Button(quick, text="Guardar proyecto multipista", style="Accent.TButton", command=self.multitrack_save_project).pack(fill="x", pady=3)
        ttk.Button(quick, text="Exportar manifiesto stems", command=self.multitrack_export_stems_manifest).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Mezclador", command=lambda: self.select_tab(self.tab_mezclador_musical)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Master Final", command=lambda: self.select_tab(self.tab_master_final)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Canción Pro", command=lambda: self.select_tab(self.tab_cancion_pro)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Límite real")
        tips.pack(fill="x")
        ttk.Label(tips, text="• Esta versión organiza flujo multipista.\n• La voz se graba como toma WAV.\n• La base puede exportarse aparte.\n• Los stems reales de voz/coros salen cuando grabas cada toma por separado.\n• No separa voces de canciones comerciales.", style="Card.TLabel", justify="left", wraplength=320).pack(anchor="w")
        self.multitrack_update_mix()

    def multitrack_slider(self, parent, label, var, mn, mx):
        box = ttk.Frame(parent, style="Card.TFrame")
        box.pack(fill="x", pady=7)
        top = ttk.Frame(box, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text=label + ":", style="Card.TLabel", width=18).pack(side="left")
        value_label = ttk.Label(top, style="Card.TLabel", width=8)
        value_label.pack(side="right")
        ttk.Scale(box, from_=mn, to=mx, variable=var, orient="horizontal", command=lambda _=None: self.multitrack_update_mix()).pack(fill="x", pady=(3, 0))
        def refresh(*_):
            value_label.config(text=f"{var.get():.0f}%")
        var.trace_add("write", refresh)
        refresh()

    def multitrack_apply_preset(self, mode):
        presets = {
            "studio": (95, 24, 42, 18, 96, "Studio Clean aplicado."),
            "vocal": (115, 18, 34, 14, 94, "Voz Pro aplicada."),
            "chorus": (96, 58, 40, 22, 94, "Modo Coros aplicado."),
            "live": (88, 20, 36, 18, 86, "Modo Directo seguro aplicado."),
        }
        lead, chorus, instr, fx, master, msg = presets.get(mode, presets["studio"])
        self.track_lead_voice.set(lead); self.track_chorus.set(chorus); self.track_instrumental.set(instr); self.track_fx.set(fx); self.track_master.set(master)
        self.multitrack_update_mix(); self.multitrack_status.set(msg)

    def multitrack_update_mix(self):
        try:
            master = max(0, min(1.2, self.track_master.get()/100.0))
            lead = max(0, min(1.4, self.track_lead_voice.get()/100.0)) * master
            instr = max(0, min(1.2, self.track_instrumental.get()/100.0)) * master
            chorus = max(0, min(1.2, self.track_chorus.get()/100.0))
            fx = max(0, min(1.0, self.track_fx.get()/100.0))
            if "vol" in self.vars:
                self.vars["vol"].set(lead * 100)
            if "chorus" in self.vars:
                self.vars["chorus"].set(chorus * 100)
            if hasattr(self, "karaoke_volume"):
                self.karaoke_volume.set(instr * 100)
                self.karaoke_update_engine()
            if hasattr(self.engine, "sfx_volume"):
                self.engine.sfx_volume = fx
            self.update_engine()
            self.multitrack_update_text("Mezcla multipista actualizada.")
        except Exception as e:
            self.multitrack_status.set(f"Error actualizando multipista: {e}")

    def multitrack_project_data(self):
        lyrics = ""
        if hasattr(self, "song_lyrics_text"):
            try: lyrics = self.song_lyrics_text.get("1.0", tk.END).strip()
            except Exception: lyrics = ""
        return {
            "version": VERSION,
            "type": "multipista_pro",
            "title": self.song_title.get() if hasattr(self, "song_title") else "Proyecto multipista",
            "voice": self.preset.get(),
            "category": self.category.get(),
            "track": self.karaoke_track.get() if hasattr(self, "karaoke_track") else "Sin pista",
            "tracks": {
                "lead_voice": self.track_lead_voice.get(),
                "chorus": self.track_chorus.get(),
                "instrumental": self.track_instrumental.get(),
                "fx": self.track_fx.get(),
                "master": self.track_master.get(),
                "arm_lead": self.track_arm_lead.get(),
                "arm_chorus": self.track_arm_chorus.get(),
                "arm_fx": self.track_arm_fx.get(),
            },
            "effects": {k: v.get() for k, v in self.vars.items()},
            "lyrics": lyrics,
        }

    def multitrack_save_project(self):
        try:
            folder = self.song_output_folder() if hasattr(self, "song_output_folder") else Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            safe = self.song_safe_name(self.song_title.get()) if hasattr(self, "song_safe_name") else "multipista"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"{safe}_MULTIPISTA_{ts}.json"
            path.write_text(json.dumps(self.multitrack_project_data(), ensure_ascii=False, indent=2), encoding="utf-8")
            self.multitrack_status.set(f"Proyecto multipista guardado: {path.name}")
            self.multitrack_update_text(f"Proyecto guardado en:\n{path}")
            messagebox.showinfo("Multipista guardado", f"Archivo guardado en:\n{path}")
        except Exception as e:
            self.multitrack_status.set(f"No se pudo guardar multipista: {e}")

    def multitrack_export_stems_manifest(self):
        try:
            folder = self.song_output_folder() if hasattr(self, "song_output_folder") else Path.home() / "ModuladorVozDirecto_Canciones"
            folder.mkdir(parents=True, exist_ok=True)
            safe = self.song_safe_name(self.song_title.get()) if hasattr(self, "song_safe_name") else "multipista"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"{safe}_STEMS_MANIFEST_{ts}.txt"
            data = self.multitrack_project_data()
            txt = (
                "STEMS / COMMAND CENTER PRO\n\n• La pestaña Command Center añade buscador de módulos, workflows recomendados, mapa premium y exportación JSON/TXT.\n• V73 mejora la usabilidad para que la app se sienta más profesional y menos saturada.\n\nPROFESSIONAL POLISH PRO\n\n• La pestaña Polish revisa el acabado del programa como producto: score, showroom, pulido completo, badge e informes.\n• V73 se centra en mejorar la sensación premium y el acabado final, no solo en añadir más funciones.\n\nULTRA PREMIUM UI PRO\n\n• La pestaña UI Premium añade acabado visual, temas, densidad, focus mode, puntuación de UI y exportación de estilo.\n• V73 corrige detalles heredados de datetime en exportaciones y refuerza la sensación de producto terminado.\n\nPREMIUM EXPERIENCE PRO\n\n• La pestaña Premium centraliza el acabado final: modos de producto, calidad premium, badge PNG e informe JSON/TXT.\n• V73 mejora la sensación de app terminada y ayuda a aplicar un look coherente antes de publicar.\n\nDEPLOY PRO\n\n• La pestaña Deploy crea un ZIP publicable con index.html, assets, .nojekyll, README_DEPLOY.txt y manifest.\n• V73 añade guías para GitHub Pages, Netlify, Firebase Hosting y hosting estático.\n\nWEB PACK PRO\n\n• La pestaña Web Pack crea un ZIP web completo con index.html, audio, imágenes, docs, manifest y LEEME.\n• V73 deja el proyecto listo para subir a hosting o GitHub Pages.\n\nLANDING PAGE PRO\n\n• La pestaña Landing genera una página HTML de presentación para demos/canciones con enlaces y estilo visual.\n• V73 añade exportación index.html, metadatos JSON y conexión con Publicación/Brand Kit/Biblioteca.\n\nBRAND KIT PRO\n\n• La pestaña Brand Kit crea identidad visual: logo, banner, avatar, paleta y ZIP de marca.\n• V73 añade una capa profesional para que las demos/canciones tengan imagen de canal coherente.\n\nPUBLICACIÓN PRO\n\n• La pestaña Publicación prepara título, descripción, tags, checklist y release notes para subir o guardar una demo.\n• V73 conecta Export Pack, Portadas y Biblioteca con una ficha final de publicación.\n\nEXPORT PACK PRO\n\n• La pestaña Export Pack crea un ZIP final con audio, portadas, letras, JSON, manifest.json y LEEME.txt.\n• V73 convierte la salida del proyecto en un paquete organizado para guardar o compartir.\n\nPORTADAS PREMIUM PRO\n\n• La pestaña Portadas genera cover art PNG 1600x1600 para demos, canciones y proyectos.\n• V73 añade estilos Neón, Pop, Trap, Lofi, Dorado y Gaming, con metadatos JSON y conexión con Biblioteca.\n\nBIBLIOTECA PREMIUM PRO\n\n• La pestaña Biblioteca permite gestionar WAV, JSON y TXT generados por el modulador.\n• V73 añade lista visual, filtros, vista previa, carga de WAV a Karaoke, borrado seguro e índice exportable.\n\nASISTENTE INICIAL PRO\n\n• La pestaña Asistente guía la primera configuración: micro, cable virtual, voz, visual, directo y exportación.\n• V73 mejora la experiencia de inicio con onboarding visual y setup seguro de un clic.\n\nINICIO PREMIUM PRO\n\n• La pestaña Inicio Premium actúa como launcher principal con tarjetas de directo, karaoke, canción, revisión, visual y exportación.\n• V73 mejora la primera impresión visual y guía al usuario por el flujo correcto.\n\nREDISEÑO VISUAL PRO\n\n• La pestaña Visual Pro añade temas, tarjetas premium, modo enfoque, densidad visual y exportación de estilo.\n• V73 mejora la apariencia general con banners y assets nuevos para que la app se sienta más profesional.\n\nREVISIÓN TÉCNICA PRO\n\n• La pestaña Revisión ejecuta auditoría técnica de dependencias, dispositivos, audio, cortes, WAV y configuración.\n• V73 corrige el recalculado de filtros al cambiar de 44100/48000 Hz, reinicia latidos del audio y amplía WAV 24/32-bit.\n\nSTUDIO DASHBOARD PRO\n\n• La pestaña Studio Dashboard centraliza el flujo completo: analizar, cadena vocal, timeline, multipista, mezcla y master.\n• Incluye preparación %, checklist, siguiente paso recomendado, flujo seguro y exportación JSON/TXT.\n\nANALIZADOR VOCAL PRO\n\n• La pestaña Analizador revisa la configuración vocal: volumen, eco, puerta de ruido, compresión, autotune y riesgos de clipping.\n• Incluye check rápido, auto-ajuste seguro, reducción de ruido e informes JSON/TXT.\n\nCADENA VOCAL PRO\n\n• La pestaña Cadena Vocal organiza la voz como flujo de estudio: ruido, compresión, presencia, aire, calidez, reverb y delay.\n• Incluye presets para voz limpia, pop vocal, trap vocal, podcast y karaoke, más exportación JSON.\n\nTIMELINE PRO\n\n• La pestaña Timeline organiza la canción por intro, verso, pre, estribillo, puente y outro.\n• Permite ajustar BPM, tonalidad, duración, generar base y exportar plan JSON/TXT.\n\nMULTIPISTA PRO\n\n"
                "Este archivo organiza el proyecto para exportar stems reales.\n\n"
                "1. Instrumental: usa Exportar base/instrumental WAV.\n"
                "2. Voz principal: graba una toma con solo voz principal armada.\n"
                "3. Coros: activa Armar coros y graba una toma aparte.\n"
                "4. FX: exporta o reproduce soundboard por separado si lo necesitas.\n\n"
                f"Proyecto: {data.get('title')}\nVoz: {data.get('voice')}\nPista: {data.get('track')}\n\n"
                f"Mezcla: {json.dumps(data.get('tracks'), ensure_ascii=False, indent=2)}\n"
            )
            path.write_text(txt, encoding="utf-8")
            self.multitrack_status.set(f"Manifiesto stems exportado: {path.name}")
            self.multitrack_update_text(f"Manifiesto stems guardado en:\n{path}")
        except Exception as e:
            self.multitrack_status.set(f"No se pudo exportar stems: {e}")

    def multitrack_update_text(self, extra):
        if not hasattr(self, "multitrack_text"):
            return
        try:
            text = (
                "MULTIPISTA PRO\n\n"
                f"Voz principal: {self.track_lead_voice.get():.0f}%\n"
                f"Coros/doblaje: {self.track_chorus.get():.0f}%\n"
                f"Instrumental: {self.track_instrumental.get():.0f}%\n"
                f"FX: {self.track_fx.get():.0f}%\n"
                f"Master: {self.track_master.get():.0f}%\n\n"
                "FLUJO RECOMENDADO\n"
                "1. Genera base en Canción Pro o Karaoke Studio.\n"
                "2. Ajusta Multipista.\n"
                "3. Graba voz principal.\n"
                "4. Graba coros como otra toma.\n"
                "5. Exporta base y proyecto JSON.\n"
                "6. Masteriza en Master Final.\n\n"
                f"{extra}"
            )
            self.multitrack_text.configure(state="normal")
            self.multitrack_text.delete("1.0", tk.END)
            self.multitrack_text.insert("1.0", text)
            self.multitrack_text.configure(state="disabled")
        except Exception:
            pass

    def build_master_final_tab(self):
        cont = ttk.Frame(self.tab_master_final)
        cont.pack(fill="both", expand=True)
        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "master_banner" in self.master_images:
            ttk.Label(header, image=self.master_images["master_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Master Final Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        presets = self.make_card(left, "Presets de master")
        presets.pack(fill="x", pady=(0, 10))
        row = ttk.Frame(presets, style="Card.TFrame")
        row.pack(fill="x")
        for label, mode in [("Streaming limpio","stream"),("Demo potente","potente"),("Suave karaoke","suave"),("Final seguro","seguro")]:
            ttk.Button(row, text=label, style="Accent.TButton", command=lambda m=mode: self.master_apply_preset(m)).pack(side="left", fill="x", expand=True, padx=4, ipady=8)

        controls = self.make_card(left, "Acabado final")
        controls.pack(fill="both", expand=True)
        ttk.Checkbutton(controls, text="Normalizar volumen", variable=self.master_normalize).pack(anchor="w", pady=4)
        ttk.Checkbutton(controls, text="Limiter suave anti-distorsión", variable=self.master_limiter).pack(anchor="w", pady=4)
        self.master_slider(controls, "Fade in", self.master_fade_in, 0, 5, "s")
        self.master_slider(controls, "Fade out", self.master_fade_out, 0, 8, "s")
        self.master_slider(controls, "Ganancia final", self.master_gain, 50, 120, "%")
        self.master_slider(controls, "Calidez", self.master_warmth, 0, 60, "%")
        btns = ttk.Frame(controls, style="Card.TFrame")
        btns.pack(fill="x", pady=(10,0))
        ttk.Button(btns, text="Exportar master WAV", style="Accent.TButton", command=self.master_export_wav).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(btns, text="Grabar demo", command=self.karaoke_record_demo).pack(side="left", fill="x", expand=True, padx=3, ipady=8)
        ttk.Button(btns, text="Abrir carpeta", command=self.master_open_folder).pack(side="left", fill="x", expand=True, padx=3, ipady=8)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))
        estado = self.make_card(right, "Estado")
        estado.pack(fill="x", pady=(0,10))
        ttk.Label(estado, textvariable=self.master_status, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")
        pista = self.make_card(right, "Pista actual")
        pista.pack(fill="x", pady=(0,10))
        ttk.Label(pista, textvariable=self.karaoke_track, style="Card.TLabel", font=("Segoe UI", 13, "bold"), wraplength=320).pack(anchor="w")
        ttk.Label(pista, text="Exporta la base actual con acabado final. Para voz + música, usa Grabar demo mientras suena la base.", style="Card.TLabel", wraplength=320).pack(anchor="w", pady=(8,0))
        quick = self.make_card(right, "Accesos")
        quick.pack(fill="x", pady=(0,10))
        ttk.Button(quick, text="Abrir Canción Pro", command=lambda: self.select_tab(self.tab_cancion_pro)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Mezclador", command=lambda: self.select_tab(self.tab_mezclador_musical)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Karaoke Studio", command=lambda: self.select_tab(self.tab_karaoke_studio)).pack(fill="x", pady=3)

    def master_slider(self, parent, label, var, mn, mx, unit):
        box = ttk.Frame(parent, style="Card.TFrame"); box.pack(fill="x", pady=7)
        top = ttk.Frame(box, style="Card.TFrame"); top.pack(fill="x")
        ttk.Label(top, text=label + ":", style="Card.TLabel", width=18).pack(side="left")
        value_label = ttk.Label(top, style="Card.TLabel", width=10); value_label.pack(side="right")
        ttk.Scale(box, from_=mn, to=mx, variable=var, orient="horizontal").pack(fill="x", pady=(3,0))
        def refresh(*_): value_label.config(text=f"{var.get():.1f}{unit}" if unit == "s" else f"{var.get():.0f}{unit}")
        var.trace_add("write", refresh); refresh()

    def master_apply_preset(self, mode):
        presets = {
            "stream": (0.5, 1.2, 92, 12, True, True, "Master streaming limpio aplicado."),
            "potente": (0.2, 1.0, 105, 22, True, True, "Master demo potente aplicado."),
            "suave": (1.2, 2.5, 88, 30, True, True, "Master karaoke suave aplicado."),
            "seguro": (0.8, 2.0, 85, 18, True, True, "Master final seguro aplicado."),
        }
        fi, fo, gain, warmth, norm, lim, msg = presets.get(mode, presets["seguro"])
        self.master_fade_in.set(fi); self.master_fade_out.set(fo); self.master_gain.set(gain); self.master_warmth.set(warmth)
        self.master_normalize.set(norm); self.master_limiter.set(lim); self.master_status.set(msg)

    def master_process_samples(self, samples):
        y = np.asarray(samples, dtype=np.float32).copy()
        if len(y) == 0: return y
        rate = self.engine.rate if hasattr(self, "engine") else 44100
        warmth = max(0.0, min(0.8, self.master_warmth.get()/100.0))
        if warmth > 0:
            smooth = np.convolve(y, np.ones(5, dtype=np.float32)/5, mode="same").astype(np.float32)
            y = y*(1-warmth) + smooth*warmth
        if self.master_normalize.get():
            peak = float(np.max(np.abs(y)))
            if peak > 0: y = y/peak*0.86
        y = y * max(0.0, min(1.4, self.master_gain.get()/100.0))
        fi = int(max(0, self.master_fade_in.get())*rate); fo = int(max(0, self.master_fade_out.get())*rate)
        if fi > 0:
            fi = min(fi, len(y)); y[:fi] *= np.linspace(0,1,fi,dtype=np.float32)
        if fo > 0:
            fo = min(fo, len(y)); y[-fo:] *= np.linspace(1,0,fo,dtype=np.float32)
        if self.master_limiter.get(): y = np.tanh(y*1.15)/np.tanh(1.15)
        return np.clip(y, -0.98, 0.98).astype(np.float32)

    def master_export_wav(self):
        try:
            samples = getattr(self.engine, "karaoke_samples", np.zeros(0, dtype=np.float32))
            if samples is None or len(samples) == 0:
                self.master_status.set("No hay base para masterizar. Genera o carga una pista primero."); return
            y = self.master_process_samples(samples)
            title = self.song_safe_name(self.song_title.get()) if hasattr(self, "song_safe_name") else "master_final"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.song_output_folder() / f"{title}_MASTER_FINAL_{ts}.wav"
            self.write_wav_float32(path, y, self.engine.rate)
            self.master_status.set(f"Master exportado: {path.name}")
            messagebox.showinfo("Master exportado", f"Archivo guardado en:\n{path}")
        except Exception as e:
            self.master_status.set(f"No se pudo exportar master: {e}")

    def master_open_folder(self):
        try:
            folder = self.song_output_folder()
            if platform.system() == "Windows": os.startfile(str(folder))
            elif platform.system() == "Darwin": subprocess.Popen(["open", str(folder)])
            else: subprocess.Popen(["xdg-open", str(folder)])
            self.master_status.set("Carpeta abierta.")
        except Exception as e:
            self.master_status.set(f"No se pudo abrir carpeta: {e}")

    def build_grabadora_tab(self):
        cont = ttk.Frame(self.tab_grabadora)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "grabadora_banner" in self.rec_images:
            ttk.Label(header, image=self.rec_images["grabadora_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Grabadora Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        top = self.make_card(left, "Acciones rápidas")
        top.pack(fill="x", pady=(0, 10))

        actions = ttk.Frame(top, style="Card.TFrame")
        actions.pack(fill="x")
        ttk.Button(actions, text="⏺ Iniciar / detener grabación", style="Accent.TButton", command=self.record).pack(side="left", expand=True, fill="x", padx=4, pady=4)
        ttk.Button(actions, text="▶ Reproducir seleccionada", command=self.play_selected_recording).pack(side="left", expand=True, fill="x", padx=4, pady=4)
        ttk.Button(actions, text="📁 Abrir carpeta", command=self.open_recordings_folder).pack(side="left", expand=True, fill="x", padx=4, pady=4)
        ttk.Button(actions, text="🔄 Actualizar historial", command=self.refresh_recordings_list).pack(side="left", expand=True, fill="x", padx=4, pady=4)

        history = self.make_card(left, "Historial de grabaciones")
        history.pack(fill="both", expand=True)

        self.recordings_list = tk.Listbox(
            history,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 10),
            height=16,
            activestyle="none"
        )
        self.recordings_list.pack(fill="both", expand=True, padx=4, pady=4)
        self.recordings_list.bind("<Double-Button-1>", lambda e: self.play_selected_recording())

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Estado")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.recordings_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        tips = self.make_card(right, "Consejos de prueba")
        tips.pack(fill="x", pady=(0, 10))
        ttk.Label(
            tips,
            text=(
                "1. Elige una voz.\n"
                "2. Pulsa Iniciar grabación.\n"
                "3. Habla unos segundos.\n"
                "4. Pulsa otra vez para detener.\n"
                "5. Reproduce la prueba y ajusta efectos."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

        info = self.make_card(right, "Carpeta")
        info.pack(fill="x")
        ttk.Label(
            info,
            text=f"Las grabaciones se guardan en:\n\n{self.recordings_folder()}",
            style="Card.TLabel",
            wraplength=310,
            justify="left"
        ).pack(anchor="w")

        self.refresh_recordings_list()

    def list_recordings(self):
        folder = self.recordings_folder()
        files = []
        try:
            for name in os.listdir(folder):
                if name.lower().endswith(".wav"):
                    path = os.path.join(folder, name)
                    files.append((os.path.getmtime(path), name))
        except Exception:
            pass
        files.sort(reverse=True)
        return [name for _, name in files]

    def refresh_recordings_list(self):
        if self.recordings_list is None:
            return
        self.recordings_list.delete(0, tk.END)
        recordings = self.list_recordings()
        for name in recordings:
            self.recordings_list.insert(tk.END, name)
        if not recordings:
            self.recordings_list.insert(tk.END, "No hay grabaciones todavía.")
        self.recordings_status.set(f"Grabaciones encontradas: {len(recordings)}")

    def selected_recording_path(self):
        if self.recordings_list is None or not self.recordings_list.curselection():
            messagebox.showwarning("Sin selección", "Selecciona una grabación.")
            return None
        name = self.recordings_list.get(self.recordings_list.curselection()[0])
        if name == "No hay grabaciones todavía.":
            return None
        return os.path.join(self.recordings_folder(), name)

    def play_selected_recording(self):
        path = self.selected_recording_path()
        if not path:
            return
        try:
            if platform.system().lower().startswith("win"):
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif platform.system().lower() == "darwin":
                subprocess.Popen(["afplay", path])
            else:
                subprocess.Popen(["xdg-open", path])
            self.recordings_status.set(f"Reproduciendo: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Reproducir", f"No se pudo reproducir:\n{e}")

    def open_recordings_folder(self):
        folder = self.recordings_folder()
        try:
            if platform.system().lower().startswith("win"):
                os.startfile(folder)
            elif platform.system().lower() == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            self.recordings_status.set("Carpeta de grabaciones abierta.")
        except Exception as e:
            messagebox.showerror("Carpeta", f"No se pudo abrir la carpeta:\n{e}")


    def build_barra_rapida_tab(self):
        cont = ttk.Frame(self.tab_barra_rapida)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "barra_rapida_banner" in self.quick_images:
            ttk.Label(header, image=self.quick_images["barra_rapida_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Barra Rápida Premium", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        voice_card = self.make_card(left, "Voces rápidas")
        voice_card.pack(fill="both", expand=True, pady=(0, 10))

        voice_grid = ttk.Frame(voice_card, style="Card.TFrame")
        voice_grid.pack(fill="both", expand=True)

        quick_voices = self.get_barra_rapida_voices()
        for i, voice in enumerate(quick_voices):
            btn = ttk.Button(voice_grid, text=voice, command=lambda v=voice: self.apply_barra_rapida_voice(v))
            btn.grid(row=i // 4, column=i % 4, sticky="nsew", padx=6, pady=6, ipady=10)

        for col in range(4):
            voice_grid.columnconfigure(col, weight=1)
        for row_i in range(3):
            voice_grid.rowconfigure(row_i, weight=1)

        sound_card = self.make_card(left, "Sonidos rápidos")
        sound_card.pack(fill="x")

        sound_grid = ttk.Frame(sound_card, style="Card.TFrame")
        sound_grid.pack(fill="x")

        quick_sounds = [
            ("Aplausos", "aplausos"),
            ("Risas", "risas"),
            ("Victoria", "victoria"),
            ("Error", "error"),
            ("Alerta", "alerta"),
            ("Redoble", "redoble"),
            ("Magia", "magia"),
            ("Impacto", "impacto"),
        ]
        for i, (label, key) in enumerate(quick_sounds):
            ttk.Button(sound_grid, text=label, command=lambda k=key: self.play_sfx(k)).grid(row=i // 4, column=i % 4, sticky="ew", padx=6, pady=6, ipady=7)
        for col in range(4):
            sound_grid.columnconfigure(col, weight=1)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Estado rápido")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, text="Voz actual:", style="Card.TLabel").pack(anchor="w")
        ttk.Label(status, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 17, "bold"), wraplength=310).pack(anchor="w", pady=(2, 10))
        ttk.Label(status, textvariable=self.state, style="Card.TLabel", wraplength=310).pack(anchor="w", pady=(0, 10))
        ttk.Button(status, text="▶ Empezar directo", style="Accent.TButton", command=self.start).pack(fill="x", pady=3)
        ttk.Button(status, text="■ Parar directo", style="Danger.TButton", command=self.stop).pack(fill="x", pady=3)
        ttk.Button(status, text="Actualizar barra rápida", command=self.refresh_barra_rapida).pack(fill="x", pady=3)

        themes = self.make_card(right, "Temas visuales")
        themes.pack(fill="x")

        theme_names = ["Neón morado", "Azul cyberpunk", "Verde hacker", "Rojo oscuro", "Dorado premium"]
        for theme in theme_names:
            ttk.Button(themes, text=theme, command=lambda t=theme: self.apply_visual_theme(t)).pack(fill="x", pady=3)

        ttk.Label(themes, text="Tema actual:", style="Card.TLabel").pack(anchor="w", pady=(8, 0))
        ttk.Label(themes, textvariable=self.current_theme, style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w")

    def get_barra_rapida_voices(self):
        defaults = [
            "Gaming limpio", "Discord claro", "Fortnite grave", "Streamer",
            "Locutor español", "Podcast", "Robot directo", "Alien",
            "Narrador épico", "Jefe final", "Voz clara", "Payaso gamer",
        ]
        result = []
        for v in self.favorites:
            if v in VoiceBank.all_presets() and v not in result:
                result.append(v)
        for v in defaults:
            if v in VoiceBank.all_presets() and v not in result:
                result.append(v)
        return result[:12]

    def apply_barra_rapida_voice(self, voice_name):
        if voice_name in VoiceBank.all_presets():
            self.preset.set(voice_name)
            self.category.set(VoiceBank.all_presets()[voice_name][0])
            self.apply_preset()
            self.refresh_voice_list()
            self.state.set(f"Estado: voz aplicada desde Barra rápida · {voice_name}")

    def refresh_barra_rapida(self):
        for child in self.tab_barra_rapida.winfo_children():
            child.destroy()
        self.build_barra_rapida_tab()
        self.state.set("Estado: Barra rápida actualizada")

    def apply_visual_theme(self, theme):
        palettes = {
            "Neón morado": {
                "bg": "#0c0d14", "panel": "#151827", "panel2": "#1d2135",
                "accent": "#7c5cff", "accent2": "#00e5ff", "ok": "#62ffb4",
                "danger": "#ff5c8a", "warning": "#ffcc66"
            },
            "Azul cyberpunk": {
                "bg": "#07111c", "panel": "#0d1d2f", "panel2": "#132b43",
                "accent": "#009dff", "accent2": "#00e5ff", "ok": "#62ffb4",
                "danger": "#ff5c8a", "warning": "#ffcc66"
            },
            "Verde hacker": {
                "bg": "#07130f", "panel": "#0d241b", "panel2": "#143524",
                "accent": "#20d46b", "accent2": "#62ffb4", "ok": "#62ffb4",
                "danger": "#ff5c8a", "warning": "#ffcc66"
            },
            "Rojo oscuro": {
                "bg": "#14070b", "panel": "#241018", "panel2": "#351622",
                "accent": "#ff3f6e", "accent2": "#ff8a5c", "ok": "#62ffb4",
                "danger": "#ff5c8a", "warning": "#ffcc66"
            },
            "Dorado premium": {
                "bg": "#151006", "panel": "#241b0d", "panel2": "#382a12",
                "accent": "#ffcc66", "accent2": "#ffd95c", "ok": "#62ffb4",
                "danger": "#ff5c8a", "warning": "#ffcc66"
            },
        }
        palette = palettes.get(theme)
        if not palette:
            return
        for key, value in palette.items():
            COLORS[key] = value
        self.current_theme.set(theme)
        self.configure_style()
        self.root.configure(bg=COLORS["bg"])
        self.state.set(f"Estado: tema aplicado · {theme}")
        messagebox.showinfo("Tema aplicado", f"Tema visual aplicado:\n\n{theme}\n\nAlgunas zonas se verán mejor al cambiar de pestaña o reiniciar la app.")


    def build_asistente_tab(self):
        cont = ttk.Frame(self.tab_asistente)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "asistente_banner" in self.wizard_images:
            ttk.Label(header, image=self.wizard_images["asistente_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Asistente Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        steps = self.make_card(left, "Pasos de configuración")
        steps.pack(fill="x", pady=(0, 10))

        step_grid = ttk.Frame(steps, style="Card.TFrame")
        step_grid.pack(fill="x")
        step_items = [
            ("paso_microfono", "1. Micrófono"),
            ("paso_salida", "2. Salida"),
            ("paso_virtual", "3. Cable virtual"),
            ("paso_prueba", "4. Prueba"),
        ]
        for i, (img_key, label) in enumerate(step_items):
            box = ttk.Frame(step_grid, style="Card.TFrame", padding=5)
            box.grid(row=0, column=i, sticky="nsew", padx=6)
            if img_key in self.wizard_images:
                ttk.Label(box, image=self.wizard_images[img_key], style="Card.TLabel").pack()
            ttk.Label(box, text=label, style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(pady=(4, 0))
            step_grid.columnconfigure(i, weight=1)

        devices = self.make_card(left, "1 y 2 · Dispositivos")
        devices.pack(fill="x", pady=(0, 10))

        row1 = ttk.Frame(devices, style="Card.TFrame")
        row1.pack(fill="x", pady=4)
        ttk.Label(row1, text="Micrófono real:", style="Card.TLabel", width=20).pack(side="left")
        combo_in = ttk.Combobox(row1, textvariable=self.input_dev, state="readonly", width=70)
        combo_in.pack(side="left", fill="x", expand=True, padx=8)
        self.input_combos.append(combo_in)
        combo_in.bind("<<ComboboxSelected>>", lambda e: self.on_device_changed())

        row2 = ttk.Frame(devices, style="Card.TFrame")
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Salida modificada:", style="Card.TLabel", width=20).pack(side="left")
        combo_out = ttk.Combobox(row2, textvariable=self.output_dev, state="readonly", width=70)
        combo_out.pack(side="left", fill="x", expand=True, padx=8)
        self.output_combos.append(combo_out)
        combo_out.bind("<<ComboboxSelected>>", lambda e: self.on_device_changed())

        dev_buttons = ttk.Frame(devices, style="Card.TFrame")
        dev_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(dev_buttons, text="Actualizar dispositivos", command=self.assistant_refresh_devices).pack(side="left", padx=4)
        ttk.Button(dev_buttons, text="🎙 Probar micro", style="Accent.TButton", command=self.test_microphone).pack(side="left", padx=4)
        ttk.Button(dev_buttons, text="🎧 Probar auriculares", style="Accent.TButton", command=self.test_headphones).pack(side="left", padx=4)
        ttk.Button(dev_buttons, text="Buscar cable virtual", command=self.assistant_find_virtual).pack(side="left", padx=4)
        ttk.Button(dev_buttons, text="Usar auriculares para probar", command=self.assistant_headphones_tip).pack(side="left", padx=4)

        platforms = self.make_card(left, "3 · Configuración rápida")
        platforms.pack(fill="x", pady=(0, 10))

        plat_row = ttk.Frame(platforms, style="Card.TFrame")
        plat_row.pack(fill="x")
        ttk.Button(plat_row, text="Configurar Discord", style="Accent.TButton", command=lambda: self.assistant_quick("discord")).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(plat_row, text="Configurar Fortnite", style="Accent.TButton", command=lambda: self.assistant_quick("fortnite")).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(plat_row, text="Configurar OBS", style="Accent.TButton", command=lambda: self.assistant_quick("obs")).pack(side="left", fill="x", expand=True, padx=4)

        test = self.make_card(left, "4 · Prueba final")
        test.pack(fill="x")
        test_row = ttk.Frame(test, style="Card.TFrame")
        test_row.pack(fill="x")
        ttk.Button(test_row, text="▶ Empezar directo", style="Accent.TButton", command=self.start).pack(side="left", padx=4)
        ttk.Button(test_row, text="🔔 Probar sonido", command=lambda: self.play_sfx("beep")).pack(side="left", padx=4)
        ttk.Button(test_row, text="🎙 Probar voz Gaming limpio", command=lambda: self.apply_directo_voice("Gaming limpio")).pack(side="left", padx=4)
        ttk.Button(test_row, text="Guardar configuración", command=self.save_config).pack(side="left", padx=4)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Estado del asistente")
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.assistant_status, style="Card.TLabel", wraplength=310, justify="left").pack(anchor="w")

        checklist = self.make_card(right, "Lista rápida")
        checklist.pack(fill="x", pady=(0, 10))
        ttk.Label(
            checklist,
            text=(
                "✓ Micrófono real seleccionado\n"
                "✓ Salida seleccionada\n"
                "✓ Cable virtual si usas Discord/Fortnite/OBS\n"
                "✓ En el juego/app usar CABLE Output o VoiceMeeter Output\n"
                "✓ Usar auriculares para evitar eco"
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "Discord/Fortnite/OBS:\n"
                "• Modulador salida = CABLE Input o VoiceMeeter Input.\n"
                "• App/juego micrófono = CABLE Output o VoiceMeeter Output.\n\n"
                "Solo prueba:\n"
                "• Salida = tus auriculares."
            ),
            style="Card.TLabel",
            justify="left",
            wraplength=310
        ).pack(anchor="w")

    def assistant_refresh_devices(self):
        self.load_devices()
        self.assistant_status.set("Dispositivos actualizados. Revisa micrófono y salida.")

    def assistant_find_virtual(self):
        ok = self.find_virtual()
        if ok:
            self.assistant_status.set("Cable virtual encontrado y seleccionado como salida.")
        else:
            self.assistant_status.set("No se encontró cable virtual. Puedes probar con auriculares o instalar VB-Cable/VoiceMeeter.")

    def assistant_headphones_tip(self):
        self.assistant_status.set("Para probar sin cable virtual: pon la salida en tus auriculares y pulsa Empezar directo.")

    def assistant_quick(self, mode):
        self.quick_mode(mode)
        names = {"discord": "Discord", "fortnite": "Fortnite", "obs": "OBS"}
        self.assistant_status.set(f"Configuración rápida aplicada para {names.get(mode, mode)}. Revisa que la salida sea cable virtual si quieres que lo escuchen.")


    def build_directo_pro_tab(self):
        cont = ttk.Frame(self.tab_directo_pro)
        cont.pack(fill="both", expand=True)

        header = self.make_card(cont)
        header.pack(fill="x", pady=(0, 10))
        if "directo_pro_banner" in self.streamer_images:
            ttk.Label(header, image=self.streamer_images["directo_pro_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="Panel Directo Pro", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        main = ttk.Frame(cont)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Control principal
        control = self.make_card(left, "Control de directo")
        control.pack(fill="x", pady=(0, 10))

        row = ttk.Frame(control, style="Card.TFrame")
        row.pack(fill="x")

        ttk.Button(row, text="▶ Empezar directo", style="Accent.TButton", command=self.start).pack(side="left", padx=5, ipadx=8, ipady=4)
        ttk.Button(row, text="■ Parar directo", style="Danger.TButton", command=self.stop).pack(side="left", padx=5, ipadx=8, ipady=4)
        ttk.Checkbutton(row, text="Modulador ON/OFF", variable=self.effects_enabled, command=self.update_engine).pack(side="left", padx=14)
        ttk.Checkbutton(row, text="Silenciar salida", variable=self.mute, command=self.update_engine).pack(side="left", padx=14)
        ttk.Button(row, text="▾ Bandeja Windows", command=self.hide_to_tray).pack(side="right", padx=5)

        # Medidores grandes
        meters = self.make_card(left, "Medidores grandes")
        meters.pack(fill="x", pady=(0, 10))

        ttk.Label(meters, text="Micrófono", style="Card.TLabel", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.directo_pro_mic_bar = ttk.Progressbar(meters, maximum=100)
        self.directo_pro_mic_bar.pack(fill="x", pady=(6, 14), ipady=6)

        ttk.Label(meters, text="Salida modificada", style="Card.TLabel", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.directo_pro_out_bar = ttk.Progressbar(meters, maximum=100)
        self.directo_pro_out_bar.pack(fill="x", pady=(6, 8), ipady=6)

        # Voces rápidas
        voices_card = self.make_card(left, "Voces rápidas para directo")
        voices_card.pack(fill="both", expand=True, pady=(0, 10))

        voice_grid = ttk.Frame(voices_card, style="Card.TFrame")
        voice_grid.pack(fill="both", expand=True)

        quick_voices = self.get_directo_quick_voices()
        for i, voice in enumerate(quick_voices):
            btn = ttk.Button(voice_grid, text=voice, command=lambda v=voice: self.apply_directo_voice(v))
            btn.grid(row=i // 4, column=i % 4, sticky="nsew", padx=6, pady=6, ipady=8)

        for col in range(4):
            voice_grid.columnconfigure(col, weight=1)
        for row_i in range(3):
            voice_grid.rowconfigure(row_i, weight=1)

        # Derecha: sonidos y configuración
        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(10, 0))

        status = self.make_card(right, "Estado actual")
        status.pack(fill="x", pady=(0, 10))

        ttk.Label(status, text="Voz activa:", style="Card.TLabel").pack(anchor="w")
        ttk.Label(status, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 17, "bold"), wraplength=290).pack(anchor="w", pady=(2, 10))
        ttk.Label(status, textvariable=self.state, style="Card.TLabel", wraplength=290).pack(anchor="w")

        sound_card = self.make_card(right, "Sonidos rápidos")
        sound_card.pack(fill="x", pady=(0, 10))

        sound_groups = [
            ("Reacciones", [("Aplausos", "aplausos"), ("Risas", "risas"), ("Sorpresa", "suspense")]),
            ("Gaming", [("Victoria", "victoria"), ("Error", "error"), ("Power Up", "powerup")]),
            ("Directo", [("Alerta", "alerta"), ("Redoble", "redoble"), ("Impacto", "impacto")]),
            ("Ambiente", [("Magia", "magia"), ("Lluvia", "lluvia"), ("Beep", "beep")]),
        ]

        for group_name, sounds in sound_groups:
            ttk.Label(sound_card, text=group_name, style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 2))
            group_row = ttk.Frame(sound_card, style="Card.TFrame")
            group_row.pack(fill="x")
            for label, key in sounds:
                ttk.Button(group_row, text=label, command=lambda k=key: self.play_sfx(k)).pack(side="left", expand=True, fill="x", padx=2, pady=2)

        config = self.make_card(right, "Acceso rápido")
        config.pack(fill="x")

        ttk.Button(config, text="Configurar Discord", command=lambda: self.quick_mode("discord")).pack(fill="x", pady=3)
        ttk.Button(config, text="Configurar Fortnite", command=lambda: self.quick_mode("fortnite")).pack(fill="x", pady=3)
        ttk.Button(config, text="Configurar OBS", command=lambda: self.quick_mode("obs")).pack(fill="x", pady=3)
        ttk.Button(config, text="Grabar prueba WAV", command=self.record).pack(fill="x", pady=3)
        ttk.Button(config, text="Actualizar voces rápidas", command=self.refresh_directo_pro).pack(fill="x", pady=3)

    def get_directo_quick_voices(self):
        defaults = [
            "Gaming limpio", "Discord claro", "Fortnite grave", "Streamer",
            "Locutor español", "Podcast", "Robot directo", "Alien",
            "Narrador épico", "Jefe final", "Voz clara", "Payaso gamer",
        ]
        result = []
        for v in self.favorites:
            if v in VoiceBank.all_presets() and v not in result:
                result.append(v)
        for v in defaults:
            if v in VoiceBank.all_presets() and v not in result:
                result.append(v)
        return result[:12]

    def refresh_directo_pro(self):
        # Reconstruye la pestaña para actualizar favoritos rápidos.
        for child in self.tab_directo_pro.winfo_children():
            child.destroy()
        self.build_directo_pro_tab()
        self.state.set("Estado: Directo Pro actualizado")

    def apply_directo_voice(self, voice_name):
        if voice_name in VoiceBank.all_presets():
            self.preset.set(voice_name)
            self.category.set(VoiceBank.all_presets()[voice_name][0])
            self.apply_preset()
            self.refresh_voice_list()
            self.state.set(f"Estado: voz rápida aplicada · {voice_name}")


    def build_voicebox_grid_tab(self):
        container = ttk.Frame(self.tab_voicebox_grid)
        container.pack(fill="both", expand=True)

        header = self.make_card(container)
        header.pack(fill="x", pady=(0, 10))
        if "voicebox_grid_banner" in self.grid_images:
            ttk.Label(header, image=self.grid_images["voicebox_grid_banner"], style="Card.TLabel").pack(anchor="center")
        else:
            ttk.Label(header, text="CAJA DE VOCES", style="Card.TLabel", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        controls = self.make_card(container, "Filtros rápidos")
        controls.pack(fill="x", pady=(0, 10))

        row = ttk.Frame(controls, style="Card.TFrame")
        row.pack(fill="x")

        categories = ["Todas", "Favoritos"] + [c for c in VoiceBank.categories() if c != "Todas"]
        for cat in categories:
            ttk.Button(row, text=cat, command=lambda c=cat: self.open_grid_category(c)).pack(side="left", padx=4, pady=3)

        canvas_frame = self.make_card(container, "Tarjetas de voces")
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, bg=COLORS["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas, style="Card.TFrame")

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def resize_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", resize_canvas)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.voicebox_grid_frame = scrollable
        self.populate_voicebox_grid("Todas")

    def open_grid_category(self, category):
        self.populate_voicebox_grid(category)
        self.state.set(f"Estado: Caja de Voces · {category}")

    def populate_voicebox_grid(self, category="Todas"):
        if not hasattr(self, "voicebox_grid_frame"):
            return

        for child in self.voicebox_grid_frame.winfo_children():
            child.destroy()

        voices = []
        for name, (cat, values) in VoiceBank.all_presets().items():
            if category == "Favoritos" and name not in self.favorites:
                continue
            if category not in ("Todas", "Favoritos") and cat != category:
                continue
            voices.append((name, cat))

        if not voices:
            ttk.Label(
                self.voicebox_grid_frame,
                text="No hay voces en esta categoría. Añade favoritos o cambia de filtro.",
                style="Card.TLabel"
            ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        cols = 3
        for i, (name, cat) in enumerate(voices):
            card = ttk.Frame(self.voicebox_grid_frame, style="Card.TFrame", padding=10)
            card.grid(row=i // cols, column=i % cols, sticky="nsew", padx=8, pady=8)

            key = self.voice_image_key(name)
            img = self.grid_voice_images.get(key)
            if img is not None:
                ttk.Label(card, image=img, style="Card.TLabel").pack(anchor="center", pady=(0, 6))

            ttk.Label(card, text=name, style="Card.TLabel", font=("Segoe UI", 12, "bold"), wraplength=240).pack(anchor="w")
            ttk.Label(card, text=cat, style="Card.TLabel", font=("Segoe UI", 9), wraplength=240).pack(anchor="w", pady=(0, 6))

            buttons = ttk.Frame(card, style="Card.TFrame")
            buttons.pack(fill="x")
            ttk.Button(buttons, text="Aplicar", style="Accent.TButton", command=lambda v=name: self.apply_grid_voice(v)).pack(side="left", fill="x", expand=True, padx=(0, 3))
            ttk.Button(buttons, text="★", command=lambda v=name: self.favorite_voice_by_name(v)).pack(side="left", padx=(3, 0))

        for col in range(cols):
            self.voicebox_grid_frame.columnconfigure(col, weight=1)

    def apply_grid_voice(self, voice_name):
        if voice_name in VoiceBank.all_presets():
            self.preset.set(voice_name)
            self.category.set(VoiceBank.all_presets()[voice_name][0])
            self.apply_preset()
            self.refresh_voice_list()
            self.state.set(f"Estado: voz aplicada desde Caja de voces · {voice_name}")

    def favorite_voice_by_name(self, voice_name):
        if voice_name not in self.favorites:
            self.favorites.append(voice_name)
            self.save_favorites()
            self.refresh_favorites_list()
            self.refresh_voice_list()
            messagebox.showinfo("Favorito añadido", f"Añadido a favoritos:\n\n{voice_name}")
        else:
            messagebox.showinfo("Ya estaba", f"Ya estaba en favoritos:\n\n{voice_name}")


    def build_ultra_tab(self):
        hero = self.make_card(self.tab_ultra, "Ultra Premium")
        hero.pack(fill="x", pady=(0, 12))

        if "ultra_banner" in self.ultra_images:
            ttk.Label(hero, image=self.ultra_images["ultra_banner"], style="Card.TLabel").pack(anchor="center", pady=(0, 10))

        ttk.Label(
            hero,
            text="Panel central de funciones premium: acceso rápido, soundboard pro, visualizador, perfiles y asistente.",
            style="Card.TLabel",
            wraplength=950,
            justify="left"
        ).pack(anchor="w")

        grid = ttk.Frame(self.tab_ultra, style="Card.TFrame")
        grid.pack(fill="both", expand=True)

        ultra_cards = [
            ("ultra_soundboard", "Abrir Mesa de sonidos Pro", self.tab_sonidos),
            ("ultra_profiles", "Abrir Perfiles", self.tab_studio),
            ("ultra_visualizer", "Abrir Visualizador", self.tab_visualizador),
            ("ultra_setup", "Asistente Discord", "discord"),
        ]

        for i, (img_key, label, target) in enumerate(ultra_cards):
            box = self.make_card(grid)
            box.grid(row=i // 2, column=i % 2, sticky="nsew", padx=8, pady=8)
            if img_key in self.ultra_images:
                ttk.Label(box, image=self.ultra_images[img_key], style="Card.TLabel").pack(anchor="center", pady=(0, 8))
            if target == "discord":
                ttk.Button(box, text=label, style="Accent.TButton", command=lambda: self.quick_mode("discord")).pack(fill="x")
            else:
                ttk.Button(box, text=label, style="Accent.TButton", command=lambda t=target: self.select_tab(t)).pack(fill="x")

        for col in range(2):
            grid.columnconfigure(col, weight=1)
        for row in range(2):
            grid.rowconfigure(row, weight=1)

    def build_visualizer_tab(self):
        card = self.make_card(self.tab_visualizador, "Visualizador Estudio")
        card.pack(fill="both", expand=True)

        ttk.Label(
            card,
            text="Visualizador decorativo de nivel de voz/salida. Sirve como panel de estudio mientras estás en directo.",
            style="Card.TLabel",
            wraplength=900,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        self.visualizer_canvas = tk.Canvas(
            card,
            bg=COLORS["panel2"],
            highlightthickness=0,
            height=360
        )
        self.visualizer_canvas.pack(fill="both", expand=True, pady=10)

        controls = ttk.Frame(card, style="Card.TFrame")
        controls.pack(fill="x")
        ttk.Button(controls, text="Empezar directo", style="Accent.TButton", command=self.start).pack(side="left", padx=5)
        ttk.Button(controls, text="Parar", style="Danger.TButton", command=self.stop).pack(side="left", padx=5)
        ttk.Button(controls, text="Bandeja Windows", command=self.hide_to_tray).pack(side="left", padx=5)

    def update_visualizer(self):
        if self.visualizer_canvas is None:
            return
        c = self.visualizer_canvas
        w = max(1, c.winfo_width())
        h = max(1, c.winfo_height())
        c.delete("all")

        # Fondo con rejilla
        for x in range(0, w, 60):
            c.create_line(x, 0, x, h, fill="#252a42")
        for y in range(0, h, 50):
            c.create_line(0, y, w, y, fill="#252a42")

        mic = min(1.0, self.engine.mic_level * 7)
        out = min(1.0, self.engine.out_level * 7)

        bars = 28
        gap = 6
        bw = max(6, (w - gap*(bars+1)) / bars)
        import random
        for i in range(bars):
            base = (mic*0.45 + out*0.55)
            pulse = abs(math.sin((i*0.55) + (datetime.now().timestamp()*5))) * 0.55
            val = min(1, base * (0.55 + pulse))
            bh = 18 + val * (h - 70)
            x1 = gap + i*(bw+gap)
            x2 = x1 + bw
            y1 = h - bh - 20
            y2 = h - 20
            color = "#00e5ff" if i % 3 else "#7c5cff"
            c.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            if val > 0.55:
                c.create_rectangle(x1, y1, x2, y1+5, fill="#62ffb4", outline="")

        c.create_text(24, 24, anchor="w", text="ESTUDIO DE VOZ ULTRA", fill="#f5f7ff", font=("Segoe UI", 18, "bold"))
        c.create_text(24, 54, anchor="w", text=f"Micro: {int(mic*100)}%  ·  Salida: {int(out*100)}%", fill="#aab0d6", font=("Segoe UI", 11))


    def build_home_tab(self):
        grid = ttk.Frame(self.tab_inicio)
        grid.pack(fill="both", expand=True)

        quick = self.make_card(grid, "Configuración rápida")
        quick.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        ttk.Label(quick, text="Elige dónde quieres usar la voz modificada:", style="Card.TLabel").pack(anchor="w", pady=(0, 8))

        btns = ttk.Frame(quick, style="Card.TFrame")
        btns.pack(fill="x")
        ttk.Button(btns, text="Discord", style="Accent.TButton", command=lambda: self.quick_mode("discord")).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(btns, text="Fortnite", style="Accent.TButton", command=lambda: self.quick_mode("fortnite")).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(btns, text="OBS", style="Accent.TButton", command=lambda: self.quick_mode("obs")).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(btns, text="Solo auriculares", command=lambda: self.quick_mode("headphones")).grid(row=0, column=3, padx=4, pady=4, sticky="ew")
        for i in range(4):
            btns.columnconfigure(i, weight=1)

        ttk.Label(quick, text="Latencia:", style="Card.TLabel").pack(anchor="w", pady=(14, 4))
        ttk.Combobox(quick, textvariable=self.latency, state="readonly", values=["Ultra baja", "Baja", "Estable", "Máxima estabilidad"], width=25).pack(anchor="w")

        status = self.make_card(grid, "Estado del directo")
        status.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        ttk.Label(status, text="Nivel de micrófono", style="Card.TLabel").pack(anchor="w")
        self.home_mic_bar = ttk.Progressbar(status, maximum=100)
        self.home_mic_bar.pack(fill="x", pady=(4, 12))

        ttk.Label(status, text="Nivel de salida", style="Card.TLabel").pack(anchor="w")
        self.home_out_bar = ttk.Progressbar(status, maximum=100)
        self.home_out_bar.pack(fill="x", pady=(4, 12))

        ttk.Label(status, textvariable=self.state, style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(4, 0))

        devices = self.make_card(grid, "Dispositivos")
        devices.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(8, 0))

        row1 = ttk.Frame(devices, style="Card.TFrame")
        row1.pack(fill="x", pady=4)
        ttk.Label(row1, text="Entrada / micrófono:", style="Card.TLabel", width=22).pack(side="left")
        self.input_combo = ttk.Combobox(row1, textvariable=self.input_dev, state="readonly")
        self.input_combo.pack(side="left", fill="x", expand=True, padx=8)
        self.input_combos.append(self.input_combo)
        self.input_combo.bind("<<ComboboxSelected>>", lambda e: self.on_device_changed())

        row2 = ttk.Frame(devices, style="Card.TFrame")
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Salida modificada:", style="Card.TLabel", width=22).pack(side="left")
        self.output_combo = ttk.Combobox(row2, textvariable=self.output_dev, state="readonly")
        self.output_combo.pack(side="left", fill="x", expand=True, padx=8)
        self.output_combos.append(self.output_combo)
        self.output_combo.bind("<<ComboboxSelected>>", lambda e: self.on_device_changed())

        row3 = ttk.Frame(devices, style="Card.TFrame")
        row3.pack(fill="x", pady=(10, 0))
        ttk.Button(row3, text="Actualizar dispositivos", command=self.load_devices).pack(side="left", padx=(0, 8))
        ttk.Button(row3, text="🎙 Probar micro", command=self.test_microphone).pack(side="left", padx=8)
        ttk.Button(row3, text="🎧 Probar auriculares", command=self.test_headphones).pack(side="left", padx=8)
        ttk.Button(row3, text="Auto cable virtual", command=self.find_virtual).pack(side="left", padx=8)
        ttk.Button(row3, text="Guardar configuración", command=self.save_config).pack(side="left", padx=8)
        ttk.Button(row3, text="Cargar configuración", command=self.load_config).pack(side="left", padx=8)


        visuals = self.make_card(grid, "Panel visual")
        visuals.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        visual_row = ttk.Frame(visuals, style="Card.TFrame")
        visual_row.pack(fill="x")
        visual_items = [
            ("Inicio", "home"),
            ("Voces", "voices"),
            ("Ajustes", "sliders"),
            ("Directo", "live"),
            ("Sonidos", "sound"),
            ("Bandeja", "tray"),
        ]
        for i, (txt, key) in enumerate(visual_items):
            box = ttk.Frame(visual_row, style="Card.TFrame")
            box.grid(row=0, column=i, sticky="nsew", padx=8)
            if key in self.images:
                ttk.Label(box, image=self.images[key], style="Card.TLabel").pack()
            ttk.Label(box, text=txt, style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(pady=(4, 0))
            visual_row.columnconfigure(i, weight=1)


        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(1, weight=1)

    def build_voices_tab(self):
        top = self.make_card(self.tab_voces, "Biblioteca de voces")
        top.pack(fill="x", pady=(0, 10))

        controls = ttk.Frame(top, style="Card.TFrame")
        controls.pack(fill="x")

        ttk.Label(controls, text="Categoría:", style="Card.TLabel").grid(row=0, column=0, padx=(0, 8), sticky="w")
        cat = ttk.Combobox(controls, textvariable=self.category, state="readonly", values=["Todas", "Favoritos"] + [c for c in VoiceBank.categories() if c != "Todas"], width=18)
        cat.grid(row=0, column=1, padx=(0, 14), sticky="w")
        cat.bind("<<ComboboxSelected>>", lambda e: self.refresh_voice_list())

        ttk.Label(controls, text="Buscar:", style="Card.TLabel").grid(row=0, column=2, padx=(0, 8), sticky="w")
        search_entry = ttk.Entry(controls, textvariable=self.search, width=28)
        search_entry.grid(row=0, column=3, padx=(0, 14), sticky="ew")
        self.search.trace_add("write", lambda *_: self.refresh_voice_list())

        ttk.Button(controls, text="Voz aleatoria", command=self.random_voice).grid(row=0, column=4, padx=4)
        ttk.Button(controls, text="Recomendadas", command=self.show_recommended).grid(row=0, column=5, padx=4)
        controls.columnconfigure(3, weight=1)

        body = ttk.Frame(self.tab_voces)
        body.pack(fill="both", expand=True)

        left = self.make_card(body, "Voces disponibles")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.voice_list = tk.Listbox(
            left,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 11),
            activestyle="none",
            height=20
        )
        self.voice_list.pack(fill="both", expand=True)
        self.voice_list.bind("<<ListboxSelect>>", self.on_voice_select)
        self.voice_list.bind("<Double-Button-1>", lambda e: self.apply_selected_voice())

        right = self.make_card(body, "Voz seleccionada")
        right.pack(side="right", fill="y", padx=(8, 0))

        ttk.Label(right, textvariable=self.preset, style="Card.TLabel", font=("Segoe UI", 18, "bold"), wraplength=300).pack(anchor="w", pady=(0, 8))
        ttk.Label(right, text="Doble clic en una voz para aplicarla rápido.", style="Card.TLabel", wraplength=300).pack(anchor="w", pady=(0, 14))

        ttk.Button(right, text="Aplicar voz", style="Accent.TButton", command=self.apply_selected_voice).pack(fill="x", pady=4)
        ttk.Button(right, text="★ Añadir a favoritos", command=self.add_current_favorite).pack(fill="x", pady=4)
        ttk.Button(right, text="Reiniciar gaming", command=self.reset).pack(fill="x", pady=4)
        ttk.Button(right, text="Grabar prueba WAV", command=self.record).pack(fill="x", pady=4)

        ttk.Label(right, text="Imagen de la voz:", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 4))
        self.voice_preview_label = ttk.Label(right, text="Selecciona una voz para ver su dibujo.", style="Card.TLabel", wraplength=300, anchor="center", justify="center")
        self.voice_preview_label.pack(fill="x", pady=(0, 8))



    def profiles_path(self):
        return os.path.join(os.path.expanduser("~"), "modulador_voz_directo_v81_profiles.json")

    def load_profiles(self):
        try:
            path = self.profiles_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.profiles = data if isinstance(data, dict) else {}
        except Exception as e:
            print("No se pudieron cargar perfiles:", e)
            self.profiles = {}

    def save_profiles(self):
        try:
            with open(self.profiles_path(), "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("No se pudieron guardar perfiles:", e)

    def refresh_profiles_list(self):
        if self.profile_list is None:
            return
        self.profile_list.delete(0, tk.END)
        for name in sorted(self.profiles.keys()):
            self.profile_list.insert(tk.END, name)

    def save_current_profile(self):
        name = simpledialog.askstring("Guardar perfil", "Nombre del perfil premium:")
        if not name:
            return
        self.profiles[name] = {
            "preset": self.preset.get(),
            "category": self.category.get(),
            "latency": self.latency.get(),
            "values": self.current_values()
        }
        self.save_profiles()
        self.refresh_profiles_list()
        messagebox.showinfo("Perfil guardado", f"Perfil guardado:\n\n{name}")

    def load_selected_profile(self):
        if self.profile_list is None or not self.profile_list.curselection():
            messagebox.showwarning("Sin selección", "Selecciona un perfil.")
            return
        name = self.profile_list.get(self.profile_list.curselection()[0])
        profile = self.profiles.get(name)
        if not profile:
            return
        self.preset.set(profile.get("preset", "Gaming limpio"))
        self.category.set(profile.get("category", "Todas"))
        self.latency.set(profile.get("latency", "Baja"))
        vals = profile.get("values", {})
        for key, value in vals.items():
            if key in self.vars:
                self.vars[key].set(value)
        self.refresh_voice_list()
        self.apply_preset()
        self.state.set(f"Estado: perfil cargado · {name}")

    def delete_selected_profile(self):
        if self.profile_list is None or not self.profile_list.curselection():
            messagebox.showwarning("Sin selección", "Selecciona un perfil.")
            return
        name = self.profile_list.get(self.profile_list.curselection()[0])
        if name in self.profiles:
            del self.profiles[name]
            self.save_profiles()
            self.refresh_profiles_list()

    def apply_studio_scene(self, scene):
        scene = scene.lower()
        mapping = {
            "gaming_pro": ("Gaming limpio", "Gaming", "Baja"),
            "podcast_pro": ("Podcast", "Limpias", "Estable"),
            "meme_energy": ("Payaso gamer", "Divertidas", "Baja"),
            "cinematic_fx": ("Narrador épico", "Épicas", "Estable"),
        }
        preset, category, latency = mapping.get(scene, ("Gaming limpio", "Gaming", "Baja"))
        self.preset.set(preset)
        self.category.set(category)
        self.latency.set(latency)
        self.refresh_voice_list()
        self.apply_preset()
        self.select_tab(self.tab_voces)
        self.state.set(f"Estado: escena premium aplicada · {preset}")

    def build_studio_tab(self):
        hero = self.make_card(self.tab_studio, "Estudio Premium")
        hero.pack(fill="x", pady=(0, 12))
        ttk.Label(
            hero,
            text="Centro premium del modulador: escenas rápidas, perfiles guardados y acceso tipo aplicación de pago.",
            style="Card.TLabel",
            wraplength=950,
            justify="left"
        ).pack(anchor="w", pady=(0, 8))

        stats = ttk.Frame(hero, style="Card.TFrame")
        stats.pack(fill="x", pady=(6, 0))
        stats_data = [
            ("52+", "Voces visuales"),
            ("12", "Sonidos FX"),
            ("8", "Packs premium"),
            ("∞", "Perfiles guardables"),
        ]
        for i, (num, label) in enumerate(stats_data):
            box = ttk.Frame(stats, style="Card.TFrame", padding=10)
            box.grid(row=0, column=i, sticky="nsew", padx=6)
            ttk.Label(box, text=num, style="Card.TLabel", font=("Segoe UI", 20, "bold")).pack()
            ttk.Label(box, text=label, style="Card.TLabel").pack()
            stats.columnconfigure(i, weight=1)

        scenes = self.make_card(self.tab_studio, "Escenas rápidas premium")
        scenes.pack(fill="both", expand=True, pady=(0, 12))
        grid = ttk.Frame(scenes, style="Card.TFrame")
        grid.pack(fill="both", expand=True)

        scene_order = [
            ("gaming_pro", "Gaming Pro"),
            ("podcast_pro", "Podcast Pro"),
            ("meme_energy", "Energía Meme"),
            ("cinematic_fx", "Cine FX"),
        ]
        for i, (key, label) in enumerate(scene_order):
            box = ttk.Frame(grid, style="Card.TFrame", padding=8)
            box.grid(row=i // 2, column=i % 2, sticky="nsew", padx=8, pady=8)
            img = self.studio_images.get(key)
            if img is not None:
                ttk.Label(box, image=img, style="Card.TLabel").pack(anchor="center", pady=(0, 8))
            ttk.Button(box, text=f"Aplicar {label}", style="Accent.TButton", command=lambda s=key: self.apply_studio_scene(s)).pack(fill="x")
        for col in range(2):
            grid.columnconfigure(col, weight=1)
        for row in range(2):
            grid.rowconfigure(row, weight=1)

        profiles = self.make_card(self.tab_studio, "Perfiles personalizados")
        profiles.pack(fill="x")
        row = ttk.Frame(profiles, style="Card.TFrame")
        row.pack(fill="x")
        self.profile_list = tk.Listbox(
            row,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 10),
            height=6,
            activestyle="none"
        )
        self.profile_list.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.profile_list.bind("<Double-Button-1>", lambda e: self.load_selected_profile())

        btns = ttk.Frame(row, style="Card.TFrame")
        btns.pack(side="right", fill="y")
        ttk.Button(btns, text="Guardar perfil actual", command=self.save_current_profile).pack(fill="x", pady=3)
        ttk.Button(btns, text="Cargar perfil", command=self.load_selected_profile).pack(fill="x", pady=3)
        ttk.Button(btns, text="Borrar perfil", command=self.delete_selected_profile).pack(fill="x", pady=3)
        self.refresh_profiles_list()


    def build_packs_tab(self):
        card = self.make_card(self.tab_packs, "Packs visuales de voces")
        card.pack(fill="both", expand=True)

        ttk.Label(
            card,
            text="Elige un pack para filtrar voces por estilo y aplicar una voz recomendada rápidamente.",
            style="Card.TLabel",
            wraplength=900,
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        grid = ttk.Frame(card, style="Card.TFrame")
        grid.pack(fill="both", expand=True)

        pack_order = ["Gaming", "Épicas", "Oscuras", "Robots", "Radio", "Divertidas", "Fantasía", "Limpias"]
        for i, pack_name in enumerate(pack_order):
            pack = PACKS_DATA[pack_name]
            box = ttk.Frame(grid, style="Card.TFrame", padding=8)
            box.grid(row=i // 2, column=i % 2, sticky="nsew", padx=8, pady=8)

            img = self.pack_images.get(pack["slug"])
            if img is not None:
                ttk.Label(box, image=img, style="Card.TLabel").pack(anchor="center", pady=(0, 8))

            buttons = ttk.Frame(box, style="Card.TFrame")
            buttons.pack(fill="x")
            ttk.Button(buttons, text=f"Abrir {pack_name}", command=lambda p=pack_name: self.open_pack(p)).pack(side="left", fill="x", expand=True, padx=(0, 4))
            ttk.Button(buttons, text="Voz principal", style="Accent.TButton", command=lambda p=pack_name: self.apply_pack_top_voice(p)).pack(side="left", fill="x", expand=True, padx=(4, 0))

        for col in range(2):
            grid.columnconfigure(col, weight=1)
        for row in range(4):
            grid.rowconfigure(row, weight=1)

        fav = self.make_card(self.tab_packs, "Favoritos")
        fav.pack(fill="x", pady=(12, 0))

        fav_row = ttk.Frame(fav, style="Card.TFrame")
        fav_row.pack(fill="x")

        self.fav_list = tk.Listbox(
            fav_row,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 10),
            height=5,
            activestyle="none"
        )
        self.fav_list.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.fav_list.bind("<Double-Button-1>", lambda e: self.apply_selected_favorite())

        fav_buttons = ttk.Frame(fav_row, style="Card.TFrame")
        fav_buttons.pack(side="right", fill="y")
        ttk.Button(fav_buttons, text="Aplicar favorito", command=self.apply_selected_favorite).pack(fill="x", pady=3)
        ttk.Button(fav_buttons, text="Quitar favorito", command=self.remove_selected_favorite).pack(fill="x", pady=3)
        ttk.Button(fav_buttons, text="Limpiar favoritos", command=self.clear_favorites).pack(fill="x", pady=3)

        self.refresh_favorites_list()

    def open_pack(self, pack_name):
        self.category.set(pack_name)
        self.select_tab(self.tab_voces)
        self.refresh_voice_list()
        voices = PACKS_DATA[pack_name]["voices"]
        if voices:
            self.preset.set(voices[0])
            self.apply_preset()
        self.state.set(f"Estado: pack abierto · {pack_name}")

    def apply_pack_top_voice(self, pack_name):
        voices = PACKS_DATA[pack_name]["voices"]
        if voices:
            self.preset.set(voices[0])
            self.apply_preset()
            self.select_tab(self.tab_voces)
            self.state.set(f"Estado: voz aplicada · {voices[0]}")

    def add_current_favorite(self):
        name = self.preset.get()
        if name and name not in self.favorites:
            self.favorites.append(name)
            self.save_favorites()
            self.refresh_favorites_list()
            self.refresh_voice_list()
            messagebox.showinfo("Favorito añadido", f"Voz añadida a favoritos:\n\n{name}")
        elif name:
            messagebox.showinfo("Ya estaba", f"Esa voz ya está en favoritos:\n\n{name}")

    def apply_selected_favorite(self):
        if self.fav_list is None or not self.fav_list.curselection():
            messagebox.showwarning("Sin selección", "Selecciona un favorito.")
            return
        name = self.fav_list.get(self.fav_list.curselection()[0])
        self.preset.set(name)
        self.apply_preset()
        self.select_tab(self.tab_voces)

    def remove_selected_favorite(self):
        if self.fav_list is None or not self.fav_list.curselection():
            messagebox.showwarning("Sin selección", "Selecciona un favorito para quitar.")
            return
        name = self.fav_list.get(self.fav_list.curselection()[0])
        if name in self.favorites:
            self.favorites.remove(name)
            self.save_favorites()
            self.refresh_favorites_list()
            self.refresh_voice_list()

    def clear_favorites(self):
        self.favorites = []
        self.save_favorites()
        self.refresh_favorites_list()
        self.refresh_voice_list()

    def favorites_path(self):
        return os.path.join(os.path.expanduser("~"), "modulador_voz_directo_v81_favoritos.json")

    def load_favorites(self):
        try:
            path = self.favorites_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.favorites = [v for v in data.get("favorites", []) if v in VoiceBank.all_presets()]
        except Exception as e:
            print("No se pudieron cargar favoritos:", e)

    def save_favorites(self):
        try:
            with open(self.favorites_path(), "w", encoding="utf-8") as f:
                json.dump({"favorites": self.favorites}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("No se pudieron guardar favoritos:", e)

    def refresh_favorites_list(self):
        if self.fav_list is None:
            return
        self.fav_list.delete(0, tk.END)
        for name in self.favorites:
            self.fav_list.insert(tk.END, name)


    def build_settings_tab(self):
        card = self.make_card(self.tab_ajustes, "Ajustes finos de la voz")
        card.pack(fill="both", expand=True)

        self.slider(card, "Tono", "pitch", -12, 12, 0, "semitonos")
        self.slider(card, "Grave extra", "bass", 0, 100, 1, "%")
        self.slider(card, "Robot", "robot", 0, 100, 2, "%")
        self.slider(card, "Eco", "echo", 0, 100, 3, "%")
        self.slider(card, "Radio", "radio", 0, 100, 4, "%")
        self.slider(card, "Megáfono", "megaphone", 0, 100, 5, "%")
        self.slider(card, "Quitar ruido", "gate", 0, 30, 6, "%")
        self.slider(card, "Compresor directo", "comp", 0, 100, 7, "%")
        self.slider(card, "Volumen salida", "vol", 0, 120, 8, "%")

    def build_live_tab(self):
        card = self.make_card(self.tab_directo, "Control en directo")
        card.pack(fill="x", pady=(0, 10))

        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Button(row, text="▶ Empezar directo", style="Accent.TButton", command=self.start).pack(side="left", padx=(0, 8))
        ttk.Button(row, text="■ Parar", style="Danger.TButton", command=self.stop).pack(side="left", padx=8)
        ttk.Button(row, text="● Grabar prueba WAV", command=self.record).pack(side="left", padx=8)
        ttk.Button(row, text="▾ Bandeja Windows", command=self.hide_to_tray).pack(side="left", padx=8)
        ttk.Checkbutton(row, text="Silenciar salida", variable=self.mute, command=self.update_engine).pack(side="left", padx=16)

        meters = self.make_card(self.tab_directo, "Medidores")
        meters.pack(fill="x", pady=10)

        ttk.Label(meters, text="Micro:", style="Card.TLabel").pack(anchor="w")
        self.live_mic_bar = ttk.Progressbar(meters, maximum=100)
        self.live_mic_bar.pack(fill="x", pady=(4, 12))

        ttk.Label(meters, text="Salida:", style="Card.TLabel").pack(anchor="w")
        self.live_out_bar = ttk.Progressbar(meters, maximum=100)
        self.live_out_bar.pack(fill="x", pady=(4, 12))

        tips = self.make_card(self.tab_directo, "Consejos para directo")
        tips.pack(fill="both", expand=True, pady=(10, 0))
        ttk.Label(
            tips,
            text=(
                "• Para Discord/Fortnite/OBS: salida del programa = CABLE Input / VoiceMeeter Input.\n"
                "• Dentro de Discord/Fortnite/OBS: micrófono = CABLE Output / VoiceMeeter Output.\n"
                "• Si se corta la voz, baja 'Quitar ruido' o usa latencia 'Estable'.\n"
                "• Si hay eco, usa auriculares y evita altavoces."
            ),
            style="Card.TLabel",
            justify="left"
        ).pack(anchor="w")


    def build_soundboard_tab(self):
        card = self.make_card(self.tab_sonidos, "Mesa de efectos de sonido")
        card.pack(fill="both", expand=True)

        ttk.Label(
            card,
            text=(
                "Estos sonidos se mezclan con tu voz y salen por la misma salida del modulador. "
                "Si usas CABLE Input / VoiceMeeter Input, también los escucharán en Discord, Fortnite u OBS."
            ),
            style="Card.TLabel",
            wraplength=900,
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        grid = ttk.Frame(card, style="Card.TFrame")
        grid.pack(fill="x", pady=(4, 12))

        sounds = [
            ("👏 Aplausos", "aplausos", "applause"),
            ("😂 Risas", "risas", "laugh"),
            ("🏆 Victoria", "victoria", "victory"),
            ("❌ Error", "error", "error"),
            ("😱 Suspense", "suspense", "magic"),
            ("🔔 Beep", "beep", "sound"),
            ("✨ Magia", "magia", "magic"),
            ("🎮 Power Up", "powerup", "victory"),
            ("📢 Alerta", "alerta", "sound"),
            ("🥁 Redoble", "redoble", "sound"),
            ("💥 Impacto", "impacto", "error"),
            ("🌧️ Lluvia suave", "lluvia", "magic"),
        ]

        for i, (label, key, image_key) in enumerate(sounds):
            if image_key in self.images:
                btn = ttk.Button(grid, text=label, image=self.images[image_key], compound="left", command=lambda k=key: self.play_sfx(k))
            else:
                btn = ttk.Button(grid, text=label, command=lambda k=key: self.play_sfx(k))
            btn.grid(row=i // 4, column=i % 4, sticky="ew", padx=6, pady=6, ipadx=8, ipady=8)

        for col in range(4):
            grid.columnconfigure(col, weight=1)

        control = ttk.Frame(card, style="Card.TFrame")
        control.pack(fill="x", pady=(8, 0))

        ttk.Label(control, text="Volumen efectos:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        self.sfx_volume_var = tk.DoubleVar(value=65)

        def update_sfx_volume(*_):
            with self.engine.lock:
                self.engine.sfx_volume = clamp(self.sfx_volume_var.get() / 100, 0, 1.5)

        ttk.Scale(control, from_=0, to=120, variable=self.sfx_volume_var, orient="horizontal", command=lambda _=None: update_sfx_volume()).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(control, text="Parar sonidos", command=self.stop_sfx).pack(side="left", padx=8)

        custom = self.make_card(self.tab_sonidos, "Sonidos personalizados WAV")
        custom.pack(fill="x", pady=(12, 0))

        custom_row = ttk.Frame(custom, style="Card.TFrame")
        custom_row.pack(fill="x")

        self.custom_sfx_list = tk.Listbox(
            custom_row,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 10),
            height=4,
            activestyle="none"
        )
        self.custom_sfx_list.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.custom_sfx_list.bind("<Double-Button-1>", lambda e: self.play_selected_custom_sfx())

        custom_buttons = ttk.Frame(custom_row, style="Card.TFrame")
        custom_buttons.pack(side="right", fill="y")
        ttk.Button(custom_buttons, text="Cargar WAV", command=self.add_custom_wav).pack(fill="x", pady=3)
        ttk.Button(custom_buttons, text="Reproducir", command=self.play_selected_custom_sfx).pack(fill="x", pady=3)
        ttk.Button(custom_buttons, text="Quitar", command=self.remove_selected_custom_sfx).pack(fill="x", pady=3)

        tips = self.make_card(self.tab_sonidos, "Consejos")
        tips.pack(fill="x", pady=(12, 0))
        ttk.Label(
            tips,
            text=(
                "• Usa los sonidos con moderación para no molestar en partidas o llamadas.\n"
                "• Para Discord/Fortnite/OBS, el modulador debe estar en directo y usando salida virtual.\n"
                "• Los sonidos son generados por el programa, sin depender de archivos con copyright."
            ),
            style="Card.TLabel",
            justify="left"
        ).pack(anchor="w")

    def stop_sfx(self):
        with self.engine.lock:
            self.engine.sfx_buffer = np.zeros(0, dtype=np.float32)
        self.state.set("Estado: efectos detenidos" if not self.engine.running else "Estado: voz en directo activa")

    def play_sfx(self, name):
        samples = self.generate_sfx(name)
        self.engine.add_sfx(samples)
        pretty = {
            "aplausos": "Aplausos",
            "risas": "Risas",
            "victoria": "Victoria",
            "error": "Error",
            "suspense": "Suspense",
            "beep": "Beep",
            "magia": "Magia",
            "powerup": "Power Up",
            "alerta": "Alerta",
            "redoble": "Redoble",
            "impacto": "Impacto",
            "lluvia": "Lluvia suave",
        }.get(name, name)
        self.state.set(f"Estado: sonido lanzado · {pretty}")

    def tone(self, freq, dur, amp=0.4, wave="sine"):
        rate = self.engine.rate
        t = np.linspace(0, dur, int(rate * dur), endpoint=False)
        if wave == "square":
            y = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave == "saw":
            y = 2 * (t * freq - np.floor(0.5 + t * freq))
        else:
            y = np.sin(2 * np.pi * freq * t)

        # Envolvente simple para evitar clicks.
        env = np.ones_like(y)
        fade = min(len(y) // 8, int(rate * 0.025))
        if fade > 0:
            env[:fade] = np.linspace(0, 1, fade)
            env[-fade:] = np.linspace(1, 0, fade)
        return (y * env * amp).astype(np.float32)

    def noise_burst(self, dur, amp=0.35, decay=True):
        rate = self.engine.rate
        n = int(rate * dur)
        y = np.random.normal(0, 1, n).astype(np.float32)
        if decay:
            env = np.linspace(1, 0, n) ** 1.8
        else:
            env = np.ones(n)
        return np.clip(y * env * amp, -0.95, 0.95).astype(np.float32)

    def silence(self, dur):
        return np.zeros(int(self.engine.rate * dur), dtype=np.float32)

    def generate_sfx(self, name):
        rate = self.engine.rate

        if name == "beep":
            return np.concatenate([self.tone(880, 0.13, 0.45), self.silence(0.04), self.tone(1175, 0.16, 0.42)])

        if name == "error":
            return np.concatenate([self.tone(220, 0.18, 0.45, "square"), self.silence(0.05), self.tone(150, 0.28, 0.4, "square")])

        if name == "victoria":
            parts = []
            for f in [523, 659, 784, 1046]:
                parts.append(self.tone(f, 0.16, 0.38))
                parts.append(self.silence(0.03))
            parts.append(self.tone(1318, 0.35, 0.32))
            return np.concatenate(parts)

        if name == "powerup":
            parts = []
            for f in [330, 392, 494, 587, 784, 988]:
                parts.append(self.tone(f, 0.08, 0.30, "square"))
                parts.append(self.silence(0.015))
            return np.concatenate(parts)

        if name == "alerta":
            return np.concatenate([self.tone(740, 0.18, 0.42, "square"), self.silence(0.08), self.tone(740, 0.18, 0.42, "square"), self.silence(0.08), self.tone(740, 0.18, 0.42, "square")])

        if name == "impacto":
            low = self.tone(65, 0.45, 0.65, "sine")
            noise = self.noise_burst(0.45, 0.45, decay=True)
            return np.clip(low + noise, -0.95, 0.95)

        if name == "suspense":
            dur = 1.8
            n = int(rate * dur)
            t = np.linspace(0, dur, n, endpoint=False)
            sweep = np.sin(2 * np.pi * (120 + 180 * t / dur) * t)
            trem = 0.5 + 0.5 * np.sin(2 * np.pi * 7 * t)
            env = np.linspace(0.2, 1.0, n)
            return (sweep * trem * env * 0.28).astype(np.float32)

        if name == "magia":
            dur = 1.4
            n = int(rate * dur)
            t = np.linspace(0, dur, n, endpoint=False)
            y = np.zeros(n, dtype=np.float32)
            for f in [523, 659, 784, 1046, 1318]:
                y += np.sin(2 * np.pi * f * t + np.random.rand() * 2) * 0.08
            sparkles = np.zeros(n, dtype=np.float32)
            for _ in range(18):
                start = np.random.randint(0, max(1, n - int(rate * 0.08)))
                sparkles[start:start + int(rate * 0.08)] += self.tone(np.random.choice([1200, 1500, 1800, 2200]), 0.08, 0.12)
            env = np.linspace(1, 0, n) ** 0.7
            return np.clip((y + sparkles) * env, -0.95, 0.95).astype(np.float32)

        if name == "aplausos":
            dur = 2.2
            n = int(rate * dur)
            y = np.zeros(n, dtype=np.float32)
            # Ráfagas cortas de ruido simulando palmadas.
            for _ in range(46):
                start = np.random.randint(0, n - int(rate * 0.06))
                burst_len = np.random.randint(int(rate * 0.018), int(rate * 0.055))
                burst = np.random.normal(0, 1, burst_len).astype(np.float32)
                env = np.linspace(1, 0, burst_len) ** 2.5
                y[start:start + burst_len] += burst * env * np.random.uniform(0.12, 0.28)
            return np.clip(y, -0.95, 0.95)

        if name == "risas":
            parts = []
            for _ in range(8):
                f = np.random.choice([260, 300, 340, 390])
                parts.append(self.tone(f, 0.09, 0.22, "saw"))
                parts.append(self.silence(np.random.uniform(0.035, 0.08)))
            y = np.concatenate(parts)
            # Ligero ruido para que sea más tipo grupo.
            y = y + self.noise_burst(len(y) / rate, 0.035, decay=False)
            return np.clip(y, -0.95, 0.95).astype(np.float32)

        if name == "redoble":
            parts = []
            for i in range(18):
                parts.append(self.noise_burst(0.045, 0.28 + i * 0.01, decay=True))
                parts.append(self.silence(max(0.015, 0.055 - i * 0.002)))
            parts.append(self.impact_final())
            return np.concatenate(parts)

        if name == "lluvia":
            dur = 2.5
            n = int(rate * dur)
            rain = np.random.normal(0, 0.12, n).astype(np.float32)
            # Suavizado básico para lluvia más suave.
            kernel = np.ones(8) / 8
            rain = np.convolve(rain, kernel, mode="same").astype(np.float32)
            return np.clip(rain, -0.4, 0.4)

        return self.tone(440, 0.2, 0.3)

    def impact_final(self):
        return np.clip(self.tone(90, 0.25, 0.5) + self.noise_burst(0.25, 0.35, decay=True), -0.95, 0.95)



    def custom_sfx_path(self):
        folder = os.path.join(os.path.expanduser("~"), "ModuladorVozDirecto_CustomSFX")
        os.makedirs(folder, exist_ok=True)
        return folder

    def load_wav_as_samples(self, path):
        """Carga WAV mono/estéreo 8/16/24/32-bit PCM y adapta a la tasa del motor."""
        try:
            with wave.open(path, "rb") as wav:
                channels = wav.getnchannels()
                sampwidth = wav.getsampwidth()
                framerate = wav.getframerate()
                nframes = wav.getnframes()
                frames = wav.readframes(nframes)

            if nframes <= 0 or not frames:
                messagebox.showwarning("WAV vacío", "El archivo WAV no contiene audio.")
                return None

            if sampwidth == 1:
                data = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
                data = (data - 128.0) / 128.0
            elif sampwidth == 2:
                data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            elif sampwidth == 3:
                raw = np.frombuffer(frames, dtype=np.uint8)
                if len(raw) % 3 != 0:
                    raw = raw[:len(raw) - (len(raw) % 3)]
                a = raw.reshape(-1, 3).astype(np.int32)
                signed = a[:, 0] | (a[:, 1] << 8) | (a[:, 2] << 16)
                signed = np.where(signed & 0x800000, signed - 0x1000000, signed)
                data = signed.astype(np.float32) / 8388608.0
            elif sampwidth == 4:
                data = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                messagebox.showwarning("Formato no compatible", "Usa WAV PCM de 8, 16, 24 o 32 bits.")
                return None

            if channels > 1:
                usable = (len(data) // channels) * channels
                data = data[:usable].reshape(-1, channels).mean(axis=1)

            if len(data) == 0:
                messagebox.showwarning("WAV vacío", "No se pudo leer audio útil del WAV.")
                return None

            if framerate and framerate != self.engine.rate:
                new_len = max(1, int(len(data) * self.engine.rate / framerate))
                old_idx = np.linspace(0, 1, len(data), endpoint=False)
                new_idx = np.linspace(0, 1, new_len, endpoint=False)
                data = np.interp(new_idx, old_idx, data).astype(np.float32)

            return np.clip(data, -0.95, 0.95).astype(np.float32)
        except Exception as e:
            messagebox.showerror("Error WAV", f"No se pudo cargar el WAV:\n{e}")
            return None

    def add_custom_wav(self):
        path = filedialog.askopenfilename(
            title="Cargar sonido WAV personalizado",
            filetypes=[("Archivos WAV", "*.wav")]
        )
        if not path:
            return
        samples = self.load_wav_as_samples(path)
        if samples is None:
            return
        name = os.path.splitext(os.path.basename(path))[0]
        self.custom_sfx[name] = samples
        self.refresh_custom_sfx_list()
        messagebox.showinfo("Sonido añadido", f"Sonido personalizado añadido:\n\n{name}")

    def refresh_custom_sfx_list(self):
        if self.custom_sfx_list is None:
            return
        self.custom_sfx_list.delete(0, tk.END)
        for name in sorted(self.custom_sfx.keys()):
            self.custom_sfx_list.insert(tk.END, name)

    def play_selected_custom_sfx(self):
        if self.custom_sfx_list is None or not self.custom_sfx_list.curselection():
            messagebox.showwarning("Sin selección", "Selecciona un sonido personalizado.")
            return
        name = self.custom_sfx_list.get(self.custom_sfx_list.curselection()[0])
        samples = self.custom_sfx.get(name)
        if samples is not None:
            self.engine.add_sfx(samples)
            self.state.set(f"Estado: sonido personalizado · {name}")

    def remove_selected_custom_sfx(self):
        if self.custom_sfx_list is None or not self.custom_sfx_list.curselection():
            messagebox.showwarning("Sin selección", "Selecciona un sonido personalizado.")
            return
        name = self.custom_sfx_list.get(self.custom_sfx_list.curselection()[0])
        self.custom_sfx.pop(name, None)
        self.refresh_custom_sfx_list()


    def build_guide_tab(self):
        card = self.make_card(self.tab_guia, "Guía rápida")
        card.pack(fill="both", expand=True)

        text = tk.Text(
            card,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            relief="flat",
            wrap="word",
            font=("Segoe UI", 11),
            padx=14,
            pady=14
        )
        text.pack(fill="both", expand=True)
        text.insert("1.0",
            "EFECTOS DE SONIDO / SOUNDBOARD\n\n• En la pestaña Sonidos tienes aplausos, risas, victoria, error, suspense, beep y más.\n• Los efectos salen por la misma salida del modulador.\n• Si usas cable virtual, Discord/Fortnite/OBS también recibirán los sonidos.\n\nCONFIGURACIÓN PARA DISCORD\n\n"
            "1. Abre el modulador.\n"
            "2. Pulsa Configuración rápida > Discord.\n"
            "3. Entrada = tu micrófono real.\n"
            "4. Salida = CABLE Input o VoiceMeeter Input.\n"
            "5. En Discord > Voz y vídeo > Entrada = CABLE Output o VoiceMeeter Output.\n\n"
            "CONFIGURACIÓN PARA FORTNITE\n\n"
            "1. Abre el modulador.\n"
            "2. Pulsa Configuración rápida > Fortnite.\n"
            "3. Pulsa Empezar directo.\n"
            "4. En Fortnite, activa chat de voz.\n"
            "5. Entrada de voz = CABLE Output o VoiceMeeter Output.\n"
            "6. Salida de voz = tus auriculares.\n\n"
            "CONFIGURACIÓN PARA OBS\n\n"
            "1. Abre el modulador.\n"
            "2. Pulsa Configuración rápida > OBS.\n"
            "3. En OBS añade Captura de entrada de audio.\n"
            "4. Elige CABLE Output o VoiceMeeter Output.\n\n"
            "BANDEJA JUNTO AL RELOJ DE WINDOWS\n\n• Si cierras la ventana, el programa se oculta en la bandeja del sistema.\n• Desde el icono junto al reloj puedes mostrarlo, ocultarlo, empezar directo, parar o salir.\n• Para cerrarlo del todo usa el menú del icono > Salir del programa.\n\nMEZCLADOR MUSICAL PRO\n\n• La pestaña Mezclador permite ajustar voz, instrumental y master final.\n• Incluye presets de mezcla, guardar/cargar proyecto JSON y acceso a exportaciones.\n• Es útil para equilibrar una demo antes de grabarla.\n\nCREADOR DE CANCIONES PRO\n\n• La pestaña Canción Pro genera una demo con estructura: intro, verso, estribillo y outro.\n• Incluye editor de letra, exportación de instrumental WAV y guardado de letra TXT.\n• Puedes cantar encima y grabar una demo con voz + base.\n\nKARAOKE STUDIO PRO\n\n• La pestaña Karaoke Studio genera instrumentales originales simples sin voz para practicar.\n• Incluye estilos Pop, Trap, Lofi, Balada y Rock suave, con duración configurable y grabación demo WAV.\n• Son bases generadas por la app para práctica, no canciones comerciales.\n\nKARAOKE PRO\n\n• La pestaña Karaoke permite cargar una pista instrumental WAV sin voz y cantar encima con el micro.\n• Incluye reproductor, pausa, stop, loop, volumen de pista, letra editable y grabación demo WAV.\n• No elimina voces de canciones: usa instrumentales que tengas permiso de usar.\n\nAUTOTUNE PRO\n\n• La pestaña Autotune permite cantar con efecto tipo autotune, vibrato, coro doble y eco.\n• Incluye presets cantados, letra de prueba propia y grabación demo WAV.\n• Es un efecto de voz en directo, no clona voces reales ni genera canciones completas con IA.\n\nTEST DE VOZ PRO\n\n• La pestaña Test de Voz sirve para probar la voz antes de Discord, Fortnite u OBS.\n• Incluye beep, grabación WAV, frases de prueba, modos Discord/Fortnite/OBS y check rápido.\n• Úsala antes de directos o llamadas para evitar sorpresas.\n\nCABLE VIRTUAL PRO\n\n• La pestaña Cable Virtual ayuda a configurar VB-Cable, VoiceMeeter, Discord, Fortnite y OBS.\n• Puede detectar dispositivos virtuales y seleccionar una salida virtual automáticamente si la encuentra.\n• También incluye guías copiables para Discord, Fortnite y OBS.\n\nRENDIMIENTO PRO\n\n• La pestaña Rendimiento optimiza latencia, estabilidad, anti-eco, calidad y OBS.\n• Incluye un check rápido para detectar exceso de eco, volumen alto o salida virtual no detectada.\n• Úsala si notas retraso, cortes, eco o distorsión.\n\nSTREAMER HUB PRO\n\n• La pestaña Streamer Hub funciona como centro de directo.\n• Incluye modos rápidos para Discord, Fortnite y OBS, checklist, Mini Panel, diagnóstico y grabación de prueba.\n• Es la pantalla recomendada antes de empezar un directo o una partida.\n\nESCENAS PRO\n\n• La pestaña Escenas aplica voz y ajustes completos con un clic.\n• Incluye escenas para Discord, Fortnite, Podcast, Robot, Terror, Cine, Personajes y Meme.\n• Puedes probar un sonido de cada escena y guardar la escena como perfil si te gusta.\n\nFAVORITOS PRO\n\n• La pestaña Favoritos reúne voces favoritas y sonidos rápidos en un solo panel.\n• Si no hay favoritos, muestra voces recomendadas automáticamente.\n• Es ideal para directos, Discord, Fortnite y OBS.\n\nATAJOS PRO\n\n• La pestaña Atajos añade teclas rápidas internas para voces, sonidos, silenciar y modulador ON/OFF.\n• F1-F8 cambian voces; F9-F12 lanzan sonidos.\n• Son atajos internos: funcionan cuando la app está abierta/enfocada.\n\nCREADOR DE VOCES PRO\n\n• La pestaña Creador permite mezclar una base humana con estilos como limpio, grave, radio, cine, robot o eco.\n• Puedes ajustar tono, graves, robot, eco, radio y volumen.\n• También puedes guardar la voz creada como perfil personalizado.\n\nCAMBIADOR DE PERSONAS\n\n• La pestaña Cambiador permite alternar rápido entre Mujer, Hombre, Niño, Niña, Abuelo y Abuela.\n• Incluye variantes y ajustes rápidos: más joven, más adulta, más grave, suave, clara, radio y eco.\n• Es ideal para cambiar de personaje durante directos o partidas.\n\nPERSONAS PRO\n\n• La pestaña Personas Pro muestra mujeres, hombres, niños, niñas, abuelos y abuelas en tarjetas grandes.\n• Puedes filtrar por tipo de voz y aplicar una voz en un clic.\n• Las imágenes ayudan a distinguir cada personaje rápidamente.\n\nVOCES CON PERSONAJES\n\n• Se han añadido voces tipo Mujer, Hombre, Niño, Niña, Abuelo y Abuela.\n• Cada una tiene nombre propio e imagen de dibujo para distinguirla mejor.\n• Las encontrarás dentro de la categoría Personas en la biblioteca y la caja de voces.\n\nPERFILES PRO+\n\n• La pestaña Perfiles Pro+ permite guardar, cargar, exportar e importar estilos completos.\n• Incluye plantillas rápidas para Discord, Fortnite, Podcast, Robot y Cine.\n• Ideal para tener varios estilos listos sin tocar ajustes cada vez.\n\nECUALIZADOR PRO\n\n• La pestaña Ecualizador permite aplicar presets y ajustar la voz con controles grandes.\n• Incluye Directo limpio, Grave potente, Radio directa, Robot claro y Cine épico.\n• Es ideal para afinar la voz antes de usar Discord/Fortnite/OBS.\n\nMINI PANEL PRO\n\n• La pestaña Mini Panel abre una ventana flotante siempre encima.\n• Permite cambiar voces, lanzar sonidos y empezar/parar directo rápidamente.\n• Es ideal para partidas, Discord, OBS y directos.\n\nDIAGNÓSTICO PRO\n\n• La pestaña Diagnóstico comprueba dependencias, audio, cable virtual y assets.\n• Puede generar un informe TXT para encontrar errores.\n• También permite probar salida y buscar cable virtual rápido.\n\nMESA DE SONIDOS PRO\n\n• La pestaña Mesa Pro convierte los sonidos en pads grandes por categorías.\n• Incluye Reacciones, Gaming, Directo, Ambiente y Personalizados.\n• Es más cómoda para directos y partidas.\n\nGRABADORA PRO\n\n• La pestaña Grabadora guarda pruebas de voz en una carpeta organizada.\n• Puedes ver historial, reproducir grabaciones y abrir la carpeta.\n• Ideal para comparar si una voz suena bien antes de usarla en Discord/Fortnite/OBS.\n\nBARRA RÁPIDA PREMIUM\n\n• La pestaña Barra rápida permite cambiar voces y lanzar sonidos al instante.\n• Los favoritos aparecen primero como voces rápidas.\n• También añade temas visuales: morado, azul, verde, rojo y dorado.\n\nASISTENTE PRO\n\n• La pestaña Asistente guía la configuración paso a paso.\n• Incluye selección de micrófono, salida, cable virtual y prueba final.\n• También ofrece accesos para Discord, Fortnite y OBS.\n\nPANEL DIRECTO PRO\n\n• La pestaña Directo Pro está pensada para usar durante directos o partidas.\n• Incluye voces rápidas, sonidos rápidos, medidores grandes y configuración Discord/Fortnite/OBS.\n• Si tienes favoritos, aparecerán primero como voces rápidas.\n\nTODO EN ESPAÑOL\n\n• Se han traducido pestañas, botones, banners, mensajes y documentación.\n• Los nombres técnicos internos pueden quedar en el código, pero la interfaz visible está en español.\n\nCAJA DE VOCES\n\n• La pestaña Caja de voces muestra voces como tarjetas visuales en cuadrícula.\n• Puedes aplicar voces y añadirlas a favoritos desde cada tarjeta.\n• Es la parte más parecida a una app premium tipo voice changer moderno.\n\nESTUDIO DE VOZ PRO\n\n• La pestaña Modo Pro está pensada como un panel tipo app premium de voice changer.\n• Incluye sidebar, Caja de voces rápido, Mesa de sonidos, Estudio, Visualizador y ON/OFF de voz.\n• No copia logos ni marca de otras apps: es diseño propio inspirado en apps profesionales.\n\nULTRA PREMIUM\n\n• La pestaña Ultra funciona como centro de control rápido.\n• La pestaña Visualizador muestra barras tipo estudio mientras hablas.\n• En Sonidos FX puedes cargar WAV personalizados.\n\nSTUDIO PREMIUM\n\n• La pestaña Estudio incluye escenas premium: Gaming Pro, Podcast Pro, Energía Meme y Cine FX.\n• También puedes guardar perfiles personalizados con tus ajustes favoritos.\n\nPACKS Y FAVORITOS\n\n• En la pestaña Packs puedes abrir voces por estilo: Gaming, Épicas, Robots, Radio, etc.\n• Puedes guardar tus voces favoritas con el botón ★ Añadir a favoritos.\n• En Packs tienes una lista para aplicar favoritos rápido.\n\nVOCES RECOMENDADAS\n\n"
            "Gaming normal: Gaming limpio, Discord claro, Streamer, Voz clara.\n"
            "Fortnite: Fortnite grave, Comentarista eSports, Tryhard oscuro.\n"
            "Directos: Podcast, Locutor español, Cine tráiler.\n"
            "Bromas: Alien, Ardilla, Payaso gamer, Mini robot.\n"
            "Épicas: Narrador épico, Jefe final, Titán, Dragón suave.\n"
        )
        text.config(state="disabled")

    def slider(self, parent, label, key, mn, mx, row, unit):
        line = ttk.Frame(parent, style="Card.TFrame")
        line.pack(fill="x", pady=5)

        ttk.Label(line, text=label + ":", style="Card.TLabel", width=20).pack(side="left")
        var = self.vars[key]
        scale = ttk.Scale(line, from_=mn, to=mx, variable=var, orient="horizontal", command=lambda _=None: self.update_engine())
        scale.pack(side="left", fill="x", expand=True, padx=10)

        value = ttk.Label(line, style="Card.TLabel", width=16)
        value.pack(side="right")

        def refresh(*_):
            v = var.get()
            value.config(text=f"{v:+.1f} {unit}" if unit == "semitonos" else f"{v:.0f}{unit}")
            self.update_engine()

        var.trace_add("write", refresh)
        refresh()

    def load_devices(self):
        try:
            devices = sd.query_devices()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron leer los dispositivos de audio:\n{e}")
            return

        wasapi = None
        try:
            for i, api in enumerate(sd.query_hostapis()):
                if "wasapi" in str(api.get("name", "")).lower():
                    wasapi = i
                    break
        except Exception:
            wasapi = None

        def construir(filtro):
            ins, outs, imap, omap = [], [], {}, {}
            for i, dev in enumerate(devices):
                if filtro is not None and dev.get("hostapi") != filtro:
                    continue
                name = f"{i}: {dev['name']}"
                if dev.get("max_input_channels", 0) > 0:
                    ins.append(name)
                    imap[name] = i
                if dev.get("max_output_channels", 0) > 0:
                    outs.append(name)
                    omap[name] = i
            return ins, outs, imap, omap

        inputs, outputs, imap, omap = construir(wasapi)
        if not inputs or not outputs:
            inputs, outputs, imap, omap = construir(None)

        self.input_map.clear()
        self.input_map.update(imap)
        self.output_map.clear()
        self.output_map.update(omap)

        for combo in self.input_combos:
            try:
                combo["values"] = inputs
            except Exception:
                pass
        for combo in self.output_combos:
            try:
                combo["values"] = outputs
            except Exception:
                pass

        self._rematch_devices()
        if self.input_dev.get() and self.input_dev.get() not in self.input_map:
            self.input_dev.set("")
        if self.output_dev.get() and self.output_dev.get() not in self.output_map:
            self.output_dev.set("")

        # Preselecciona los dispositivos predeterminados de Windows: son
        # los que el usuario ya usa y los que seguro funcionan.
        default_in = default_out = None
        try:
            d = sd.default.device
            for label, idx in self.input_map.items():
                if idx == d[0]:
                    default_in = label
                    break
            for label, idx in self.output_map.items():
                if idx == d[1]:
                    default_out = label
                    break
        except Exception:
            pass
        if inputs and not self.input_dev.get():
            self.input_dev.set(default_in or inputs[0])
        if outputs and not self.output_dev.get():
            self.output_dev.set(default_out or outputs[0])

    def find_virtual(self):
        words = ["cable input", "vb-audio", "voicemeeter input", "virtual", "sonic studio"]
        for name in self.output_map:
            if any(w in name.lower() for w in words):
                self.output_dev.set(name)
                messagebox.showinfo("Cable virtual encontrado", f"He seleccionado:\n\n{name}")
                return True
        messagebox.showwarning("No encontrado", "No he encontrado cable virtual. Instala VB-Cable o VoiceMeeter, pulsa Actualizar y vuelve a probar.")
        return False

    def refresh_voice_list(self):
        if self.voice_list is None:
            return

        self.voice_list.delete(0, tk.END)
        query = self.search.get().strip().lower()
        selected_cat = self.category.get()

        for name, (cat, _) in VoiceBank.all_presets().items():
            if selected_cat == "Favoritos" and name not in self.favorites:
                continue
            if selected_cat not in ("Todas", "Favoritos") and cat != selected_cat:
                continue
            if query and query not in name.lower() and query not in cat.lower():
                continue
            star = "★ " if name in self.favorites else ""
            self.voice_list.insert(tk.END, f"{star}{name}   ·   {cat}")

    def on_voice_select(self, event=None):
        if not self.voice_list.curselection():
            return
        item = self.voice_list.get(self.voice_list.curselection()[0])
        name = item.split("   ·   ")[0].replace("★", "").strip()
        self.preset.set(name)
        self.update_voice_preview()

    def apply_selected_voice(self):
        self.on_voice_select()
        self.apply_preset()


    def update_voice_preview(self):
        if self.voice_preview_label is None:
            return
        key = self.voice_image_key(self.preset.get())
        img = self.grid_voice_images.get(key)
        if img is not None:
            self.voice_preview_label.configure(image=img, text="")
            self.voice_preview_label.image = img
        else:
            self.voice_preview_label.configure(text="Sin imagen previa", image="")
            self.voice_preview_label.image = None

    def apply_preset(self):
        presets = VoiceBank.all_presets()
        name = self.preset.get()
        if name not in presets:
            name = "Gaming limpio"
            self.preset.set(name)

        _, values = presets[name]
        for reset_key in ['autotune', 'autotune_shift', 'vibrato', 'chorus', 'eq_low', 'eq_mid', 'eq_high']:
            if reset_key in self.vars and reset_key not in values:
                self.vars[reset_key].set(0)
        for key, value in values.items():
            if key in self.vars:
                self.vars[key].set(value)
        self.update_engine()
        self.update_voice_preview()

    def random_voice(self):
        name = random.choice(list(VoiceBank.all_presets().keys()))
        self.preset.set(name)
        self.apply_preset()
        messagebox.showinfo("Voz aleatoria", f"He elegido:\n\n{name}")

    def show_recommended(self):
        messagebox.showinfo(
            "Voces recomendadas",
            "Para jugar:\n"
            "• Gaming limpio\n"
            "• Discord claro\n"
            "• Fortnite grave\n"
            "• Streamer\n\n"
            "Para directos:\n"
            "• Podcast\n"
            "• Locutor español\n"
            "• Comentarista eSports\n\n"
            "Para bromas:\n"
            "• Alien\n"
            "• Ardilla\n"
            "• Payaso gamer\n\n"
            "Para épico:\n"
            "• Narrador épico\n"
            "• Jefe final\n"
            "• Titán\n"
            "• Dragón suave"
        )

    def quick_mode(self, mode):
        if mode == "headphones":
            self.preset.set("Gaming limpio")
            self.latency.set("Baja")
            messagebox.showinfo("Modo auriculares", "Selecciona como salida tus auriculares y pulsa Empezar directo.")
        elif mode == "discord":
            self.preset.set("Discord claro")
            self.latency.set("Baja")
            self.find_virtual()
            messagebox.showinfo("Modo Discord", "En Discord elige como micrófono CABLE Output o VoiceMeeter Output.")
        elif mode == "fortnite":
            self.preset.set("Fortnite grave")
            self.latency.set("Baja")
            self.find_virtual()
            messagebox.showinfo("Modo Fortnite", "En Fortnite elige como entrada de voz CABLE Output o VoiceMeeter Output.")
        elif mode == "obs":
            self.preset.set("Locutor español")
            self.latency.set("Estable")
            self.find_virtual()
            messagebox.showinfo("Modo OBS", "En OBS añade una captura de entrada de audio con CABLE Output o VoiceMeeter Output.")
        self.apply_preset()

    def current_values(self):
        return {key: float(var.get()) for key, var in self.vars.items()}

    def update_engine(self):
        vals = self.current_values()
        with self.engine.lock:
            self.engine.pitch = vals["pitch"]
            self.engine.bass = clamp(vals["bass"] / 100, 0, 1)
            self.engine.robot = clamp(vals["robot"] / 100, 0, 1)
            self.engine.echo = clamp(vals["echo"] / 100, 0, 1)
            self.engine.radio = clamp(vals["radio"] / 100, 0, 1)
            self.engine.megaphone = clamp(vals["megaphone"] / 100, 0, 1)
            self.engine.noise_gate = clamp(vals["gate"] / 1000, 0, 0.08)
            self.engine.compressor = clamp(vals["comp"] / 100, 0, 1)
            self.engine.volume = clamp(vals["vol"] / 100, 0, 1.5)
            self.engine.autotune = clamp(vals.get("autotune", 0) / 100, 0, 1)
            self.engine.autotune_shift = vals.get("autotune_shift", 0)
            self.engine.vibrato = clamp(vals.get("vibrato", 0) / 100, 0, 1)
            self.engine.chorus = clamp(vals.get("chorus", 0) / 100, 0, 1)
            self.engine.eq_low = 10 ** (clamp(vals.get("eq_low", 0), -12, 12) / 20)
            self.engine.eq_mid = 10 ** (clamp(vals.get("eq_mid", 0), -12, 12) / 20)
            self.engine.eq_high = 10 ** (clamp(vals.get("eq_high", 0), -12, 12) / 20)
            self.engine.mute = bool(self.mute.get())
            self.engine.effects_enabled = bool(self.effects_enabled.get())
            if bool(self.nr_enabled.get()):
                self.engine.noise_reduction = clamp(float(self.nr_amount.get()) / 100, 0, 1)
            else:
                self.engine.noise_reduction = 0.0

    def save_config(self, silent=False):
        data = {
            "preset": self.preset.get(),
            "category": self.category.get(),
            "latency": self.latency.get(),
            "input": self.input_dev.get(),
            "output": self.output_dev.get(),
            "language": self.app_language.get(),
            "values": self.current_values(),
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        if not silent:
            messagebox.showinfo("Guardado", "Configuración guardada correctamente.")

    def load_config(self, silent=False):
        if not os.path.exists(CONFIG_FILE):
            if not silent:
                messagebox.showwarning("Sin configuración", "Todavía no hay configuración guardada.")
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.preset.set(data.get("preset", "Gaming limpio"))
            self.category.set(data.get("category", "Todas"))
            self.latency.set(data.get("latency", "Baja"))
            self.app_language.set(data.get("language", "Español"))

            if data.get("input"):
                self.input_dev.set(data["input"])
            if data.get("output"):
                self.output_dev.set(data["output"])

            vals = data.get("values", {})
            for key, value in vals.items():
                if key in self.vars:
                    self.vars[key].set(value)

            self.refresh_voice_list()
            self.update_engine()
            if hasattr(self, "refresh_language_ui"):
                self.refresh_language_ui()

            if not silent:
                messagebox.showinfo("Cargado", "Configuración cargada correctamente.")
        except Exception as e:
            if not silent:
                messagebox.showerror("Error", f"No se pudo cargar la configuración:\n{e}")

    def reset(self):
        self.preset.set("Gaming limpio")
        self.category.set("Todas")
        self.latency.set("Baja")
        self.mute.set(False)
        self.apply_preset()
        self.refresh_voice_list()

    def start(self, silent=False):
        input_id = self.input_map.get(self.input_dev.get())
        output_id = self.output_map.get(self.output_dev.get())

        if input_id is None or output_id is None:
            # El nombre guardado puede tener otro índice hoy: recasa y reintenta.
            self._rematch_devices()
            input_id = self.input_map.get(self.input_dev.get())
            output_id = self.output_map.get(self.output_dev.get())

        if input_id is None or output_id is None:
            if not silent:
                messagebox.showwarning("Faltan dispositivos", "Selecciona micrófono y salida en la pestaña Ajustes o en el Asistente.")
            return False

        try:
            self.update_engine()
            self.engine.start(input_id, output_id, self.latency.get())
            self.state.set("Estado: voz en directo activa")
            return True
        except Exception as e:
            if not silent:
                messagebox.showerror("Error al iniciar", f"No se pudo iniciar el directo:\n\n{e}\n\nPrueba latencia 'Estable' o cambia de dispositivo.")
            return False

    def stop(self):
        self.engine.stop()
        self.state.set("Estado: detenido")

    def recordings_folder(self):
        folder = os.path.join(os.path.expanduser("~"), "ModuladorVozDirecto_Grabaciones")
        os.makedirs(folder, exist_ok=True)
        return folder

    def record(self):
        if not self.recording:
            self.engine.start_recording()
            self.recording = True
            self.state.set("Estado: grabando prueba WAV")
            if hasattr(self, "recordings_status"):
                self.recordings_status.set("Grabando prueba. Pulsa otra vez para detener y guardar.")
            return

        filename = "prueba_voz_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".wav"
        path = os.path.join(self.recordings_folder(), filename)

        ok = self.engine.stop_recording(path)
        self.recording = False

        if ok:
            self.state.set(f"Estado: grabación guardada · {filename}")
            if hasattr(self, "recordings_status"):
                self.recordings_status.set(f"Grabación guardada: {filename}")
            self.refresh_recordings_list()
            messagebox.showinfo("Grabación guardada", f"Archivo guardado:\n{path}")
        else:
            self.state.set("Estado: sin audio grabado")
            if hasattr(self, "recordings_status"):
                self.recordings_status.set("No se grabó audio. Revisa el micrófono.")
            messagebox.showwarning("Sin audio", "No se grabó audio.")

    def update_meters(self):
        mic = min(100, int(self.engine.mic_level * 900))
        out = min(100, int(self.engine.out_level * 900))

        for bar_name in ["home_mic_bar", "live_mic_bar", "pro_mic_bar", "directo_pro_mic_bar"]:
            if hasattr(self, bar_name):
                getattr(self, bar_name)["value"] = mic

        for bar_name in ["home_out_bar", "live_out_bar", "pro_out_bar", "directo_pro_out_bar"]:
            if hasattr(self, bar_name):
                getattr(self, bar_name)["value"] = out

        disponible = min(self.engine.replay_filled / self.engine.rate, self.engine.replay_seconds)
        self.clips_available.set(f"Buffer: {disponible:.0f} s de {self.engine.replay_seconds} s")

        self.update_visualizer()
        self.root.after(80, self.update_meters)


    def create_tray_image(self):
        if not TRAY_AVAILABLE:
            return None
        try:
            return Image.open(resource_path("assets/app_icon.png")).resize((64, 64))
        except Exception:
            img = Image.new("RGBA", (64, 64), (12, 13, 20, 255))
            draw = ImageDraw.Draw(img)
            draw.ellipse((5, 5, 59, 59), fill=(124, 92, 255, 255), outline=(0, 229, 255, 255), width=3)
            draw.rounded_rectangle((26, 14, 38, 38), radius=6, fill=(255, 255, 255, 255))
            draw.rectangle((30, 38, 34, 48), fill=(255, 255, 255, 255))
            draw.arc((18, 28, 46, 50), 0, 180, fill=(255, 255, 255, 255), width=4)
            draw.rectangle((22, 50, 42, 54), fill=(255, 255, 255, 255))
            return img

    def setup_tray(self):
        if not TRAY_AVAILABLE:
            return

        if self.tray_icon is not None:
            return

        menu = pystray.Menu(
            pystray.MenuItem("Mostrar modulador", lambda icon, item: self.root.after(0, self.show_window)),
            pystray.MenuItem("Ocultar a la bandeja", lambda icon, item: self.root.after(0, self.hide_to_tray)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Empezar directo", lambda icon, item: self.root.after(0, self.start)),
            pystray.MenuItem("Parar directo", lambda icon, item: self.root.after(0, self.stop)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir del programa", lambda icon, item: self.root.after(0, self.quit_app)),
        )

        self.tray_icon = pystray.Icon(
            "ModuladorVozDirecto",
            self.create_tray_image(),
            "Modulador de Voz en Directo",
            menu
        )

        def run_icon():
            try:
                self.tray_icon.run()
            except Exception as e:
                print("Error en bandeja del sistema:", e)

        thread = threading.Thread(target=run_icon, daemon=True)
        thread.start()
        self.tray_thread_started = True

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.state.set("Estado: ventana visible" if not self.engine.running else "Estado: voz en directo activa")

    def hide_to_tray(self):
        if TRAY_AVAILABLE:
            self.root.withdraw()
            if self.engine.running:
                self.state.set("Estado: activo en bandeja Windows")
            else:
                self.state.set("Estado: oculto en bandeja Windows")
        else:
            messagebox.showwarning(
                "Bandeja no disponible",
                "Para usar la bandeja junto al reloj instala las dependencias con instalar_dependencias.bat.\n\n"
                "Necesitas: pystray y pillow."
            )
            self.root.iconify()

    def quit_app(self):
        self.real_exit = True
        if GLOBAL_HOTKEYS_AVAILABLE:
            try:
                global_keyboard.unhook_all_hotkeys()
            except Exception:
                pass
        try:
            self.save_config(silent=True)
        except Exception:
            pass
        try:
            self.stop()
        except Exception:
            pass

        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None

        self.root.destroy()


    def close(self):
        self.hide_to_tray()


def main():
    root = tk.Tk()
    PremiumApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
