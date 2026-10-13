"""
Dynamic Video Overlay Engine.
Handles:
1. Top-Left Corner Video: Random selection from 'All Editable Asset/Top Left Corner Video' with true RGBA transparency.
2. Bottom Video Progress Walker: Cat/Outro animation from 'All Editable Asset/Video Ends Video' walking left-to-right across the bottom to indicate remaining time.
"""
import math
import random
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw

from src.core.config_loader import get_project_paths


class OverlayVideoClip:
    """Decodes and caches video frames with full RGBA transparency support."""
    def __init__(self, video_path: Path, target_width: Optional[int] = None, target_height: Optional[int] = None, auto_crop_alpha: bool = False):
        self.video_path = Path(video_path).resolve()
        self.target_width = target_width
        self.target_height = target_height
        self.auto_crop_alpha = auto_crop_alpha
        self.frames: List[Image.Image] = []
        self.fps = 30.0
        self.duration = 0.0
        self.has_alpha = False
        self._load_clip()

    def _load_clip(self):
        if not self.video_path.exists() or self.video_path.stat().st_size < 1024:
            return

        # 1. Probe stream info and alpha mode via ffprobe
        cmd_probe = [
            "ffprobe", "-v", "error",
            "-show_streams", "-of", "json",
            str(self.video_path)
        ]
        orig_w, orig_h = 1920, 1080
        try:
            res = subprocess.run(cmd_probe, capture_output=True, text=True)
            import json
            info = json.loads(res.stdout)
            for s in info.get("streams", []):
                if s.get("codec_type") == "video":
                    orig_w = int(s.get("width", 1920))
                    orig_h = int(s.get("height", 1080))
                    tags = s.get("tags", {})
                    if tags.get("alpha_mode") == "1" or "alpha" in s.get("pix_fmt", ""):
                        self.has_alpha = True
                    r_fps = s.get("r_frame_rate", "30/1")
                    try:
                        self.fps = eval(r_fps)
                    except Exception:
                        self.fps = 30.0
                    break
        except Exception:
            self.fps = 30.0

        codec_flag = ["-c:v", "libvpx-vp9"] if self.video_path.suffix.lower() == ".webm" else []

        cmd = [
            "ffmpeg", "-v", "error",
            *codec_flag,
            "-i", str(self.video_path),
            "-f", "rawvideo",
            "-pix_fmt", "rgba",
            "-"
        ]

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            frame_bytes = orig_w * orig_h * 4
            raw_frames = []
            max_cached_frames = 1200
            
            while len(raw_frames) < max_cached_frames:
                raw = proc.stdout.read(frame_bytes)
                if not raw or len(raw) < frame_bytes:
                    break
                raw_frames.append(raw)
            proc.terminate()

            if not raw_frames:
                return

            # If auto_crop_alpha is requested, compute union bounding box across all frames
            crop_box = None
            if self.auto_crop_alpha:
                all_ymin, all_ymax, all_xmin, all_xmax = orig_h, 0, orig_w, 0
                has_content = False
                for raw in raw_frames:
                    arr = np.frombuffer(raw, dtype=np.uint8).reshape((orig_h, orig_w, 4))
                    alpha = arr[:, :, 3]
                    y_idx, x_idx = np.where(alpha > 15)
                    if len(y_idx) > 0:
                        has_content = True
                        all_ymin = min(all_ymin, int(y_idx.min()))
                        all_ymax = max(all_ymax, int(y_idx.max()))
                        all_xmin = min(all_xmin, int(x_idx.min()))
                        all_xmax = max(all_xmax, int(x_idx.max()))

                if has_content and (all_xmax > all_xmin) and (all_ymax > all_ymin):
                    pad = 12
                    crop_box = (
                        max(0, all_xmin - pad),
                        max(0, all_ymin - pad),
                        min(orig_w, all_xmax + pad),
                        min(orig_h, all_ymax + pad)
                    )

            # Process and resize frames
            for raw in raw_frames:
                arr = np.frombuffer(raw, dtype=np.uint8).reshape((orig_h, orig_w, 4))
                img = Image.fromarray(arr, "RGBA")
                
                if crop_box:
                    img = img.crop(crop_box)
                
                if self.target_width or self.target_height:
                    cur_w, cur_h = img.size
                    if self.target_width and self.target_height:
                        out_w, out_h = self.target_width, self.target_height
                    elif self.target_width:
                        out_w = self.target_width
                        out_h = int(cur_h * (self.target_width / float(cur_w)))
                    else:
                        out_h = self.target_height
                        out_w = int(cur_w * (self.target_height / float(cur_h)))
                    img = img.resize((out_w, out_h), Image.Resampling.LANCZOS)
                
                self.frames.append(img)

            self.duration = len(self.frames) / self.fps if self.fps > 0 else 0.0
        except Exception as e:
            print(f"[OverlayVideoClip] Failed loading {self.video_path.name}: {e}")

    def get_frame_at_time(self, elapsed_sec: float, loop: bool = True) -> Optional[Image.Image]:
        if not self.frames:
            return None
        if loop:
            idx = int(elapsed_sec * self.fps) % len(self.frames)
        else:
            idx = min(int(elapsed_sec * self.fps), len(self.frames) - 1)
        return self.frames[idx]


class TopCornerVideoManager:
    """Manages dynamic random top-left corner video overlays."""
    def __init__(self):
        paths = get_project_paths()
        assets_dir = paths.get("assets", paths["root"] / "assets")
        self.source_dirs = [
            paths.get("top_corner_video", assets_dir / "All Editable Asset" / "Top Left Corner Video"),
            assets_dir / "All Editable Asset" / "Top Left Corner Video",
            paths["root"] / "All Editable Asset" / "Top Left Corner Video",
            assets_dir / "All Editable Asset" / "Top Corner Video"
        ]
        self.clip: Optional[OverlayVideoClip] = None
        self.chosen_file: Optional[Path] = None
        self.pos_x = 40
        self.pos_y = 20
        self.target_width = 260

    def pick_and_load_random_video(self) -> bool:
        valid_files = []
        for sdir in self.source_dirs:
            if sdir.exists():
                for ext in ["*.webm", "*.mp4", "*.mov", "*.mkv", "*.avi"]:
                    for f in sdir.glob(ext):
                        if f.is_file() and f.stat().st_size > 5000:
                            valid_files.append(f)

        if not valid_files:
            print("[TopCornerVideo] No valid video assets found in 'All Editable Asset/Top Left Corner Video'")
            return False

        # Randomly choose one video
        self.chosen_file = random.choice(valid_files)
        print(f"\n[TopCornerVideo] Selected random top-left overlay: '{self.chosen_file.name}' ({len(valid_files)} available)")
        
        # Load with auto_crop_alpha=True to remove empty transparent space and place cleanly in top-left
        self.clip = OverlayVideoClip(self.chosen_file, target_width=self.target_width, auto_crop_alpha=True)
        if self.clip and self.clip.frames:
            print(f"  [TopCornerVideo] Loaded {len(self.clip.frames)} frames ({self.clip.duration:.2f}s, Alpha: {self.clip.has_alpha})")
            return True
        return False

    def render_overlay(self, canvas: Image.Image, current_time: float) -> Image.Image:
        if not self.clip or not self.clip.frames:
            return canvas

        frame_img = self.clip.get_frame_at_time(current_time, loop=True)
        if frame_img is None:
            return canvas

        canvas_rgba = canvas.convert("RGBA")
        canvas_rgba.paste(frame_img, (self.pos_x, self.pos_y), frame_img)
        return canvas_rgba.convert("RGB")


class VideoEndsVideoManager:
    """
    Manages dynamic bottom video overlay (Video Ends Video).
    Functions as a visual progress walker (walking Left to Right across the bottom of the screen).
    """
    def __init__(self):
        paths = get_project_paths()
        assets_dir = paths.get("assets", paths["root"] / "assets")
        self.source_dir = paths.get(
            "video_ends_video",
            assets_dir / "All Editable Asset" / "Video Ends Video"
        )
        self.clip: Optional[OverlayVideoClip] = None
        self.chosen_file: Optional[Path] = None
        self.target_width = 220

    def pick_and_load_random_video(self) -> bool:
        if not self.source_dir.exists():
            return False

        valid_files = []
        for ext in ["*.webm", "*.mp4", "*.mov", "*.mkv", "*.avi"]:
            for f in self.source_dir.glob(ext):
                if f.is_file() and f.stat().st_size > 5000:
                    valid_files.append(f)

        if not valid_files:
            print("[VideoEndsVideo] No valid video assets found in 'All Editable Asset/Video Ends Video'")
            return False

        self.chosen_file = random.choice(valid_files)
        print(f"\n[VideoEndsVideo] Selected random bottom walker: '{self.chosen_file.name}' ({len(valid_files)} available)")
        
        self.clip = OverlayVideoClip(self.chosen_file, target_width=self.target_width)
        if self.clip and self.clip.frames:
            print(f"  [VideoEndsVideo] Loaded {len(self.clip.frames)} frames ({self.clip.duration:.2f}s, Alpha: {self.clip.has_alpha})")
            return True
        return False

    def render_overlay(self, canvas: Image.Image, current_time: float, total_duration: float) -> Image.Image:
        if not self.clip or not self.clip.frames:
            return canvas

        frame_img = self.clip.get_frame_at_time(current_time, loop=True)
        if frame_img is None:
            return canvas

        fw, fh = frame_img.size

        # Dynamic Left-to-Right Progress Walk
        progress = min(1.0, max(0.0, current_time / max(0.1, total_duration)))
        start_x = 25
        end_x = 1920 - fw - 25
        pos_x = int(start_x + progress * (end_x - start_x))
        pos_y = 1080 - fh - 25

        canvas_rgba = canvas.convert("RGBA")
        canvas_rgba.paste(frame_img, (pos_x, pos_y), frame_img)
        return canvas_rgba.convert("RGB")
