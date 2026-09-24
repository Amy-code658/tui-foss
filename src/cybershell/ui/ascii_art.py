"""Byte's Linux Adventure - Visual Assets & ASCII Art.

Friendly, playful, and approachable terminal art, banners, and decorations.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

# =============================================================================
# ANSI Color Sequences & Styling Helpers (Soft & Warm Palette)
# =============================================================================

RESET: str = "\033[0m"
BOLD: str = "\033[1m"
DIM: str = "\033[2m"

# Soft, Warm Color Palette
GREEN: str = "\033[92m"    # Sprout green 🌱
YELLOW: str = "\033[93m"   # Warm star yellow ⭐ / hints 💡
BLUE: str = "\033[94m"     # Soft sky blue
MAGENTA: str = "\033[95m"  # Gentle lavender / badges 🏆
CYAN: str = "\033[96m"     # Soft teal / water
WHITE: str = "\033[97m"    # Clean text
RED: str = "\033[91m"      # Soft alert (used sparingly)

ANSI_REGEX = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences to obtain raw character text."""
    return ANSI_REGEX.sub("", str(text))


def visual_len(text: str) -> int:
    """Calculate the visible terminal display length of a styled string."""
    return len(strip_ansi(text))


# =============================================================================
# Friendly Adventure Logos
# =============================================================================

ADVENTURE_LOGO: str = """  ____  _   _ _____ _____ _ ____    _     ___ _   _ _   _ __  __ 
 | __ )| | | |_   _| ____( ) ___|  | |   |_ _| \\ | | | | \\ \\/ / 
 |  _ \\| |_| | | | |  _| |/\\___ \\  | |    | ||  \\| | | | |>  <  
 | |_) |\\__, | | | | |___   ___) | | |___ | || |\\  | |_| |/ . \\ 
 |____/ |___/  |_| |_____| |____/  |_____|___|_| \\_|\\___//_/ \\_\\
        _    ______     _______ _   _ _____ _   _ ____  _____ 
       / \\  |  _ \\ \\   / / ____| \\ | |_   _| | | |  _ \\| ____|
      / _ \\ | | | \\ \\ / /|  _| |  \\| | | | | | | | |_) |  _|  
     / ___ \\| |_| |\\ V / | |___| |\\  | | | | |_| |  _ <| |___ 
    /_/   \\_\\____/  \\_/  |_____|_| \\_| |_|  \\___/|_| \\_\\_____|"""

ADVENTURE_LOGO_COMPACT: str = r"""[ :: BYTE'S LINUX ADVENTURE • A TERMINAL JOURNEY :: ]"""

# Preserved for backward compatibility
CYBER_LOGO = ADVENTURE_LOGO
CYBER_LOGO_COMPACT = ADVENTURE_LOGO_COMPACT
CYBER_LOGO_BLOCK = ADVENTURE_LOGO


def get_logo(styled: bool = False, wide: bool = False) -> str:
    """Return the friendly adventure logo with soft green/yellow styling."""
    raw = ADVENTURE_LOGO
    if not styled:
        return raw

    styled_lines = []
    lines = raw.strip("\n").splitlines()
    colors = [GREEN, GREEN, YELLOW, YELLOW, BLUE, BLUE]
    for idx, line in enumerate(lines):
        color = colors[idx % len(colors)]
        styled_lines.append(f"{BOLD}{color}{line}{RESET}")
    return "\n".join(styled_lines)


# =============================================================================
# Mascot & Guide Illustrations (Clean ASCII)
# =============================================================================

FIELD_MANUAL_HEADER: str = r"""
        [ FIELD MANUAL & RULES ]
             (\__/)
             (・ω・)  "Welcome to Linux!"
            / >*
"""

PORTRAIT_BYTE: List[str] = [
    r"     (\__/)     ",
    r"     (・ω・)      ",
    r"    / >*        ",
    r"   (  Byte  )   ",
    r"    '------'    ",
]

PORTRAIT_FERN: List[str] = [
    r"     .-''''-.   ",
    r"    /  *    \   ",
    r"   |  (^‿^)  |  ",
    r"   (  Fern  )   ",
    r"    '------'    ",
]

PORTRAIT_PENNY: List[str] = [
    r"     .------.   ",
    r"    /  [oo] \   ",
    r"   |  (•‿•)  |  ",
    r"   ( Penny  )   ",
    r"    '------'    ",
]

PORTRAIT_NOVA: List[str] = [
    r"     .------.   ",
    r"    /  *    \   ",
    r"   |  (★‿★)  |  ",
    r"   (  Nova  )   ",
    r"    '------'    ",
]

AVATARS: Dict[str, str] = {
    "byte": "(・ω・)",
    "fern": "(^‿^)",
    "penny": "(•‿•)",
    "nova": "(★‿★)",
    "guide": "(・ω・)",
    "player": "(^o^)",
    "cipher": "(•‿•)",
    "glitch": "(・ω・)",
    "aegis": "(^‿^)",
    "sentinel": "(★‿★)",
    "boss": "(★‿★)",
    "overlord": "(★‿★)",
}

PORTRAITS: Dict[str, List[str]] = {
    "byte": PORTRAIT_BYTE,
    "fern": PORTRAIT_FERN,
    "penny": PORTRAIT_PENNY,
    "nova": PORTRAIT_NOVA,
    "guide": PORTRAIT_BYTE,
    "player": PORTRAIT_BYTE,
    # Backward compatibility aliases
    "cipher": PORTRAIT_PENNY,
    "glitch": PORTRAIT_BYTE,
    "aegis": PORTRAIT_FERN,
    "sentinel": PORTRAIT_NOVA,
    "boss": PORTRAIT_NOVA,
    "overlord": PORTRAIT_NOVA,
    "sentinel boss": PORTRAIT_NOVA,
}


def get_portrait(npc_name: str, styled: bool = False) -> List[str]:
    """Retrieve the multi-line ASCII portrait for a specified guide."""
    key = str(npc_name).strip().lower()
    raw_lines = PORTRAITS.get(key, PORTRAIT_BYTE)
    if not styled:
        return list(raw_lines)
    return [f"{GREEN}{line}{RESET}" for line in raw_lines]


def get_avatar_badge(npc_name: str) -> str:
    """Return a compact emoji / face avatar for a guide."""
    key = str(npc_name).strip().lower()
    return AVATARS.get(key, "(・ω・)")


# =============================================================================
# Friendly Celebration & Progress Banners
# =============================================================================

def get_access_granted_banner(
    title: str = "OBJECTIVE COMPLETE",
    xp_awarded: int = 50,
    streak: int = 0,
    badge: Optional[str] = None,
    width: int = 50,
    styled: bool = True,
) -> str:
    """Render a cheerful success card when an objective is cleared."""
    width = max(34, width)
    inner = width - 2
    b_top = f"╭{'─' * inner}╮"
    b_bot = f"╰{'─' * inner}╯"

    lines = [
        b_top,
        f"│{f'[+] OBJECTIVE COMPLETE':^{inner}}│",
        f"│{title[:inner - 2]:^{inner}}│",
        f"│{f'+{xp_awarded} XP':^{inner}}│",
    ]
    if streak > 1:
        lines.append(f"│{f'Streak: {streak} in a row':^{inner}}│")
    if badge:
        lines.append(f"│{f'New Badge: [{badge}]':^{inner}}│")
    lines.append(b_bot)

    plain = "\n".join(lines)
    if not styled:
        return plain
    return f"{BOLD}{GREEN}{plain}{RESET}"


def get_level_unlocked_banner(
    sector_num: int,
    sector_name: str,
    width: int = 50,
    styled: bool = True,
) -> str:
    """Render a friendly level transition card."""
    width = max(34, width)
    inner = width - 2
    b_top = f"╭{'─' * inner}╮"
    b_bot = f"╰{'─' * inner}╯"
    lines = [
        b_top,
        f"│{f'[+] LEVEL {sector_num:02d} UNLOCKED':^{inner}}│",
        f"│{sector_name.title():^{inner}}│",
        b_bot,
    ]
    plain = "\n".join(lines)
    if not styled:
        return plain
    return f"{BOLD}{YELLOW}{plain}{RESET}"


VICTORY_BANNER: str = """╭──────────────────────────────────────────────────────────────╮
│                                                              │
│                 [ ADVENTURE COMPLETE ]                       │
│                                                              │
│           You explored all 15 Linux worlds and               │
│               solved every puzzle! Great job!                │
│                                                              │
│                  [ MASTER EXPLORER ]                         │
╰──────────────────────────────────────────────────────────────╯"""

# Backward compatibility stub
DEFEAT_BANNER: str = """╭──────────────────────────────────────────────────────────────╮
│                  Let's take a quick breath :)                │
│                 Mistakes are a great way to learn!           │
╰──────────────────────────────────────────────────────────────╯"""


def get_victory_banner(styled: bool = False) -> str:
    """Return the celebration banner for finishing the adventure."""
    if not styled:
        return VICTORY_BANNER
    return f"{BOLD}{GREEN}{VICTORY_BANNER}{RESET}"


def get_defeat_banner(styled: bool = False) -> str:
    """Friendly encouraging reminder."""
    if not styled:
        return DEFEAT_BANNER
    return f"{YELLOW}{DEFEAT_BANNER}{RESET}"


# Backward compatibility stubs for old tests
def format_boss_hp_bar(hp: int, max_hp: int = 100, bar_width: int = 16, styled: bool = False) -> str:
    """Friendly progress indicator (kept for backward compatibility)."""
    return ""


def get_siren_banner(text: str = "", width: int = 76, styled: bool = False) -> str:
    """Alert banner (kept for backward compatibility)."""
    return ""
