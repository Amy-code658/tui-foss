"""Subtle Ambient Effects for Byte's Linux Adventure.

Provides individually toggleable:
- Physics-based vertical falling rain with gentle light-shading
- Content-aware panel and buffer raindrops
- Calm background animations and status pulses
- Live calm rain demo watcher

Zero emoji, light blue/slate shaded, non-intrusive.
"""

from __future__ import annotations

import random
import re
import sys
import time
from typing import Any, Dict, List, Optional

try:
    from cybershell.ui.theme import (
        DIM,
        FG_CYAN,
        FG_GREEN,
        FG_MUTED,
        RESET,
        get_active_theme,
    )
except ImportError:
    FG_MUTED = "\033[90m"
    FG_CYAN = "\033[96m"
    FG_GREEN = "\033[92m"
    RESET = "\033[0m"
    DIM = "\033[2m"

# Drop characters from sharp head to soft misty tail
RAIN_HEAD_CHARS = ["│", "|", "'", "’", "·"]
RAIN_TAIL_CHARS = ["·", "˙", ",", "."]
ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# Light-shaded gentle rain colors (light sky-blue and soft pale mist)
LIGHT_HEAD_COLOR = "\033[38;2;165;210;250m"  # Soft light sky blue
LIGHT_MID_COLOR = "\033[2;38;2;135;185;235m"  # Dim light blue
LIGHT_TAIL_COLOR = "\033[2;38;2;105;155;205m" # Very dim misty blue


class AmbienceManager:
    """Manages physics-based falling rain and visual atmosphere."""

    def __init__(
        self,
        rain_enabled: bool = False,
        calm_animations: bool = False,
        ambience_enabled: bool = False,
    ) -> None:
        self.rain_enabled: bool = rain_enabled
        self.calm_animations: bool = calm_animations
        self.ambience_enabled: bool = ambience_enabled
        self._frame: int = 0
        self._last_tick: float = time.time()

        # Active falling droplets: each is {"col": int, "y": float, "speed": float, "char": str, "length": int}
        self._drops: List[Dict[str, Any]] = []
        self._init_drops(width=80, height=24, count=24)

    def _init_drops(self, width: int = 80, height: int = 24, count: int = 24) -> None:
        """Seed initial raindrops distributed vertically across screen."""
        self._drops = []
        w = max(20, width)
        h = max(10, height)
        for _ in range(count):
            self._drops.append({
                "col": random.randint(0, w - 1),
                "y": random.uniform(0, h),
                "speed": random.choice([1.0, 1.0, 1.2]),
                "char": random.choice(RAIN_HEAD_CHARS),
                "length": random.choice([2, 3, 4]),
            })

    def advance_rain(self, width: int = 80, height: int = 24) -> None:
        """Step all falling raindrops downwards by their fall speed."""
        w = max(20, width)
        h = max(10, height)

        alive_drops: List[Dict[str, Any]] = []
        for drop in self._drops:
            drop["y"] += drop["speed"]
            # Keep drops until their tail falls past the bottom
            if drop["y"] - drop["length"] < h:
                # Wrap within width if terminal was resized
                if drop["col"] < w:
                    alive_drops.append(drop)

        # Spawn new droplets at top
        target_count = max(15, min(int(w * 0.35), 40))
        while len(alive_drops) < target_count:
            alive_drops.append({
                "col": random.randint(0, w - 1),
                "y": random.uniform(-4, 0),
                "speed": random.choice([1.0, 1.0, 1.2]),
                "char": random.choice(RAIN_HEAD_CHARS),
                "length": random.choice([2, 3, 4]),
            })

        self._drops = alive_drops

    def get_rain_char_at(self, col: int, row: int, color: str = "") -> Optional[str]:
        """Return the light-shaded droplet character if a raindrop is at (col, row)."""
        if not self.rain_enabled:
            return None

        # Check all active drops
        for drop in self._drops:
            if drop["col"] == col:
                head_y = int(drop["y"])
                dist = head_y - row
                if dist == 0:
                    # Head of the drop
                    c = color or LIGHT_HEAD_COLOR
                    return f"{c}{drop['char']}{RESET}"
                elif dist == 1:
                    # Mid streak
                    c = color or LIGHT_MID_COLOR
                    return f"{DIM}{c}·{RESET}"
                elif 1 < dist <= drop["length"]:
                    # Faint tail
                    c = color or LIGHT_TAIL_COLOR
                    return f"{DIM}{c}.{RESET}"

        return None

    def toggle_rain(self) -> bool:
        """Toggle rain effect on or off. Returns new state."""
        self.rain_enabled = not self.rain_enabled
        if self.rain_enabled and not self._drops:
            self._init_drops()
        return self.rain_enabled

    def toggle_calm_animations(self) -> bool:
        """Toggle calm animations on or off. Returns new state."""
        self.calm_animations = not self.calm_animations
        return self.calm_animations

    def toggle_ambience(self) -> bool:
        """Toggle general ambience on or off. Returns new state."""
        self.ambience_enabled = not self.ambience_enabled
        return self.ambience_enabled

    def get_status_summary(self) -> str:
        """Return a readable single-line summary of ambient states."""
        r_state = "ON" if self.rain_enabled else "OFF"
        c_state = "ON" if self.calm_animations else "OFF"
        a_state = "ON" if self.ambience_enabled else "OFF"
        return f"Rain: {r_state} | Calm Anim: {c_state} | Ambience: {a_state}"

    def generate_rain_backdrop(self, width: int = 80, height: int = 10, density: float = 0.04) -> List[str]:
        """Generate subtle background rain lines with downward falling drops."""
        if not self.rain_enabled:
            return [" " * width for _ in range(height)]

        self.advance_rain(width=width, height=height)
        lines: List[str] = []
        for r in range(height):
            lines.append(self.render_rain_line(width, density=density, row=r))
        return lines

    def render_rain_line(self, width: int, density: float = 0.06, color: str = "", row: int = 0) -> str:
        """Render a single line containing falling light-shaded rain drops."""
        if not self.rain_enabled or width <= 0:
            return " " * max(0, width)

        # Make sure drops exist
        if not self._drops:
            self._init_drops(width=width, count=int(width * 0.35))

        chars: List[str] = []
        for c in range(width):
            ch = self.get_rain_char_at(c, row, color=color)
            if ch is not None:
                chars.append(ch)
            else:
                chars.append(" ")
        return "".join(chars)

    def pad_with_rain(self, text: str, width: int, color: str = "", row: int = 0) -> str:
        """Pad visible text to width, filling trailing space with falling raindrops if enabled."""
        stripped = ANSI_ESCAPE_RE.sub("", text)
        v_len = len(stripped)
        if v_len >= width:
            return text

        needed = width - v_len
        if not self.rain_enabled:
            return text + (" " * needed)

        trail_chars: List[str] = []
        for col_idx in range(v_len, width):
            ch = self.get_rain_char_at(col_idx, row, color=color)
            if ch is not None:
                trail_chars.append(ch)
            else:
                trail_chars.append(" ")

        return text + "".join(trail_chars)

    def watch_falling_rain(self, width: int = 70, height: int = 18, duration: float = 2.5) -> None:
        """Peaceful live visualizer showcasing the light-shaded rain falling down."""
        was_on = self.rain_enabled
        self.rain_enabled = True
        self._init_drops(width=width, height=height, count=int(width * 0.35))

        start_time = time.time()
        try:
            while time.time() - start_time < duration:
                self.advance_rain(width=width, height=height)
                sys.stdout.write("\033[H\033[J")
                sys.stdout.write(f"\n  {DIM}{FG_CYAN}:: AMBIENT FALLING RAIN // LIGHT SHADED ::{RESET}\n")
                for r in range(height):
                    line = self.render_rain_line(width, row=r)
                    sys.stdout.write("  " + line + "\n")
                sys.stdout.flush()
                time.sleep(0.07)
        except (KeyboardInterrupt, Exception):
            pass
        finally:
            self.rain_enabled = was_on

    def get_ambience_pulse(self) -> str:
        """Return subtle animation pulse indicator if calm animations are enabled."""
        if not self.calm_animations:
            return ""
        self._frame = (self._frame + 1) % 4
        pulses = ["~", "≈", "∽", "–"]
        return f"{DIM}{FG_MUTED}[{pulses[self._frame]}]{RESET}"


_global_ambience: Optional[AmbienceManager] = None


def get_ambience_manager() -> AmbienceManager:
    """Return application-wide AmbienceManager singleton."""
    global _global_ambience
    if _global_ambience is None:
        _global_ambience = AmbienceManager()
    return _global_ambience
