"""
Multi-Track Studio Audio Mixer.
Composes Voiceover + Synchronized SFX Hits + Ambient BGM Bed into a single pristine audio master.
"""
import numpy as np
from scipy.io import wavfile
from pathlib import Path
from typing import List, Optional, Tuple
from src.audio.sfx_manager import SFXEvent, SFX_DIR
import subprocess

SAMPLE_RATE = 44100


class AudioMixer:
    def __init__(self):
        self.sfx_cache = {}

    def _load_wav_as_float32(self, file_path: Path) -> Tuple[np.ndarray, int]:
        """Loads WAV and normalizes to float32 stereo (-1.0 to 1.0)."""
        sr, data = wavfile.read(str(file_path))
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        elif data.dtype == np.uint8:
            data = (data.astype(np.float32) - 128) / 128.0

        if data.ndim == 1:
            data = np.column_stack((data, data))
        return data, sr

    def create_composite_sfx_track(
        self,
        sfx_events: List[SFXEvent],
        total_duration: float,
        output_sfx_path: Path
    ) -> Path:
        """
        Creates a single continuous WAV file containing all SFX hits at exact timestamps.
        """
        total_samples = int(total_duration * SAMPLE_RATE) + (SAMPLE_RATE * 2)
        sfx_master = np.zeros((total_samples, 2), dtype=np.float32)

        for event in sfx_events:
            sfx_file = SFX_DIR / f"{event.name}.wav"
            if not sfx_file.exists():
                continue

            try:
                data, sr = self._load_wav_as_float32(sfx_file)
                # Resample if needed
                if sr != SAMPLE_RATE:
                    continue

                start_sample = int(event.timestamp * SAMPLE_RATE)
                end_sample = min(total_samples, start_sample + len(data))
                chunk_len = end_sample - start_sample

                if chunk_len > 0 and start_sample < total_samples:
                    # Apply event volume multiplier
                    scaled_data = data[:chunk_len] * event.volume
                    sfx_master[start_sample:end_sample] += scaled_data
            except Exception as e:
                print(f"[AudioMixer] Warning: Failed to insert SFX '{event.name}': {e}")

        # Soft limiting to ensure loud, crisp punch without global attenuation
        sfx_master = np.clip(sfx_master, -0.98, 0.98)
        int16_sfx = (sfx_master * 32767).astype(np.int16)
        output_sfx_path.parent.mkdir(parents=True, exist_ok=True)
        wavfile.write(str(output_sfx_path), SAMPLE_RATE, int16_sfx)
        return output_sfx_path
