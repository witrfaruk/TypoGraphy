"""
Configuration loader and environment manager for the Typography Video Engine.
"""
import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from src.core.types import StyleProfile

_curr = Path(__file__).resolve()
if len(_curr.parents) >= 3 and _curr.parents[2].name.lower() == "code":
    CODE_DIR = _curr.parents[2]
    PROJECT_ROOT = CODE_DIR.parent
else:
    PROJECT_ROOT = _curr.parents[2]
    CODE_DIR = PROJECT_ROOT / "code" if (PROJECT_ROOT / "code").exists() else PROJECT_ROOT

CONFIG_DIR = CODE_DIR / "config" if (CODE_DIR / "config").exists() else PROJECT_ROOT / "config"
FONTS_DIR = CONFIG_DIR / "fonts"
ASSETS_DIR = PROJECT_ROOT / "assets"
LOCAL_LIBRARY_DIR = ASSETS_DIR / "local_library"
CACHE_DIR = ASSETS_DIR / "cache"
INPUT_VOICE_DIR = CODE_DIR / "input" / "voice" if (CODE_DIR / "input").exists() else PROJECT_ROOT / "input" / "voice"
AUDIO_DIR = PROJECT_ROOT / "Audio"
BGM_DIR = ASSETS_DIR / "Background Music" if (ASSETS_DIR / "Background Music").exists() else PROJECT_ROOT / "Background Music"
FINAL_VIDEO_DIR = PROJECT_ROOT / "Final Video"
OUTPUT_DEBUG_DIR = CODE_DIR / "output" / "debug"
STYLE_PROFILE_PATH = CONFIG_DIR / "style_profile.json"
SYSTEM_CONFIG_PATH = CONFIG_DIR / "system_config.yaml"
ALL_EDITABLE_ASSET_DIR = (
    ASSETS_DIR / "All Editable Asset"
    if (ASSETS_DIR / "All Editable Asset").exists()
    else PROJECT_ROOT / "All Editable Asset"
)
TOP_CORNER_VIDEO_DIR = ALL_EDITABLE_ASSET_DIR / "Top Left Corner Video"
VIDEO_ENDS_VIDEO_DIR = ALL_EDITABLE_ASSET_DIR / "Video Ends Video"


def get_project_paths() -> Dict[str, Path]:
    return {
        "root": PROJECT_ROOT,
        "code": CODE_DIR,
        "config": CONFIG_DIR,
        "fonts": FONTS_DIR,
        "assets": ASSETS_DIR,
        "local_library": LOCAL_LIBRARY_DIR,
        "cache": CACHE_DIR,
        "input_voice": INPUT_VOICE_DIR,
        "audio": AUDIO_DIR,
        "bgm": BGM_DIR,
        "output_renders": FINAL_VIDEO_DIR,
        "final_video": FINAL_VIDEO_DIR,
        "output_debug": OUTPUT_DEBUG_DIR,
        "style_profile": STYLE_PROFILE_PATH,
        "system_config": SYSTEM_CONFIG_PATH,
        "all_editable_asset": ALL_EDITABLE_ASSET_DIR,
        "top_corner_video": TOP_CORNER_VIDEO_DIR,
        "video_ends_video": VIDEO_ENDS_VIDEO_DIR,
    }


def ensure_directories_exist():
    for name, path in get_project_paths().items():
        if name in ["style_profile", "system_config"]:
            continue
        path.mkdir(parents=True, exist_ok=True)


def load_system_config() -> Dict[str, Any]:
    default_config = {
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "qwen3.5:9b",
            "timeout_seconds": 90,
        },
        "whisper": {
            "model_size": "small",
            "device": "auto",
            "compute_type": "auto",
            "vad_filter": True,
        },
        "rendering": {
            "use_nvenc": True,
            "fps": 60,
            "preset": "p6",
            "crf": 19,
        },
        "assets": {
            "pexels_api_key": os.getenv("PEXELS_API_KEY", ""),
            "prefer_local": True,
            "download_cache": True,
        }
    }

    if SYSTEM_CONFIG_PATH.exists():
        try:
            with open(SYSTEM_CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
                default_config.update(loaded)
        except Exception as e:
            print(f"[Warning] Failed to parse system_config.yaml: {e}. Using defaults.")

    return default_config


def save_system_config(config_data: Dict[str, Any]):
    ensure_directories_exist()
    with open(SYSTEM_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)


def load_style_profile(profile_path: Optional[Path] = None) -> StyleProfile:
    path = profile_path or STYLE_PROFILE_PATH
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return StyleProfile.model_validate(data)
        except Exception as e:
            print(f"[Warning] Failed to load style profile from {path}: {e}. Falling back to default.")
    
    return StyleProfile()


def save_style_profile(profile: StyleProfile, profile_path: Optional[Path] = None):
    ensure_directories_exist()
    path = profile_path or STYLE_PROFILE_PATH
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, indent=2)
    print(f"[Config] Saved style profile to {path}")


def list_available_fonts() -> List[str]:
    ensure_directories_exist()
    font_extensions = {".ttf", ".otf", ".woff", ".woff2"}
    fonts = []
    if FONTS_DIR.exists():
        for f in FONTS_DIR.iterdir():
            if f.suffix.lower() in font_extensions:
                fonts.append(f.name)
    return fonts
