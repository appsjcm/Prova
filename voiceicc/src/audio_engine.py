"""Motor de audio DSP de VoiceICC (AudioEngine): efectos en tiempo real,
pitch/formant, autotune, reduccion de ruido, EQ, medidores y perfilado.
Sin dependencias de interfaz (tkinter). Extraido de voiceicc.py (fase A.2)."""

import math
import time
import threading
import numpy as np
import sounddevice as sd


def clamp(value, low, high):
    return max(low, min(high, value))


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
        # Conversión de voz neuronal LOCAL (RVC), opcional. Si hay un backend
        # cargado, reemplaza la cadena DSP como fuente de la voz.
        self.rvc_backend = None
        self.rvc_enabled = False
        self.rvc_failures = 0
        self.rvc_disabled_reason = ""
        self.rvc_failure_limit = 20
        self.autotune = 0.0
        self.autotune_shift = 0.0
        # Autotune REAL: detecta el tono y lo corrige a una escala.
        self.autotune_real = 0.0
        self.at_scale_semitones = list(range(12))  # cromática por defecto
        self._at_buf = np.zeros(0, dtype=np.float32)
        self._at_correction = 0.0
        self._at_skip = 0
        self.vibrato = 0.0
        self.chorus = 0.0
        self.human_realism = 0.0
        self.human_warmth = 0.0
        self.human_breath = 0.0
        self.de_ess = 0.0
        self.clarity = 0.0
        self.transient = 0.0
        self.modern_space = 0.0
        self.vocal_focus = 0.0
        self.proximity = 0.0
        self.smart_level = 0.0
        self.fx_ducking = 0.0
        self._human_phase = 0.0
        self._human_noise_state = 0.0
        self._human_rng = np.random.default_rng(20260711)
        self._polish_low_state = 0.0
        self._polish_env_state = 0.0
        self._modern_room_buf = np.zeros(int(self.rate * 0.22), dtype=np.float32)
        self._modern_room_pos = 0
        self._focus_low_state = 0.0
        self._proximity_low_state = 0.0
        self._smart_gain = 1.0
        self._fx_duck_env = 0.0

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
        # Perfilado del motor: tiempo de proceso por bloque (s).
        self._proc_last = 0.0
        self._proc_ema = 0.0     # media móvil exponencial
        self._proc_max = 0.0     # peor bloque desde el último reset
        self._proc_frames = 0    # tamaño de bloque real
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

        # Cambiador de formantes (voces "reales"): desplaza la envolvente
        # espectral sin tocar el tono (STFT + OLA como la reducción de ruido).
        self.formant = 1.0
        self._fm_kernel = (np.ones(9) / 9.0).astype(np.float32)
        self._fm_in = np.zeros(0, dtype=np.float32)
        self._fm_ola = np.zeros(self._nr_frame, dtype=np.float32)
        self._fm_outq = np.zeros(0, dtype=np.float32)
        self._fm_primed = False

        # Mesa de sonidos: efectos de sonido mezclados con la voz.
        self.sfx_buffer = np.zeros(0, dtype=np.float32)
        self.sfx_volume = 0.65

        # Monitor "escucharme": segunda salida (auriculares) que reproduce
        # la misma voz procesada que va al cable virtual.
        self.monitor_enabled = False
        self.monitor_stream = None
        self.monitor_buf = np.zeros(0, dtype=np.float32)

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
        self._human_phase = 0.0
        self._human_noise_state = 0.0
        self._polish_low_state = 0.0
        self._polish_env_state = 0.0
        self._modern_room_buf[:] = 0
        self._modern_room_pos = 0
        self._nr_in = np.zeros(0, dtype=np.float32)
        self._nr_ola = np.zeros(self._nr_frame, dtype=np.float32)
        self._nr_outq = np.zeros(0, dtype=np.float32)
        self._nr_gain_prev = None
        self._nr_primed = False
        self._nr_learn_left = 0
        self._eq_tail[:] = 0
        self._fm_in = np.zeros(0, dtype=np.float32)
        self._fm_ola = np.zeros(self._nr_frame, dtype=np.float32)
        self._fm_outq = np.zeros(0, dtype=np.float32)
        self._fm_primed = False

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


    def detect_pitch_hz(self, buf):
        """Frecuencia fundamental por autocorrelación (voz monofónica).
        Devuelve 0 si no hay tono claro (silencio o ruido)."""
        n = len(buf)
        if n < 512:
            return 0.0
        if float(np.sqrt(np.mean(buf * buf))) < 0.01:
            return 0.0
        rate = self.rate
        min_hz, max_hz = 70.0, 500.0
        min_lag = int(rate / max_hz)
        max_lag = min(int(rate / min_hz), n - 1)
        x = buf - float(np.mean(buf))
        # Autocorrelación completa vía FFT (mucho más rápida que el bucle
        # de retardos): r = IFFT(|FFT(x)|^2), tomando la mitad positiva.
        m = 1
        while m < 2 * n:
            m *= 2
        spec = np.fft.rfft(x, m)
        r = np.fft.irfft(spec * np.conj(spec), m)[:n]
        energia = float(r[0]) + 1e-9
        tramo = r[min_lag:max_lag]
        if len(tramo) == 0:
            return 0.0
        mejor_lag = int(np.argmax(tramo)) + min_lag
        mejor_val = float(r[mejor_lag]) / energia
        if mejor_val < 0.35:
            return 0.0
        # Interpolación parabólica alrededor del pico para más precisión.
        if min_lag < mejor_lag < max_lag - 1:
            a, b, c = float(r[mejor_lag - 1]), float(r[mejor_lag]), float(r[mejor_lag + 1])
            denom = (a - 2 * b + c)
            if abs(denom) > 1e-9:
                mejor_lag = mejor_lag + 0.5 * (a - c) / denom
        return rate / mejor_lag if mejor_lag > 0 else 0.0

    def _snap_semitones(self, freq_hz):
        """Semitonos que hay que subir/bajar para caer en la nota más
        cercana de la escala activa (referencia A4 = 440 Hz)."""
        if freq_hz <= 0:
            return 0.0
        midi = 69.0 + 12.0 * math.log2(freq_hz / 440.0)
        octava = math.floor(midi / 12.0)
        candidatos = []
        for oct_off in (octava - 1, octava, octava + 1):
            for st in self.at_scale_semitones:
                candidatos.append(oct_off * 12 + st)
        objetivo = min(candidatos, key=lambda m: abs(m - midi))
        return float(objetivo - midi)

    def real_autotune_fx(self, x, amount):
        """Autotune real: detecta el tono del bloque, calcula la corrección
        hacia la escala y desplaza el tono suavemente (sin clics)."""
        if amount <= 0.01 or len(x) == 0:
            self._at_buf = np.zeros(0, dtype=np.float32)
            return x
        self._at_buf = np.concatenate([self._at_buf, x])[-2048:]
        # La detección es lo más caro: se hace 1 de cada 4 bloques y entre
        # medias se mantiene la última corrección (la voz no salta de nota
        # tan rápido, así que el resultado es idéntico al oído).
        if self._at_skip <= 0:
            freq = self.detect_pitch_hz(self._at_buf)
            objetivo = self._snap_semitones(freq) if freq > 0 else 0.0
            self._at_target = max(-4.0, min(4.0, objetivo)) * amount
            self._at_skip = 3
        else:
            self._at_skip -= 1
        objetivo = getattr(self, "_at_target", 0.0)
        # Suavizado temporal: evita saltos bruscos entre bloques.
        self._at_correction = 0.7 * self._at_correction + 0.3 * objetivo
        if abs(self._at_correction) < 0.05:
            return x
        return self.pitch_shift(x, self._at_correction, state="autotune_real")

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

    def formant_fx(self, x, ratio):
        """Desplaza los formantes (envolvente espectral) sin cambiar el tono."""
        frame = self._nr_frame
        hop = self._nr_hop
        if not self._fm_primed:
            self._fm_outq = np.zeros(frame, dtype=np.float32)
            self._fm_primed = True
        self._fm_in = np.concatenate([self._fm_in, x])
        n_bins = frame // 2 + 1
        bins = np.arange(n_bins, dtype=np.float64)
        while len(self._fm_in) >= frame:
            seg = self._fm_in[:frame] * self._nr_window
            spec = np.fft.rfft(seg)
            mag = np.abs(spec)
            env = mag
            for shift in range(1, 6):
                env = np.maximum(env, np.concatenate([mag[shift:], mag[-shift:]]))
                env = np.maximum(env, np.concatenate([mag[:shift], mag[:-shift]]))
            env = np.convolve(env, self._fm_kernel)[4:4 + n_bins] + 1e-9
            env_w = np.interp(bins / ratio, bins, env)
            gain = np.clip(env_w / env, 0.1, 10.0)
            out = np.fft.irfft(spec * gain, frame).astype(np.float32)
            self._fm_ola = self._fm_ola + out
            self._fm_outq = np.concatenate([self._fm_outq, self._fm_ola[:hop]])
            self._fm_ola = np.concatenate([self._fm_ola[hop:], np.zeros(hop, dtype=np.float32)])
            self._fm_in = self._fm_in[hop:]
        need = len(x)
        if len(self._fm_outq) >= need:
            y = self._fm_outq[:need]
            self._fm_outq = self._fm_outq[need:]
        else:
            y = np.concatenate([np.zeros(need - len(self._fm_outq), dtype=np.float32), self._fm_outq])
            self._fm_outq = np.zeros(0, dtype=np.float32)
        return y.astype(np.float32)

    def formant_stream(self, x, ratio):
        if abs(ratio - 1.0) > 0.02:
            return self.formant_fx(x, ratio)
        if len(self._fm_in) or len(self._fm_outq):
            self._fm_in = np.zeros(0, dtype=np.float32)
            self._fm_ola = np.zeros(self._nr_frame, dtype=np.float32)
            self._fm_outq = np.zeros(0, dtype=np.float32)
            self._fm_primed = False
        return x

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


    def human_realism_fx(self, x, amount=0.0, warmth=0.0, breath=0.0):
        """Naturalizador de baja latencia sin clonación ni modelos de identidad.

        Usa microdinámica ligada a la envolvente real de la voz, saturación
        cálida muy suave y aire condicionado por la señal. Evita LFOs fuertes
        que puedan producir un sonido artificial o mareante.
        """
        amount = float(clamp(amount, 0, 1))
        warmth = float(clamp(warmth, 0, 1))
        breath = float(clamp(breath, 0, 1))
        if len(x) == 0 or (amount <= 0 and warmth <= 0 and breath <= 0):
            return x

        y = x.astype(np.float32, copy=True)
        n = len(y)
        env = np.abs(y)
        # Envolvente suavizada por ventanas cortas: conserva dicción y evita bombeo.
        kernel = np.ones(24, dtype=np.float32) / 24.0
        smooth_env = np.convolve(env, kernel, mode="same").astype(np.float32)
        voiced = np.clip((smooth_env - 0.0015) * 38.0, 0.0, 1.0)

        if amount > 0:
            # Ruido lento interpolado, no una oscilación periódica audible.
            step = 96
            anchors = max(2, int(np.ceil(n / step)) + 1)
            random_points = self._human_rng.normal(0.0, 1.0, anchors).astype(np.float32)
            slow = np.interp(np.arange(n), np.arange(anchors) * step, random_points).astype(np.float32)
            micro_gain = 1.0 + slow * voiced * (0.0025 + 0.0065 * amount)
            # Pequeña recuperación de palabras débiles, sin comprimir en exceso.
            support = 1.0 + np.clip(0.07 - smooth_env, 0.0, 0.07) * voiced * (0.7 * amount)
            y *= micro_gain * support

        if warmth > 0:
            drive = 1.0 + 0.85 * warmth
            saturated = np.tanh(y * drive) / max(1.0, np.tanh(drive))
            y = y * (1.0 - 0.13 * warmth) + saturated * (0.13 * warmth)

        if breath > 0:
            noise = self._human_rng.normal(0.0, 1.0, n).astype(np.float32)
            airy = np.empty_like(noise)
            airy[0] = noise[0] - self._human_noise_state
            airy[1:] = noise[1:] - 0.96 * noise[:-1]
            self._human_noise_state = float(noise[-1])
            # El aire acompaña a la voz, no aparece durante silencios.
            y += airy * voiced * (0.00020 + 0.00055 * breath)

        self._human_phase = (self._human_phase + n) % self.rate
        return self.soft_limit(y)

    def voice_polish_fx(self, x, de_ess=0.0, clarity=0.0, transient=0.0):
        """Pulido vocal rápido: de-esser, claridad y ataque controlado."""
        de_ess = float(clamp(de_ess, 0, 1))
        clarity = float(clamp(clarity, 0, 1))
        transient = float(clamp(transient, 0, 1))
        if len(x) == 0 or (de_ess <= 0 and clarity <= 0 and transient <= 0):
            return x
        y = x.astype(np.float32, copy=True)
        n = len(y)

        # Separación aproximada de agudos mediante low-pass de un polo con estado.
        low = np.empty_like(y)
        state = float(self._polish_low_state)
        alpha = 0.22
        for i, sample in enumerate(y):
            state += alpha * (float(sample) - state)
            low[i] = state
        self._polish_low_state = state
        high = y - low

        if de_ess > 0:
            hf_env = np.convolve(np.abs(high), np.ones(18, dtype=np.float32) / 18.0, mode="same")
            speech_env = np.convolve(np.abs(y), np.ones(40, dtype=np.float32) / 40.0, mode="same") + 1e-5
            ratio = hf_env / speech_env
            reduction = np.clip((ratio - 0.42) * (0.70 * de_ess), 0.0, 0.62)
            high *= (1.0 - reduction).astype(np.float32)

        if clarity > 0:
            # Realce de presencia moderado y dependiente de la señal.
            y = low + high * (1.0 + 0.24 * clarity)
        else:
            y = low + high

        if transient > 0:
            env = np.abs(y)
            smooth = np.convolve(env, np.ones(52, dtype=np.float32) / 52.0, mode="same")
            attack = np.clip(env - smooth * 1.08, 0.0, 0.12)
            gain = 1.0 + attack * (2.1 * transient)
            y *= gain.astype(np.float32)

        return self.soft_limit(y)

    def vocal_focus_fx(self, x, focus=0.0, proximity=0.0):
        """Enfoque vocal y proximidad de baja latencia, sin cambiar identidad."""
        focus = float(clamp(focus, 0, 1))
        proximity = float(clamp(proximity, 0, 1))
        if len(x) == 0 or (focus <= 0 and proximity <= 0):
            return x
        y = x.astype(np.float32, copy=True)
        low = np.empty_like(y)
        state = float(self._focus_low_state)
        alpha = 0.11
        for i, sample in enumerate(y):
            state += alpha * (float(sample) - state)
            low[i] = state
        self._focus_low_state = state
        detail = y - low
        if focus > 0:
            # Presencia adaptativa: evita enfatizar silencios y siseo.
            env = np.convolve(np.abs(y), np.ones(36, dtype=np.float32) / 36.0, mode="same")
            voiced = np.clip((env - 0.001) * 32.0, 0.0, 1.0)
            y += detail * voiced * (0.16 * focus)
        if proximity > 0:
            body = np.empty_like(y)
            pstate = float(self._proximity_low_state)
            palpha = 0.035
            for i, sample in enumerate(y):
                pstate += palpha * (float(sample) - pstate)
                body[i] = pstate
            self._proximity_low_state = pstate
            body = np.tanh(body * 1.35)
            y = y * (1.0 - 0.055 * proximity) + body * (0.10 * proximity)
        return self.soft_limit(y)

    def smart_level_fx(self, x, amount=0.0):
        """Nivelador lento para voz: corrige distancia sin bombeo agresivo."""
        amount = float(clamp(amount, 0, 1))
        if len(x) == 0 or amount <= 0:
            return x
        rms = float(np.sqrt(np.mean(x * x) + 1e-10))
        if rms < 0.0012:
            desired = 1.0
        else:
            desired = float(np.clip(0.075 / rms, 0.72, 1.85))
        # Ataque más rápido que la recuperación para evitar saltos audibles.
        coeff = 0.16 if desired < self._smart_gain else 0.035
        self._smart_gain += (desired - self._smart_gain) * coeff
        gain = 1.0 + (self._smart_gain - 1.0) * (0.72 * amount)
        return self.soft_limit(x * gain)

    def modern_space_fx(self, x, amount=0.0, ducking=0.0):
        """Early reflections modernas de baja latencia, sin cola embarrada."""
        amount = float(clamp(amount, 0, 1))
        ducking = float(clamp(ducking, 0, 1))
        if amount <= 0.001 or len(x) == 0:
            return x
        n = len(x)
        size = len(self._modern_room_buf)
        idx_w = (self._modern_room_pos + np.arange(n)) % size
        taps = [(0.013, 0.34), (0.027, 0.23), (0.049, 0.15), (0.083, 0.09)]
        wet = np.zeros(n, dtype=np.float32)
        for seconds, gain in taps:
            delay = int(self.rate * seconds)
            idx_r = (idx_w - delay) % size
            wet += self._modern_room_buf[idx_r] * gain
        # Amortiguación para evitar un sonido metálico.
        wet = np.convolve(wet, np.array([0.18, 0.32, 0.32, 0.18], dtype=np.float32), mode="same")
        self._modern_room_buf[idx_w] = x + wet * (0.16 * amount)
        self._modern_room_pos = int((self._modern_room_pos + n) % size)
        # Ducking inteligente: el espacio baja mientras se habla y vuelve en pausas.
        speech = float(np.sqrt(np.mean(x * x) + 1e-10))
        target = float(np.clip(speech * 18.0, 0.0, 1.0))
        coeff = 0.22 if target > self._fx_duck_env else 0.045
        self._fx_duck_env += (target - self._fx_duck_env) * coeff
        wet_gain = 0.55 * amount * (1.0 - 0.78 * ducking * self._fx_duck_env)
        return self.soft_limit(x + wet * wet_gain)

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
            autotune_real = self.autotune_real
            vibrato = self.vibrato
            chorus = self.chorus
            human_realism = self.human_realism
            human_warmth = self.human_warmth
            human_breath = self.human_breath
            de_ess = self.de_ess
            clarity = self.clarity
            transient = self.transient
            modern_space = self.modern_space
            vocal_focus = self.vocal_focus
            proximity = self.proximity
            smart_level = self.smart_level
            fx_ducking = self.fx_ducking
            eq_low = self.eq_low
            eq_mid = self.eq_mid
            eq_high = self.eq_high
            formant = self.formant
            recording = self.recording

        # Conversión de voz por IA local (RVC): si hay un modelo cargado y
        # activo, produce la voz; si no entrega bloque, cae a la cadena DSP.
        conv = None
        clean = None
        rvc = self.rvc_backend
        if (not mute) and self.rvc_enabled and rvc is not None and rvc.ready:
            rvc_failed = False
            try:
                clean = self.noise_reduce_stream(x)
                conv = rvc.process_block(clean, self.rate)
            except Exception:
                conv = None
                rvc_failed = True
            if conv is None:
                rvc_failed = True
            if conv is not None and len(conv) != len(x):
                conv = None
                rvc_failed = True
            if conv is not None:
                self.rvc_failures = 0
                self.rvc_disabled_reason = ""
            elif rvc_failed:
                self.rvc_failures += 1
                if self.rvc_failures >= self.rvc_failure_limit:
                    self.rvc_enabled = False
                    self.rvc_disabled_reason = "Voz IA desactivada temporalmente: el modelo fallo varias veces seguidas."
                    try:
                        rvc.enabled = False
                    except Exception:
                        pass

        if mute:
            y = np.zeros_like(x)
        elif conv is not None:
            # La voz IA ya define el timbre; solo volumen y limitador.
            y = self.soft_limit(conv * volume)
        elif not effects_enabled:
            # Modo voz limpia: deja pasar el micro sin cambiar la voz, pero mantiene soundboard.
            y = clean if clean is not None else self.noise_reduce_stream(x)
            y = self.soft_limit(y * volume)
        else:
            y = clean if clean is not None else self.noise_reduce_stream(x)
            y = self.gate(y, noise_gate)
            y = self.pitch_shift(y, pitch)
            y = self.formant_stream(y, formant)
            y = self.real_autotune_fx(y, autotune_real)
            y = self.autotune_fx(y, autotune, autotune_shift)
            y = self.vibrato_fx(y, vibrato)
            y = self.chorus_fx(y, chorus)
            y = self.human_realism_fx(y, human_realism, human_warmth, human_breath)
            y = self.voice_polish_fx(y, de_ess, clarity, transient)
            y = self.vocal_focus_fx(y, vocal_focus, proximity)
            y = self.smart_level_fx(y, smart_level)
            y = self.add_bass(y, bass)
            y = self.eq3_fx(y, eq_low, eq_mid, eq_high)
            y = self.robot_fx(y, robot)
            y = self.echo_fx(y, echo)
            y = self.radio_fx(y, radio)
            y = self.megaphone_fx(y, megaphone)
            y = self.modern_space_fx(y, modern_space, fx_ducking)
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
        if self.monitor_enabled:
            with self.lock:
                self.monitor_buf = np.concatenate([self.monitor_buf, y])
                # si el monitor se retrasa, recorta para no acumular eco.
                if len(self.monitor_buf) > self.rate:
                    self.monitor_buf = self.monitor_buf[-self.rate // 5:]
        return y.reshape(-1, 1).astype(np.float32)

    def callback(self, indata, outdata, frames, time_info, status):
        self.callback_count += 1
        if status:
            self.xrun_count += 1
        t0 = time.perf_counter()
        try:
            y = self.process(indata)
            if outdata.shape[1] > 1:
                outdata[:] = np.repeat(y, outdata.shape[1], axis=1)
            else:
                outdata[:] = y
        except Exception as e:
            print("Error de audio:", e)
            outdata[:] = np.zeros_like(outdata)
        # Perfilado: tiempo de proceso por bloque y carga de CPU del DSP
        # (tiempo de proceso / duración del bloque). >1.0 = no llega a tiempo.
        dt = time.perf_counter() - t0
        self._proc_last = dt
        self._proc_ema = dt if self._proc_ema == 0.0 else (0.92 * self._proc_ema + 0.08 * dt)
        if dt > self._proc_max:
            self._proc_max = dt
        self._proc_frames = int(frames) or self._proc_frames

    def perf_stats(self):
        """Estadísticas de rendimiento del motor para la interfaz.
        load = tiempo de proceso / duración del bloque (0..1 sano; >1 = corta)."""
        frames = self._proc_frames or 0
        block_s = (frames / self.rate) if (frames and self.rate) else 0.0
        avg_ms = self._proc_ema * 1000.0
        max_ms = self._proc_max * 1000.0
        block_ms = block_s * 1000.0
        load = (self._proc_ema / block_s) if block_s > 0 else 0.0
        return {
            "frames": frames,
            "rate": self.rate,
            "block_ms": block_ms,
            "avg_ms": avg_ms,
            "max_ms": max_ms,
            "load": load,
            "xruns": self.xrun_count,
        }

    def reset_perf_stats(self):
        self._proc_ema = 0.0
        self._proc_max = 0.0

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
        self.stop_monitor()
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        self.stream = None
        self.running = False

    def _monitor_callback(self, outdata, frames, time_info, status):
        with self.lock:
            n = min(frames, len(self.monitor_buf))
            chunk = self.monitor_buf[:n]
            self.monitor_buf = self.monitor_buf[n:]
        salida = np.zeros(frames, dtype=np.float32)
        if n:
            salida[:n] = chunk
        if outdata.shape[1] > 1:
            outdata[:] = np.repeat(salida.reshape(-1, 1), outdata.shape[1], axis=1)
        else:
            outdata[:] = salida.reshape(-1, 1)

    def start_monitor(self, device_id):
        """Abre la segunda salida para escucharte (auriculares)."""
        if self.monitor_stream is not None:
            self.monitor_enabled = True
            return True
        ultimo = None
        for ch in (2, 1):
            try:
                stream = sd.OutputStream(
                    samplerate=self.rate,
                    channels=ch,
                    dtype="float32",
                    device=device_id,
                    callback=self._monitor_callback,
                )
                stream.start()
            except Exception as e:
                ultimo = e
                continue
            with self.lock:
                self.monitor_buf = np.zeros(0, dtype=np.float32)
            self.monitor_stream = stream
            self.monitor_enabled = True
            return True
        print("No se pudo abrir el monitor:", ultimo)
        self.monitor_enabled = False
        return False

    def stop_monitor(self):
        self.monitor_enabled = False
        stream = self.monitor_stream
        self.monitor_stream = None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        with self.lock:
            self.monitor_buf = np.zeros(0, dtype=np.float32)

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
