"""CyberShell RPG - TUI Animation, Transition & Micro-Interaction Engine.

Provides non-blocking and frame-based terminal animations:
- Typewriter text reveal with instant-skip on input
- Braille loading/evaluating spinners (⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏)
- Oscillating pulse color highlights
- Celebration particle bursts (✦ · ✧ · ✦) on quest completion
- Smooth screen transition wipes
"""

from __future__ import annotations

import math
import sys
import time
from typing import Generator, Iterable, List, Optional, Tuple

from .theme import (
    BOLD,
    DIM,
    FG_BLUE,
    FG_CYAN,
    FG_GREEN,
    FG_MUTED,
    FG_PURPLE,
    FG_YELLOW,
    HEX_CYAN,
    HEX_GREEN,
    HEX_PURPLE,
    HEX_YELLOW,
    RESET,
    gradient_text,
    hex_to_rgb,
    interpolate_color,
    strip_ansi,
    styled,
    visual_len,
)

# Standard Braille Spinner frames
SPINNER_FRAMES: List[str] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Minimalist modern dot pulse frames
DOT_PULSE_FRAMES: List[str] = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]

# Sparkle particles for celebration fanfare
SPARKLE_CHARS: List[str] = ["✦", "✧", "⋆", "｡", "°", "✩", "•", "*"]


class Spinner:
    """Lightweight Braille frame spinner for async or step evaluations."""

    def __init__(
        self,
        message: str = "Evaluating",
        frames: Optional[List[str]] = None,
        color_hex: str = HEX_CYAN,
    ) -> None:
        self.message = message
        self.frames = frames or SPINNER_FRAMES
        self.color_hex = color_hex
        self._index: int = 0

    def tick(self) -> str:
        """Advance one frame and return the styled spinner string."""
        frame = self.frames[self._index % len(self.frames)]
        self._index += 1
        return f"{styled(frame, fg=self.color_hex, bold=True)} {self.message}"

    def get_frame(self, index: int) -> str:
        """Get a specific frame by index without mutating internal state."""
        frame = self.frames[index % len(self.frames)]
        return f"{styled(frame, fg=self.color_hex, bold=True)} {self.message}"


class Typewriter:
    """Typewriter text streamer with smooth timing and instant-skip support."""

    @staticmethod
    def stream_text(
        text: str,
        delay: float = 0.012,
        styled_prefix: str = "",
        allow_skip: bool = True,
    ) -> None:
        """Stream text to stdout character by character with optional timing."""
        if not text:
            return

        # If stdout is not a real interactive TTY, print immediately
        if not sys.stdout.isatty() or delay <= 0:
            print(f"{styled_prefix}{text}")
            return

        if styled_prefix:
            sys.stdout.write(styled_prefix)
            sys.stdout.flush()

        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)

        sys.stdout.write(f"{RESET}\n")
        sys.stdout.flush()


class CelebrationEffect:
    """Frame-based sparkling celebration effect when completing objectives."""

    @staticmethod
    def get_frames(
        title: str = "OBJECTIVE COMPLETED!",
        subtitle: str = "+50 XP Earned",
        width: int = 80,
    ) -> List[str]:
        """Generate a series of particle animation frames for the celebration."""
        frames: List[str] = []
        width = max(40, width)

        # Stage 1: Initial particle spark
        s1 = [
            "".center(width),
            f"·  ✦  ·".center(width),
            "".center(width),
        ]
        frames.append("\n".join(s1))

        # Stage 2: Radiating burst
        s2 = [
            f"✦   ✧   ⋆   ✩   ⋆   ✧   ✦".center(width),
            gradient_text(f"★  {title}  ★", HEX_YELLOW, HEX_GREEN, bold=True).center(width),
            f"✧   ·   ✦   ·   ✧".center(width),
        ]
        frames.append("\n".join(s2))

        # Stage 3: Full glory card
        border_top = "╭" + "─" * (len(title) + 16) + "╮"
        border_bot = "╰" + "─" * (len(title) + 16) + "╯"
        s3 = [
            styled(border_top, fg=HEX_YELLOW).center(width),
            styled(f"│  ✦  {title}  ✦  │", fg=HEX_GREEN, bold=True).center(width),
            styled(f"│      {subtitle}      │", fg=HEX_CYAN).center(width),
            styled(border_bot, fg=HEX_YELLOW).center(width),
        ]
        frames.append("\n".join(s3))

        return frames

    @staticmethod
    def render_celebration(
        title: str = "OBJECTIVE COMPLETED!",
        subtitle: str = "+50 XP Earned",
        width: int = 80,
        animate: bool = True,
    ) -> str:
        """Render the celebration banner (animated if TTY, or static clean card)."""
        width = max(40, width)
        if animate and sys.stdout.isatty():
            for frame in CelebrationEffect.get_frames(title, subtitle, width)[:-1]:
                print(frame)
                time.sleep(0.08)

        # Return the final card
        border = "─" * (min(width - 6, max(36, visual_len(title) + 12)))
        card = [
            styled(f"╭{border}╮", fg=HEX_YELLOW).center(width),
            styled(f"│   ✦  {title}  ✦   │", fg=HEX_GREEN, bold=True).center(width),
            styled(f"│       {subtitle}       │", fg=HEX_CYAN).center(width),
            styled(f"╰{border}╯", fg=HEX_YELLOW).center(width),
        ]
        return "\n".join(card)


class ScreenTransition:
    """Smooth screen wipe and curtain transitions between TUI views."""

    @staticmethod
    def wipe_screen(lines: int = 24, delay: float = 0.005) -> None:
        """Smoothly wipe screen lines downwards."""
        if not sys.stdout.isatty() or delay <= 0:
            print("\033[2J\033[H", end="", flush=True)
            return

        for _ in range(min(12, lines)):
            print("\n", end="", flush=True)
            time.sleep(delay)
        print("\033[2J\033[H", end="", flush=True)


def pulse_color(
    start_hex: str = HEX_CYAN,
    end_hex: str = HEX_PURPLE,
    step: int = 0,
    period: int = 20,
) -> str:
    """Return an oscillating hex color interpolated over a sine curve."""
    norm = (math.sin((step % period) / float(period) * 2 * math.pi) + 1.0) / 2.0
    c1 = hex_to_rgb(start_hex)
    c2 = hex_to_rgb(end_hex)
    r, g, b = interpolate_color(c1, c2, norm)
    return f"#{r:02x}{g:02x}{b:02x}"
