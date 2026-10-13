# ⚡ Kinetic Typography Auto-Reel Engine

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-CUDA%20%2F%20CPU-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-NVENC%20Hardware%20Encoder-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)
![Faster Whisper](https://img.shields.io/badge/Faster--Whisper-Word--Level%20AI-blue?style=for-the-badge)
![60 FPS](https://img.shields.io/badge/Output-1080x1920%20%40%2060FPS-blueviolet?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A local-first, GPU-accelerated autonomous short-form kinetic typography video engine.**  
*Drop a voice audio file $\rightarrow$ Get a viral 1080x1920 60 FPS Instagram Reel / YouTube Short in ~25 seconds with ZERO manual editing!*

</div>

---

## 🌟 Key Features

```
┌─────────────────┐     ┌──────────────────────┐     ┌───────────────────────┐     ┌──────────────────────┐
│   Voice Audio   │ ──► │ Faster-Whisper + VAD │ ──► │ Silence Auto-Cut (✂️) │ ──► │  1.4x Tempo Speedup  │
│  (.wav / .mp3)  │     │ (Word Timestamps ms) │     │ (Dead Air Removal)    │     │ (Natural Voice Pitch)│
└─────────────────┘     └──────────────────────┘     └───────────────────────┘     └──────────────────────┘
                                                                                               │
┌─────────────────┐     ┌──────────────────────┐     ┌───────────────────────┐                 ▼
│   Final Reel    │ ◄── │ FFmpeg NVENC 60 FPS  │ ◄── │ 3D Emoji Stickers (✨)│ ◄── ┌──────────────────────┐
│ (1080x1920 .mp4)│     │ + Random BGM (~2.5%) │     │ + Dynamic Safe-Bounds │     │ Spatial Layout Engine│
└─────────────────┘     └──────────────────────┘     └───────────────────────┘     │ (Matcha / Drunk / Star)
                                                                                   └──────────────────────┘
```

- 🎤 **Single-Input Autonomous Workflow**: Only input is your voice recording. No scripts, timelines, or manual keyframes required.
- ✂️ **Smart Silence & Dead-Air Auto-Cutter**: Detects dead-air pauses ($>0.5\text{s}$) and seamlessly jump-cuts them with generous vocal padding ($140\text{ms}$) and a smooth $25\text{ms}$ cosine ($S$-curve) crossfade.
- ⚡ **1.4x Dynamic Pacing Acceleration**: Automatically accelerates video and speech tempo to **1.4x** with high-fidelity pitch preservation for ultra-high viewer retention.
- 🔤 **Spatial Multi-Scale Typography Roles**:
  - 👑 **Hero Word** $\rightarrow$ `Matcha World` (Giant $175\text{px}-190\text{px}$, Neon Yellow `#FFE600` / Electric Blue `#1877F2`)
  - 🏷️ **Secondary / Main Word** $\rightarrow$ `Drunk Clown` (Top-Right / Secondary, $85\text{px}-95\text{px}$)
  - ✍️ **Subtext / Gyan** $\rightarrow$ `Always in the Star` (Bottom-Right / Italic, $78\text{px}-88\text{px}$)
- 🛡️ **Zero-Overflow Dynamic Auto-Fitting**: Strictly computes character bounding boxes and downscales text dynamically to guarantee text never overflows the 1080px canvas width.
- 🎭 **Real 3D Animated Emoji Stickers**: Displays authentic high-res 3D emojis (`thinking`, `money_bag`, `fire`, `brain`, `rocket`, `light_bulb`, `chart_increasing`, etc.) with pop-in scale physics.
- 🎵 **Random Ambient BGM Auto-Ducking**: Automatically selects a fresh, non-repetitive background track from `Background Music/` on every render and ducks it at a whisper-subtle ~2.5% volume.
- 🚀 **NVIDIA NVENC Hardware Pipeline**: High-speed pipe directly into FFmpeg NVENC 60 FPS hardware encoder ($10\text{Mbps}$ bitrate) rendering a full reel in under 30 seconds.

---

## 💻 System Requirements & Prerequisites

To run this engine smoothly on any machine:

| Component | Minimum Requirement | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 / 11, Linux, macOS | Windows 11 (64-bit) |
| **Python** | Python 3.10 or 3.11 | Python 3.10+ |
| **FFmpeg** | FFmpeg with `libx264` support | FFmpeg with NVIDIA `h264_nvenc` |
| **GPU / VRAM** | CPU (Fallback enabled) | NVIDIA RTX GPU (4GB+ VRAM) |
| **RAM** | 8 GB System RAM | 16 GB System RAM |
| **Local LLM (Optional)**| Local Ollama with `qwen3.5:9b` | Running Ollama (`ollama serve`) |

---

## 🚀 Quick Start Guide

### 1. Clone & Setup Environment

```bash
git clone https://github.com/witrfaruk/TypoGraphy.git
cd TypoGraphy

# Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # On Windows
# source .venv/bin/activate # On Linux/macOS

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Verify Your Environment

Run the built-in diagnostic script to ensure all dependencies, GPU acceleration, and FFmpeg encoders are ready:

```bash
python verify_env.py
```

---

## 🎬 How to Generate Videos

### Method 1: 1-Click Launcher (Easiest)
1. Drop your voice audio file (`.wav`, `.mp3`, `.m4a`) into the **[`Audio/`](file:///C:/Users/User/OneDrive/Documents/Video/Audio)** folder.
2. Double-click **[`Generate_Video.bat`](file:///C:/Users/User/OneDrive/Documents/Video/Generate_Video.bat)**.
3. Your final 60 FPS video will appear directly in **[`Final Video/`](file:///C:/Users/User/OneDrive/Documents/Video/Final%20Video)**!

### Method 2: Command Line (CLI)

```bash
# Render latest audio in Audio/ folder at default 1.4x speed:
python run_pipeline.py

# Render a specific audio file:
python run_pipeline.py --audio "Audio/my_speech.wav"

# Custom speed (e.g. 1.3x or 1.5x):
python run_pipeline.py --speed 1.3

# Dark Canvas Mode:
python run_pipeline.py --dark

# Process all audio files in batch:
python run_pipeline.py --all
```

### Method 3: Real-Time Auto-Watcher Mode
Keep the background watcher running so videos automatically render the second you drop an audio file into `Audio/`:
- Double-click **[`Watch_Audio_Folder.bat`](file:///C:/Users/User/OneDrive/Documents/Video/Watch_Audio_Folder.bat)** or run:
```bash
python run_pipeline.py --watch
```

---

## 📁 Directory Structure

```text
WitrFaruk Video/
├── 🎙️ Audio/                    # Drop your input voice recordings here (.wav, .mp3)
├── 🎬 Final Video/              # All rendered 1080x1920 60FPS videos land here
├── ⚙️ Generate_Video.bat        # 1-Click Double-click Video Generator
│
├── 🎨 assets/                   # Project assets & media libraries
│   ├── Background Music/        # 18 BGM tracks automatically shuffled per video
│   ├── All Editable Asset/      # Top corner overlay videos & walking outro videos
│   ├── sfx/                     # Sound effect hits, whooshes, and accents
│   └── cache/                   # Auto-cleaned render buffers
│
├── 💻 code/                     # Engine source code & configurations (Tucked away)
│   ├── src/                     # Core typography engine, speech modules & renderers
│   ├── config/                  # Fonts (Matcha World, etc.), style profile & system config
│   ├── run_pipeline.py          # Master pipeline script
│   ├── verify_env.py            # Environment & GPU diagnostics
│   ├── requirements.txt         # Python dependencies
│   ├── remove_metadata.py       # Standalone video metadata sanitizer
│   └── Watch_Audio_Folder.bat   # Real-time folder watcher script
│
├── 📄 README.md                 # Project documentation & guide
├── 📜 LICENSE                   # MIT License
└── 🙈 .gitignore                # Git exclude rules
```

---

## ⚙️ Customization & CLI Options

| Flag | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `--audio <path>` | `-a` | Path to specific input audio file | Latest in `Audio/` |
| `--speed <float>`| `-s` | Video & voice tempo multiplier (pitch preserved) | `1.40` |
| `--dark` | `-d` | Renders with dark dotted grid background canvas | `False` (Clean Light) |
| `--no-trim` | - | Disables dead-air silence auto-cutting | `False` (Auto-cut ON) |
| `--bgm <path>` | - | Specify a specific BGM track instead of random | `Random` |
| `--watch` | `-w` | Continuous folder watcher for automated batching | `False` |
| `--all` | - | Processes all unrendered audio files in `Audio/` | `False` |

---

## 📄 License

MIT License. Free for commercial and personal content creation.
