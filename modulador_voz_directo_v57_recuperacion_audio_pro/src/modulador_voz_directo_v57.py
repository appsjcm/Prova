
import json
import os
import sys
from pathlib import Path
import wave
import threading
import subprocess
import platform
import random
import time
import math
from datetime import datetime
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
    from PIL import Image, ImageDraw, ImageTk
    TRAY_AVAILABLE = True
except Exception:
    pystray = None
    Image = None
    ImageDraw = None
    TRAY_AVAILABLE = False

# Atajos globales: funcionan aunque el juego o Discord tengan el foco.
try:
    import keyboard as global_keyboard
    GLOBAL_HOTKEYS_AVAILABLE = True
except Exception:
    global_keyboard = None
    GLOBAL_HOTKEYS_AVAILABLE = False


APP_NAME = "Modulador de Voz en Directo"
VERSION = "57.0 Recuperación de Audio Pro"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "modulador_voz_directo_v57_config.json")


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
            outdata[:] = self.process(indata)
        except Exception as e:
            print("Error de audio:", e)
            outdata[:] = np.zeros_like(outdata)

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
        self.reset_buffers()
        self.stream = sd.Stream(
            samplerate=self.rate,
            blocksize=block,
            dtype="float32",
            channels=1,
            device=(input_id, output_id),
            callback=self.callback,
            latency="low" if block <= 512 else "high",
        )
        self.stream.start()
        self.running = True

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
        self.root.title(f"{APP_NAME} V{VERSION} - Español")
        self.root.geometry("1160x820")
        self.root.minsize(1040, 740)

        self.engine = AudioEngine()
        self.input_map = {}
        self.output_map = {}
        self.recording = False
        self.tray_icon = None
        self.tray_thread_started = False
        self.real_exit = False
        self.welcome_shown = False

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

    def build_ui(self):
        main = ttk.Frame(self.root, padding=18)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 12))

        left = ttk.Frame(header)
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text="🎙️ Modulador de Voz en Directo", font=("Segoe UI", 28, "bold")).pack(anchor="w")
        ttk.Label(left, text="V57 Recuperación de Audio Pro · interfaz visual · imágenes propias · soundboard · bandeja Windows", style="Muted.TLabel", font=("Segoe UI", 11)).pack(anchor="w")

        right = ttk.Frame(header)
        right.pack(side="right")
        ttk.Label(right, textvariable=self.state, style="Accent.TLabel").pack(anchor="e")
        ttk.Label(right, text="Micrófono real → Voz modificada → Cable virtual", style="Muted.TLabel").pack(anchor="e")

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)

        self.tab_inicio = ttk.Frame(self.notebook, padding=14)
        self.tab_pro = ttk.Frame(self.notebook, padding=14)
        self.tab_asistente = ttk.Frame(self.notebook, padding=14)
        self.tab_barra_rapida = ttk.Frame(self.notebook, padding=14)
        self.tab_mesa_pro = ttk.Frame(self.notebook, padding=14)
        self.tab_diagnostico = ttk.Frame(self.notebook, padding=14)
        self.tab_mini_panel = ttk.Frame(self.notebook, padding=14)
        self.tab_ecualizador = ttk.Frame(self.notebook, padding=14)
        self.tab_perfiles_pro = ttk.Frame(self.notebook, padding=14)
        self.tab_personas_pro = ttk.Frame(self.notebook, padding=14)
        self.tab_cambiador_personas = ttk.Frame(self.notebook, padding=14)
        self.tab_creador_voces = ttk.Frame(self.notebook, padding=14)
        self.tab_atajos = ttk.Frame(self.notebook, padding=14)
        self.tab_favoritos_pro = ttk.Frame(self.notebook, padding=14)
        self.tab_escenas_pro = ttk.Frame(self.notebook, padding=14)
        self.tab_streamer_hub = ttk.Frame(self.notebook, padding=14)
        self.tab_rendimiento = ttk.Frame(self.notebook, padding=14)
        self.tab_ruido = ttk.Frame(self.notebook, padding=14)
        self.tab_cable_virtual = ttk.Frame(self.notebook, padding=14)
        self.tab_test_voz = ttk.Frame(self.notebook, padding=14)
        self.tab_autotune = ttk.Frame(self.notebook, padding=14)
        self.tab_karaoke = ttk.Frame(self.notebook, padding=14)
        self.tab_karaoke_studio = ttk.Frame(self.notebook, padding=14)
        self.tab_cancion_pro = ttk.Frame(self.notebook, padding=14)
        self.tab_mezclador_musical = ttk.Frame(self.notebook, padding=14)
        self.tab_master_final = ttk.Frame(self.notebook, padding=14)
        self.tab_studio_dashboard = ttk.Frame(self.notebook, padding=14)
        self.tab_analizador_vocal = ttk.Frame(self.notebook, padding=14)
        self.tab_cadena_vocal = ttk.Frame(self.notebook, padding=14)
        self.tab_timeline_pro = ttk.Frame(self.notebook, padding=14)
        self.tab_multipista = ttk.Frame(self.notebook, padding=14)
        self.tab_clips = ttk.Frame(self.notebook, padding=14)
        self.tab_grabadora = ttk.Frame(self.notebook, padding=14)
        self.tab_directo_pro = ttk.Frame(self.notebook, padding=14)
        self.tab_voicebox_grid = ttk.Frame(self.notebook, padding=14)
        self.tab_ultra = ttk.Frame(self.notebook, padding=14)
        self.tab_voces = ttk.Frame(self.notebook, padding=14)
        self.tab_studio = ttk.Frame(self.notebook, padding=14)
        self.tab_packs = ttk.Frame(self.notebook, padding=14)
        self.tab_ajustes = ttk.Frame(self.notebook, padding=14)
        self.tab_directo = ttk.Frame(self.notebook, padding=14)
        self.tab_sonidos = ttk.Frame(self.notebook, padding=14)
        self.tab_visualizador = ttk.Frame(self.notebook, padding=14)
        self.tab_guia = ttk.Frame(self.notebook, padding=14)

        self.notebook.add(self.tab_inicio, text="🏠 Inicio")
        self.notebook.add(self.tab_pro, text="🎛 Modo Pro")
        self.notebook.add(self.tab_asistente, text="🧭 Asistente")
        self.notebook.add(self.tab_barra_rapida, text="⚡ Barra rápida")
        self.notebook.add(self.tab_mesa_pro, text="🎚 Mesa Pro")
        self.notebook.add(self.tab_diagnostico, text="🛠 Diagnóstico")
        self.notebook.add(self.tab_mini_panel, text="🪟 Mini Panel")
        self.notebook.add(self.tab_ecualizador, text="🎚 Ecualizador")
        self.notebook.add(self.tab_perfiles_pro, text="👤 Perfiles Pro+")
        self.notebook.add(self.tab_personas_pro, text="👥 Personas Pro")
        self.notebook.add(self.tab_cambiador_personas, text="🎭 Cambiador")
        self.notebook.add(self.tab_creador_voces, text="🧪 Creador")
        self.notebook.add(self.tab_atajos, text="⌨ Atajos")
        self.notebook.add(self.tab_favoritos_pro, text="⭐ Favoritos")
        self.notebook.add(self.tab_escenas_pro, text="🎬 Escenas")
        self.notebook.add(self.tab_streamer_hub, text="📡 Streamer Hub")
        self.notebook.add(self.tab_rendimiento, text="🚀 Rendimiento")
        self.notebook.add(self.tab_ruido, text="🤫 Ruido")
        self.notebook.add(self.tab_cable_virtual, text="🔌 Cable Virtual")
        self.notebook.add(self.tab_test_voz, text="🎙 Test de Voz")
        self.notebook.add(self.tab_autotune, text="🎵 Autotune")
        self.notebook.add(self.tab_karaoke, text="🎤 Karaoke")
        self.notebook.add(self.tab_karaoke_studio, text="🎧 Karaoke Studio")
        self.notebook.add(self.tab_cancion_pro, text="🎼 Canción Pro")
        self.notebook.add(self.tab_mezclador_musical, text="🎚 Mezclador")
        self.notebook.add(self.tab_master_final, text="💿 Master Final")
        self.notebook.add(self.tab_studio_dashboard, text="🏁 Studio")
        self.notebook.add(self.tab_analizador_vocal, text="📊 Analizador")
        self.notebook.add(self.tab_cadena_vocal, text="🎙 Cadena Vocal")
        self.notebook.add(self.tab_timeline_pro, text="🧱 Timeline")
        self.notebook.add(self.tab_multipista, text="🎛 Multipista")
        self.notebook.add(self.tab_clips, text="🎬 Clips")
        self.notebook.add(self.tab_grabadora, text="⏺ Grabadora")
        self.notebook.add(self.tab_directo_pro, text="🎬 Directo Pro")
        self.notebook.add(self.tab_voicebox_grid, text="▦ Caja de voces")
        self.notebook.add(self.tab_ultra, text="💠 Ultra")
        self.notebook.add(self.tab_voces, text="🎙 Voces")
        self.notebook.add(self.tab_studio, text="💎 Estudio")
        self.notebook.add(self.tab_packs, text="🧩 Packs")
        self.notebook.add(self.tab_ajustes, text="🎚 Ajustes")
        self.notebook.add(self.tab_directo, text="▶ Directo")
        self.notebook.add(self.tab_sonidos, text="🔊 Sonidos")
        self.notebook.add(self.tab_visualizador, text="📊 Visualizador")
        self.notebook.add(self.tab_guia, text="📘 Guía")

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


    def show_welcome(self):
        if self.welcome_shown:
            return
        self.welcome_shown = True

        win = tk.Toplevel(self.root)
        win.title("Bienvenido a Estudio de Voz Ultra")
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
            ttk.Label(frame, text="Estudio de Voz Ultra", font=("Segoe UI", 28, "bold")).pack(pady=(0, 14))

        ttk.Label(
            frame,
            text="V57 Recuperación de Audio Pro está preparada para directo, Discord, Fortnite, OBS, soundboard y perfiles personalizados.",
            style="Muted.TLabel",
            wraplength=690,
            justify="center",
            font=("Segoe UI", 11)
        ).pack(pady=(0, 16))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Configurar Discord", style="Accent.TButton", command=lambda: [self.quick_mode("discord"), win.destroy()]).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(buttons, text="Configurar Fortnite", style="Accent.TButton", command=lambda: [self.quick_mode("fortnite"), win.destroy()]).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(buttons, text="Abrir Studio", command=lambda: [self.notebook.select(self.tab_studio_dashboard), win.destroy()]).pack(side="left", expand=True, fill="x", padx=5)
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

        ttk.Button(sidebar, text="⚡ Barra rápida", style="Accent.TButton", command=lambda: self.notebook.select(self.tab_barra_rapida)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🧭 Asistente", command=lambda: self.notebook.select(self.tab_asistente)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎙 Caja de voces", command=lambda: self.notebook.select(self.tab_voicebox_grid)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎬 Directo Pro", command=lambda: self.notebook.select(self.tab_directo_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🏁 Studio", command=lambda: self.notebook.select(self.tab_studio_dashboard)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="📊 Analizador", command=lambda: self.notebook.select(self.tab_analizador_vocal)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎙 Cadena Vocal", command=lambda: self.notebook.select(self.tab_cadena_vocal)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🧱 Timeline", command=lambda: self.notebook.select(self.tab_timeline_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎛 Multipista", command=lambda: self.notebook.select(self.tab_multipista)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="💿 Master Final", command=lambda: self.notebook.select(self.tab_master_final)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎚 Mezclador", command=lambda: self.notebook.select(self.tab_mezclador_musical)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎼 Canción Pro", command=lambda: self.notebook.select(self.tab_cancion_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎧 Karaoke Studio", command=lambda: self.notebook.select(self.tab_karaoke_studio)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎤 Karaoke", command=lambda: self.notebook.select(self.tab_karaoke)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎵 Autotune", command=lambda: self.notebook.select(self.tab_autotune)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎙 Test de Voz", command=lambda: self.notebook.select(self.tab_test_voz)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🔌 Cable Virtual", command=lambda: self.notebook.select(self.tab_cable_virtual)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🚀 Rendimiento", command=lambda: self.notebook.select(self.tab_rendimiento)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🤫 Ruido", command=lambda: self.notebook.select(self.tab_ruido)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="📡 Streamer Hub", command=lambda: self.notebook.select(self.tab_streamer_hub)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎬 Escenas", command=lambda: self.notebook.select(self.tab_escenas_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="⭐ Favoritos", command=lambda: self.notebook.select(self.tab_favoritos_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="⌨ Atajos", command=lambda: self.notebook.select(self.tab_atajos)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🧪 Creador", command=lambda: self.notebook.select(self.tab_creador_voces)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎭 Cambiador", command=lambda: self.notebook.select(self.tab_cambiador_personas)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="👥 Personas Pro", command=lambda: self.notebook.select(self.tab_personas_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="👤 Perfiles Pro+", command=lambda: self.notebook.select(self.tab_perfiles_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎚 Ecualizador", command=lambda: self.notebook.select(self.tab_ecualizador)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🪟 Mini Panel", command=lambda: self.notebook.select(self.tab_mini_panel)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🛠 Diagnóstico", command=lambda: self.notebook.select(self.tab_diagnostico)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎬 Clips", command=lambda: self.notebook.select(self.tab_clips)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="⏺ Grabadora", command=lambda: self.notebook.select(self.tab_grabadora)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🎚 Mesa Pro", command=lambda: self.notebook.select(self.tab_mesa_pro)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="🔊 Mesa de sonidos", command=lambda: self.notebook.select(self.tab_sonidos)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="💎 Estudio", command=lambda: self.notebook.select(self.tab_studio)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="📊 Visualizador", command=lambda: self.notebook.select(self.tab_visualizador)).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="⚙ Ajustes", command=lambda: self.notebook.select(self.tab_ajustes)).pack(fill="x", pady=4)
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
            ttk.Button(box, text="Abrir", command=lambda t=target: self.notebook.select(t)).pack(fill="x", pady=(6, 0))
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
        ttk.Button(acciones, text="Abrir Canción Pro", command=lambda: self.notebook.select(self.tab_cancion_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Karaoke Studio", command=lambda: self.notebook.select(self.tab_karaoke_studio)).pack(fill="x", pady=3)
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
        ttk.Button(acciones, text="Abrir Karaoke", command=lambda: self.notebook.select(self.tab_karaoke)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Autotune", command=lambda: self.notebook.select(self.tab_autotune)).pack(fill="x", pady=3)

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
            f"TÍTULO: {title}\\n\\n"
            "[Intro]\\n"
            "Respira, la pista empieza,\\n"
            "todo listo para cantar.\\n\\n"
            "[Verso 1]\\n"
            "Tengo luces en la mente,\\n"
            "una voz que quiere sonar,\\n"
            "voy probando cada frase,\\n"
            "hasta encontrar mi lugar.\\n\\n"
            "[Pre-estribillo]\\n"
            "Sube un poco el autotune,\\n"
            "deja el eco respirar,\\n"
            "si la mezcla queda limpia,\\n"
            "ya lo puedo publicar.\\n\\n"
            "[Estribillo]\\n"
            "Canto fuerte sobre el beat,\\n"
            "mi demo empieza a brillar,\\n"
            "grabo todo en un WAV,\\n"
            "y lo vuelvo a mejorar.\\n\\n"
            "[Outro]\\n"
            "La canción se va apagando,\\n"
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
            "ESTRUCTURA DE CANCIÓN\\n\\n"
            "Intro: entrada suave.\\n"
            "Verso: base media para cantar claro.\\n"
            "Estribillo: más energía.\\n"
            "Outro: final con fade.\\n\\n"
            "EXPORTACIÓN\\n\\n"
            "- Exportar instrumental WAV guarda solo la base.\\n"
            "- Grabar demo cantada guarda voz + base si está sonando.\\n"
            "- Guardar letra TXT exporta el texto del editor.\\n\\n"
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
            self.song_update_info(f"Instrumental exportado en:\\n{path}")
            messagebox.showinfo("Instrumental exportado", f"Archivo guardado en:\\n{path}")
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
            messagebox.showinfo("Letra guardada", f"Archivo guardado en:\\n{path}")
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
            ("Abrir Karaoke", lambda: self.notebook.select(self.tab_karaoke)),
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
            "KARAOKE STUDIO PRO\\n\\n"
            "Genera instrumentales originales simples para cantar encima.\\n"
            "No usan canciones comerciales ni voces de terceros.\\n\\n"
            "LETRA RÁPIDA\\n\\n"
            "[Verso]\\n"
            "Hoy me subo al escenario,\\n"
            "con mi voz y mi señal,\\n"
            "la base suena de fondo,\\n"
            "todo listo para cantar.\\n\\n"
            "[Estribillo]\\n"
            "Karaoke en mi habitación,\\n"
            "autotune en el corazón,\\n"
            "grabo demo y pruebo el beat,\\n"
            "hasta encontrar mi mejor versión.\\n\\n"
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
            self.karaoke_studio_update_text(f"Instrumental generado: {title}\\nPulsa Play y canta encima.")
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
        ttk.Button(acciones, text="Abrir Autotune", command=lambda: self.notebook.select(self.tab_autotune)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Grabadora", command=lambda: self.notebook.select(self.tab_grabadora)).pack(fill="x", pady=3)

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
            "KARAOKE PRO - LETRA DE PRUEBA\\n\\n"
            "[Verso]\\n"
            "Luces en la pantalla,\\n"
            "mi voz empieza a sonar,\\n"
            "con la pista instrumental,\\n"
            "ya me puedo preparar.\\n\\n"
            "[Pre-estribillo]\\n"
            "Sube el autotune,\\n"
            "dale brillo a la señal,\\n"
            "si la mezcla queda limpia,\\n"
            "lista para publicar.\\n\\n"
            "[Estribillo]\\n"
            "Canto encima del beat,\\n"
            "todo suena mucho mejor,\\n"
            "grabo demo en WAV,\\n"
            "y guardo mi configuración.\\n\\n"
            "Notas:\\n"
            "- Puedes borrar esta letra y escribir la tuya.\\n"
            "- Usa instrumentales sin voz que tengas permiso de usar.\\n"
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
        ttk.Button(acciones, text="Abrir Test de Voz", command=lambda: self.notebook.select(self.tab_test_voz)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Grabadora", command=lambda: self.notebook.select(self.tab_grabadora)).pack(fill="x", pady=3)

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
            "LETRA DE PRUEBA PROPIA\\n\\n"
            "Hoy mi voz se enciende,\\n"
            "brilla fuerte en la señal,\\n"
            "si el eco no se pierde,\\n"
            "todo suena natural.\\n\\n"
            "Sube un poco el autotune,\\n"
            "dale brillo al corazón,\\n"
            "grabo una demo rápida,\\n"
            "y reviso la canción.\\n\\n"
            "PRUEBAS RECOMENDADAS\\n\\n"
            "1. Canta una frase corta.\\n"
            "2. Graba demo WAV.\\n"
            "3. Ajusta Autotune, Vibrato y Coro.\\n"
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
        ttk.Button(quick, text="Abrir Rendimiento", command=lambda: self.notebook.select(self.tab_rendimiento)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Cable Virtual", command=lambda: self.notebook.select(self.tab_cable_virtual)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Grabadora", command=lambda: self.notebook.select(self.tab_grabadora)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Streamer Hub", command=lambda: self.notebook.select(self.tab_streamer_hub)).pack(fill="x", pady=3)

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
        ttk.Button(acciones, text="Abrir Favoritos", command=lambda: self.notebook.select(self.tab_favoritos_pro)).pack(fill="x", pady=3)

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
        ttk.Button(acciones, text="Abrir Asistente", command=lambda: self.notebook.select(self.tab_asistente)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Diagnóstico", command=lambda: self.notebook.select(self.tab_diagnostico)).pack(fill="x", pady=3)

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
        ttk.Button(acciones, text="Abrir Diagnóstico", command=lambda: self.notebook.select(self.tab_diagnostico)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Streamer Hub", command=lambda: self.notebook.select(self.tab_streamer_hub)).pack(fill="x", pady=3)

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
                if etiqueta.endswith(nombre):
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
            ("tile_escenas", "Escenas", lambda: self.notebook.select(self.tab_escenas_pro)),
            ("tile_favoritos", "Favoritos", lambda: self.notebook.select(self.tab_favoritos_pro)),
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
        ttk.Button(quick_row3, text="Diagnóstico", command=lambda: self.notebook.select(self.tab_diagnostico)).pack(side="left", fill="x", expand=True, padx=3, ipady=8)

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
        ttk.Button(accesos, text="Escenas Pro", command=lambda: self.notebook.select(self.tab_escenas_pro)).pack(fill="x", pady=3)
        ttk.Button(accesos, text="Favoritos Pro", command=lambda: self.notebook.select(self.tab_favoritos_pro)).pack(fill="x", pady=3)
        ttk.Button(accesos, text="Atajos Pro", command=lambda: self.notebook.select(self.tab_atajos)).pack(fill="x", pady=3)
        ttk.Button(accesos, text="Creador de Voces", command=lambda: self.notebook.select(self.tab_creador_voces)).pack(fill="x", pady=3)

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
        ttk.Button(acciones, text="Abrir Favoritos", command=lambda: self.notebook.select(self.tab_favoritos_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Directo Pro", command=lambda: self.notebook.select(self.tab_directo_pro)).pack(fill="x", pady=3)
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
        ttk.Button(acciones, text="Abrir Caja de Voces", command=lambda: self.notebook.select(self.tab_voicebox_grid)).pack(fill="x", pady=3)
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
        ttk.Button(acciones, text="Abrir Cambiador", command=lambda: self.notebook.select(self.tab_cambiador_personas)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Creador", command=lambda: self.notebook.select(self.tab_creador_voces)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Directo Pro", command=lambda: self.notebook.select(self.tab_directo_pro)).pack(fill="x", pady=3)

        tips = self.make_card(right, "Consejos")
        tips.pack(fill="x")
        ttk.Label(
            tips,
            text=(
                "• Los atajos no son globales: no reemplazan teclas del juego.\\n"
                "• Úsalos cuando la ventana esté enfocada.\\n"
                "• Para directos, combina Atajos Pro con Mini Panel.\\n"
                "• F1-F8 cambian voces.\\n"
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
        ttk.Button(acciones, text="Abrir Cambiador", command=lambda: self.notebook.select(self.tab_cambiador_personas)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Personas Pro", command=lambda: self.notebook.select(self.tab_personas_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Perfiles Pro+", command=lambda: self.notebook.select(self.tab_perfiles_pro)).pack(fill="x", pady=3)
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
        return os.path.join(os.path.expanduser("~"), "modulador_voz_directo_v57_voces.json")

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
        ttk.Button(acciones, text="Abrir Personas Pro", command=lambda: self.notebook.select(self.tab_personas_pro)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Mini Panel", command=lambda: self.notebook.select(self.tab_mini_panel)).pack(fill="x", pady=3)

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
        ttk.Button(acciones, text="Abrir Ecualizador", command=lambda: self.notebook.select(self.tab_ecualizador)).pack(fill="x", pady=3)
        ttk.Button(acciones, text="Abrir Mini Panel", command=lambda: self.notebook.select(self.tab_mini_panel)).pack(fill="x", pady=3)

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
        ttk.Button(actions, text="Abrir Grabadora", command=lambda: self.notebook.select(self.tab_grabadora)).pack(fill="x", pady=3)
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
        ttk.Button(row, text="Abrir Directo Pro", command=lambda: self.notebook.select(self.tab_directo_pro)).pack(side="left", expand=True, fill="x", padx=4, pady=4)

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
        ttk.Button(access, text="Caja de voces", command=lambda: [self.notebook.select(self.tab_voicebox_grid), win.lift()]).pack(fill="x", pady=2)
        ttk.Button(access, text="Mesa Pro", command=lambda: [self.notebook.select(self.tab_mesa_pro), win.lift()]).pack(fill="x", pady=2)
        ttk.Button(access, text="Directo Pro", command=lambda: [self.notebook.select(self.tab_directo_pro), win.lift()]).pack(fill="x", pady=2)

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
        ttk.Button(controls, text="Abrir mesa clásica", command=lambda: self.notebook.select(self.tab_sonidos)).pack(fill="x", pady=3)
        ttk.Button(controls, text="Abrir Directo Pro", command=lambda: self.notebook.select(self.tab_directo_pro)).pack(fill="x", pady=3)

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

        tips = self.make_card(right, "Objetivo V57")
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
            self.notebook.select(getattr(self, attr))
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

        ttk.Button(checklist, text="Abrir Cadena Vocal", command=lambda: self.notebook.select(self.tab_cadena_vocal)).pack(fill="x", pady=3)
        if hasattr(self, "tab_mezclador_musical"):
            ttk.Button(checklist, text="Abrir Mezclador", command=lambda: self.notebook.select(self.tab_mezclador_musical)).pack(fill="x", pady=3)
        if hasattr(self, "tab_master_final"):
            ttk.Button(checklist, text="Abrir Master Final", command=lambda: self.notebook.select(self.tab_master_final)).pack(fill="x", pady=3)
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
            ttk.Button(acc, text="Abrir Autotune", command=lambda: self.notebook.select(self.tab_autotune)).pack(fill="x", pady=3)
        if hasattr(self, "tab_karaoke"):
            ttk.Button(acc, text="Abrir Karaoke", command=lambda: self.notebook.select(self.tab_karaoke)).pack(fill="x", pady=3)
        if hasattr(self, "tab_mezclador_musical"):
            ttk.Button(acc, text="Abrir Mezclador", command=lambda: self.notebook.select(self.tab_mezclador_musical)).pack(fill="x", pady=3)
        if hasattr(self, "tab_master_final"):
            ttk.Button(acc, text="Abrir Master Final", command=lambda: self.notebook.select(self.tab_master_final)).pack(fill="x", pady=3)
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
        ttk.Button(acc, text="Abrir Canción Pro", command=lambda: self.notebook.select(self.tab_cancion_pro)).pack(fill="x", pady=3)
        ttk.Button(acc, text="Abrir Multipista", command=lambda: self.notebook.select(self.tab_multipista)).pack(fill="x", pady=3)
        if hasattr(self, "tab_master_final"):
            ttk.Button(acc, text="Abrir Master Final", command=lambda: self.notebook.select(self.tab_master_final)).pack(fill="x", pady=3)

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
        ttk.Button(quick, text="Abrir Mezclador", command=lambda: self.notebook.select(self.tab_mezclador_musical)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Master Final", command=lambda: self.notebook.select(self.tab_master_final)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Canción Pro", command=lambda: self.notebook.select(self.tab_cancion_pro)).pack(fill="x", pady=3)

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
                "STEMS / STUDIO DASHBOARD PRO\n\n• La pestaña Studio Dashboard centraliza el flujo completo: analizar, cadena vocal, timeline, multipista, mezcla y master.\n• Incluye preparación %, checklist, siguiente paso recomendado, flujo seguro y exportación JSON/TXT.\n\nANALIZADOR VOCAL PRO\n\n• La pestaña Analizador revisa la configuración vocal: volumen, eco, puerta de ruido, compresión, autotune y riesgos de clipping.\n• Incluye check rápido, auto-ajuste seguro, reducción de ruido e informes JSON/TXT.\n\nCADENA VOCAL PRO\n\n• La pestaña Cadena Vocal organiza la voz como flujo de estudio: ruido, compresión, presencia, aire, calidez, reverb y delay.\n• Incluye presets para voz limpia, pop vocal, trap vocal, podcast y karaoke, más exportación JSON.\n\nTIMELINE PRO\n\n• La pestaña Timeline organiza la canción por intro, verso, pre, estribillo, puente y outro.\n• Permite ajustar BPM, tonalidad, duración, generar base y exportar plan JSON/TXT.\n\nMULTIPISTA PRO\n\n"
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
        ttk.Button(quick, text="Abrir Canción Pro", command=lambda: self.notebook.select(self.tab_cancion_pro)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Mezclador", command=lambda: self.notebook.select(self.tab_mezclador_musical)).pack(fill="x", pady=3)
        ttk.Button(quick, text="Abrir Karaoke Studio", command=lambda: self.notebook.select(self.tab_karaoke_studio)).pack(fill="x", pady=3)

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
        ttk.Combobox(row1, textvariable=self.input_dev, state="readonly", values=self.input_combo["values"] if hasattr(self, "input_combo") else [], width=70).pack(side="left", fill="x", expand=True, padx=8)

        row2 = ttk.Frame(devices, style="Card.TFrame")
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Salida modificada:", style="Card.TLabel", width=20).pack(side="left")
        ttk.Combobox(row2, textvariable=self.output_dev, state="readonly", values=self.output_combo["values"] if hasattr(self, "output_combo") else [], width=70).pack(side="left", fill="x", expand=True, padx=8)

        dev_buttons = ttk.Frame(devices, style="Card.TFrame")
        dev_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(dev_buttons, text="Actualizar dispositivos", command=self.assistant_refresh_devices).pack(side="left", padx=4)
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
                ttk.Button(box, text=label, style="Accent.TButton", command=lambda t=target: self.notebook.select(t)).pack(fill="x")

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

        row2 = ttk.Frame(devices, style="Card.TFrame")
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Salida modificada:", style="Card.TLabel", width=22).pack(side="left")
        self.output_combo = ttk.Combobox(row2, textvariable=self.output_dev, state="readonly")
        self.output_combo.pack(side="left", fill="x", expand=True, padx=8)

        row3 = ttk.Frame(devices, style="Card.TFrame")
        row3.pack(fill="x", pady=(10, 0))
        ttk.Button(row3, text="Actualizar dispositivos", command=self.load_devices).pack(side="left", padx=(0, 8))
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
        return os.path.join(os.path.expanduser("~"), "modulador_voz_directo_v57_profiles.json")

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
        self.notebook.select(self.tab_voces)
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
        self.notebook.select(self.tab_voces)
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
            self.notebook.select(self.tab_voces)
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
        self.notebook.select(self.tab_voces)

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
        return os.path.join(os.path.expanduser("~"), "modulador_voz_directo_v57_favoritos.json")

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
        try:
            with wave.open(path, "rb") as wav:
                channels = wav.getnchannels()
                sampwidth = wav.getsampwidth()
                framerate = wav.getframerate()
                frames = wav.readframes(wav.getnframes())

            if sampwidth == 1:
                data = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
                data = (data - 128) / 128.0
            elif sampwidth == 2:
                data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                messagebox.showwarning("Formato no compatible", "Usa WAV de 8 o 16 bits.")
                return None

            if channels > 1:
                data = data.reshape(-1, channels).mean(axis=1)

            if framerate != self.engine.rate:
                old_idx = np.arange(len(data))
                new_len = int(len(data) * self.engine.rate / framerate)
                new_idx = np.linspace(0, len(data)-1, new_len)
                data = np.interp(new_idx, old_idx, data).astype(np.float32)

            return np.clip(data, -0.95, 0.95)
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

        inputs = []
        outputs = []
        self.input_map.clear()
        self.output_map.clear()

        for i, dev in enumerate(devices):
            name = f"{i}: {dev['name']}"
            if dev.get("max_input_channels", 0) > 0:
                inputs.append(name)
                self.input_map[name] = i
            if dev.get("max_output_channels", 0) > 0:
                outputs.append(name)
                self.output_map[name] = i

        self.input_combo["values"] = inputs
        self.output_combo["values"] = outputs

        if inputs and not self.input_dev.get():
            self.input_dev.set(inputs[0])
        if outputs and not self.output_dev.get():
            self.output_dev.set(outputs[0])

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
            if not silent:
                messagebox.showwarning("Faltan dispositivos", "Selecciona micrófono y salida.")
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
