"""
Kinetic Typography Spatial Layout Engine with Custom Requested Fonts:
- Main Word (Hero / Highlight): Dantene (config/fonts/Dantene.otf)
- Normal Word (Body / Content): Retro Romance (config/fonts/Retro Romance.ttf)
- Supporting Word (Connectors / Articles): Sprucken (config/fonts/Sprucken_PERSONAL_USE_ONLY.otf)

Features:
- Canvas: 1920x1080 (16:9 Landscape @ 60 FPS).
- Background: Soothing Light Pastel Lilac (#ECE8F6).
- Strict Word Limit: 1 to 4 words per scene.
- Zero-clipping exact glyph bounding box positioning.
- Layouts: Center Stack, Vertical Left Word (90° rotated), Quotes Accent, Pexels B-Roll.
"""
import os
import math
import random
import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from src.core.types import WordTiming, Scene

FONTS_DIR = Path("config/fonts")

# Custom fonts requested by user
FONT_MAIN = "Dantene.otf"
FONT_NORMAL = "Retro Romance.ttf"
FONT_SUPPORTING = "Sprucken_PERSONAL_USE_ONLY.otf"

CONNECTORS = {
    "a", "an", "the", "in", "to", "for", "of", "at", "by", "as", "if",
    "or", "and", "but", "so", "is", "it", "on", "with", "from", "up",
    "about", "into", "that", "you", "your", "my", "me", "do", "before", "then"
}


def strip_unicode_emojis(text: str) -> str:
    """Removes unicode emojis and broken characters."""
    if not text:
        return ""
    clean = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\ufe0f\ud800-\udbff\udc00-\udfff]', '', text)
    clean = re.sub(r'[^\x00-\x7F]+', ' ', clean)
    return " ".join(clean.split()).strip()


@dataclass
class VisualWord:
    text: str
    start_time: float
    end_time: float
    role: str  # 'hero', 'secondary', 'connector', 'vertical'
    font_path: str
    font_size: int
    color: str
    position: Tuple[int, int]
    alignment: str = "center"
    rotation: float = 0.0
    animation_style: str = "elastic_pop"
    box_color: Optional[str] = None
    box_text_color: Optional[str] = None


@dataclass
class KineticFrameComposition:
    chunk_id: int
    start_time: float
    end_time: float
    animation_style: str
    box_color: str
    box_text_color: str
    words: List[VisualWord] = field(default_factory=list)
    layout_type: str = "center_stack"
    video_clip_path: Optional[str] = None
    image_path: Optional[str] = None
    is_broll: bool = False


def get_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """Loads a TTF/OTF font from config/fonts with fallback."""
    ttf_path = FONTS_DIR / font_name
    if ttf_path.exists():
        try:
            return ImageFont.truetype(str(ttf_path), size)
        except Exception:
            pass
    # Fallback options
    for preferred in [FONT_MAIN, FONT_NORMAL, FONT_SUPPORTING, "Poppins-ExtraBold.ttf", "Kanit-ExtraBold.ttf"]:
        p = FONTS_DIR / preferred
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
    for f in FONTS_DIR.glob("*.*"):
        if f.suffix.lower() in [".ttf", ".otf"]:
            try:
                return ImageFont.truetype(str(f), size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_full_canvas_background(width: int = 1920, height: int = 1080) -> Image.Image:
    """
    Creates the clean, modern pastel lilac background matching the reference video (#ECE8F6).
    """
    canvas = Image.new("RGB", (width, height), (236, 232, 246))
    return canvas


class KineticLayoutPlanner:
    def __init__(self, dark_mode: bool = False):
        self.canvas_w = 1920
        self.canvas_h = 1080
        
        # Exact fonts requested by user
        self.font_main = FONT_MAIN
        self.font_normal = FONT_NORMAL
        self.font_supporting = FONT_SUPPORTING

        # Color palette
        self.color_navy = "#1E1B4B"        # Deep Indigo Navy (Normal word)
        self.color_purple = "#7C3AED"      # Vibrant Royal Purple (Main word)
        self.color_supporting = "#4C4675"  # Soft Violet Slate (Supporting word)
        self.color_white = "#FFFFFF"       # Crisp White (B-Roll normal word)
        self.color_broll_purple = "#A78BFA" # Soft Violet Purple (B-Roll main word)

    def _resolve_word_style(
        self,
        word: WordTiming,
        hero_target: Optional[WordTiming],
        is_broll: bool = False
    ) -> Tuple[str, str, str, int]:
        """
        Determines the role, font, color, and size for a word based on user requirements:
        - Main word -> Dantene.otf (Purple)
        - Normal word -> Retro Romance.ttf (Navy / White)
        - Supporting word -> Sprucken.otf (Supporting Slate)
        """
        w_clean = word.word.lower().strip(",.!?\"'")
        is_hero = (word == hero_target or word.is_emphasis or w_clean in {
            "stop", "chasing", "insanely", "good", "sales", "coding", "marketing",
            "sweeping", "floors", "best", "business", "starting", "dominate",
            "game", "skill", "reputation", "system", "number", "one"
        })

        if is_hero:
            role = "hero"
            font = self.font_main
            color = self.color_broll_purple if is_broll else self.color_purple
            size = 160
        elif w_clean in CONNECTORS:
            role = "connector"
            font = self.font_supporting
            color = "#DDD6FE" if is_broll else self.color_supporting
            size = 125
        else:
            role = "secondary"
            font = self.font_normal
            color = self.color_white if is_broll else self.color_navy
            size = 135

        return role, font, color, size

    def plan_scene_composition(
        self,
        scene: Scene,
        scene_idx: int
    ) -> KineticFrameComposition:
        """
        Plans 16:9 spatial layout for 1-4 words matching the reference video style.
        """
        words_chunk = scene.words
        if not words_chunk:
            return KineticFrameComposition(
                chunk_id=scene_idx,
                start_time=scene.start_time,
                end_time=scene.end_time,
                animation_style="elastic_pop",
                box_color=self.color_purple,
                box_text_color="#FFFFFF",
                layout_type="center_stack"
            )

        start_t = words_chunk[0].start
        end_t = words_chunk[-1].end
        n_words = min(4, len(words_chunk))
        words_subset = words_chunk[:n_words]

        layout_type = getattr(scene, "layout_type", "center_stack")
        is_broll = bool(scene.video_clip_path or scene.image_path)

        # Resolve hero target word
        hero_target = None
        if scene.hero_word:
            for w in words_subset:
                if w.word.lower().strip(",.!?\"'") == scene.hero_word.lower().strip(",.!?\"'"):
                    hero_target = w
                    break
        if not hero_target:
            # Pick non-connector longest word
            non_conn = [w for w in words_subset if w.word.lower().strip(",.!?\"'") not in CONNECTORS]
            hero_target = max(non_conn, key=lambda w: len(w.word)) if non_conn else words_subset[0]

        if is_broll:
            visual_words = self._layout_broll(words_subset, hero_target)
        elif layout_type == "vertical_left" and n_words >= 3:
            visual_words = self._layout_vertical_left(words_subset, hero_target)
        elif layout_type == "quotes_accent":
            visual_words = self._layout_quotes_accent(words_subset, hero_target)
        elif layout_type == "two_line_flow" and n_words >= 3:
            visual_words = self._layout_two_line_flow(words_subset, hero_target)
        else:
            visual_words = self._layout_center_stack(words_subset, hero_target)

        return KineticFrameComposition(
            chunk_id=scene_idx,
            start_time=start_t,
            end_time=end_t,
            animation_style="elastic_pop",
            box_color=self.color_purple,
            box_text_color="#FFFFFF",
            words=visual_words,
            layout_type=layout_type,
            video_clip_path=scene.video_clip_path,
            image_path=scene.image_path,
            is_broll=is_broll
        )

    def _layout_center_stack(
        self,
        words: List[WordTiming],
        hero_target: WordTiming
    ) -> List[VisualWord]:
        """
        Classic reference video center stack with user requested fonts:
        Line 1: Hero word (Dantene, Purple).
        Line 2: Normal / Supporting words (Retro Romance / Sprucken).
        """
        n = len(words)
        visual_words = []

        if n == 1:
            w = words[0]
            role, font, color, size = self._resolve_word_style(w, hero_target)
            visual_words.append(
                VisualWord(
                    text=strip_unicode_emojis(w.word),
                    start_time=w.start,
                    end_time=w.end,
                    role=role,
                    font_path=font,
                    font_size=size + 15,
                    color=color,
                    position=(960, 540),
                    alignment="center"
                )
            )
            return visual_words

        if n == 2:
            w0, w1 = words[0], words[1]
            r0, f0, c0, s0 = self._resolve_word_style(w0, hero_target)
            r1, f1, c1, s1 = self._resolve_word_style(w1, hero_target)
            
            visual_words.append(
                VisualWord(
                    text=strip_unicode_emojis(w0.word),
                    start_time=w0.start,
                    end_time=w0.end,
                    role=r0,
                    font_path=f0,
                    font_size=s0,
                    color=c0,
                    position=(960, 440),
                    alignment="center"
                )
            )
            visual_words.append(
                VisualWord(
                    text=strip_unicode_emojis(w1.word),
                    start_time=w1.start,
                    end_time=w1.end,
                    role=r1,
                    font_path=f1,
                    font_size=s1,
                    color=c1,
                    position=(960, 620),
                    alignment="center"
                )
            )
            return visual_words

        # 3 or 4 words: Split into 2 lines
        split_idx = 1 if words[0] == hero_target else (2 if n == 4 else 1)
        line1_words = words[:split_idx]
        line2_words = words[split_idx:]

        # Line 1 measurement
        l1_boxes = []
        for w in line1_words:
            role, font_name, color, size = self._resolve_word_style(w, hero_target)
            t = strip_unicode_emojis(w.word)
            f = get_font(font_name, size)
            bbox = f.getbbox(t)
            tw = max(10, bbox[2] - bbox[0])
            l1_boxes.append((w, t, role, font_name, color, size, tw))

        tot_w1 = sum(b[6] for b in l1_boxes) + (len(l1_boxes) - 1) * 35
        curr_x1 = 960 - (tot_w1 // 2)

        for w, t, role, font_name, color, size, tw in l1_boxes:
            visual_words.append(
                VisualWord(
                    text=t,
                    start_time=w.start,
                    end_time=w.end,
                    role=role,
                    font_path=font_name,
                    font_size=size,
                    color=color,
                    position=(curr_x1 + (tw // 2), 430),
                    alignment="center"
                )
            )
            curr_x1 += tw + 35

        # Line 2 measurement
        l2_boxes = []
        for w in line2_words:
            role, font_name, color, size = self._resolve_word_style(w, hero_target)
            t = strip_unicode_emojis(w.word)
            f = get_font(font_name, size)
            bbox = f.getbbox(t)
            tw = max(10, bbox[2] - bbox[0])
            l2_boxes.append((w, t, role, font_name, color, size, tw))

        tot_w2 = sum(b[6] for b in l2_boxes) + (len(l2_boxes) - 1) * 30
        curr_x2 = 960 - (tot_w2 // 2)

        for w, t, role, font_name, color, size, tw in l2_boxes:
            visual_words.append(
                VisualWord(
                    text=t,
                    start_time=w.start,
                    end_time=w.end,
                    role=role,
                    font_path=font_name,
                    font_size=size,
                    color=color,
                    position=(curr_x2 + (tw // 2), 620),
                    alignment="center"
                )
            )
            curr_x2 += tw + 30

        return visual_words

    def _layout_vertical_left(
        self,
        words: List[WordTiming],
        hero_target: WordTiming
    ) -> List[VisualWord]:
        """
        Signature vertical word layout:
        Left: 1 vertical word rotated 90 degrees in Dantene (Purple).
        Right: 2-3 lines stacked in Retro Romance / Sprucken.
        """
        visual_words = []
        vert_word = words[0]
        right_words = words[1:]

        # Left vertical word in Dantene
        vert_text = strip_unicode_emojis(vert_word.word)
        visual_words.append(
            VisualWord(
                text=vert_text,
                start_time=vert_word.start,
                end_time=vert_word.end,
                role="hero",
                font_path=self.font_main,
                font_size=140,
                color=self.color_purple,
                position=(600, 540),
                alignment="center",
                rotation=90.0
            )
        )

        # Right lines
        if len(right_words) == 2:
            w0, w1 = right_words[0], right_words[1]
            r0, f0, c0, s0 = self._resolve_word_style(w0, hero_target)
            r1, f1, c1, s1 = self._resolve_word_style(w1, hero_target)
            
            visual_words.append(
                VisualWord(
                    text=strip_unicode_emojis(w0.word),
                    start_time=w0.start,
                    end_time=w0.end,
                    role=r0,
                    font_path=f0,
                    font_size=s0,
                    color=c0,
                    position=(1050, 440),
                    alignment="left"
                )
            )
            visual_words.append(
                VisualWord(
                    text=strip_unicode_emojis(w1.word),
                    start_time=w1.start,
                    end_time=w1.end,
                    role=r1,
                    font_path=f1,
                    font_size=s1,
                    color=c1,
                    position=(1050, 620),
                    alignment="left"
                )
            )
        else:
            w0, w1, w2 = right_words[0], right_words[1], right_words[2]
            r0, f0, c0, s0 = self._resolve_word_style(w0, hero_target)
            r2, f2, c2, s2 = self._resolve_word_style(w2, hero_target)
            
            visual_words.append(
                VisualWord(
                    text=strip_unicode_emojis(f"{w0.word} {w1.word}"),
                    start_time=w0.start,
                    end_time=w1.end,
                    role=r0,
                    font_path=f0,
                    font_size=s0 - 10,
                    color=c0,
                    position=(1040, 440),
                    alignment="left"
                )
            )
            visual_words.append(
                VisualWord(
                    text=strip_unicode_emojis(w2.word),
                    start_time=w2.start,
                    end_time=w2.end,
                    role=r2,
                    font_path=f2,
                    font_size=s2,
                    color=c2,
                    position=(1040, 620),
                    alignment="left"
                )
            )

        return visual_words

    def _layout_quotes_accent(
        self,
        words: List[WordTiming],
        hero_target: WordTiming
    ) -> List[VisualWord]:
        """
        Quotes layout: hero keyword wrapped in quotes in Dantene.
        """
        visual_words = []
        for w in words:
            t = strip_unicode_emojis(w.word)
            role, font_name, color, size = self._resolve_word_style(w, hero_target)
            if w == hero_target:
                t = f'"{t.strip(",.!?")}"'
                font_name = self.font_main
                color = self.color_purple
                size = 155
                role = "hero"

            visual_words.append(
                VisualWord(
                    text=t,
                    start_time=w.start,
                    end_time=w.end,
                    role=role,
                    font_path=font_name,
                    font_size=size,
                    color=color,
                    position=(0, 0),
                    alignment="center"
                )
            )

        if len(visual_words) <= 2:
            for i, vw in enumerate(visual_words):
                vw.position = (960, 440 + i * 180)
        else:
            vw0 = visual_words[0]
            vw0.position = (960, 430)
            rem_words = visual_words[1:]
            
            widths = []
            for vw in rem_words:
                f = get_font(vw.font_path, vw.font_size)
                bbox = f.getbbox(vw.text)
                widths.append(max(10, bbox[2] - bbox[0]))
                
            tot_w = sum(widths) + (len(rem_words) - 1) * 30
            curr_x = 960 - (tot_w // 2)
            for i, vw in enumerate(rem_words):
                vw.position = (curr_x + (widths[i] // 2), 620)
                curr_x += widths[i] + 30

        return visual_words

    def _layout_two_line_flow(
        self,
        words: List[WordTiming],
        hero_target: WordTiming
    ) -> List[VisualWord]:
        return self._layout_center_stack(words, hero_target)

    def _layout_broll(
        self,
        words: List[WordTiming],
        hero_target: WordTiming
    ) -> List[VisualWord]:
        """
        Pexels B-Roll Video scene layout with Dantene (Hero), Retro Romance (Normal), Sprucken (Supporting).
        """
        visual_words = []
        n = len(words)

        if n <= 2:
            for i, w in enumerate(words):
                role, font_name, color, size = self._resolve_word_style(w, hero_target, is_broll=True)
                visual_words.append(
                    VisualWord(
                        text=strip_unicode_emojis(w.word),
                        start_time=w.start,
                        end_time=w.end,
                        role=role,
                        font_path=font_name,
                        font_size=size,
                        color=color,
                        position=(960, 450 + i * 170),
                        alignment="center"
                    )
                )
            return visual_words

        # 3 or 4 words
        split_idx = 2 if n == 4 else 1
        line1 = words[:split_idx]
        line2 = words[split_idx:]

        # Line 1
        l1_boxes = []
        for w in line1:
            role, font_name, color, size = self._resolve_word_style(w, hero_target, is_broll=True)
            t = strip_unicode_emojis(w.word)
            f = get_font(font_name, size)
            bbox = f.getbbox(t)
            tw = max(10, bbox[2] - bbox[0])
            l1_boxes.append((w, t, role, font_name, color, size, tw))

        tot_w1 = sum(b[6] for b in l1_boxes) + (len(l1_boxes) - 1) * 30
        curr_x1 = 960 - (tot_w1 // 2)

        for w, t, role, font_name, color, size, tw in l1_boxes:
            visual_words.append(
                VisualWord(
                    text=t,
                    start_time=w.start,
                    end_time=w.end,
                    role=role,
                    font_path=font_name,
                    font_size=size,
                    color=color,
                    position=(curr_x1 + (tw // 2), 440),
                    alignment="center"
                )
            )
            curr_x1 += tw + 30

        # Line 2
        l2_boxes = []
        for w in line2:
            role, font_name, color, size = self._resolve_word_style(w, hero_target, is_broll=True)
            t = strip_unicode_emojis(w.word)
            f = get_font(font_name, size)
            bbox = f.getbbox(t)
            tw = max(10, bbox[2] - bbox[0])
            l2_boxes.append((w, t, role, font_name, color, size, tw))

        tot_w2 = sum(b[6] for b in l2_boxes) + (len(l2_boxes) - 1) * 30
        curr_x2 = 960 - (tot_w2 // 2)

        for w, t, role, font_name, color, size, tw in l2_boxes:
            visual_words.append(
                VisualWord(
                    text=t,
                    start_time=w.start,
                    end_time=w.end,
                    role=role,
                    font_path=font_name,
                    font_size=size,
                    color=color,
                    position=(curr_x2 + (tw // 2), 620),
                    alignment="center"
                )
            )
            curr_x2 += tw + 30

        return visual_words
