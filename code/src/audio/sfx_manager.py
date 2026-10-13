"""
SFX Timeline Director & Event Dispatcher.
Assigns rich sound effects across the entire video timeline for maximum punch and engagement.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from src.core.types import TimelinePlan, Scene, WordTiming
from src.audio.sfx_generator import SFXGenerator

SFX_DIR = Path("assets/sfx")


@dataclass
class SFXEvent:
    name: str
    timestamp: float  # In seconds
    volume: float = 0.40  # Relative volume (0.0 to 1.0)


class SFXManager:
    def __init__(self):
        self.sfx_files = SFXGenerator.generate_all_sfx(SFX_DIR)

    def plan_sfx_events(self, timeline: TimelinePlan) -> List[SFXEvent]:
        """
        Plans tasteful, high-impact SFX hits ONLY at key punchline moments and major keywords.
        Guarantees zero repetitive spamming.
        """
        events: List[SFXEvent] = []
        last_sfx_time = -10.0
        min_sfx_interval = 1.6  # Minimum 1.6s spacing between SFX hits

        # 1. Opening Hook impact whoosh
        events.append(SFXEvent(name="whoosh_fast", timestamp=0.08, volume=0.85))
        last_sfx_time = 0.08

        # High-impact trigger categories
        money_keywords = {"million", "10k", "100k", "dollar", "dollars", "money", "cash", "wealth", "rich", "profit", "cost", "$"}
        warning_keywords = {"never", "wrong", "mistake", "danger", "stop", "trap", "fail", "failure", "broke", "kill", "lose"}
        growth_keywords = {"scale", "grow", "growth", "dominate", "mastery", "10x", "winner", "elite"}
        power_keywords = {"secret", "truth", "power", "rule", "protocol"}

        for s_idx, scene in enumerate(timeline.scenes):
            s_start = scene.start_time

            # A. 3D Sticker Pop (Major visual event)
            if scene.sticker_name and (s_start - last_sfx_time) >= min_sfx_interval:
                events.append(SFXEvent(name="pop_bubble", timestamp=s_start + 0.04, volume=0.90))
                last_sfx_time = s_start + 0.04
                continue

            # B. Analyze words in scene for rare key impact words
            for w in scene.words:
                w_text = w.word.lower().strip(",.!?\"'")
                w_start = w.start

                if (w_start - last_sfx_time) < min_sfx_interval:
                    continue

                # 1. Money / Wealth -> Cash Register or Bell Ding
                if any(k in w_text for k in money_keywords) or "$" in w_text:
                    sfx = "cash_register" if ("million" in w_text or "$" in w_text) else "bell_ding"
                    events.append(SFXEvent(name=sfx, timestamp=w_start, volume=0.95))
                    last_sfx_time = w_start
                    break

                # 2. Warning / Fatal Flaw -> Warning Alert
                if any(k in w_text for k in warning_keywords):
                    events.append(SFXEvent(name="warning_alert", timestamp=w_start, volume=0.90))
                    last_sfx_time = w_start
                    break

                # 3. Growth / Dominate / 10X -> Growth Riser
                if any(k in w_text for k in growth_keywords):
                    events.append(SFXEvent(name="growth_riser", timestamp=w_start, volume=0.85))
                    last_sfx_time = w_start
                    break

                # 4. Secret / Truth / Power -> Laser Zap
                if any(k in w_text for k in power_keywords):
                    events.append(SFXEvent(name="laser_zap", timestamp=w_start, volume=0.85))
                    last_sfx_time = w_start
                    break

                # 5. Major Emphasis Hero Word (Pill Box Pop)
                if (w.is_emphasis or (scene.hero_word and w_text == scene.hero_word.lower())) and len(w_text) >= 5:
                    if (w_start - last_sfx_time) >= 2.5:  # Strict 2.5s spacing for generic hero pops
                        events.append(SFXEvent(name="pop_bubble", timestamp=w_start, volume=0.90))
                        last_sfx_time = w_start
                        break

        # Sort all events chronologically
        events.sort(key=lambda e: e.timestamp)
        return events
