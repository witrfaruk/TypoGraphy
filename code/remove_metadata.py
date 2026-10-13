"""
Standalone One-Click Video Metadata Remover.
Run: python remove_metadata.py "path/to/video.mp4"
Or run without arguments to sanitize all videos in 'Final Video/' folder.
"""
import sys
from pathlib import Path

# Ensure code root is in sys.path
_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from src.core.metadata_remover import MetadataRemover
from src.core.config_loader import get_project_paths


def main():
    paths = get_project_paths()
    remover = MetadataRemover()

    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if not target.exists():
            print(f"[!] File not found: {target}")
            return
        remover.strip_metadata(target)
    else:
        final_dir = paths["final_video"]
        print(f"\n========================================================")
        print(f"  VIDEO METADATA SANITIZER")
        print(f"========================================================")
        print(f"Scanning '{final_dir.resolve()}' for videos...\n")
        
        videos = list(final_dir.glob("*.mp4"))
        if not videos:
            print("No .mp4 videos found in 'Final Video/' folder.")
            return

        for v in videos:
            remover.strip_metadata(v)

        print(f"\nAll {len(videos)} video(s) sanitized successfully!")


if __name__ == "__main__":
    main()
