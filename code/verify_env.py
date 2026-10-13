"""
System & Environment Verification Script.
Checks:
- Python dependencies (faster-whisper, pydantic, cv2, torch, etc.)
- GPU & CUDA availability
- FFmpeg installation & NVENC hardware encoder
- Ollama service & model availability
- Reference training dataset status
"""
import sys
import os
import subprocess
import requests
from pathlib import Path

def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_python_deps():
    print_header("1. Checking Python Dependencies")
    modules = [
        ("pydantic", "Pydantic V2"),
        ("faster_whisper", "Faster Whisper"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("torch", "PyTorch"),
        ("yaml", "PyYAML"),
        ("requests", "Requests"),
    ]
    all_ok = True
    for mod, name in modules:
        try:
            m = __import__(mod)
            ver = getattr(m, "__version__", "loaded")
            print(f"  [OK] {name:<20} : version {ver}")
        except ImportError as e:
            print(f"  [FAIL] {name:<20} : MISSING ({e})")
            all_ok = False
    return all_ok

def check_gpu():
    print_header("2. Checking GPU & Hardware Acceleration")
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        print(f"  PyTorch CUDA available : {cuda_avail}")
        if cuda_avail:
            print(f"  Device Name            : {torch.cuda.get_device_name(0)}")
            print(f"  VRAM Total (GB)        : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
        else:
            print("  [Info] Running with CPU fallback for PyTorch / CTranslate2.")
    except Exception as e:
        print(f"  [Error] checking torch cuda: {e}")

def check_ffmpeg():
    print_header("3. Checking FFmpeg & NVENC")
    try:
        res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0]
            print(f"  [OK] {first_line}")
        else:
            print("  [FAIL] FFmpeg returned non-zero exit code.")
            return False
    except FileNotFoundError:
        print("  [FAIL] FFmpeg is NOT found on PATH.")
        return False

    # Check for NVENC encoder
    try:
        enc_res = subprocess.run(["ffmpeg", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        has_nvenc = "h264_nvenc" in enc_res.stdout
        has_libass = "--enable-libass" in enc_res.stdout or "ass" in enc_res.stdout
        print(f"  [OK] NVIDIA NVENC support : {'YES (h264_nvenc)' if has_nvenc else 'NO (software libx264)'}")
        print(f"  [OK] libass Subtitles      : {'YES' if has_libass else 'NO'}")
    except Exception as e:
        print(f"  [Warning] Checking encoders: {e}")
    return True

def check_ollama():
    print_header("4. Checking Local Ollama")
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            data = r.json()
            models = [m.get("name") for m in data.get("models", [])]
            print(f"  [OK] Ollama is active on http://localhost:11434")
            print(f"  [OK] Available models : {', '.join(models) if models else 'None'}")
            if any("qwen" in m or "llama" in m for m in models):
                print(f"  [OK] Found recommended LLM model.")
            else:
                print(f"  [Warning] Recommended model (qwen3.5:9b or llama3.1:8b) not detected.")
            return True
        else:
            print(f"  [FAIL] Ollama responded with status code {r.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] Cannot connect to Ollama: {e}")
        print("         Make sure Ollama is running (`ollama serve`).")
        return False

def check_reference_dataset():
    print_header("5. Checking Reference Video Training Set")
    ref_dir = Path("TypoGraphy Edit")
    if not ref_dir.exists():
        print(f"  [FAIL] Directory '{ref_dir}' not found.")
        return False
    mp4_files = list(ref_dir.glob("*.mp4"))
    print(f"  [OK] Found {len(mp4_files)} reference videos in '{ref_dir.resolve()}'")
    if len(mp4_files) >= 10:
        print(f"  [OK] Reference volume is sufficient for style distillation.")
    else:
        print(f"  [Info] Fewer than 10 reference videos found.")
    return True

if __name__ == "__main__":
    print("Starting Automated Typography Video Engine Environment Verification...")
    p_ok = check_python_deps()
    check_gpu()
    f_ok = check_ffmpeg()
    o_ok = check_ollama()
    r_ok = check_reference_dataset()

    print_header("Summary")
    if p_ok and f_ok and o_ok and r_ok:
        print("  >>> ALL SYSTEMS GO. Ready for Phase 1 (Reference Style Distillation) <<<")
    else:
        print("  >>> Some checks reported warnings or missing dependencies. Review above. <<<")
