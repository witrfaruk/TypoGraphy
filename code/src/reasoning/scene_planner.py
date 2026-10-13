"""
Scene Planner & AI Motion Director.
Decomposes audio transcript into synchronized kinetic scenes matching the reference video:
- Clean 16:9 Landscape Layouts (Center Stack, Vertical Left Accent, Quotes Accent, B-Roll Overlay).
- Deep Indigo Navy (#1E1B4B) + Vibrant Royal Purple (#7C3AED) Theme.
- Selectively fetches AT MOST 5 relevant Pexels B-roll video/photo clips.
- Zero pre-recorded character cutouts.
"""
import re
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from src.core.types import StyleProfile, WordTiming, Scene, TimelinePlan
from src.reasoning.ollama_client import OllamaClient
from src.core.stock_image_service import StockImageService


def strip_unicode_emojis(text: str) -> str:
    """Removes unicode emojis and broken characters."""
    if not text:
        return ""
    clean = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\ufe0f\ud800-\udbff\udc00-\udfff]', '', text)
    clean = re.sub(r'[^\x00-\x7F]+', ' ', clean)
    return " ".join(clean.split()).strip()


STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", 
    "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", 
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", 
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", 
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", 
    "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", 
    "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", 
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", 
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", 
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
    "listen", "hey", "gonna", "wanna", "look", "know", "actually", "basically", "like", "tell"
}


def extract_visual_query_from_script(scene_text: str, context_text: str = "") -> str:
    """
    Intelligently extracts 2-3 high-impact visual search keywords from the spoken script/sentence.
    """
    clean = re.sub(r'[^a-zA-Z\s]', ' ', scene_text.lower())
    tokens = [w for w in clean.split() if len(w) > 2 and w not in STOPWORDS]
    
    if len(tokens) >= 2:
        return f"{tokens[0]} {tokens[1]}"
    elif len(tokens) == 1:
        # Check context for complementary noun
        clean_ctx = re.sub(r'[^a-zA-Z\s]', ' ', context_text.lower())
        ctx_tokens = [w for w in clean_ctx.split() if len(w) > 2 and w not in STOPWORDS and w != tokens[0]]
        if ctx_tokens:
            return f"{tokens[0]} {ctx_tokens[0]}"
        return tokens[0]
    
    # Fallback to context
    clean_ctx = re.sub(r'[^a-zA-Z\s]', ' ', context_text.lower())
    ctx_tokens = [w for w in clean_ctx.split() if len(w) > 2 and w not in STOPWORDS]
    if len(ctx_tokens) >= 2:
        return f"{ctx_tokens[0]} {ctx_tokens[1]}"
    return "focus success motivation"


class ScenePlanner:
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.client = ollama_client or OllamaClient()
        self.stock_media_svc = StockImageService()

    def plan_timeline(
        self,
        audio_file_name: str,
        full_transcript: str,
        words: List[WordTiming],
        total_duration: float,
        style_profile: StyleProfile
    ) -> TimelinePlan:
        """
        Decomposes transcript into rapid kinetic scenes matching reference aesthetic.
        """
        if not words:
            return TimelinePlan(
                audio_file=audio_file_name,
                total_duration=total_duration,
                top_hook="",
                top_badge="",
                top_icon="fire",
                bottom_subtext="",
                scenes=[]
            )

        # 1. Generate scenes with strictly <= 4 words
        raw_scenes = self._fallback_rule_based_scenes(words, full_transcript)

        # 2. Align words and assign layouts + Pexels B-roll (max 5)
        final_scenes = self._align_words_and_assign_broll(raw_scenes, words, total_duration, full_transcript)

        return TimelinePlan(
            audio_file=audio_file_name,
            total_duration=total_duration,
            top_hook="",
            top_badge="",
            top_icon="fire",
            bottom_subtext="",
            scenes=final_scenes
        )

    def _fallback_rule_based_scenes(
        self,
        words: List[WordTiming],
        full_transcript: str
    ) -> List[Dict[str, Any]]:
        """
        Groups spoken words into rapid, high-impact beats of STRICTLY 1 to 4 words per scene.
        """
        scenes = []
        if not words:
            return scenes

        conjunctions_or_breaks = {
            "and", "or", "that", "if", "to", "but", "so", "as", "before", "then",
            "in", "the", "do", "pick", "build", "stop", "care", "get", "see", "at",
            "is", "for", "on", "not", "with", "by", "from", "up", "about", "into"
        }
        
        chunks = []
        current_chunk = []
        
        for i, w in enumerate(words):
            current_chunk.append(w)
            w_text = w.word.strip()
            has_punct = any(w_text.endswith(p) for p in [".", ",", "!", "?", ";", ":"])
            
            # Punctuation break after 2+ words
            if len(current_chunk) >= 2 and has_punct:
                chunks.append(current_chunk)
                current_chunk = []
                continue
            
            # Conjunction break at 3 words
            if len(current_chunk) == 3:
                if i + 1 < len(words):
                    next_w = words[i + 1].word.lower().strip(",.!?\"'")
                    if next_w in conjunctions_or_breaks:
                        chunks.append(current_chunk)
                        current_chunk = []
                        continue

            # Hard cap: 4 words max
            if len(current_chunk) >= 4:
                chunks.append(current_chunk)
                current_chunk = []
                continue

        if current_chunk:
            chunks.append(current_chunk)

        for s_idx, chunk in enumerate(chunks, 1):
            text = " ".join(w.word for w in chunk)
            hero = max([w.word for w in chunk], key=len) if chunk else ""
            scenes.append({
                "scene_id": s_idx,
                "text_segment": strip_unicode_emojis(text),
                "hero_word": strip_unicode_emojis(hero),
                "words": chunk
            })

        return scenes

    def _align_words_and_assign_broll(
        self,
        raw_scenes: List[Dict[str, Any]],
        words: List[WordTiming],
        total_duration: float,
        full_transcript: str = ""
    ) -> List[Scene]:
        """
        Aligns words, assigns typography layout style, and dynamically fetches Pexels stock photos/media matching the script.
        """
        final_scenes: List[Scene] = []
        broll_count = 0
        max_broll = 4
        
        # Available typography layouts
        layout_styles = ["center_stack", "vertical_left", "quotes_accent", "center_stack", "two_line_flow"]
        total_raw = len(raw_scenes)

        # Calculate spaced intervals for B-roll to maintain high dynamic visual rhythm
        interval = max(3, total_raw // (max_broll + 1)) if total_raw > 4 else 2

        for s_idx, raw_s in enumerate(raw_scenes, 1):
            scene_words = raw_s.get("words", [])
            if not scene_words:
                continue

            s_start = scene_words[0].start
            s_end = scene_words[-1].end
            scene_text = " ".join(w.word for w in scene_words)

            # Choose hero word
            hero_candidates = [w.word for w in scene_words if len(w.word.strip(",.!?\"'")) >= 4]
            hero = hero_candidates[0] if hero_candidates else scene_words[0].word

            # Check if this scene qualifies for script-driven Pexels Photo / Media
            broll_media_path = None
            is_broll_scene = False
            
            # Strategically space B-roll photos according to rhythm (avoiding consecutive scenes)
            prev_was_broll = (final_scenes and (final_scenes[-1].image_path is not None or final_scenes[-1].video_clip_path is not None))
            qualifies_for_broll = (s_idx % interval == 0 or broll_count == 0) and not prev_was_broll

            if broll_count < max_broll and qualifies_for_broll:
                # Dynamically extract visual search query from script
                visual_query = extract_visual_query_from_script(scene_text, full_transcript)
                
                # Fetch stock photo / video live from Pexels API
                media_file = self.stock_media_svc.fetch_video_or_image_for_query(visual_query, s_idx)
                if media_file and media_file.exists():
                    broll_media_path = str(media_file)
                    is_broll_scene = True
                    broll_count += 1
                    print(f"  [Pexels Stock Media {broll_count}/{max_broll}] Script: \"{scene_text}\" -> Search: \"{visual_query}\" -> Saved: {media_file.name}")

            # Assign layout type
            if is_broll_scene:
                layout_type = "b_roll"
            else:
                layout_type = layout_styles[s_idx % len(layout_styles)]

            final_scenes.append(
                Scene(
                    scene_id=s_idx,
                    start_time=s_start,
                    end_time=s_end,
                    text_segment=strip_unicode_emojis(raw_s.get("text_segment", "")),
                    visual_concept="kinetic reference aesthetic",
                    words=scene_words,
                    animation_style="elastic_pop",
                    box_color="#7C3AED",
                    box_text_color="#FFFFFF",
                    sticker_name=None,
                    hero_word=strip_unicode_emojis(hero),
                    graphic_tag=None,
                    image_path=broll_media_path if broll_media_path and broll_media_path.endswith(('.jpg', '.jpeg', '.png')) else None,
                    video_clip_path=broll_media_path if broll_media_path and broll_media_path.endswith(('.mp4', '.mov')) else None,
                    layout_type=layout_type
                )
            )

        print(f"[ScenePlanner] Generated {len(final_scenes)} scenes ({broll_count} Pexels B-roll clips, {len(final_scenes) - broll_count} pure kinetic typography scenes).")
        return final_scenes
