"""Datos de voces de VoiceICC: catálogo de packs (PACKS_DATA) y banco de
voces (VoiceBank). Módulo de datos puro, sin dependencias de interfaz ni
audio. Extraído de voiceicc.py en la modularización por fases (fase A.1)."""

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
            # VOICE CHARACTERS PRO - personajes ficticios con voz e identidad propia
            "Luna Vega": ("Personajes Premium", dict(pitch=1.2, bass=8, robot=0, echo=0, radio=0, megaphone=0, gate=4, comp=30, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=86, human_warmth=38, human_breath=8, de_ess=34, clarity=24, transient=16, modern_space=5, eq_low=1, eq_mid=0, eq_high=2)),
            "Nora Pulse": ("Personajes Premium", dict(pitch=0.8, bass=7, robot=0, echo=0, radio=0, megaphone=0, gate=5, comp=38, vol=93, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=82, human_warmth=30, human_breath=6, de_ess=38, clarity=32, transient=22, modern_space=3, eq_low=0, eq_mid=1, eq_high=2)),
            "Leo Nova": ("Personajes Premium", dict(pitch=-0.8, bass=14, robot=0, echo=0, radio=0, megaphone=0, gate=4, comp=32, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=87, human_warmth=44, human_breath=7, de_ess=28, clarity=22, transient=15, modern_space=4, eq_low=1, eq_mid=0, eq_high=1)),
            "Bruno Atlas": ("Personajes Premium", dict(pitch=-1.4, bass=19, robot=0, echo=0, radio=0, megaphone=0, gate=5, comp=42, vol=93, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=84, human_warmth=54, human_breath=5, de_ess=26, clarity=20, transient=13, modern_space=3, eq_low=2, eq_mid=0, eq_high=0)),
            "Mia Echo": ("Personajes Premium", dict(pitch=1.0, bass=6, robot=0, echo=1, radio=0, megaphone=0, gate=4, comp=34, vol=92, autotune=5, autotune_shift=0, vibrato=1, chorus=3, human_realism=78, human_warmth=30, human_breath=8, de_ess=40, clarity=26, transient=15, modern_space=12, eq_low=0, eq_mid=1, eq_high=2)),
            "Kai Flux": ("Personajes Premium", dict(pitch=-0.3, bass=11, robot=0, echo=0, radio=0, megaphone=0, gate=5, comp=40, vol=94, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=82, human_warmth=34, human_breath=5, de_ess=32, clarity=36, transient=24, modern_space=3, eq_low=1, eq_mid=1, eq_high=2)),
            "Zoe Neon": ("Personajes Premium", dict(pitch=1.4, bass=4, robot=0, echo=1, radio=0, megaphone=0, gate=4, comp=36, vol=93, autotune=12, autotune_shift=0, vibrato=1, chorus=4, human_realism=72, human_warmth=24, human_breath=6, de_ess=42, clarity=34, transient=18, modern_space=16, eq_low=0, eq_mid=1, eq_high=3)),
            "Axel Noir": ("Personajes Premium", dict(pitch=-1.8, bass=23, robot=0, echo=1, radio=0, megaphone=0, gate=5, comp=48, vol=95, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=78, human_warmth=58, human_breath=4, de_ess=24, clarity=18, transient=20, modern_space=14, eq_low=2, eq_mid=0, eq_high=0)),
            "Alma Story": ("Personajes Premium", dict(pitch=0.2, bass=10, robot=0, echo=0, radio=0, megaphone=0, gate=4, comp=28, vol=91, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=90, human_warmth=52, human_breath=10, de_ess=32, clarity=16, transient=10, modern_space=6, eq_low=1, eq_mid=0, eq_high=1)),
            "Hugo Reed": ("Personajes Premium", dict(pitch=-1.5, bass=20, robot=0, echo=0, radio=0, megaphone=0, gate=5, comp=34, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=92, human_warmth=60, human_breath=9, de_ess=22, clarity=14, transient=10, modern_space=5, eq_low=2, eq_mid=0, eq_high=0)),
            "Nico Spark": ("Personajes Premium", dict(pitch=2.6, bass=1, robot=0, echo=0, radio=0, megaphone=0, gate=3, comp=26, vol=89, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=83, human_warmth=24, human_breath=9, de_ess=40, clarity=28, transient=18, modern_space=4, eq_low=0, eq_mid=1, eq_high=2)),
            "Eva Bloom": ("Personajes Premium", dict(pitch=3.0, bass=0, robot=0, echo=0, radio=0, megaphone=0, gate=3, comp=26, vol=89, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=84, human_warmth=24, human_breath=9, de_ess=42, clarity=27, transient=17, modern_space=4, eq_low=0, eq_mid=1, eq_high=2)),
            # V1.2 REAL VOICE CORE - cambios sutiles y pulido vocal de baja latencia
            "Voz natural equilibrada V1.4": ("Real Voice V1.4", dict(pitch=0.0, bass=8, robot=0, echo=0, radio=0, megaphone=0, gate=4, comp=27, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=94, human_warmth=42, human_breath=6, de_ess=36, clarity=24, transient=12, modern_space=2, vocal_focus=40, proximity=18, smart_level=54, fx_ducking=72, eq_low=0, eq_mid=0, eq_high=1)),
            "Podcast íntimo natural V1.4": ("Real Voice V1.4", dict(pitch=0.0, bass=12, robot=0, echo=0, radio=0, megaphone=0, gate=5, comp=34, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=95, human_warmth=56, human_breath=5, de_ess=34, clarity=17, transient=9, modern_space=1, vocal_focus=28, proximity=46, smart_level=68, fx_ducking=82, eq_low=1, eq_mid=0, eq_high=0)),
            "Streaming claro V1.4": ("Real Voice V1.4", dict(pitch=0.0, bass=7, robot=0, echo=0, radio=0, megaphone=0, gate=6, comp=39, vol=93, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=88, human_warmth=31, human_breath=3, de_ess=39, clarity=42, transient=25, modern_space=1, vocal_focus=58, proximity=10, smart_level=72, fx_ducking=88, eq_low=-1, eq_mid=1, eq_high=2)),
            "Narración cine humana V1.4": ("Real Voice V1.4", dict(pitch=-0.7, bass=17, robot=0, echo=0, radio=0, megaphone=0, gate=5, comp=37, vol=93, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=93, human_warmth=64, human_breath=7, de_ess=27, clarity=18, transient=13, modern_space=9, vocal_focus=31, proximity=55, smart_level=60, fx_ducking=74, eq_low=2, eq_mid=0, eq_high=0)),
            "Canto limpio moderno V1.4": ("Real Voice V1.4", dict(pitch=0.0, bass=7, robot=0, echo=0, radio=0, megaphone=0, gate=3, comp=35, vol=92, autotune=7, autotune_shift=0, vibrato=1, chorus=2, human_realism=84, human_warmth=32, human_breath=5, de_ess=42, clarity=30, transient=16, modern_space=14, vocal_focus=46, proximity=14, smart_level=48, fx_ducking=78, eq_low=0, eq_mid=1, eq_high=2)),
            "Game Chat ultra limpio V1.4": ("Real Voice V1.4", dict(pitch=0.0, bass=5, robot=0, echo=0, radio=0, megaphone=0, gate=8, comp=43, vol=94, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=82, human_warmth=24, human_breath=2, de_ess=34, clarity=48, transient=30, modern_space=0, vocal_focus=66, proximity=4, smart_level=78, fx_ducking=92, eq_low=-2, eq_mid=2, eq_high=2)),
            "Broadcast Clean Next": ("FX Smart V1.4", dict(pitch=0.0, bass=9, robot=0, echo=0, radio=0, megaphone=0, gate=6, comp=42, vol=94, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=84, human_warmth=34, human_breath=2, de_ess=40, clarity=48, transient=25, modern_space=2, vocal_focus=62, proximity=18, smart_level=80, fx_ducking=90, eq_low=0, eq_mid=1, eq_high=2)),
            "Spatial Creator Duck": ("FX Smart V1.4", dict(pitch=0.0, bass=7, robot=0, echo=0, radio=0, megaphone=0, gate=5, comp=36, vol=93, autotune=0, autotune_shift=0, vibrato=0, chorus=3, human_realism=76, human_warmth=28, human_breath=3, de_ess=38, clarity=34, transient=17, modern_space=34, vocal_focus=45, proximity=10, smart_level=60, fx_ducking=94, eq_low=0, eq_mid=1, eq_high=3)),
            "Cinematic Hybrid Duck": ("FX Smart V1.4", dict(pitch=-0.5, bass=21, robot=0, echo=1, radio=0, megaphone=0, gate=5, comp=49, vol=95, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=72, human_warmth=52, human_breath=2, de_ess=28, clarity=22, transient=34, modern_space=31, vocal_focus=34, proximity=48, smart_level=58, fx_ducking=86, eq_low=2, eq_mid=0, eq_high=1)),
            "Voz femenina natural V1.2": ("Real Voice V1.2", dict(pitch=0.8, bass=7, robot=0, echo=0, radio=0, megaphone=0, gate=4, comp=29, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=90, human_warmth=40, human_breath=7, de_ess=38, clarity=24, transient=14, modern_space=3, eq_low=1, eq_mid=0, eq_high=2)),
            "Voz masculina natural V1.2": ("Real Voice V1.2", dict(pitch=-0.7, bass=14, robot=0, echo=0, radio=0, megaphone=0, gate=4, comp=31, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=90, human_warmth=48, human_breath=6, de_ess=30, clarity=22, transient=14, modern_space=3, eq_low=1, eq_mid=0, eq_high=1)),
            "Podcast íntimo V1.2": ("Real Voice V1.2", dict(pitch=0, bass=13, robot=0, echo=0, radio=0, megaphone=0, gate=5, comp=40, vol=93, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=88, human_warmth=56, human_breath=5, de_ess=34, clarity=18, transient=10, modern_space=2, eq_low=2, eq_mid=0, eq_high=1)),
            "Streamer claro V1.2": ("Real Voice V1.2", dict(pitch=0, bass=9, robot=0, echo=0, radio=0, megaphone=0, gate=6, comp=43, vol=94, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=82, human_warmth=34, human_breath=4, de_ess=36, clarity=42, transient=28, modern_space=2, eq_low=0, eq_mid=1, eq_high=3)),
            "Narrador cálido V1.2": ("Real Voice V1.2", dict(pitch=-1.2, bass=19, robot=0, echo=0, radio=0, megaphone=0, gate=5, comp=36, vol=93, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=92, human_warmth=64, human_breath=8, de_ess=24, clarity=16, transient=12, modern_space=7, eq_low=2, eq_mid=0, eq_high=0)),
            "Pop moderno sutil": ("Real Voice V1.2", dict(pitch=0.4, bass=7, robot=0, echo=1, radio=0, megaphone=0, gate=4, comp=38, vol=93, autotune=10, autotune_shift=0, vibrato=1, chorus=3, human_realism=76, human_warmth=30, human_breath=5, de_ess=42, clarity=32, transient=18, modern_space=18, eq_low=0, eq_mid=1, eq_high=3)),
            # MODERN VOICE FX - efectos actuales para creador, gaming y vídeo
            "Creator Clean 2026": ("FX Modernos", dict(pitch=0, bass=9, robot=0, echo=0, radio=0, megaphone=0, gate=6, comp=46, vol=94, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=80, human_warmth=30, human_breath=3, de_ess=38, clarity=48, transient=32, modern_space=2, eq_low=0, eq_mid=1, eq_high=3)),
            "Neon Pop Wide": ("FX Modernos", dict(pitch=0.5, bass=6, robot=0, echo=1, radio=0, megaphone=0, gate=4, comp=42, vol=94, autotune=16, autotune_shift=0, vibrato=1, chorus=5, human_realism=64, human_warmth=22, human_breath=3, de_ess=44, clarity=38, transient=18, modern_space=28, eq_low=0, eq_mid=1, eq_high=4)),
            "Cyber Radio HD": ("FX Modernos", dict(pitch=0, bass=-3, robot=5, echo=1, radio=18, megaphone=0, gate=9, comp=58, vol=93, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=35, human_warmth=8, human_breath=0, de_ess=20, clarity=42, transient=34, modern_space=4, eq_low=-2, eq_mid=2, eq_high=3)),
            "Cinematic Modern Wide": ("FX Modernos", dict(pitch=-1.0, bass=24, robot=0, echo=2, radio=0, megaphone=0, gate=5, comp=56, vol=96, autotune=0, autotune_shift=0, vibrato=0, chorus=2, human_realism=70, human_warmth=52, human_breath=3, de_ess=28, clarity=22, transient=38, modern_space=30, eq_low=3, eq_mid=0, eq_high=1)),
            "Game Chat Pro": ("FX Modernos", dict(pitch=0, bass=7, robot=0, echo=0, radio=2, megaphone=0, gate=8, comp=52, vol=94, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=72, human_warmth=22, human_breath=2, de_ess=32, clarity=52, transient=36, modern_space=0, eq_low=-1, eq_mid=2, eq_high=3)),
            "Dream Space Modern": ("FX Modernos", dict(pitch=0.2, bass=7, robot=0, echo=3, radio=0, megaphone=0, gate=4, comp=32, vol=91, autotune=4, autotune_shift=0, vibrato=1, chorus=6, human_realism=58, human_warmth=30, human_breath=5, de_ess=36, clarity=20, transient=8, modern_space=46, eq_low=0, eq_mid=0, eq_high=2)),
            # REALISTIC EFFECTS PACK PRO - efectos de entorno más suaves y creíbles
            "Radio FM realista": ("Efectos Ultra Realistas", dict(pitch=0, bass=-8, robot=0, echo=1, radio=18, megaphone=0, gate=12, comp=54, vol=90, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=20, human_warmth=8, human_breath=2)),
            "Teléfono antiguo real": ("Efectos Ultra Realistas", dict(pitch=0, bass=-16, robot=0, echo=1, radio=42, megaphone=0, gate=14, comp=62, vol=91, autotune=0, autotune_shift=0, vibrato=0, chorus=0, human_realism=12, human_warmth=-4, human_breath=0)),
            "Megáfono exterior real": ("Efectos Ultra Realistas", dict(pitch=-1, bass=4, robot=0, echo=5, radio=12, megaphone=36, gate=14, comp=72, vol=96, autotune=0, autotune_shift=0, vibrato=0, chorus=2, human_realism=10, human_warmth=8, human_breath=1)),
            "Sala estudio real": ("Efectos Ultra Realistas", dict(pitch=0, bass=12, robot=0, echo=4, radio=0, megaphone=0, gate=8, comp=52, vol=92, autotune=0, autotune_shift=0, vibrato=1, chorus=5, human_realism=38, human_warmth=18, human_breath=5)),
            "Habitación pequeña real": ("Efectos Ultra Realistas", dict(pitch=0, bass=8, robot=0, echo=8, radio=0, megaphone=0, gate=7, comp=46, vol=90, autotune=0, autotune_shift=0, vibrato=1, chorus=4, human_realism=32, human_warmth=12, human_breath=5)),
            "Cueva suave real": ("Efectos Ultra Realistas", dict(pitch=-2, bass=18, robot=0, echo=16, radio=0, megaphone=0, gate=9, comp=44, vol=88, autotune=0, autotune_shift=0, vibrato=1, chorus=10, human_realism=20, human_warmth=12, human_breath=4)),
            "Cine trailer natural": ("Efectos Ultra Realistas", dict(pitch=-5, bass=36, robot=0, echo=9, radio=0, megaphone=0, gate=10, comp=68, vol=96, autotune=0, autotune_shift=0, vibrato=1, chorus=8, human_realism=24, human_warmth=24, human_breath=4)),
            "Intercom realista": ("Efectos Ultra Realistas", dict(pitch=0, bass=-6, robot=0, echo=2, radio=26, megaphone=12, gate=15, comp=66, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=1, human_realism=10, human_warmth=0, human_breath=0)),
            # HUMAN REALISM PRO - presets todavía más sutiles y naturales, sin clonar personas reales
            "Mujer real sutil HD": ("Human Realism", dict(pitch=2, bass=7, robot=0, echo=1, radio=0, megaphone=0, gate=5, comp=34, vol=92, autotune=0, autotune_shift=0, vibrato=1, chorus=2, human_realism=68, human_warmth=42, human_breath=18, eq_low=1, eq_mid=1, eq_high=2)),
            "Mujer conversacion real": ("Human Realism", dict(pitch=1, bass=8, robot=0, echo=1, radio=0, megaphone=0, gate=5, comp=30, vol=91, autotune=0, autotune_shift=0, vibrato=1, chorus=1, human_realism=72, human_warmth=45, human_breath=22, eq_low=1, eq_mid=0, eq_high=2)),
            "Hombre real sutil HD": ("Human Realism", dict(pitch=-2, bass=16, robot=0, echo=1, radio=0, megaphone=0, gate=5, comp=35, vol=92, autotune=0, autotune_shift=0, vibrato=1, chorus=1, human_realism=68, human_warmth=52, human_breath=16, eq_low=2, eq_mid=1, eq_high=1)),
            "Hombre conversacion real": ("Human Realism", dict(pitch=-1, bass=14, robot=0, echo=1, radio=0, megaphone=0, gate=4, comp=30, vol=91, autotune=0, autotune_shift=0, vibrato=1, chorus=1, human_realism=74, human_warmth=48, human_breath=20, eq_low=2, eq_mid=0, eq_high=1)),
            "Joven real suave": ("Human Realism", dict(pitch=3, bass=5, robot=0, echo=1, radio=0, megaphone=0, gate=4, comp=28, vol=90, autotune=0, autotune_shift=0, vibrato=1, chorus=1, human_realism=70, human_warmth=32, human_breath=18, eq_low=0, eq_mid=1, eq_high=2)),
            "Mayor real narrador": ("Human Realism", dict(pitch=-3, bass=18, robot=0, echo=2, radio=0, megaphone=0, gate=6, comp=38, vol=91, autotune=0, autotune_shift=0, vibrato=2, chorus=1, human_realism=78, human_warmth=58, human_breath=24, eq_low=2, eq_mid=1, eq_high=0)),
            "Estudio humano limpio": ("Human Realism", dict(pitch=0, bass=10, robot=0, echo=1, radio=0, megaphone=0, gate=5, comp=32, vol=92, autotune=0, autotune_shift=0, vibrato=1, chorus=1, human_realism=80, human_warmth=44, human_breath=12, eq_low=1, eq_mid=1, eq_high=2)),
            "Streaming humano natural": ("Human Realism", dict(pitch=0, bass=12, robot=0, echo=1, radio=0, megaphone=0, gate=6, comp=38, vol=93, autotune=0, autotune_shift=0, vibrato=1, chorus=1, human_realism=72, human_warmth=40, human_breath=10, eq_low=1, eq_mid=1, eq_high=2)),
            # REAL VOICE FX PRO - voces genéricas más naturales, sin clonar personas reales
            "Mujer natural cálida": ("Personas Realistas", dict(pitch=5, bass=8, robot=0, echo=2, radio=0, megaphone=0, gate=7, comp=42, vol=92, autotune=0, autotune_shift=0, vibrato=4, chorus=6)),
            "Mujer radio suave": ("Personas Realistas", dict(pitch=4, bass=10, robot=0, echo=3, radio=1, megaphone=0, gate=8, comp=52, vol=94, autotune=0, autotune_shift=0, vibrato=3, chorus=8)),
            "Hombre natural cercano": ("Personas Realistas", dict(pitch=-4, bass=22, robot=0, echo=2, radio=0, megaphone=0, gate=8, comp=46, vol=92, autotune=0, autotune_shift=0, vibrato=2, chorus=4)),
            "Hombre podcast real": ("Personas Realistas", dict(pitch=-5, bass=28, robot=0, echo=1, radio=0, megaphone=0, gate=10, comp=60, vol=94, autotune=0, autotune_shift=0, vibrato=1, chorus=3)),
            "Niño natural suave": ("Personas Realistas", dict(pitch=11, bass=-4, robot=0, echo=1, radio=0, megaphone=0, gate=6, comp=38, vol=88, autotune=0, autotune_shift=0, vibrato=5, chorus=5)),
            "Niña natural suave": ("Personas Realistas", dict(pitch=13, bass=-6, robot=0, echo=1, radio=0, megaphone=0, gate=6, comp=38, vol=88, autotune=0, autotune_shift=0, vibrato=5, chorus=6)),
            "Abuelo narrador real": ("Personas Realistas", dict(pitch=-8, bass=26, robot=0, echo=3, radio=1, megaphone=0, gate=10, comp=48, vol=90, autotune=0, autotune_shift=0, vibrato=7, chorus=3)),
            "Abuela cuento real": ("Personas Realistas", dict(pitch=1, bass=12, robot=0, echo=3, radio=1, megaphone=0, gate=9, comp=48, vol=90, autotune=0, autotune_shift=0, vibrato=7, chorus=4)),
            "Locutor cine realista": ("Efectos Realistas", dict(pitch=-6, bass=32, robot=0, echo=6, radio=0, megaphone=0, gate=10, comp=68, vol=96, autotune=0, autotune_shift=0, vibrato=2, chorus=8)),
            "Sala pequeña real": ("Efectos Realistas", dict(pitch=0, bass=10, robot=0, echo=7, radio=0, megaphone=0, gate=8, comp=45, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=4)),
            "Teléfono real limpio": ("Efectos Realistas", dict(pitch=0, bass=-10, robot=0, echo=0, radio=32, megaphone=0, gate=12, comp=58, vol=92, autotune=0, autotune_shift=0, vibrato=0, chorus=0)),
            "Megáfono real exterior": ("Efectos Realistas", dict(pitch=-1, bass=6, robot=0, echo=4, radio=10, megaphone=32, gate=12, comp=70, vol=96, autotune=0, autotune_shift=0, vibrato=0, chorus=2)),
            "Estudio limpio real": ("Efectos Realistas", dict(pitch=0, bass=14, robot=0, echo=1, radio=0, megaphone=0, gate=9, comp=55, vol=93, autotune=0, autotune_shift=0, vibrato=1, chorus=3)),
            "Autotune natural suave": ("Efectos Realistas", dict(pitch=0, bass=10, robot=0, echo=3, radio=0, megaphone=0, gate=7, comp=45, vol=92, autotune=18, autotune_shift=0, vibrato=3, chorus=9)),
            # GAMING
            "Gaming limpio":        ("Gaming", dict(pitch=0,  bass=15, robot=0,  echo=0,  radio=3,  megaphone=0,  gate=8,  comp=38, vol=90, human_realism=48, human_warmth=30, de_ess=24, clarity=30, transient=14, vocal_focus=40, proximity=22, smart_level=48)),
            "Discord claro":        ("Gaming", dict(pitch=0,  bass=12, robot=0,  echo=0,  radio=0,  megaphone=0,  gate=9,  comp=58, vol=94, human_realism=46, human_warmth=26, de_ess=28, clarity=34, transient=14, vocal_focus=44, proximity=24, smart_level=56)),
            "Discord nítido":       ("Gaming", dict(pitch=0,  bass=6,  robot=0,  echo=0,  radio=5,  megaphone=0,  gate=9,  comp=64, vol=95, human_realism=44, human_warmth=22, de_ess=32, clarity=38, transient=16, vocal_focus=46, proximity=22, smart_level=60)),
            "Fortnite grave":       ("Gaming", dict(pitch=-5, bass=46, robot=0,  echo=0,  radio=0,  megaphone=0,  gate=7,  comp=52, vol=92)),
            "Fortnite épico":       ("Gaming", dict(pitch=-7, bass=58, robot=3,  echo=6,  radio=0,  megaphone=0,  gate=7,  comp=55, vol=92)),
            "Streamer":             ("Gaming", dict(pitch=1,  bass=12, robot=3,  echo=3,  radio=5,  megaphone=0,  gate=7,  comp=45, vol=88, human_realism=52, human_warmth=34, de_ess=24, clarity=30, transient=12, vocal_focus=38, proximity=24, smart_level=46)),
            "Comentarista eSports": ("Gaming", dict(pitch=1,  bass=20, robot=0,  echo=2,  radio=12, megaphone=5,  gate=8,  comp=62, vol=94, human_realism=44, human_warmth=28, de_ess=22, clarity=34, transient=16, vocal_focus=46, proximity=22, smart_level=54)),
            "Tryhard oscuro":       ("Gaming", dict(pitch=-4, bass=40, robot=4,  echo=4,  radio=4,  megaphone=0,  gate=8,  comp=50, vol=88)),
            "Gamer nocturno":       ("Gaming", dict(pitch=-2, bass=35, robot=0,  echo=8,  radio=0,  megaphone=0,  gate=7,  comp=42, vol=84)),

            # ÉPICAS
            "Narrador épico":       ("Épicas", dict(pitch=-4, bass=45, robot=0,  echo=12, radio=8,  megaphone=0,  gate=6,  comp=55, vol=92, human_realism=50, human_warmth=44, de_ess=18, clarity=30, transient=14, vocal_focus=42, proximity=24, smart_level=50)),
            "Cine tráiler":         ("Épicas", dict(pitch=-7, bass=60, robot=3,  echo=18, radio=6,  megaphone=0,  gate=7,  comp=60, vol=90, human_realism=46, human_warmth=48, de_ess=16, clarity=28, transient=16, vocal_focus=44, proximity=26, smart_level=52)),
            "Héroe final":          ("Épicas", dict(pitch=-3, bass=45, robot=0,  echo=14, radio=4,  megaphone=0,  gate=6,  comp=52, vol=90, human_realism=50, human_warmth=44, de_ess=18, clarity=30, transient=14, vocal_focus=42, proximity=24, smart_level=50)),
            "Titán":                ("Épicas", dict(pitch=-12,bass=90, robot=10, echo=20, radio=0,  megaphone=0,  gate=7,  comp=50, vol=88, formant=-4, clarity=22, transient=12, vocal_focus=32, smart_level=42)),
            "Jefe final":           ("Épicas", dict(pitch=-10,bass=70, robot=28, echo=30, radio=0,  megaphone=0,  gate=8,  comp=45, vol=88, clarity=20, transient=12, vocal_focus=30, smart_level=42)),

            # OSCURAS
            "Voz grave":            ("Oscuras", dict(pitch=-6, bass=45, robot=0,  echo=5,  radio=0,  megaphone=0,  gate=5,  comp=30, vol=90, clarity=24, transient=12, vocal_focus=34, smart_level=44, human_realism=30, human_warmth=30)),
            "Villano":              ("Oscuras", dict(pitch=-8, bass=50, robot=32, echo=22, radio=0,  megaphone=0,  gate=7,  comp=35, vol=86, formant=-2, clarity=22, transient=12, vocal_focus=34, smart_level=42)),
            "Demonio suave":        ("Oscuras", dict(pitch=-9, bass=62, robot=38, echo=18, radio=0,  megaphone=0,  gate=7,  comp=40, vol=84, clarity=22, transient=12, vocal_focus=32, smart_level=42)),
            "Monstruo cueva":       ("Oscuras", dict(pitch=-11,bass=80, robot=18, echo=45, radio=0,  megaphone=0,  gate=6,  comp=35, vol=82, formant=-5, clarity=22, transient=12, vocal_focus=32, smart_level=42)),
            "Sombra":               ("Oscuras", dict(pitch=-7, bass=58, robot=12, echo=34, radio=0,  megaphone=0,  gate=7,  comp=35, vol=80, clarity=24, transient=12, vocal_focus=34, smart_level=44)),
            "Guardián oscuro":      ("Oscuras", dict(pitch=-8, bass=68, robot=10, echo=16, radio=0,  megaphone=0,  gate=7,  comp=45, vol=86, clarity=24, transient=12, vocal_focus=34, smart_level=44, human_realism=28)),

            # ROBOTS
            "Robot directo":        ("Robots", dict(pitch=0,  bass=0,  robot=88, echo=4,  radio=12, megaphone=0,  gate=8,  comp=30, vol=84, clarity=20, transient=12, vocal_focus=34, smart_level=42, human_realism=22)),
            "Androide":             ("Robots", dict(pitch=-1, bass=10, robot=70, echo=6,  radio=20, megaphone=0,  gate=9,  comp=40, vol=86, clarity=22, transient=12, vocal_focus=34, smart_level=42, human_realism=26, human_warmth=20)),
            "IA futurista":         ("Robots", dict(pitch=2,  bass=0,  robot=55, echo=10, radio=28, megaphone=0,  gate=8,  comp=35, vol=82, clarity=24, transient=10, vocal_focus=32, smart_level=42, human_realism=28, human_warmth=18)),
            "Cyborg":               ("Robots", dict(pitch=-3, bass=30, robot=65, echo=8,  radio=25, megaphone=0,  gate=8,  comp=45, vol=86, clarity=22, transient=12, vocal_focus=34, smart_level=44, human_realism=26, human_warmth=22)),
            "Casco espacial":       ("Robots", dict(pitch=-2, bass=20, robot=25, echo=20, radio=38, megaphone=12, gate=9,  comp=50, vol=88, clarity=20, transient=10, vocal_focus=30, smart_level=44)),
            "Robot roto":           ("Robots", dict(pitch=3,  bass=0,  robot=95, echo=12, radio=35, megaphone=0,  gate=10, comp=20, vol=78)),
            "Drone":                ("Robots", dict(pitch=4,  bass=0,  robot=78, echo=9,  radio=28, megaphone=0,  gate=8,  comp=25, vol=76)),
            "Computadora retro":    ("Robots", dict(pitch=1,  bass=0,  robot=86, echo=3,  radio=45, megaphone=0,  gate=10, comp=35, vol=82, clarity=22, transient=12, vocal_focus=32, smart_level=42)),

            # RADIO
            "Locutor español":      ("Radio", dict(pitch=-3, bass=35, robot=0,  echo=6,  radio=15, megaphone=0,  gate=7,  comp=55, vol=92, human_realism=48, human_warmth=46, de_ess=20, clarity=32, transient=12, vocal_focus=44, proximity=24, smart_level=54)),
            "Radio para directo":   ("Radio", dict(pitch=-1, bass=12, robot=8,  echo=0,  radio=95, megaphone=15, gate=9,  comp=55, vol=94)),
            "Radio antigua":        ("Radio", dict(pitch=-1, bass=0,  robot=15, echo=4,  radio=100,megaphone=25, gate=12, comp=60, vol=90)),
            "Walkie Talkie":        ("Radio", dict(pitch=0,  bass=0,  robot=18, echo=2,  radio=90, megaphone=45, gate=12, comp=55, vol=88)),
            "Megáfono":             ("Radio", dict(pitch=0,  bass=0,  robot=8,  echo=4,  radio=45, megaphone=90, gate=10, comp=55, vol=96)),
            "Estadio":              ("Radio", dict(pitch=0,  bass=20, robot=4,  echo=36, radio=25, megaphone=60, gate=8,  comp=55, vol=96)),
            "Radio militar":        ("Radio", dict(pitch=-2, bass=10, robot=12, echo=2,  radio=88, megaphone=50, gate=12, comp=55, vol=90)),

            # DIVERTIDAS
            "Voz aguda":            ("Divertidas", dict(pitch=6,  bass=0,  robot=0,  echo=0,  radio=0,  megaphone=0,  gate=5,  comp=20, vol=78)),
            "Ardilla":              ("Divertidas", dict(pitch=10, bass=0,  robot=0,  echo=0,  radio=0,  megaphone=0,  gate=4,  comp=20, vol=70, formant=6)),
            "Duende":               ("Divertidas", dict(pitch=7,  bass=0,  robot=10, echo=8,  radio=0,  megaphone=0,  gate=5,  comp=25, vol=78)),
            "Payaso gamer":         ("Divertidas", dict(pitch=5,  bass=0,  robot=8,  echo=5,  radio=10, megaphone=0,  gate=6,  comp=30, vol=82)),
            "Mini robot":           ("Divertidas", dict(pitch=8,  bass=0,  robot=70, echo=4,  radio=15, megaphone=0,  gate=8,  comp=25, vol=76)),
            "Caricatura":           ("Divertidas", dict(pitch=9,  bass=0,  robot=3,  echo=2,  radio=0,  megaphone=0,  gate=5,  comp=25, vol=74, formant=5)),
            "Gnomo rápido":         ("Divertidas", dict(pitch=8,  bass=0,  robot=6,  echo=5,  radio=0,  megaphone=0,  gate=5,  comp=25, vol=74)),

            # FANTASÍA
            "Alien":                ("Fantasía", dict(pitch=8,  bass=0,  robot=60, echo=15, radio=5,  megaphone=0,  gate=8,  comp=25, vol=78, formant=4, clarity=22, transient=10, vocal_focus=30, smart_level=42, de_ess=26)),
            "Fantasma":             ("Fantasía", dict(pitch=-2, bass=20, robot=10, echo=58, radio=0,  megaphone=0,  gate=6,  comp=20, vol=76, clarity=22, transient=10, vocal_focus=30, smart_level=40)),
            "Eco mágico":           ("Fantasía", dict(pitch=2,  bass=0,  robot=8,  echo=55, radio=0,  megaphone=0,  gate=5,  comp=20, vol=76)),
            "Hechicero":            ("Fantasía", dict(pitch=-3, bass=35, robot=12, echo=40, radio=0,  megaphone=0,  gate=6,  comp=35, vol=84)),
            "Criatura mágica":      ("Fantasía", dict(pitch=4,  bass=15, robot=25, echo=38, radio=0,  megaphone=0,  gate=6,  comp=25, vol=78)),
            "Portal dimensional":   ("Fantasía", dict(pitch=1,  bass=25, robot=40, echo=60, radio=8,  megaphone=0,  gate=8,  comp=30, vol=80)),
            "Dragón suave":         ("Fantasía", dict(pitch=-9, bass=85, robot=15, echo=24, radio=0,  megaphone=0,  gate=7,  comp=42, vol=86, formant=-4, clarity=22, transient=12, vocal_focus=32, smart_level=42)),
            "Mago neón":            ("Fantasía", dict(pitch=2,  bass=18, robot=18, echo=45, radio=6,  megaphone=0,  gate=6,  comp=28, vol=82)),


            # PERSONAS — voces humanas con cadena de naturalidad para que suenen
            # a persona real (aliento, calidez, de-esser, claridad y presencia),
            # no a simple cambio de tono. Eco casi a cero (una voz real no
            # reverbera) y de-esser alto cuando el tono sube (evita el "seseo").
            "Mujer Lucía":         ("Personas", dict(pitch=2,  bass=8,  robot=0,  echo=1,  radio=0,  megaphone=0,  gate=9,  comp=40, vol=91, formant=3,  human_realism=64, human_warmth=44, human_breath=16, de_ess=30, clarity=22, transient=10, vocal_focus=30, proximity=16, smart_level=42)),
            "Mujer Sofía":         ("Personas", dict(pitch=1,  bass=10, robot=0,  echo=1,  radio=0,  megaphone=0,  gate=9,  comp=42, vol=91, formant=2,  human_realism=68, human_warmth=46, human_breath=20, de_ess=28, clarity=20, transient=9,  vocal_focus=28, proximity=18, smart_level=44)),
            "Hombre Diego":        ("Personas", dict(pitch=-1, bass=20, robot=0,  echo=1,  radio=0,  megaphone=0,  gate=8,  comp=44, vol=92, formant=-1, human_realism=62, human_warmth=50, human_breath=10, de_ess=16, clarity=26, transient=12, vocal_focus=34, proximity=22, smart_level=46)),
            "Hombre Marcos":       ("Personas", dict(pitch=-3, bass=30, robot=0,  echo=1,  radio=0,  megaphone=0,  gate=8,  comp=44, vol=91, formant=-2, human_realism=60, human_warmth=54, human_breath=8,  de_ess=14, clarity=28, transient=14, vocal_focus=36, proximity=24, smart_level=48)),
            "Niño Leo":            ("Personas", dict(pitch=5,  bass=0,  robot=0,  echo=1,  radio=0,  megaphone=0,  gate=6,  comp=26, vol=84, formant=5,  human_realism=66, human_warmth=34, human_breath=20, de_ess=34, clarity=24, transient=8,  vocal_focus=26, proximity=12, smart_level=40)),
            "Niño Nico":           ("Personas", dict(pitch=4,  bass=0,  robot=0,  echo=1,  radio=0,  megaphone=0,  gate=6,  comp=26, vol=84, formant=4,  human_realism=66, human_warmth=36, human_breath=18, de_ess=32, clarity=24, transient=8,  vocal_focus=26, proximity=12, smart_level=40)),
            "Niña Luna":           ("Personas", dict(pitch=6,  bass=0,  robot=0,  echo=1,  radio=0,  megaphone=0,  gate=6,  comp=26, vol=84, formant=5,  human_realism=68, human_warmth=34, human_breath=22, de_ess=36, clarity=24, transient=7,  vocal_focus=24, proximity=12, smart_level=40)),
            "Niña Emma":           ("Personas", dict(pitch=5,  bass=2,  robot=0,  echo=1,  radio=0,  megaphone=0,  gate=6,  comp=28, vol=85, formant=5,  human_realism=66, human_warmth=36, human_breath=20, de_ess=34, clarity=24, transient=8,  vocal_focus=24, proximity=12, smart_level=40)),
            "Abuelo Paco":         ("Personas", dict(pitch=-2, bass=24, robot=0,  echo=1,  radio=0,  megaphone=0,  gate=8,  comp=46, vol=89, formant=-1, vibrato=9,  human_realism=64, human_warmth=52, human_breath=24, de_ess=18, clarity=16, transient=6,  vocal_focus=24, proximity=20, smart_level=42)),
            "Abuelo José":         ("Personas", dict(pitch=-2, bass=22, robot=0,  echo=1,  radio=0,  megaphone=0,  gate=8,  comp=44, vol=89, formant=-1, vibrato=7,  human_realism=64, human_warmth=50, human_breath=22, de_ess=18, clarity=18, transient=6,  vocal_focus=26, proximity=20, smart_level=42)),
            "Abuela Carmen":       ("Personas", dict(pitch=1,  bass=10, robot=0,  echo=1,  radio=0,  megaphone=0,  gate=9,  comp=44, vol=89, formant=2,  vibrato=9,  human_realism=64, human_warmth=48, human_breath=24, de_ess=26, clarity=16, transient=6,  vocal_focus=24, proximity=18, smart_level=42)),
            "Abuela Lola":         ("Personas", dict(pitch=2,  bass=8,  robot=0,  echo=1,  radio=0,  megaphone=0,  gate=9,  comp=44, vol=89, formant=2,  vibrato=11, human_realism=64, human_warmth=48, human_breath=26, de_ess=26, clarity=16, transient=6,  vocal_focus=24, proximity=18, smart_level=42)),

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
            "Voz clara":            ("Limpias", dict(pitch=0,  bass=8,  robot=0,  echo=0,  radio=0,  megaphone=0,  gate=8,  comp=45, vol=90, human_realism=58, human_warmth=38, human_breath=10, de_ess=26, clarity=26, transient=10, vocal_focus=34, proximity=18, smart_level=44)),
            "Podcast":              ("Limpias", dict(pitch=-1, bass=28, robot=0,  echo=2,  radio=6,  megaphone=0,  gate=9,  comp=60, vol=92, human_realism=56, human_warmth=48, human_breath=8, de_ess=22, clarity=30, transient=12, vocal_focus=40, proximity=24, smart_level=52)),
            "Nocturna suave":       ("Limpias", dict(pitch=-2, bass=30, robot=0,  echo=10, radio=0,  megaphone=0,  gate=7,  comp=35, vol=82, human_realism=60, human_warmth=52, human_breath=14, de_ess=20, clarity=18, transient=8, vocal_focus=30, proximity=22, smart_level=42)),
            "Voz cálida":           ("Limpias", dict(pitch=-1, bass=35, robot=0,  echo=1,  radio=0,  megaphone=0,  gate=7,  comp=50, vol=90, human_realism=58, human_warmth=56, human_breath=10, de_ess=18, clarity=22, transient=10, vocal_focus=34, proximity=24, smart_level=46)),
        }

    @staticmethod
    def categories():
        cats = ["Todas"]
        for category, _ in VoiceBank.all_presets().values():
            if category not in cats:
                cats.append(category)
        return cats
