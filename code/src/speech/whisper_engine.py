"""
Whisper Speech-to-Text & Word-Level Timing Engine.
Uses faster-whisper with word-level alignment, confidence scoring, and VAD filtering.
"""
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from faster_whisper import WhisperModel
from src.core.types import WordTiming
from src.core.config_loader import load_system_config


class SpeechTranscriber:
    def __init__(self, model_size: Optional[str] = None, device: Optional[str] = None):
        cfg = load_system_config().get("whisper", {})
        self.model_size = model_size or cfg.get("model_size", "medium")
        self.device = device or cfg.get("device", "auto")
        self.vad_filter = cfg.get("vad_filter", True)

        # Device & compute type resolution
        if self.device == "auto":
            # Test if GPU CUDA is available for ctranslate2
            try:
                import ctranslate2
                if "cuda" in ctranslate2.get_supported_compute_types("cuda"):
                    self.device = "cuda"
                    self.compute_type = "float16"
                else:
                    self.device = "cpu"
                    self.compute_type = "int8"
            except Exception:
                self.device = "cpu"
                self.compute_type = "int8"
        else:
            self.compute_type = "float16" if self.device == "cuda" else "int8"

        print(f"[WhisperEngine] Initializing Whisper model '{self.model_size}' on {self.device.upper()} ({self.compute_type})...")
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )
        print("[WhisperEngine] Model loaded successfully.")

    def transcribe_audio(self, audio_path: Path) -> Tuple[str, List[WordTiming], float]:
        """
        Transcribes an audio file with exact word-level start/end timestamps.
        Returns:
            (full_transcript, list_of_word_timings, total_duration_seconds)
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        print(f"[WhisperEngine] Transcribing: {audio_path.name}")
        segments, info = self.model.transcribe(
            str(audio_path),
            word_timestamps=True,
            vad_filter=self.vad_filter,
            vad_parameters=dict(min_silence_duration_ms=400),
            beam_size=5
        )

        all_words: List[WordTiming] = []
        transcript_parts: List[str] = []

        for segment in segments:
            transcript_parts.append(segment.text.strip())
            if segment.words:
                for w in segment.words:
                    clean_word = w.word.strip()
                    if clean_word:
                        all_words.append(
                            WordTiming(
                                word=clean_word,
                                start=round(w.start, 3),
                                end=round(w.end, 3),
                                probability=round(w.probability, 3),
                                is_emphasis=False,
                                highlight_color=None
                            )
                        )

        full_transcript = " ".join(transcript_parts).strip()
        duration = round(info.duration, 2)
        print(f"[WhisperEngine] Completed: {len(all_words)} words transcribed across {duration}s.")
        return full_transcript, all_words, duration


# Singleton helper
_transcriber_instance: Optional[SpeechTranscriber] = None

def get_transcriber() -> SpeechTranscriber:
    global _transcriber_instance
    if _transcriber_instance is None:
        _transcriber_instance = SpeechTranscriber()
    return _transcriber_instance
