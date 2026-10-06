"""CyberShell RPG - Modern TUI Design System & Theme Engine.

Inspired by Tokyo Night, Catppuccin Mocha, and Claude Code Minimal.
Provides 24-bit TrueColor palettes with automatic 256/16-color ANSI fallbacks,
color gradients, pill tags, and modern text styling.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a string."""
    return ANSI_ESCAPE_RE.sub("", str(text))


def visual_len(text: str) -> int:
    """Return visible terminal display width of text, ignoring ANSI escape codes."""
    clean = strip_ansi(text)
    w = 0
    for char in clean:
        eaw = unicodedata.east_asian_width(char)
        if eaw in ('F', 'W'):
            w += 2
        else:
            # Emoji fallback: many non-EAW chars are still wide emojis
            if ord(char) >= 0x1F000:
                w += 2
            else:
                w += 1
    return w


# =============================================================================
# Color Conversions (Hex, RGB, TrueColor, 256 Fallbacks)
# =============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color (e.g. '#7aa2f7' or '7aa2f7') to (R, G, B) tuple."""
    clean = hex_color.lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) != 6:
        return (200, 200, 200)
    try:
        return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))
    except ValueError:
        return (200, 200, 200)


def rgb_to_ansi256(r: int, g: int, b: int) -> int:
    """Approximate an RGB color to the closest standard ANSI 256 color code."""
    # Greyscale ramp check (code 232 to 255)
    if abs(r - g) < 8 and abs(g - b) < 8:
        grey = (r + g + b) // 3
        if grey < 8:
            return 16
        if grey > 248:
            return 231
        return 232 + int(((grey - 8) / 240) * 23)

    # 6x6x6 color cube (code 16 to 231)
    r_idx = int((r / 255) * 5 + 0.5)
    g_idx = int((g / 255) * 5 + 0.5)
    b_idx = int((b / 255) * 5 + 0.5)
    return 16 + (36 * r_idx) + (6 * g_idx) + b_idx


def supports_truecolor() -> bool:
    """Detect if current terminal environment supports 24-bit TrueColor."""
    colorterm = os.environ.get("COLORTERM", "").lower()
    if colorterm in ("truecolor", "24bit"):
        return True
    term = os.environ.get("TERM", "").lower()
    if any(x in term for x in ("kitty", "alacritty", "iterm", "wezterm", "xterm-256color")):
        return True
    # Default to TrueColor for modern terminals
    return True


def fg_rgb(r: int, g: int, b: int) -> str:
    """Generate ANSI foreground escape sequence."""
    if supports_truecolor():
        return f"\033[38;2;{r};{g};{b}m"
    return f"\033[38;5;{rgb_to_ansi256(r, g, b)}m"


def bg_rgb(r: int, g: int, b: int) -> str:
    """Generate ANSI background escape sequence."""
    if supports_truecolor():
        return f"\033[48;2;{r};{g};{b}m"
    return f"\033[48;5;{rgb_to_ansi256(r, g, b)}m"


def fg_hex(hex_str: str) -> str:
    """Generate ANSI foreground escape sequence from hex color."""
    r, g, b = hex_to_rgb(hex_str)
    return fg_rgb(r, g, b)


def bg_hex(hex_str: str) -> str:
    """Generate ANSI background escape sequence from hex color."""
    r, g, b = hex_to_rgb(hex_str)
    return bg_rgb(r, g, b)


# =============================================================================
# Modern Color Tokens & Multi-Theme System
# =============================================================================

RESET: str = "\033[0m"
BOLD: str = "\033[1m"
DIM: str = "\033[2m"
ITALIC: str = "\033[3m"
UNDERLINE: str = "\033[4m"


@dataclass
class Theme:
    """Developer-inspired color theme definition."""

    id: str
    display_name: str
    is_light: bool = False
    bg_dark: str = "#1a1b26"
    surface: str = "#24283b"
    surface_light: str = "#2f354f"
    border: str = "#414868"
    border_focus: str = "#7aa2f7"
    text: str = "#c0caf5"
    text_muted: str = "#565f89"
    cyan: str = "#7dcfff"
    blue: str = "#7aa2f7"
    green: str = "#9ece6a"
    yellow: str = "#e0af68"
    purple: str = "#bb9af7"
    red: str = "#f7768e"
    teal: str = "#1abc9c"
    white: str = "#ffffff"

    @property
    def fg_cyan(self) -> str:
        return fg_hex(self.cyan)

    @property
    def fg_blue(self) -> str:
        return fg_hex(self.blue)

    @property
    def fg_green(self) -> str:
        return fg_hex(self.green)

    @property
    def fg_yellow(self) -> str:
        return fg_hex(self.yellow)

    @property
    def fg_purple(self) -> str:
        return fg_hex(self.purple)

    @property
    def fg_red(self) -> str:
        return fg_hex(self.red)

    @property
    def fg_white(self) -> str:
        return fg_hex(self.white)

    @property
    def fg_teal(self) -> str:
        return fg_hex(self.teal)

    @property
    def fg_text(self) -> str:
        return fg_hex(self.text)

    @property
    def fg_muted(self) -> str:
        return fg_hex(self.text_muted)

    @property
    def fg_border(self) -> str:
        return fg_hex(self.border)

    @property
    def fg_border_focus(self) -> str:
        return fg_hex(self.border_focus)

    @property
    def bg_surface(self) -> str:
        return bg_hex(self.surface)

    @property
    def bg_dark_ansi(self) -> str:
        return bg_hex(self.bg_dark)


THEMES: Dict[str, Theme] = {
    "tokyo-night": Theme(
        id="tokyo-night",
        display_name="Tokyo Night",
        is_light=False,
        bg_dark="#1a1b26", surface="#24283b", surface_light="#2f354f",
        border="#414868", border_focus="#7aa2f7",
        text="#c0caf5", text_muted="#565f89",
        cyan="#7dcfff", blue="#7aa2f7", green="#9ece6a",
        yellow="#e0af68", purple="#bb9af7", red="#f7768e",
        teal="#1abc9c", white="#ffffff",
    ),
    "dracula": Theme(
        id="dracula",
        display_name="Dracula",
        is_light=False,
        bg_dark="#282a36", surface="#343746", surface_light="#44475a",
        border="#6272a4", border_focus="#bd93f9",
        text="#f8f8f2", text_muted="#929ac4",
        cyan="#8be9fd", blue="#6272a4", green="#50fa7b",
        yellow="#f1fa8c", purple="#bd93f9", red="#ff5555",
        teal="#8be9fd", white="#ffffff",
    ),
    "catppuccin-mocha": Theme(
        id="catppuccin-mocha",
        display_name="Catppuccin Mocha",
        is_light=False,
        bg_dark="#1e1e2e", surface="#25263a", surface_light="#313244",
        border="#45475a", border_focus="#89b4fa",
        text="#cdd6f4", text_muted="#7f849c",
        cyan="#89dceb", blue="#89b4fa", green="#a6e3a1",
        yellow="#f9e2af", purple="#cba6f7", red="#f38ba8",
        teal="#94e2d5", white="#ffffff",
    ),
    "catppuccin-latte": Theme(
        id="catppuccin-latte",
        display_name="Catppuccin Latte (Light)",
        is_light=True,
        bg_dark="#eff1f5", surface="#e6e9ef", surface_light="#ccd0da",
        border="#bcc0cc", border_focus="#1e66f5",
        text="#4c4f69", text_muted="#8c8fa1",
        cyan="#04a5e5", blue="#1e66f5", green="#40a02b",
        yellow="#df8e1d", purple="#8839ef", red="#d20f39",
        teal="#179299", white="#202020",
    ),
    "nord": Theme(
        id="nord",
        display_name="Nord",
        is_light=False,
        bg_dark="#2e3440", surface="#3b4252", surface_light="#434c5e",
        border="#4c566a", border_focus="#88c0d0",
        text="#eceff4", text_muted="#7b88a1",
        cyan="#88c0d0", blue="#81a1c1", green="#a3be8c",
        yellow="#ebcb8b", purple="#b48ead", red="#bf616a",
        teal="#8fbcbb", white="#ffffff",
    ),
    "everforest": Theme(
        id="everforest",
        display_name="Everforest",
        is_light=False,
        bg_dark="#2d353b", surface="#343f44", surface_light="#3d484d",
        border="#475258", border_focus="#a7c080",
        text="#d3c6aa", text_muted="#7a8478",
        cyan="#7fbbb3", blue="#83c092", green="#a7c080",
        yellow="#dbbc7f", purple="#d699b6", red="#e67e80",
        teal="#83c092", white="#ffffff",
    ),
    "ocean": Theme(
        id="ocean",
        display_name="Ocean",
        is_light=False,
        bg_dark="#0f172a", surface="#1e293b", surface_light="#334155",
        border="#475569", border_focus="#0ea5e9",
        text="#f8fafc", text_muted="#64748b",
        cyan="#38bdf8", blue="#0ea5e9", green="#0d9488",
        yellow="#eab308", purple="#a855f7", red="#f43f5e",
        teal="#14b8a6", white="#ffffff",
    ),
}
