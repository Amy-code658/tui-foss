"""CyberShell RPG - Modern TUI Design System & Theme Engine.

Inspired by Tokyo Night, Catppuccin Mocha, and Claude Code Minimal.
Provides 24-bit TrueColor palettes with automatic 256/16-color ANSI fallbacks,
color gradients, pill tags, and modern text styling.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import List, Optional, Tuple, Union

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
# Modern Color Tokens (Tokyo Night / Claude Slate Theme)
# =============================================================================

RESET: str = "\033[0m"
BOLD: str = "\033[1m"
DIM: str = "\033[2m"
ITALIC: str = "\033[3m"
UNDERLINE: str = "\033[4m"

# Palette Hex Definition
HEX_BG_DARK: str = "#1a1b26"       # Dark slate canvas
HEX_SURFACE: str = "#24283b"       # Panel / card surface
HEX_SURFACE_LIGHT: str = "#2f354f" # Selection / active element
HEX_BORDER: str = "#414868"        # Subtle hairline border
HEX_BORDER_FOCUS: str = "#7aa2f7"  # Active window border
HEX_TEXT: str = "#c0caf5"          # Crisp primary text
HEX_TEXT_MUTED: str = "#565f89"    # Secondary muted subtext
HEX_CYAN: str = "#7dcfff"          # Electric cyan (focus/prompt)
HEX_BLUE: str = "#7aa2f7"          # Tokyo blue (links/paths)
HEX_GREEN: str = "#9ece6a"         # Emerald / spring green (success)
HEX_YELLOW: str = "#e0af68"        # Warm amber (warnings/hints)
HEX_PURPLE: str = "#bb9af7"        # Soft violet / magenta (badges/rare)
HEX_RED: str = "#f7768e"           # Rose red (errors/alerts)
HEX_TEAL: str = "#1abc9c"          # Vivid teal
HEX_WHITE: str = "#ffffff"         # Pure white

# ANSI Sequences
FG_TEXT: str = fg_hex(HEX_TEXT)
FG_MUTED: str = fg_hex(HEX_TEXT_MUTED)
FG_BORDER: str = fg_hex(HEX_BORDER)
FG_BORDER_FOCUS: str = fg_hex(HEX_BORDER_FOCUS)
FG_CYAN: str = fg_hex(HEX_CYAN)
FG_BLUE: str = fg_hex(HEX_BLUE)
FG_GREEN: str = fg_hex(HEX_GREEN)
FG_YELLOW: str = fg_hex(HEX_YELLOW)
FG_PURPLE: str = fg_hex(HEX_PURPLE)
FG_RED: str = fg_hex(HEX_RED)
FG_WHITE: str = fg_hex(HEX_WHITE)

BG_SURFACE: str = bg_hex(HEX_SURFACE)
BG_SURFACE_LIGHT: str = bg_hex(HEX_SURFACE_LIGHT)
BG_BLUE: str = bg_hex(HEX_BLUE)
BG_GREEN: str = bg_hex(HEX_GREEN)
BG_PURPLE: str = bg_hex(HEX_PURPLE)
BG_CYAN: str = bg_hex(HEX_CYAN)


# =============================================================================
# Modern Styling & Pill Badges Helpers
# =============================================================================

def styled(
    text: str,
    fg: Optional[Union[str, Tuple[int, int, int]]] = None,
    bg: Optional[Union[str, Tuple[int, int, int]]] = None,
    bold: bool = False,
    dim: bool = False,
    italic: bool = False,
    underline: bool = False,
) -> str:
    """Format text with ANSI codes and styles."""
    codes: List[str] = []
    if bold:
        codes.append(BOLD)
    if dim:
        codes.append(DIM)
    if italic:
        codes.append(ITALIC)
    if underline:
        codes.append(UNDERLINE)

    if fg:
        if isinstance(fg, tuple):
            codes.append(fg_rgb(*fg))
        elif fg.startswith("#"):
            codes.append(fg_hex(fg))
        else:
            codes.append(fg)

    if bg:
        if isinstance(bg, tuple):
            codes.append(bg_rgb(*bg))
        elif bg.startswith("#"):
            codes.append(bg_hex(bg))
        else:
            codes.append(bg)

    prefix = "".join(codes)
    if not prefix:
        return str(text)
    return f"{prefix}{text}{RESET}"


def pill(
    label: str,
    fg_hex_color: str = HEX_BG_DARK,
    bg_hex_color: str = HEX_BLUE,
    bold: bool = True,
    styled_mode: bool = True,
) -> str:
    """Create a modern Lualine / Claude Code style pill tag."""
    if not styled_mode:
        return f"[{label}]"

    r_bg, g_bg, b_bg = hex_to_rgb(bg_hex_color)
    r_fg, g_fg, b_fg = hex_to_rgb(fg_hex_color)

    bold_code = BOLD if bold else ""
    return (
        f"{fg_rgb(r_bg, g_bg, b_bg)}{bg_rgb(r_bg, g_bg, b_bg)}"
        f"{fg_rgb(r_fg, g_fg, b_fg)}{bold_code} {label} "
        f"{RESET}{fg_rgb(r_bg, g_bg, b_bg)}{RESET}"
    )


def badge(
    label: str,
    color_hex: str = HEX_CYAN,
    styled_mode: bool = True,
) -> str:
    """Create a minimalist subtle bracket badge (e.g. `[ SHELL ]`)."""
    if not styled_mode:
        return f"[{label}]"
    r, g, b = hex_to_rgb(color_hex)
    return (
        f"{FG_MUTED}[{RESET}"
        f"{BOLD}{fg_rgb(r, g, b)}{label}{RESET}"
        f"{FG_MUTED}]{RESET}"
    )


# =============================================================================
# Color Interpolation & Linear Gradients
# =============================================================================

def interpolate_color(
    c1: Tuple[int, int, int],
    c2: Tuple[int, int, int],
    factor: float,
) -> Tuple[int, int, int]:
    """Linearly interpolate between two RGB colors (factor between 0.0 and 1.0)."""
    factor = max(0.0, min(1.0, factor))
    r = int(c1[0] + (c2[0] - c1[0]) * factor)
    g = int(c1[1] + (c2[1] - c1[1]) * factor)
    b = int(c1[2] + (c2[2] - c1[2]) * factor)
    return (r, g, b)


def gradient_text(
    text: str,
    start_hex: str = HEX_CYAN,
    end_hex: str = HEX_PURPLE,
    bold: bool = True,
    styled_mode: bool = True,
) -> str:
    """Render smooth 24-bit TrueColor horizontal gradient across a string."""
    if not styled_mode or not text:
        return text

    clean_chars = list(text)
    if len(clean_chars) <= 1:
        return styled(text, fg=start_hex, bold=bold)

    rgb1 = hex_to_rgb(start_hex)
    rgb2 = hex_to_rgb(end_hex)

    out: List[str] = []
    total = len(clean_chars) - 1
    bold_seq = BOLD if bold else ""

    for i, char in enumerate(clean_chars):
        if char == " ":
            out.append(" ")
            continue
        factor = i / float(total)
        r, g, b = interpolate_color(rgb1, rgb2, factor)
        out.append(f"{bold_seq}{fg_rgb(r, g, b)}{char}")

    out.append(RESET)
    return "".join(out)
