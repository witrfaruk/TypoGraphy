"""
Kinetic Typography Motion Renderer - Reference Video Aesthetic.
Features:
- Canvas: 1920x1080 (16:9 Landscape @ 60 FPS).
- Pure Kinetic Typography on Clean Pastel Lilac (#ECE8F6) Canvas.
- Selectively renders Pexels HD B-Roll Video/Photo Clips (max 5) with dark glass overlay and white/violet typography.
- Word-by-word reveal with elastic spring pop bounce on entry.
- Reference layout styles: Center Stack, Vertical Left Word (90° rotated), Quotes Accent, B-Roll Overlay.
- Synchronized sound effects (SFX) + Studio Voice Normalization + BGM Mixing.
- 60 FPS FFmpeg NVENC Hardware Accelerated Streaming.
"""
import os
import math
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np

from src.core.types import TimelinePlan, StyleProfile, Scene
from src.core.config_loader import get_project_paths, load_system_config
from src.typography.kinetic_layout import (
    KineticLayoutPlanner, KineticFrameComposition, VisualWord,
    create_full_canvas_background, get_font, strip_unicode_emojis
)
from src.audio.sfx_manager import SFXManager
from src.audio.audio_mixer import AudioMixer
from src.core.overlay_manager import (
    TopCornerVideoManager, VideoEndsVideoManager
)


class VideoClipReader:
    """Reads frames from local Pexels video clips for background playback."""
    def __init__(self, clip_path: str):
        self.clip_path = clip_path
        self.cap = cv2.VideoCapture(clip_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = max(1, int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.last_frame = None

    def get_frame(self, elapsed_seconds: float) -> Optional[Image.Image]:
        if not self.cap.isOpened():
            return self.last_frame
        
        target_frame = int(elapsed_seconds * self.fps) % self.total_frames
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame_bgr = self.cap.read()
        if not ret or frame_bgr is None:
            return self.last_frame

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        
        # Center crop to 16:9
        iw, ih = img.size
        target_ratio = 16.0 / 9.0
        curr_ratio = iw / float(ih)
        if curr_ratio > target_ratio:
            new_w = int(ih * target_ratio)
            crop_box = ((iw - new_w) // 2, 0, (iw + new_w) // 2, ih)
        else:
            new_h = int(iw / target_ratio)
            crop_box = (0, (ih - new_h) // 2, iw, (ih + new_h) // 2)
            
        cropped = img.crop(crop_box)
        resized = cropped.resize((1920, 1080), Image.Resampling.BILINEAR)
        self.last_frame = resized
        return resized

    def close(self):
        if self.cap:
            self.cap.release()


class MotionTypographyRenderer:
    def __init__(self, style_profile: StyleProfile, dark_mode: bool = False):
        self.style = style_profile
        self.canvas_w = 1920
        self.canvas_h = 1080
        self.fps = 60
        self.dark_mode = dark_mode
        self.layout_planner = KineticLayoutPlanner(dark_mode=dark_mode)
        self.paths = get_project_paths()
        self.sfx_manager = SFXManager()
        self.audio_mixer = AudioMixer()
        
        # Clean pastel lilac base canvas (#ECE8F6)
        self.base_canvas = create_full_canvas_background(self.canvas_w, self.canvas_h)
        self.video_readers: Dict[str, VideoClipReader] = {}
        self.cached_images: Dict[str, Image.Image] = {}

        # Dynamic Overlays (Top-Left Corner Video & Bottom Video Ends Video)
        self.top_corner_mgr = TopCornerVideoManager()
        self.video_ends_mgr = VideoEndsVideoManager()

    def _get_bgm_track(self, specified_bgm: Optional[Path] = None) -> Optional[Path]:
        """Finds a background music track from Background Music directory or specified path."""
        if specified_bgm and Path(specified_bgm).exists():
            return Path(specified_bgm).resolve()
        assets_dir = self.paths.get("assets", self.paths["root"] / "assets")
        bgm_dir = self.paths.get("bgm", assets_dir / "Background Music")
        if bgm_dir.exists():
            tracks = []
            for ext in ["*.mp3", "*.wav", "*.m4a", "*.aac"]:
                tracks.extend(list(bgm_dir.glob(ext)))
            if tracks:
                import random
                return random.choice(tracks).resolve()
        return None

    def render_timeline_to_video(
        self,
        timeline: TimelinePlan,
        audio_path: Path,
        output_video_path: Path,
        bgm_path: Optional[Path] = None
    ) -> Path:
        """
        Renders the full 16:9 Landscape kinetic typography video matching the reference aesthetic.
        """
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        total_duration = timeline.total_duration
        total_frames = int(total_duration * self.fps)
        
        print(f"\n[MotionRenderer] Rendering 16:9 Kinetic Video matching Reference Style: {output_video_path.name}")
        print(f"  - Theme Style  : Pastel Lilac (#ECE8F6) + Royal Purple (#7C3AED) + Deep Navy (#1E1B4B)")
        print(f"  - Layouts      : Center Stack, Vertical Left Word, Quotes Accent, Pexels B-Roll")
        print(f"  - Canvas Layout: {self.canvas_w}x{self.canvas_h} @ {self.fps} FPS")
        print(f"  - Total Frames : {total_frames} frames ({total_duration:.2f}s)")

        # Initialize dynamic overlay assets (random top-corner & video ends video)
        self.top_corner_mgr.pick_and_load_random_video()
        self.video_ends_mgr.pick_and_load_random_video()

        # 1. Plan and Generate Synchronized SFX
        sfx_events = self.sfx_manager.plan_sfx_events(timeline)
        sfx_track_path = self.paths["assets"] / "cache" / "sfx_master.wav"
        self.audio_mixer.create_composite_sfx_track(sfx_events, total_duration, sfx_track_path)
        print(f"  - SFX Layer    : {len(sfx_events)} synchronized sound effects hits mixed")

        selected_bgm = self._get_bgm_track(bgm_path)
        if selected_bgm:
            print(f"  - BGM Bed      : {selected_bgm.name} (~18% volume)")

        # Generate per-scene visual compositions
        compositions: List[KineticFrameComposition] = []
        for s_idx, scene in enumerate(timeline.scenes):
            comp = self.layout_planner.plan_scene_composition(scene, s_idx)
            compositions.append(comp)

        if not compositions:
            raise ValueError("Timeline has no scenes to render.")

        # Chain end_time of each comp to start_time of the next to eliminate blank gaps
        for i in range(len(compositions) - 1):
            compositions[i].end_time = compositions[i + 1].start_time
        compositions[-1].end_time = total_duration

        # Initialize video clip readers for any B-Roll scenes
        for comp in compositions:
            if comp.video_clip_path and comp.video_clip_path not in self.video_readers:
                try:
                    self.video_readers[comp.video_clip_path] = VideoClipReader(comp.video_clip_path)
                except Exception as e:
                    print(f"[MotionRenderer] Could not open video clip {comp.video_clip_path}: {e}")

        # FFmpeg Hardware / Software config
        cfg = load_system_config().get("rendering", {})
        use_nvenc = cfg.get("use_nvenc", True)
        encoder = "h264_nvenc" if use_nvenc else "libx264"

        vocal_filter = (
            "highpass=f=80,"
            "equalizer=f=240:t=q:w=1.4:g=3.0,"
            "equalizer=f=1000:t=q:w=1.8:g=-2.0,"
            "equalizer=f=4500:t=q:w=1.2:g=5.0,"
            "dynaudnorm=f=100:g=12:m=3.5:p=0.95,volume=1.0[v_aud]"
        )

        bgm_vol = "0.18"
        sfx_vol = "1.25"

        if selected_bgm and selected_bgm.exists():
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{self.canvas_w}x{self.canvas_h}",
                "-pix_fmt", "rgb24",
                "-r", str(self.fps),
                "-i", "-",
                "-i", str(audio_path.resolve()),
                "-i", str(sfx_track_path.resolve()),
                "-stream_loop", "-1",
                "-i", str(selected_bgm.resolve()),
                "-filter_complex", (
                    f"[1:a]{vocal_filter};"
                    f"[2:a]volume={sfx_vol}[sfx_aud];"
                    f"[3:a]volume={bgm_vol}[bgm_aud];"
                    f"[v_aud][sfx_aud][bgm_aud]amix=inputs=3:duration=first:dropout_transition=2:normalize=0,"
                    f"alimiter=limit=0.98:attack=5:release=50[aout]"
                ),
                "-map", "0:v",
                "-map", "[aout]",
                "-map_metadata", "-1",
                "-map_chapters", "-1",
                "-fflags", "+bitexact",
                "-brand", "mp42",
                "-c:v", encoder,
                "-preset", "p7" if encoder == "h264_nvenc" else "slow",
                "-b:v", "25M",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "320k",
                "-shortest",
                str(output_video_path.resolve())
            ]
        else:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{self.canvas_w}x{self.canvas_h}",
                "-pix_fmt", "rgb24",
                "-r", str(self.fps),
                "-i", "-",
                "-i", str(audio_path.resolve()),
                "-i", str(sfx_track_path.resolve()),
                "-filter_complex", (
                    f"[1:a]{vocal_filter};"
                    f"[2:a]volume={sfx_vol}[sfx_aud];"
                    f"[v_aud][sfx_aud]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,"
                    f"alimiter=limit=0.98:attack=5:release=50[aout]"
                ),
                "-map", "0:v",
                "-map", "[aout]",
                "-map_metadata", "-1",
                "-map_chapters", "-1",
                "-fflags", "+bitexact",
                "-brand", "mp42",
                "-c:v", encoder,
                "-preset", "p7" if encoder == "h264_nvenc" else "slow",
                "-b:v", "25M",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "320k",
                "-shortest",
                str(output_video_path.resolve())
            ]

        print("[MotionRenderer] Streaming frame buffer directly to FFmpeg NVENC...")
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        curr_comp_idx = 0
        num_comps = len(compositions)

        try:
            for frame_idx in range(total_frames):
                current_time = frame_idx / self.fps

                while curr_comp_idx < num_comps - 1 and current_time >= compositions[curr_comp_idx].end_time:
                    curr_comp_idx += 1

                active_comp = compositions[curr_comp_idx]
                frame_img = self._render_single_frame(active_comp, timeline, current_time, total_duration)
                
                raw_bytes = frame_img.tobytes()
                try:
                    proc.stdin.write(raw_bytes)
                except (BrokenPipeError, IOError):
                    break

                if frame_idx % (self.fps * 4) == 0:
                    pct = (frame_idx / total_frames) * 100
                    print(f"  [Render Progress] {pct:4.1f}% ({frame_idx}/{total_frames} frames)...")
        finally:
            # Close all video readers
            for vr in self.video_readers.values():
                vr.close()

        proc.stdin.close()
        stderr_output = proc.stderr.read().decode("utf-8", errors="replace")
        proc.wait()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg render error: {stderr_output[:300]}")

        print(f"\n[MotionRenderer] Video successfully generated: {output_video_path.resolve()}")
        return output_video_path

    def _hex_to_rgb(self, hex_str: str) -> Tuple[int, int, int]:
        """Converts hex color string to RGB tuple."""
        clean = hex_str.lstrip("#")
        if len(clean) == 6:
            return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)
        elif len(clean) == 3:
            return int(clean[0]*2, 16), int(clean[1]*2, 16), int(clean[2]*2, 16)
        return (30, 27, 75)

    def _render_single_frame(
        self,
        comp: KineticFrameComposition,
        timeline: TimelinePlan,
        current_time: float,
        total_duration: float
    ) -> Image.Image:
        """
        Renders a single frame matching the reference video:
        - Pastel lilac (#ECE8F6) or Pexels B-Roll background.
        - Word-by-word reveal with elastic spring pop bounce on entry.
        - High contrast Royal Purple & Deep Navy typography.
        - Support for rotated vertical words and quotes.
        """
        # 1. Base Canvas Preparation
        if comp.is_broll:
            bg_frame = None
            scene_elapsed = max(0.0, current_time - comp.start_time)
            
            # Read video frame
            if comp.video_clip_path and comp.video_clip_path in self.video_readers:
                bg_frame = self.video_readers[comp.video_clip_path].get_frame(scene_elapsed)
            
            # Read image if video not available
            if bg_frame is None and comp.image_path:
                if comp.image_path not in self.cached_images:
                    if Path(comp.image_path).exists():
                        self.cached_images[comp.image_path] = Image.open(comp.image_path).convert("RGB")
                img_src = self.cached_images.get(comp.image_path)
                if img_src:
                    # Subtle Ken Burns zoom
                    dur = max(0.5, comp.end_time - comp.start_time)
                    progress = min(1.0, scene_elapsed / dur)
                    scale = 1.0 + 0.05 * progress
                    zw, zh = int(1920 * scale), int(1080 * scale)
                    z_img = img_src.resize((zw, zh), Image.Resampling.BILINEAR)
                    x_off = (zw - 1920) // 2
                    y_off = (zh - 1080) // 2
                    bg_frame = z_img.crop((x_off, y_off, x_off + 1920, y_off + 1080))

            if bg_frame is not None:
                # Apply aesthetic dark glass overlay for high contrast
                frame = bg_frame.copy()
                overlay = Image.new("RGBA", (self.canvas_w, self.canvas_h), (20, 16, 36, 140))
                frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
            else:
                frame = self.base_canvas.copy()
        else:
            frame = self.base_canvas.copy()

            # 2. Render Words (One-by-One Reveal + Elastic Spring Pop)
        for v_word in comp.words:
            if current_time < v_word.start_time:
                continue

            dt = current_time - v_word.start_time
            # Elastic spring bounce on reveal
            if dt < 0.20:
                scale_factor = 1.0 + (0.22 * math.exp(-14.0 * dt) * math.cos(20.0 * dt))
                alpha = min(255, int(255 * (dt / 0.08)))
            else:
                scale_factor = 1.0
                alpha = 255

            rendered_size = max(24, int(v_word.font_size * scale_factor))
            font = get_font(v_word.font_path, rendered_size)
            text = strip_unicode_emojis(v_word.text)

            bbox = font.getbbox(text)
            x0, y0, x1, y1 = bbox
            tw = max(10, x1 - x0)
            th = max(10, y1 - y0)

            rgb_col = self._hex_to_rgb(v_word.color)

            # Generous padding to prevent any clipping of ascenders/descenders
            pad = 50
            txt_layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
            d_layer = ImageDraw.Draw(txt_layer)

            # Exactly offset by -x0 and -y0 so glyph lands precisely at (pad, pad)
            draw_x = pad - x0
            draw_y = pad - y0

            # Soft drop shadow
            if comp.is_broll:
                shadow_col = (0, 0, 0, int(190 * (alpha / 255.0)))
                d_layer.text((draw_x + 3, draw_y + 4), text, font=font, fill=shadow_col)
            else:
                shadow_col = (30, 27, 75, int(40 * (alpha / 255.0)))
                d_layer.text((draw_x + 2, draw_y + 3), text, font=font, fill=shadow_col)

            # Main text
            d_layer.text((draw_x, draw_y), text, font=font, fill=(rgb_col[0], rgb_col[1], rgb_col[2], alpha))

            # Apply rotation if vertical word (e.g. 90 degrees)
            if abs(v_word.rotation) > 0.5:
                rotated = txt_layer.rotate(v_word.rotation, resample=Image.Resampling.BICUBIC, expand=True)
            else:
                rotated = txt_layer

            rw, rh = rotated.size
            cx, cy = v_word.position
            top_x = cx - (rw // 2)
            top_y = cy - (rh // 2)

            frame.paste(rotated, (top_x, top_y), rotated)

        # 3. Dynamic Top-Left Corner Video Overlay (Randomly picked from All Editable Asset)
        frame = self.top_corner_mgr.render_overlay(frame, current_time)

        # 4. Dynamic Bottom Video Overlay (Randomly picked from All Editable Asset)
        frame = self.video_ends_mgr.render_overlay(frame, current_time, total_duration)

        return frame
