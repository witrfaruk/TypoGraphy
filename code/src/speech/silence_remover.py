"""
Audio Silence Remover & Jump-Cutter Engine.
Automatically cuts dead-air pauses (> 0.3s) to maintain 100% viewer retention,
and realigns Whisper word-level timestamps with mathematical precision.
"""
import io
import wave
import subprocess
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from src.core.types import WordTiming
from src.core.config_loader import get_project_paths


class SilenceTrimmer:
    def __init__(
        self,
        max_pause_threshold: float = 0.42,  # Smoothly trim unnatural dead air (> 0.42s) while preserving human cadence
        target_gap: float = 0.18,           # Retain natural 180ms breath gap
        lead_pad: float = 0.10,             # 100ms lead padding before next word attack
        trail_pad: float = 0.12             # 120ms trailing padding after word tail decay
    ):
        self.max_pause_threshold = max_pause_threshold
        self.target_gap = target_gap
        self.lead_pad = lead_pad
        self.trail_pad = trail_pad
        self.paths = get_project_paths()

    def process_and_trim(
        self,
        audio_path: Path,
        words: List[WordTiming],
        original_duration: float
    ) -> Tuple[Path, List[WordTiming], float]:
        """
        Trims dead air from the audio file and re-maps all word timestamps.
        Returns:
            (trimmed_audio_path, realigned_words, new_duration)
        """
        if not words:
            return audio_path, words, original_duration

        # 1. Compute Keep Intervals in Original Timeline
        keep_intervals: List[Tuple[float, float]] = []

        # Leading speech start
        first_word_start = words[0].start
        current_chunk_start = max(0.0, first_word_start - self.lead_pad)

        for i in range(len(words) - 1):
            curr_w = words[i]
            next_w = words[i + 1]

            gap = next_w.start - curr_w.end

            if gap > self.max_pause_threshold:
                # Close current chunk with generous trailing vocal decay
                chunk_end = min(original_duration, curr_w.end + self.trail_pad)
                keep_intervals.append((current_chunk_start, chunk_end))

                # Start next chunk with clean attack
                current_chunk_start = max(0.0, next_w.start - self.lead_pad)

        # Trailing pad after last word
        last_word_end = words[-1].end
        chunk_end = min(original_duration, last_word_end + 0.25)
        keep_intervals.append((current_chunk_start, chunk_end))

        # Check if any cuts actually occurred
        total_kept_time = sum(end - start for start, end in keep_intervals)
        silence_saved = original_duration - total_kept_time

        if silence_saved <= 0.20:
            print(f"[SilenceTrimmer] Natural speech cadence detected (silence {silence_saved:.2f}s). Keeping natural flow.")
            return audio_path, words, original_duration

        print(f"[SilenceTrimmer] Dead air detected! Smoothly trimming {silence_saved:.2f}s across {len(keep_intervals)-1} pause(s)...")

        # 2. Re-map Word Timestamps mathematically to the new continuous timeline
        realigned_words: List[WordTiming] = []
        for w in words:
            new_start = self._map_timestamp_to_new_timeline(w.start, keep_intervals)
            new_end = self._map_timestamp_to_new_timeline(w.end, keep_intervals)
            # Ensure valid duration
            if new_end <= new_start:
                new_end = new_start + max(0.05, w.end - w.start)

            realigned_words.append(
                WordTiming(
                    word=w.word,
                    start=round(new_start, 3),
                    end=round(new_end, 3),
                    probability=w.probability,
                    is_emphasis=w.is_emphasis,
                    highlight_color=w.highlight_color
                )
            )

        # 3. Splice Audio using FFmpeg / PCM sample slicing with smooth cosine cross-fades
        trimmed_audio_path = self.paths["cache"] / f"{audio_path.stem}_trimmed.wav"
        self._splice_audio_pcm(audio_path, keep_intervals, trimmed_audio_path)

        new_duration = round(total_kept_time, 3)
        print(f"[SilenceTrimmer] Auto-cut complete: Audio tightened from {original_duration:.2f}s -> {new_duration:.2f}s.")
        return trimmed_audio_path, realigned_words, new_duration

    def _map_timestamp_to_new_timeline(self, orig_t: float, intervals: List[Tuple[float, float]]) -> float:
        """Translates an original timestamp into the spliced continuous timeline."""
        cumulative_new_time = 0.0

        for start, end in intervals:
            if orig_t < start:
                # Time fell in a cut-out gap, snap to chunk start
                return cumulative_new_time
            elif start <= orig_t <= end:
                return cumulative_new_time + (orig_t - start)
            else:
                cumulative_new_time += (end - start)

        return cumulative_new_time

    def _splice_audio_pcm(self, input_audio: Path, intervals: List[Tuple[float, float]], output_wav: Path):
        """Extracts and concatenates audio chunks with smooth cosine crossfade to eliminate any audio cuts or clicks."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_audio.resolve()),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            "-f", "wav",
            "-"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        wav_bytes, err = proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg audio decode error: {err.decode('utf-8', errors='replace')}")

        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            n_channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw_frames = wf.readframes(n_frames)

        # Convert to numpy array of samples
        dtype = np.int16
        audio_data = np.frombuffer(raw_frames, dtype=dtype)
        if n_channels > 1:
            audio_data = audio_data.reshape(-1, n_channels)
        else:
            audio_data = audio_data.reshape(-1, 1)

        total_samples = len(audio_data)
        spliced_chunks = []
        fade_samples = int(0.025 * sample_rate)  # 25ms smooth equal-power fade

        for start_sec, end_sec in intervals:
            start_idx = max(0, int(start_sec * sample_rate))
            end_idx = min(total_samples, int(end_sec * sample_rate))
            if end_idx <= start_idx:
                continue

            chunk = audio_data[start_idx:end_idx].copy().astype(np.float32)

            # Apply smooth S-curve (cosine) fade-in and fade-out
            if len(chunk) > fade_samples * 2:
                # Smooth cosine curve: 0.5 * (1 - cos(x))
                fade_in = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, fade_samples)))[:, None]
                fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, fade_samples)))[:, None]
                chunk[:fade_samples] *= fade_in
                chunk[-fade_samples:] *= fade_out

            spliced_chunks.append(chunk.astype(np.int16))

        if not spliced_chunks:
            spliced_audio = audio_data
        else:
            spliced_audio = np.concatenate(spliced_chunks, axis=0)

        # Write spliced audio to output WAV
        with wave.open(str(output_wav.resolve()), "wb") as out_wf:
            out_wf.setnchannels(n_channels)
            out_wf.setsampwidth(sampwidth)
            out_wf.setframerate(sample_rate)
            out_wf.writeframes(spliced_audio.tobytes())

    def apply_speed(
        self,
        audio_path: Path,
        words: List[WordTiming],
        duration: float,
        speed: float = 1.40
    ) -> Tuple[Path, List[WordTiming], float]:
        """
        Speeds up audio by factor `speed` (e.g. 1.4x) using FFmpeg atempo (maintains natural voice pitch),
        and scales all word timestamps mathematically.
        """
        if abs(speed - 1.0) < 0.01 or not words:
            return audio_path, words, duration

        output_wav = self.paths["cache"] / f"{audio_path.stem}_speed_{speed:.2f}.wav"
        output_wav.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path.resolve()),
            "-filter:a", f"atempo={speed}",
            "-vn",
            str(output_wav.resolve())
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            print(f"[Warning] Failed to apply atempo speed filter: {res.stderr.decode('utf-8', errors='replace')[:200]}")
            return audio_path, words, duration

        scaled_words: List[WordTiming] = []
        for w in words:
            scaled_words.append(
                WordTiming(
                    word=w.word,
                    start=round(w.start / speed, 3),
                    end=round(w.end / speed, 3),
                    probability=w.probability,
                    is_emphasis=w.is_emphasis,
                    highlight_color=w.highlight_color
                )
            )

        new_duration = round(duration / speed, 3)
        print(f"[AudioProcessor] Video pacing accelerated to {speed}x! Total duration: {duration:.2f}s -> {new_duration:.2f}s.")
        return output_wav, scaled_words, new_duration
