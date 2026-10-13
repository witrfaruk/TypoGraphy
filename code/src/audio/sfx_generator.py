"""
Studio SFX Audio Generator (100% Offline, Pure Python Acoustics).
Synthesizes a full suite of popular viral reel sound effects at 44.1kHz stereo WAV.
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
from pathlib import Path
from typing import Dict

SFX_DIR = Path("assets/sfx")
SAMPLE_RATE = 44100


def _apply_envelope(audio: np.ndarray, attack_sec: float, decay_sec: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = len(audio)
    attack_samples = min(n, int(attack_sec * sr))
    decay_samples = min(n - attack_samples, int(decay_sec * sr))
    sustain_samples = max(0, n - attack_samples - decay_samples)

    env = np.ones(n, dtype=np.float32)
    if attack_samples > 0:
        env[:attack_samples] = np.linspace(0.0, 1.0, attack_samples)
    if decay_samples > 0:
        env[attack_samples + sustain_samples:] = np.linspace(1.0, 0.0, decay_samples)
    return audio * env


def _butter_bandpass_filter(data: np.ndarray, lowcut: float, highcut: float, fs: int = SAMPLE_RATE, order: int = 3) -> np.ndarray:
    nyq = 0.5 * fs
    low = max(0.01, min(0.99, lowcut / nyq))
    high = max(low + 0.01, min(0.99, highcut / nyq))
    b, a = butter(order, [low, high], btype='band')
    return lfilter(b, a, data)


def _to_stereo_int16(mono_audio: np.ndarray) -> np.ndarray:
    # Normalize peak to 0.90 to avoid clipping
    peak = np.max(np.abs(mono_audio))
    if peak > 0:
        norm = mono_audio / peak * 0.90
    else:
        norm = mono_audio
    int16_mono = (norm * 32767).astype(np.int16)
    # Duplicate to stereo (2 channels)
    return np.column_stack((int16_mono, int16_mono))


class SFXGenerator:
    @staticmethod
    def generate_all_sfx(output_dir: Path = SFX_DIR) -> Dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        generators = {
            "whoosh_fast": SFXGenerator.create_whoosh_fast,
            "whoosh_deep": SFXGenerator.create_whoosh_deep,
            "pop_bubble": SFXGenerator.create_pop_bubble,
            "pop_click": SFXGenerator.create_pop_click,
            "cash_register": SFXGenerator.create_cash_register,
            "bell_ding": SFXGenerator.create_bell_ding,
            "bass_thud": SFXGenerator.create_bass_thud,
            "warning_alert": SFXGenerator.create_warning_alert,
            "laser_zap": SFXGenerator.create_laser_zap,
            "idea_ping": SFXGenerator.create_idea_ping,
            "growth_riser": SFXGenerator.create_growth_riser,
            "glitch_hit": SFXGenerator.create_glitch_hit,
        }

        generated_paths = {}
        for name, gen_func in generators.items():
            file_path = output_dir / f"{name}.wav"
            if not file_path.exists() or file_path.stat().st_size < 100:
                audio_data = gen_func()
                wavfile.write(str(file_path), SAMPLE_RATE, audio_data)
            generated_paths[name] = file_path

        return generated_paths

    @staticmethod
    def create_whoosh_fast(duration: float = 0.28) -> np.ndarray:
        """Fast airy transition swoosh."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        noise = np.random.normal(0, 1, n_samples)
        
        # Dynamic bandpass sweep from 300Hz to 2800Hz and back
        filtered = _butter_bandpass_filter(noise, 350, 3200)
        
        # Parabolic bell curve volume envelope
        env = np.sin(np.pi * (t / duration)) ** 2.2
        return _to_stereo_int16(filtered * env)

    @staticmethod
    def create_whoosh_deep(duration: float = 0.42) -> np.ndarray:
        """Heavy cinematic sub-whoosh."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        noise = np.random.normal(0, 1, n_samples)
        
        # Sub-bass sine sweep (80Hz to 180Hz to 60Hz)
        pitch = 80 + 100 * np.sin(np.pi * (t / duration))
        sub_bass = np.sin(2 * np.pi * pitch * t) * 0.6
        
        noise_filt = _butter_bandpass_filter(noise, 150, 1800) * 0.4
        env = np.sin(np.pi * (t / duration)) ** 2.0
        return _to_stereo_int16((sub_bass + noise_filt) * env)

    @staticmethod
    def create_pop_bubble(duration: float = 0.12) -> np.ndarray:
        """Crisp acoustic bubble pop for stickers and pill boxes."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        # Fast exponential pitch drop 520Hz -> 130Hz
        freq = 130 + (520 - 130) * np.exp(-35 * t)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        sine = np.sin(phase)
        
        env = np.exp(-28 * t)
        return _to_stereo_int16(sine * env)

    @staticmethod
    def create_pop_click(duration: float = 0.08) -> np.ndarray:
        """Snappy modern UI click pop."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        freq = 1800 * np.exp(-60 * t)
        sine = np.sin(2 * np.pi * freq * t)
        noise = np.random.normal(0, 0.4, n_samples) * np.exp(-80 * t)
        
        return _to_stereo_int16((sine + noise) * np.exp(-40 * t))

    @staticmethod
    def create_cash_register(duration: float = 0.48) -> np.ndarray:
        """Metallic coins + Ka-ching chime."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        # Dual harmonic bell pings (2200Hz + 3300Hz + 4400Hz)
        chime1 = np.sin(2 * np.pi * 2200 * t) * np.exp(-12 * t)
        chime2 = np.sin(2 * np.pi * 3300 * t) * np.exp(-15 * t) * 0.7
        chime3 = np.sin(2 * np.pi * 4400 * t) * np.exp(-18 * t) * 0.4
        
        # Initial mechanical metallic click
        click = np.random.normal(0, 0.6, n_samples) * np.exp(-100 * t)
        
        # Secondary delayed coin jingle (at 90ms)
        delay_s = int(0.09 * SAMPLE_RATE)
        jingle = np.zeros(n_samples)
        if delay_s < n_samples:
            t_rem = t[:n_samples - delay_s]
            jingle[delay_s:] = np.sin(2 * np.pi * 2800 * t_rem) * np.exp(-14 * t_rem) * 0.8
            
        combined = chime1 + chime2 + chime3 + click + jingle
        return _to_stereo_int16(combined)

    @staticmethod
    def create_bell_ding(duration: float = 0.55) -> np.ndarray:
        """Pure resonant harmonic chime."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        h1 = np.sin(2 * np.pi * 1250 * t) * np.exp(-8 * t)
        h2 = np.sin(2 * np.pi * 2500 * t) * np.exp(-11 * t) * 0.5
        h3 = np.sin(2 * np.pi * 3750 * t) * np.exp(-14 * t) * 0.25
        return _to_stereo_int16(h1 + h2 + h3)

    @staticmethod
    def create_bass_thud(duration: float = 0.25) -> np.ndarray:
        """Deep 60Hz punchy sub-bass impact hit."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        # Pitch drop from 110Hz to 45Hz
        freq = 45 + (110 - 45) * np.exp(-22 * t)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        sub = np.sin(phase)
        
        # Soft saturation distortion
        sub = np.tanh(sub * 2.2)
        env = np.exp(-14 * t)
        return _to_stereo_int16(sub * env)

    @staticmethod
    def create_warning_alert(duration: float = 0.28) -> np.ndarray:
        """Dual-pulse sharp warning alert beep."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        tone = np.sin(2 * np.pi * 920 * t) + 0.5 * np.sin(2 * np.pi * 1380 * t)
        
        # Dual pulse gate
        pulse_len = duration / 2.0
        p1 = (t < pulse_len * 0.8) * np.exp(-15 * (t % pulse_len))
        p2 = (t >= pulse_len) * (t < pulse_len * 1.8) * np.exp(-15 * ((t - pulse_len) % pulse_len))
        
        return _to_stereo_int16(tone * (p1 + p2))

    @staticmethod
    def create_laser_zap(duration: float = 0.22) -> np.ndarray:
        """Laser energy zap sound."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        freq = 3400 * np.exp(-28 * t)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        zap = np.sin(phase) * np.exp(-16 * t)
        return _to_stereo_int16(zap)

    @staticmethod
    def create_idea_ping(duration: float = 0.45) -> np.ndarray:
        """Sparkling lightbulb idea ping."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        p1 = np.sin(2 * np.pi * 1760 * t) * np.exp(-10 * t)
        p2 = np.sin(2 * np.pi * 3520 * t) * np.exp(-13 * t) * 0.5
        p3 = np.sin(2 * np.pi * 5280 * t) * np.exp(-16 * t) * 0.25
        return _to_stereo_int16(p1 + p2 + p3)

    @staticmethod
    def create_growth_riser(duration: float = 0.40) -> np.ndarray:
        """Ascending pitch scale sweep."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        freq = 160 + (850 - 160) * (t / duration) ** 1.8
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        env = (t / duration) ** 1.5 * np.exp(-4 * (1.0 - t / duration))
        return _to_stereo_int16(np.sin(phase) * env)

    @staticmethod
    def create_glitch_hit(duration: float = 0.16) -> np.ndarray:
        """Modern glitch transition hit."""
        n_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, n_samples)
        
        steps = np.floor(t * 40)
        freq = 400 + (steps % 5) * 350
        sine = np.sin(2 * np.pi * freq * t)
        noise = np.random.normal(0, 0.4, n_samples) * np.exp(-25 * t)
        return _to_stereo_int16((sine + noise) * np.exp(-18 * t))
