"""
Stock Media Service for Automated Video Engine.
Fetches 100% LIVE, high-resolution B-roll stock videos and images directly via Pexels API.
Strict constraints:
- Maximum 5 stock fetches across the entire video.
- Zero hardcoded static character cutouts.
- Automatic cache cleanup.
"""
import os
import io
import re
import json
import random
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, List, Dict
from PIL import Image
from src.core.config_loader import load_system_config, get_project_paths


PEXELS_PHOTO_SEARCH_URL = "https://api.pexels.com/v1/search"
PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/videos/search"


class StockImageService:
    def __init__(self):
        self.paths = get_project_paths()
        self.cache_dir = self.paths["assets"] / "cache" / "images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.video_cache_dir = self.paths["assets"] / "cache" / "videos"
        self.video_cache_dir.mkdir(parents=True, exist_ok=True)
        
        cfg = load_system_config().get("assets", {})
        self.pexels_api_key = (
            os.getenv("PEXELS_API_KEY", "") 
            or cfg.get("pexels_api_key", "")
            or "AdyvCOGIbv1ybCBHnzSYHKyR9K4r5gW4YlT2aAkmy4H8smqqTLGWWfZD"
        )
        self.fetch_count = 0
        self.max_fetches = 4

    def fetch_video_or_image_for_query(self, query: str, scene_idx: int = 0) -> Optional[Path]:
        """
        Fetches high-res 16:9 Landscape stock photo from Pexels Photo API.
        Strictly respects max 4 fetches across the entire video.
        """
        if self.fetch_count >= self.max_fetches:
            return None

        # Fetch high-res photo directly
        return self.fetch_image_for_query(query, scene_idx)

    def fetch_video_for_query(self, query: str, scene_idx: int = 0) -> Optional[Path]:
        """
        Searches Pexels for a 16:9 HD video clip and downloads it.
        """
        if self.fetch_count >= self.max_fetches:
            return None

        clean_slug = re.sub(r'[^a-zA-Z0-9]', '_', query.lower().strip())[:25]
        cached_file = self.video_cache_dir / f"vid_{clean_slug}_{scene_idx}.mp4"
        if cached_file.exists() and cached_file.stat().st_size > 50000:
            self.fetch_count += 1
            return cached_file

        if not self.pexels_api_key:
            return None

        clean_q = urllib.parse.quote(query.strip())
        page_num = (scene_idx % 2) + 1
        url = f"{PEXELS_VIDEO_SEARCH_URL}?query={clean_q}&per_page=8&page={page_num}&orientation=landscape"

        headers = {
            "Authorization": self.pexels_api_key,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
                videos = data.get("videos", [])
                if videos:
                    chosen_vid = videos[scene_idx % len(videos)]
                    video_files = chosen_vid.get("video_files", [])
                    # Look for 1080p or 720p HD file
                    best_url = None
                    for vf in video_files:
                        if vf.get("quality") == "hd" and vf.get("width", 0) >= 1280:
                            best_url = vf.get("link")
                            break
                    if not best_url and video_files:
                        best_url = video_files[0].get("link")

                    if best_url:
                        dl_req = urllib.request.Request(best_url, headers=headers)
                        with urllib.request.urlopen(dl_req, timeout=20) as dl_resp:
                            with open(cached_file, "wb") as f:
                                f.write(dl_resp.read())
                        print(f"[StockMediaService] Downloaded Pexels video clip for '{query}': {cached_file.name}")
                        self.fetch_count += 1
                        return cached_file
        except Exception as e:
            print(f"[StockMediaService] Pexels video fetch note for '{query}': {e}")

        return None

    def fetch_image_for_query(self, query: str, scene_idx: int = 0) -> Optional[Path]:
        """
        Performs a live Pexels search for context query and downloads a high-res photo.
        Returns local cached Path.
        """
        if self.fetch_count >= self.max_fetches:
            return None

        clean_slug = re.sub(r'[^a-zA-Z0-9]', '_', query.lower().strip())[:25]
        cached_file = self.cache_dir / f"img_{clean_slug}_{scene_idx}.jpg"
        if cached_file.exists() and cached_file.stat().st_size > 5000:
            self.fetch_count += 1
            return cached_file

        img_path = self._fetch_pexels_photo_live(query, cached_file, scene_idx)
        if img_path:
            self.fetch_count += 1
            return img_path

        return None

    def _fetch_pexels_photo_live(self, query: str, dest_path: Path, scene_idx: int) -> Optional[Path]:
        """Queries Pexels Photo API live and downloads high-res landscape B-roll photo."""
        if not self.pexels_api_key:
            return None

        clean_q = urllib.parse.quote(query.strip())
        page_num = (scene_idx % 3) + 1
        url = f"{PEXELS_PHOTO_SEARCH_URL}?query={clean_q}&per_page=12&page={page_num}&orientation=landscape"
        
        headers = {
            "Authorization": self.pexels_api_key,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
                photos = data.get("photos", [])
                if photos:
                    chosen_photo = photos[scene_idx % len(photos)]
                    src_dict = chosen_photo.get("src", {})
                    img_url = (
                        src_dict.get("large2x") 
                        or src_dict.get("large") 
                        or src_dict.get("landscape")
                    )
                    
                    if img_url:
                        return self._download_and_save(img_url, dest_path)
        except Exception as e:
            print(f"[StockMediaService] Pexels photo fetch note for '{query}': {e}")
        
        return None

    def _download_and_save(self, url: str, dest_path: Path) -> Optional[Path]:
        """Downloads, crops to 16:9 ratio, and saves high quality JPEG."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                raw_data = resp.read()
                img = Image.open(io.BytesIO(raw_data)).convert("RGB")
                
                # Resize and optimize to 1920x1080 (16:9 ratio)
                w, h = img.size
                target_ratio = 16.0 / 9.0
                curr_ratio = w / float(h)
                
                if curr_ratio > target_ratio:
                    new_w = int(h * target_ratio)
                    crop_box = ((w - new_w) // 2, 0, (w + new_w) // 2, h)
                else:
                    new_h = int(w / target_ratio)
                    crop_box = (0, (h - new_h) // 2, w, (h + new_h) // 2)
                    
                cropped = img.crop(crop_box)
                resized = cropped.resize((1920, 1080), Image.Resampling.LANCZOS)
                
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                resized.save(dest_path, "JPEG", quality=92)
                return dest_path
        except Exception as e:
            print(f"[StockMediaService] Image save error: {e}")
            return None

    @staticmethod
    def cleanup_all_media():
        """Cleans up temporary files in cache."""
        for cdir in [Path("assets/cache/images"), Path("assets/cache/videos")]:
            if cdir.exists():
                for f in cdir.glob("*.*"):
                    try:
                        f.unlink()
                    except Exception:
                        pass
