"""
Core data contracts and typed schemas for the Automated Typography Video Engine.
"""
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field


class CanvasConfig(BaseModel):
    width: int = Field(default=1080, description="Video width in pixels")
    height: int = Field(default=1920, description="Video height in pixels (9:16 vertical standard)")
    fps: int = Field(default=60, description="Target framerate (30 or 60 fps)")
    aspect_ratio: str = Field(default="9:16", description="Aspect ratio tag")


class TextPositionConfig(BaseModel):
    x_alignment: str = Field(default="center", description="left, center, or right")
    y_position_percentage: float = Field(default=55.0, description="Vertical position from top (0-100%)")
    max_width_percentage: float = Field(default=85.0, description="Max width text block can occupy")


class TextAnimationConfig(BaseModel):
    reveal_mode: str = Field(
        default="word_by_word_pop", 
        description="word_by_word_pop, line_by_line, karaoke_glow, or fade_slide"
    )
    pop_scale: float = Field(default=1.15, description="Scale factor on active spoken word")
    fade_duration_ms: int = Field(default=50, description="Fade in/out duration in ms")
    max_words_per_screen: int = Field(default=4, description="Target word count chunked per visual beat")


class TypographyConfig(BaseModel):
    primary_font: str = Field(default="Anthropic", description="Main font family")
    secondary_font: str = Field(default="Nunito", description="Secondary/emphasis font family")
    fallback_font: str = Field(default="Arial", description="System fallback font")
    base_font_size: int = Field(default=76, description="Base text size in pixels (1080p canvas)")
    emphasis_font_size: int = Field(default=92, description="Emphasis text size in pixels")
    default_color: str = Field(default="#FFFFFF", description="Base text hex color")
    highlight_colors: List[str] = Field(
        default_factory=lambda: ["#FFE600", "#FF4500", "#00FFB2", "#FF007F"],
        description="Palette of accent colors for emphasized words"
    )
    stroke_width: int = Field(default=5, description="Outline stroke thickness in pixels")
    stroke_color: str = Field(default="#000000", description="Outline stroke hex color")
    shadow_depth: int = Field(default=4, description="Drop shadow depth in pixels")
    shadow_color: str = Field(default="#000000B0", description="Drop shadow color with alpha")
    box_background: Optional[str] = Field(
        default=None, 
        description="Optional pill/box background hex or rgba, e.g. rgba(0,0,0,0.6)"
    )
    position: TextPositionConfig = Field(default_factory=TextPositionConfig)
    animation: TextAnimationConfig = Field(default_factory=TextAnimationConfig)


class ColorTreatmentConfig(BaseModel):
    vignette: bool = Field(default=True, description="Apply subtle dark vignette to enhance text readability")
    darken_factor: float = Field(default=0.30, description="Background darkening overlay factor (0.0 to 1.0)")
    contrast: float = Field(default=1.1, description="Color contrast adjustment")
    saturation: float = Field(default=1.05, description="Saturation multiplier")


class VisualRhythmConfig(BaseModel):
    target_scene_duration_range: Tuple[float, float] = Field(
        default=(1.2, 3.2), 
        description="Min and max target duration for background asset cuts (seconds)"
    )
    image_transition_type: str = Field(
        default="slow_zoom_in", 
        description="slow_zoom_in, slow_zoom_out, pan_left, cut"
    )
    zoom_speed: float = Field(default=1.06, description="Ken Burns zoom multiplier")
    color_treatment: ColorTreatmentConfig = Field(default_factory=ColorTreatmentConfig)


class StyleProfile(BaseModel):
    profile_version: str = "1.0"
    name: str = "Extracted Kinetic Typography Style"
    description: str = "Distilled visual and typographic profile from reference training set"
    canvas: CanvasConfig = Field(default_factory=CanvasConfig)
    typography: TypographyConfig = Field(default_factory=TypographyConfig)
    visual_rhythm: VisualRhythmConfig = Field(default_factory=VisualRhythmConfig)
    tags: List[str] = Field(default_factory=lambda: ["kinetic", "dark_aesthetic", "punchy"])


class WordTiming(BaseModel):
    word: str
    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    probability: float = Field(default=1.0, description="Whisper confidence score")
    is_emphasis: bool = Field(default=False, description="Flagged by LLM for emphasis/pop")
    highlight_color: Optional[str] = Field(default=None, description="Accent color if emphasized")


class Scene(BaseModel):
    scene_id: int
    start_time: float
    end_time: float
    text_segment: str
    visual_concept: str = Field(default="kinetic dynamic visual", description="Core visual description")
    search_keywords: List[str] = Field(default_factory=list, description="Keywords for imagery/stickers")
    asset_source: str = Field(default="local_or_remote")
    asset_path: Optional[str] = Field(default=None)
    image_path: Optional[str] = Field(default=None, description="Path to local or cached stock photo card")
    words: List[WordTiming] = Field(default_factory=list)
    visual_effect: str = Field(default="slow_zoom_in")
    animation_style: str = Field(default="pill_box", description="pill_box, elastic_pop, marker_underline, shake_impact, stat_card")
    box_color: Optional[str] = Field(default="#FFE600", description="Background color for pill box / highlight")
    box_text_color: Optional[str] = Field(default="#000000", description="Text color inside pill box")
    sticker_name: Optional[str] = Field(default=None, description="Name of 3D sticker emoji to display")
    hero_word: Optional[str] = Field(default=None, description="Primary emphasis word for this scene")
    graphic_tag: Optional[str] = Field(default=None, description="Optional stat tag like '+10X', '$1M', '100%'")
    video_clip_path: Optional[str] = Field(default=None, description="Path to pre-recorded talking head video clip")
    is_face_clip: bool = Field(default=False, description="True if playing user face video clip")
    face_segment_start_time: float = Field(default=0.0, description="Start timestamp of continuous face video block")
    cutout_path: Optional[str] = Field(default=None, description="Path to local transparent cutout PNG of person/character")
    accent_tag: Optional[str] = Field(default=None, description="Vertical creative accent tag word")
    layout_type: str = Field(default="centered", description="'centered' or 'character_left'")
    mood: Optional[str] = Field(default="punchy")


class TimelinePlan(BaseModel):
    audio_file: str
    total_duration: float
    top_hook: str = Field(default="THE NUMBER 1 SECRET TO SUCCESS", description="AI generated viral top hook headline")
    top_badge: str = Field(default="MUST WATCH", description="Top badge category text")
    top_icon: str = Field(default="fire", description="3D sticker icon name for badge (fire, zap, warning, key)")
    bottom_subtext: str = Field(default="LISTEN CAREFULLY TILL THE END", description="Bottom letterbox subtext/CTA")
    scenes: List[Scene]
    metadata: Dict[str, Any] = Field(default_factory=dict)


