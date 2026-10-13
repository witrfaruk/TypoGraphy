"""
Master Pure Kinetic Typography Video Pipeline.
One-touch execution: Voice Audio -> Whisper -> Spatial Multi-Size Typography Engine -> FFmpeg -> Final Video.
"""
import sys
import io
import time
import argparse
from pathlib import Path
from typing import Optional

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure code directory is in sys.path
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from src.core.types import StyleProfile, TimelinePlan
from src.core.config_loader import (
    load_style_profile, load_system_config, get_project_paths, ensure_directories_exist
)
from src.speech.whisper_engine import get_transcriber
from src.speech.silence_remover import SilenceTrimmer
from src.reasoning.scene_planner import ScenePlanner
from src.typography.motion_renderer import MotionTypographyRenderer
from src.core.metadata_remover import MetadataRemover


class PureTypographyPipeline:
    def __init__(self, style_profile: Optional[StyleProfile] = None, dark_mode: bool = False):
        ensure_directories_exist()
        self.paths = get_project_paths()
        self.style = style_profile or load_style_profile()
        self.transcriber = get_transcriber()
        self.silence_trimmer = SilenceTrimmer()
        self.planner = ScenePlanner()
        self.renderer = MotionTypographyRenderer(self.style, dark_mode=dark_mode)
        self.metadata_remover = MetadataRemover()

    def generate(
        self,
        audio_path: Path,
        output_path: Optional[Path] = None,
        dark_mode: bool = False,
        auto_cut: bool = True,
        speed: float = 1.30,
        bgm_path: Optional[Path] = None,
        delete_audio: bool = True
    ) -> Path:
        """
        Executes pure kinetic typography video generation for a single voice audio file
        with automatic silence dead-air trimming, 1.3x tempo speedup, and background music mixing.
        """
        audio_path = Path(audio_path).resolve()
        if not audio_path.exists():
            raise FileNotFoundError(f"Input audio file not found: {audio_path}")

        print("\n" + "=" * 65)
        print(f"  GENERATING PURE KINETIC TYPOGRAPHY REEL FOR: {audio_path.name}")
        print("=" * 65)

        start_time = time.time()

        # 1. Whisper Transcription & Exact Word Timestamps
        print("\n[Step 1/6] Transcribing audio with word-level millisecond timestamps...")
        transcript, words, duration = self.transcriber.transcribe_audio(audio_path)
        safe_transcript = transcript[:90].encode("ascii", "replace").decode("ascii")
        print(f"  Transcript: \"{safe_transcript}...\" ({len(words)} words, {duration}s)")

        # 2. Auto-Cut Silence & Dead Air (Smooth Cadence Preserved)
        if auto_cut and len(words) > 1:
            print("\n[Step 2/6] Smoothly trimming dead-air pauses for maximum viewer retention...")
            render_audio_path, render_words, render_duration = self.silence_trimmer.process_and_trim(
                audio_path=audio_path,
                words=words,
                original_duration=duration
            )
        else:
            render_audio_path, render_words, render_duration = audio_path, words, duration

        # 3. Pacing Acceleration (1.4x Speed with Natural Voice Pitch)
        if speed and abs(speed - 1.0) >= 0.02:
            print(f"\n[Step 3/6] Accelerating video pace to {speed}x (pitch-preserved)...")
            render_audio_path, render_words, render_duration = self.silence_trimmer.apply_speed(
                audio_path=render_audio_path,
                words=render_words,
                duration=render_duration,
                speed=speed
            )

        # 4. Scene & Emphasis Beat Planning
        print("\n[Step 4/6] Structuring semantic beats and emphasis words...")
        timeline = self.planner.plan_timeline(
            audio_file_name=render_audio_path.name,
            full_transcript=transcript,
            words=render_words,
            total_duration=render_duration,
            style_profile=self.style
        )
        print(f"  Planned {len(timeline.scenes)} typography scenes with exact word alignment.")

        # 5. Pure Kinetic Frame Motion Rendering via FFmpeg NVENC with BGM
        print("\n[Step 5/6] Rendering pure kinetic typography frames with NVENC & BGM...")
        target_output = output_path or (self.paths["final_video"] / f"{audio_path.stem}_kinetic_reel.mp4")
        
        self.renderer.dark_mode = dark_mode
        try:
            final_video = self.renderer.render_timeline_to_video(
                timeline=timeline,
                audio_path=render_audio_path,
                output_video_path=target_output,
                bgm_path=bgm_path
            )

            # 6. Automatic Metadata Stripping & Privacy Sanitization
            print("\n[Step 6/6] Stripping 100% metadata & sanitizing video for Reels/Shorts...")
            final_video = self.metadata_remover.strip_metadata(final_video)

            # 7. Auto-delete source audio after success to eliminate chaos
            if delete_audio and audio_path.exists() and audio_path.name != ".gitkeep" and final_video.exists():
                try:
                    time.sleep(0.2)
                    audio_path.unlink(missing_ok=True)
                    print(f"\n  [AutoClean] Deleted source audio: '{audio_path.name}' (Audio/ folder stays clean!)")
                except Exception as e:
                    print(f"  [AutoClean] Notice deleting source audio: {e}")
        finally:
            from src.core.cache_cleaner import CacheCleaner
            CacheCleaner.cleanup_all_temp_cache()

        elapsed = time.time() - start_time
        print("\n" + "=" * 65)
        print(f"  SUCCESS: Pure Kinetic Video rendered in {elapsed:.1f}s")
        print(f"  Output file: {final_video.resolve()}")
        print("=" * 65)
        return final_video

    def watch_folder(self, folder_path: Optional[Path] = None, interval_seconds: int = 3, dark_mode: bool = False, speed: float = 1.30):
        """Watches Audio/ and input/voice/ folders for newly dropped audio files and auto-renders."""
        watch_dirs = [folder_path] if folder_path else [self.paths["audio"], self.paths["input_voice"]]
        
        print("\n" + "=" * 65)
        print("  FOLDER WATCHER ACTIVE")
        for wd in watch_dirs:
            print(f"  Watching: {wd.resolve()}")
        print("  Drop any .wav, .mp3, or .m4a into your Audio/ folder.")
        print("  Videos will automatically render into 'Final Video/'.")
        print("  (Press Ctrl+C to stop)")
        print("=" * 65 + "\n")

        processed = set()
        # Pre-populate already rendered files
        for f in self.paths["final_video"].glob("*.mp4"):
            base_stem = f.stem.replace("_kinetic_reel", "")
            processed.add(base_stem)

        while True:
            for wd in watch_dirs:
                if not wd.exists():
                    continue
                for ext in ["*.wav", "*.mp3", "*.m4a", "*.aac", "*.ogg"]:
                    for audio_file in wd.glob(ext):
                        if audio_file.stem not in processed:
                            processed.add(audio_file.stem)
                            try:
                                self.generate(audio_file, dark_mode=dark_mode, speed=speed)
                            except Exception as e:
                                print(f"[FolderWatcher] Error processing {audio_file.name}: {e}")
            time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description="Automated Pure Kinetic Typography Video Generator")
    parser.add_argument("--audio", "-a", type=str, help="Path to input voice audio file (.wav, .mp3, etc.)")
    parser.add_argument("--output", "-o", type=str, help="Custom output video path (.mp4)")
    parser.add_argument("--dark", "-d", action="store_true", help="Render with dark dotted canvas mode")
    parser.add_argument("--speed", "-s", type=float, default=1.30, help="Pacing speed multiplier (default: 1.30)")
    parser.add_argument("--no-trim", action="store_true", help="Disable auto-cutting of dead-air pauses")
    parser.add_argument("--bgm", type=str, help="Path to specific background music track")
    parser.add_argument("--watch", "-w", action="store_true", help="Run in continuous folder watcher mode")
    parser.add_argument("--all", action="store_true", help="Render all unrendered audio files in Audio/ folder")
    parser.add_argument("--keep-audio", action="store_true", help="Keep source audio file after rendering")

    args = parser.parse_args()
    pipeline = PureTypographyPipeline(dark_mode=args.dark)

    if args.watch:
        pipeline.watch_folder(dark_mode=args.dark, speed=args.speed)
    elif args.audio:
        pipeline.generate(
            Path(args.audio),
            Path(args.output) if args.output else None,
            dark_mode=args.dark,
            auto_cut=not args.no_trim,
            speed=args.speed,
            bgm_path=Path(args.bgm) if args.bgm else None,
            delete_audio=not args.keep_audio
        )
    else:
        paths = get_project_paths()
        audio_dir = paths["audio"]
        
        # Strictly look into Audio/ folder first
        audio_files = []
        if audio_dir.exists():
            for ext in ["*.wav", "*.mp3", "*.m4a", "*.aac", "*.ogg"]:
                audio_files.extend(list(audio_dir.glob(ext)))
        
        # If Audio/ is empty, fallback to input/voice/
        if not audio_files and paths["input_voice"].exists():
            for ext in ["*.wav", "*.mp3", "*.m4a", "*.aac", "*.ogg"]:
                audio_files.extend(list(paths["input_voice"].glob(ext)))

        # Sort by modification time (most recent first)
        audio_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if not audio_files:
            print(f"\n[!] No audio files found in: {paths['audio'].resolve()}")
            print("    Please place your .wav or .mp3 voice recording in the 'Audio' folder.")
            print("    Or specify directly with: python run_pipeline.py --audio \"path/to/voice.wav\"\n")
            return

        if args.all:
            print(f"Found {len(audio_files)} audio file(s). Processing all...")
            for af in audio_files:
                pipeline.generate(
                    af,
                    dark_mode=args.dark,
                    auto_cut=not args.no_trim,
                    speed=args.speed,
                    bgm_path=Path(args.bgm) if args.bgm else None,
                    delete_audio=not args.keep_audio
                )
        else:
            # Process the latest audio file from Audio folder
            latest_file = audio_files[0]
            print(f"\n[Engine] Selected voice recording from Audio folder: {latest_file.name}")
            pipeline.generate(
                latest_file,
                dark_mode=args.dark,
                auto_cut=not args.no_trim,
                speed=args.speed,
                bgm_path=Path(args.bgm) if args.bgm else None,
                delete_audio=not args.keep_audio
            )


if __name__ == "__main__":
    main()
