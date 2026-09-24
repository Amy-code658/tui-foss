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
    "gruvbox": Theme(
        id="gruvbox",
        display_name="Gruvbox Dark",
        is_light=False,
        bg_dark="#282828", surface="#32302f", surface_light="#3c3836",
        border="#504945", border_focus="#fabd2f",
        text="#ebdbb2", text_muted="#928374",
        cyan="#8ec07c", blue="#83a598", green="#b8bb26",
        yellow="#fabd2f", purple="#d3869b", red="#fb4934",
        teal="#8ec07c", white="#ffffff",
    ),
    "solarized-dark": Theme(
        id="solarized-dark",
        display_name="Solarized Dark",
        is_light=False,
        bg_dark="#002b36", surface="#073642", surface_light="#0d4250",
        border="#586e75", border_focus="#268bd2",
        text="#839496", text_muted="#657b83",
        cyan="#2aa198", blue="#268bd2", green="#859900",
        yellow="#b58900", purple="#6c71c4", red="#dc322f",
        teal="#2aa198", white="#fdf6e3",
    ),
    "solarized-light": Theme(
        id="solarized-light",
        display_name="Solarized Light",
        is_light=True,
        bg_dark="#fdf6e3", surface="#eee8d5", surface_light="#e0dac5",
        border="#93a1a1", border_focus="#268bd2",
        text="#586e75", text_muted="#839496",
        cyan="#2aa198", blue="#268bd2", green="#859900",
        yellow="#b58900", purple="#6c71c4", red="#dc322f",
        teal="#2aa198", white="#002b36",
    ),
    "one-dark": Theme(
        id="one-dark",
        display_name="One Dark",
        is_light=False,
        bg_dark="#282c34", surface="#2f343e", surface_light="#353b45",
        border="#4b5263", border_focus="#61afef",
        text="#abb2bf", text_muted="#5c6370",
        cyan="#56b6c2", blue="#61afef", green="#98c379",
        yellow="#e5c07b", purple="#c678dd", red="#e06c75",
        teal="#56b6c2", white="#ffffff",
    ),
    "monokai": Theme(
        id="monokai",
        display_name="Monokai",
        is_light=False,
        bg_dark="#272822", surface="#32342b", surface_light="#3e3d32",
        border="#49483e", border_focus="#66d9ef",
        text="#f8f8f2", text_muted="#75715e",
        cyan="#66d9ef", blue="#66d9ef", green="#a6e22e",
        yellow="#e6db74", purple="#ae81ff", red="#f92672",
        teal="#a6e22e", white="#ffffff",
    ),
    "rose-pine": Theme(
        id="rose-pine",
        display_name="Rosé Pine",
        is_light=False,
        bg_dark="#191724", surface="#1f1d2e", surface_light="#26233a",
        border="#403d52", border_focus="#c4a7e7",
        text="#e0def4", text_muted="#6e6a86",
        cyan="#9ccfd8", blue="#31748f", green="#ebbcba",
        yellow="#f6c177", purple="#c4a7e7", red="#eb6f92",
        teal="#9ccfd8", white="#ffffff",
    ),
    "foss": Theme(
        id="foss",
        display_name="FOSS",
        is_light=False,
        bg_dark="#161c28", surface="#1e2638", surface_light="#28344d",
        border="#3b527a", border_focus="#58a6ff",
        text="#e6edf3", text_muted="#7d8ea6",
        cyan="#79c0ff", blue="#58a6ff", green="#7ee787",
        yellow="#f1e05a", purple="#bc8cff", red="#ff7b72",
        teal="#56d364", white="#ffffff",
    ),
    "pastel-lavender": Theme(
        id="pastel-lavender",
        display_name="Pastel Lavender",
        is_light=False,
        bg_dark="#1b1725", surface="#241f32", surface_light="#322b44",
        border="#5c4d7d", border_focus="#d4b5ff",
        text="#f4eefa", text_muted="#9987b5",
        cyan="#b5e2fa", blue="#b8c0ff", green="#bbf2c0",
        yellow="#ffdfba", purple="#d4b5ff", red="#ffb3ba",
        teal="#b5e2fa", white="#ffffff",
    ),
    "pastel-sakura": Theme(
        id="pastel-sakura",
        display_name="Pastel Sakura",
        is_light=False,
        bg_dark="#211a21", surface="#2d222e", surface_light="#3d3040",
        border="#6e4f73", border_focus="#ffb7c5",
        text="#fef2f6", text_muted="#a88aa4",
        cyan="#bfe3e2", blue="#c4bbf0", green="#c3e6cb",
        yellow="#ffe5b4", purple="#e8b4e8", red="#ff9aa2",
        teal="#bfe3e2", white="#ffffff",
    ),
    "pastel-mint": Theme(
        id="pastel-mint",
        display_name="Pastel Mint",
        is_light=False,
        bg_dark="#15211e", surface="#1d2d29", surface_light="#283e38",
        border="#446860", border_focus="#8ee4af",
        text="#eef8f5", text_muted="#7da69c",
        cyan="#a0e7e5", blue="#b4d4f8", green="#98dfaf",
        yellow="#faedcb", purple="#d0bdf4", red="#ffabab",
        teal="#a0e7e5", white="#ffffff",
    ),
    "pastel-peach": Theme(
        id="pastel-peach",
        display_name="Pastel Peach",
        is_light=False,
        bg_dark="#241c19", surface="#322622", surface_light="#44342e",
        border="#74544b", border_focus="#ffb599",
        text="#fef3ee", text_muted="#a6847a",
        cyan="#b5e6e8", blue="#c0d6f9", green="#cbe8ba",
        yellow="#ffe8a3", purple="#dfc7f7", red="#ffaba0",
        teal="#b5e6e8", white="#ffffff",
    ),
}

_active_theme_id: str = "tokyo-night"


def list_themes() -> List[Theme]:
    """Return list of all registered color themes."""
    return list(THEMES.values())


def get_active_theme() -> Theme:
    """Return currently active color theme."""
    return THEMES.get(_active_theme_id, THEMES["tokyo-night"])


# Dynamic module-level hex & ANSI sequences
HEX_BG_DARK: str = THEMES["tokyo-night"].bg_dark
HEX_SURFACE: str = THEMES["tokyo-night"].surface
HEX_SURFACE_LIGHT: str = THEMES["tokyo-night"].surface_light
HEX_BORDER: str = THEMES["tokyo-night"].border
HEX_BORDER_FOCUS: str = THEMES["tokyo-night"].border_focus
HEX_TEXT: str = THEMES["tokyo-night"].text
HEX_TEXT_MUTED: str = THEMES["tokyo-night"].text_muted
HEX_CYAN: str = THEMES["tokyo-night"].cyan
HEX_BLUE: str = THEMES["tokyo-night"].blue
HEX_GREEN: str = THEMES["tokyo-night"].green
HEX_YELLOW: str = THEMES["tokyo-night"].yellow
HEX_PURPLE: str = THEMES["tokyo-night"].purple
HEX_RED: str = THEMES["tokyo-night"].red
HEX_TEAL: str = THEMES["tokyo-night"].teal
HEX_WHITE: str = THEMES["tokyo-night"].white

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

# Convenience & backward-compatibility color aliases
CYAN: str = FG_CYAN
BLUE: str = FG_BLUE
GREEN: str = FG_GREEN
YELLOW: str = FG_YELLOW
MAGENTA: str = FG_PURPLE
PURPLE: str = FG_PURPLE
RED: str = FG_RED
WHITE: str = FG_WHITE

BG_SURFACE: str = bg_hex(HEX_SURFACE)
BG_SURFACE_LIGHT: str = bg_hex(HEX_SURFACE_LIGHT)
BG_BLUE: str = bg_hex(HEX_BLUE)
BG_GREEN: str = bg_hex(HEX_GREEN)
BG_PURPLE: str = bg_hex(HEX_PURPLE)
BG_CYAN: str = bg_hex(HEX_CYAN)


def set_theme(theme_id: str) -> bool:
    """Set the active color theme and refresh global color tokens.

    Returns:
        True if theme was successfully changed, False otherwise.
    """
    global _active_theme_id
    global HEX_BG_DARK, HEX_SURFACE, HEX_SURFACE_LIGHT, HEX_BORDER, HEX_BORDER_FOCUS
    global HEX_TEXT, HEX_TEXT_MUTED, HEX_CYAN, HEX_BLUE, HEX_GREEN, HEX_YELLOW
    global HEX_PURPLE, HEX_RED, HEX_TEAL, HEX_WHITE
    global FG_TEXT, FG_MUTED, FG_BORDER, FG_BORDER_FOCUS, FG_CYAN, FG_BLUE
    global FG_GREEN, FG_YELLOW, FG_PURPLE, FG_RED, FG_WHITE
    global CYAN, BLUE, GREEN, YELLOW, MAGENTA, PURPLE, RED, WHITE
    global BG_SURFACE, BG_SURFACE_LIGHT, BG_BLUE, BG_GREEN, BG_PURPLE, BG_CYAN

    target = theme_id.strip().lower()
    alias_map = {
        "catppuccin": "catppuccin-mocha",
        "pastel": "pastel-lavender",
        "lavender": "pastel-lavender",
        "sakura": "pastel-sakura",
        "mint": "pastel-mint",
        "peach": "pastel-peach",
    }
    if target in alias_map:
        target = alias_map[target]
    if target not in THEMES:
        # Check by display name match
        matched = next((t for t in THEMES.values() if t.display_name.lower() == target), None)
        if not matched:
            return False
        target = matched.id

    _active_theme_id = target
    t = THEMES[target]

    HEX_BG_DARK = t.bg_dark
    HEX_SURFACE = t.surface
    HEX_SURFACE_LIGHT = t.surface_light
    HEX_BORDER = t.border
    HEX_BORDER_FOCUS = t.border_focus
    HEX_TEXT = t.text
    HEX_TEXT_MUTED = t.text_muted
    HEX_CYAN = t.cyan
    HEX_BLUE = t.blue
    HEX_GREEN = t.green
    HEX_YELLOW = t.yellow
    HEX_PURPLE = t.purple
    HEX_RED = t.red
    HEX_TEAL = t.teal
    HEX_WHITE = t.white

    FG_TEXT = fg_hex(HEX_TEXT)
    FG_MUTED = fg_hex(HEX_TEXT_MUTED)
    FG_BORDER = fg_hex(HEX_BORDER)
    FG_BORDER_FOCUS = fg_hex(HEX_BORDER_FOCUS)
    FG_CYAN = fg_hex(HEX_CYAN)
    FG_BLUE = fg_hex(HEX_BLUE)
    FG_GREEN = fg_hex(HEX_GREEN)
    FG_YELLOW = fg_hex(HEX_YELLOW)
    FG_PURPLE = fg_hex(HEX_PURPLE)
    FG_RED = fg_hex(HEX_RED)
    FG_WHITE = fg_hex(HEX_WHITE)

    CYAN = FG_CYAN
    BLUE = FG_BLUE
    GREEN = FG_GREEN
    YELLOW = FG_YELLOW
    MAGENTA = FG_PURPLE
    PURPLE = FG_PURPLE
    RED = FG_RED
    WHITE = FG_WHITE

    BG_SURFACE = bg_hex(HEX_SURFACE)
    BG_SURFACE_LIGHT = bg_hex(HEX_SURFACE_LIGHT)
    BG_BLUE = bg_hex(HEX_BLUE)
    BG_GREEN = bg_hex(HEX_GREEN)
    BG_PURPLE = bg_hex(HEX_PURPLE)
    BG_CYAN = bg_hex(HEX_CYAN)

    import sys
    for mod_name in (
        "cybershell.ui.theme",
        "cybershell.ui.ascii_art",
        "cybershell.run",
        "cybershell.ui.renderer",
        "cybershell.ui.pet",
        "cybershell.ui.dashboard",
        "cybershell.ui.command_center",
    ):
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            setattr(mod, "FG_TEXT", FG_TEXT)
            setattr(mod, "FG_MUTED", FG_MUTED)
            setattr(mod, "FG_BORDER", FG_BORDER)
            setattr(mod, "FG_BORDER_FOCUS", FG_BORDER_FOCUS)
            setattr(mod, "FG_CYAN", FG_CYAN)
            setattr(mod, "FG_BLUE", FG_BLUE)
            setattr(mod, "FG_GREEN", FG_GREEN)
            setattr(mod, "FG_YELLOW", FG_YELLOW)
            setattr(mod, "FG_PURPLE", FG_PURPLE)
            setattr(mod, "FG_RED", FG_RED)
            setattr(mod, "FG_WHITE", FG_WHITE)
            setattr(mod, "BG_SURFACE", BG_SURFACE)
            setattr(mod, "BG_SURFACE_LIGHT", BG_SURFACE_LIGHT)
            setattr(mod, "CYAN", FG_CYAN)
            setattr(mod, "BLUE", FG_BLUE)
            setattr(mod, "GREEN", FG_GREEN)
            setattr(mod, "YELLOW", FG_YELLOW)
            setattr(mod, "MAGENTA", FG_PURPLE)
            setattr(mod, "RED", FG_RED)
            setattr(mod, "WHITE", FG_TEXT)

    return True



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
