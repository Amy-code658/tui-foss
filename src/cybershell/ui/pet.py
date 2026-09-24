"""Terminal Pet Companion for Byte's Linux Adventure.

A lightweight, subtle ASCII terminal pet companion that:
- Idles peacefully
- Reacts to successful commands
- Reacts to mistakes with encouraging feedback
- Celebrates streaks and level-ups
- Sleeps when idle
- Can be toggled on/off
- Zero emojis - pure clean ASCII art and developer charm!
"""

from typing import List, Optional
import time

try:
    from cybershell.ui.theme import (
        FG_CYAN,
        FG_GREEN,
        FG_YELLOW,
        FG_PURPLE,
        FG_RED,
        FG_MUTED,
        FG_TEXT,
        RESET,
        BOLD,
        DIM,
    )
except ImportError:
    FG_CYAN = "\033[96m"
    FG_GREEN = "\033[92m"
    FG_YELLOW = "\033[93m"
    FG_PURPLE = "\033[95m"
    FG_RED = "\033[91m"
    FG_MUTED = "\033[90m"
    FG_TEXT = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


# Distinct cute baby penguin poses (4 lines each)
PET_SPRITES = {
    "idle": [
        r"   .--.   ",
        r"  |o  o|  ",
        r" <( >v< )> ",
        r"  (__)__) ",
    ],
    "happy": [
        r"   .--.   ",
        r"  |^  ^|  ",
        r" <( >v< )> ",
        r"  (__)__) ",
    ],
    "celebrating": [
        r"  \\.--.// ",
        r"  (^  ^)  ",
        r"   (>O<)  ",
        r"  (__)__) ",
    ],
    "confused": [
        r"   .--. ? ",
        r"  |o  -|  ",
        r" <( >~< )> ",
        r"  (__)__) ",
    ],
    "thinking": [
        r"   .--. . ",
        r"  |•  •|o ",
        r" <( >.< )> ",
        r"  (__)__) ",
    ],
    "sleeping": [
        r"   .--.  z",
        r"  |-  -|z ",
        r" <( >-< )> ",
        r"  (__)__) ",
    ],
}

SUCCESS_QUOTES = [
    "Clean execution!",
    "The shell approves.",
    "Nice command.",
    "Syntax validated.",
    "Smooth operator.",
    "Path cleared!",
]

ERROR_QUOTES = [
    "Check the path and try again.",
    "Not quite - inspect the syntax.",
    "Every error is a lesson.",
    "Try 'help' or 'hint'.",
    "Don't worry, shells are picky.",
]

STREAK_QUOTES = [
    "Combo rolling!",
    "On fire! Keep it up!",
    "Terminal mastery unlocked!",
    "Unstoppable momentum!",
]

IDLE_QUOTES = [
    "Awaiting your command...",
    "Ready when you are.",
    "The shell is quiet.",
    "Exploring the mainframe...",
]

SLEEP_QUOTES = [
    "zZz... idle mode ...",
    "Catching some cycles...",
    "Press Enter to wake me.",
]


class TerminalPet:
    """ASCII Terminal Pet companion."""

    def __init__(self, name: str = "Byte", enabled: bool = True) -> None:
        self.name: str = name
        self.enabled: bool = enabled
        self.state: str = "idle"
        self.current_quote: str = "Ready to explore!"
        self.last_action_time: float = time.time()
        self.streak_count: int = 0
        self.commands_observed: int = 0
        self.success_count: int = 0
        self.player_name: str = ""

    def set_player_name(self, name: str) -> None:
        """Set the player's name for personalized reactions."""
        self.player_name = name.strip()

    def toggle(self) -> bool:
        """Toggle pet on or off. Returns new state."""
        self.enabled = not self.enabled
        return self.enabled

    def react_success(self, command: str = "") -> None:
        """React to a successful challenge or valid command."""
        self.last_action_time = time.time()
        self.commands_observed += 1
        self.success_count += 1
        self.streak_count += 1

        if self.streak_count >= 3:
            self.state = "celebrating"
            quote_idx = self.streak_count % len(STREAK_QUOTES)
            self.current_quote = f"{STREAK_QUOTES[quote_idx]} (x{self.streak_count})"
        else:
            self.state = "happy"
            quote_idx = self.success_count % len(SUCCESS_QUOTES)
            self.current_quote = SUCCESS_QUOTES[quote_idx]

    def react_error(self, message: str = "") -> None:
        """React to a command mistake or syntax failure."""
        self.last_action_time = time.time()
        self.commands_observed += 1
        self.streak_count = 0
        self.state = "confused"
        quote_idx = self.commands_observed % len(ERROR_QUOTES)
        self.current_quote = ERROR_QUOTES[quote_idx]

    def react_idle(self) -> None:
        """Set to idle or sleeping based on elapsed time."""
        now = time.time()
        if now - self.last_action_time > 60:
            self.state = "sleeping"
            self.current_quote = SLEEP_QUOTES[int(now) % len(SLEEP_QUOTES)]
        else:
            self.state = "idle"
            self.current_quote = IDLE_QUOTES[int(now) % len(IDLE_QUOTES)]

    def react_hint(self) -> None:
        """React when player asks for a hint."""
        self.last_action_time = time.time()
        self.state = "thinking"
        self.current_quote = "Analyzing clues..."

    def render(self, width: int = 24, height: int = 7, styled: bool = True) -> List[str]:
        """Render pet card lines strictly formatted to fit panel width and height."""
        inner_w = max(10, width)
        lines: List[str] = []

        if not self.enabled:
            # Minimal disabled placeholder
            lines.append("")
            lines.append(f"{DIM}[Pet Disabled]{RESET}" if styled else "[Pet Disabled]")
            lines.append(f"{DIM}Type ':pet' to wake{RESET}" if styled else "Type ':pet' to wake")
            while len(lines) < height:
                lines.append("")
            return lines[:height]

        sprite = PET_SPRITES.get(self.state, PET_SPRITES["idle"])

        # Cute light blue penguin palette: soft blue body, bright yellow beak & feet, white eyes
        if styled:
            c_blue = "\033[38;2;121;192;255m"   # Cute light blue
            c_yellow = "\033[38;2;241;224;90m"  # Cute yellow beak & feet
            c_white = "\033[97m"                 # White eyes & text
            c_rst = RESET
            c_bld = BOLD
        else:
            c_blue = ""
            c_yellow = ""
            c_white = ""
            c_rst = ""
            c_bld = ""

        # Sprite rows centered with light blue body, white eyes & yellow beak
        for row in sprite:
            centered = row.center(inner_w)
            if styled:
                styled_row = centered
                # Style yellow feet
                if "(__)__)" in styled_row:
                    styled_row = styled_row.replace("(__)__)", f"{c_bld}{c_yellow}(__)__){c_rst}")
                # Style yellow beak
                for beak in (">v<", ">O<", ">~<", ">.<", ">-<"):
                    if beak in styled_row:
                        styled_row = styled_row.replace(beak, f"{c_bld}{c_yellow}{beak}{c_rst}{c_blue}")
                # Style white eyes
                for eyes in ("o  o", "^  ^", "•  •", "o  -", "-  -"):
                    if eyes in styled_row:
                        styled_row = styled_row.replace(eyes, f"{c_bld}{c_white}{eyes}{c_rst}{c_blue}")
                lines.append(f"{c_blue}{styled_row}{c_rst}")
            else:
                lines.append(centered)

        # Mood / Quote line
        prefix = f"{self.name}: "
        quote_text = self.current_quote.replace("{name}", self.player_name or "Explorer")
        max_quote_len = max(4, inner_w - len(prefix) - 2)
        if len(quote_text) > max_quote_len:
            quote_text = quote_text[:max_quote_len - 3] + "..."
        full_plain = f"{self.name}: {quote_text}"
        pad_total = max(0, inner_w - len(full_plain))
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        if styled:
            quote_line = f"{' ' * pad_left}{c_bld}{c_yellow}{self.name}:{c_rst} {c_white}{quote_text}{c_rst}{' ' * pad_right}"
        else:
            quote_line = f"{' ' * pad_left}{full_plain}{' ' * pad_right}"
        lines.append(quote_line)

        # Pad to requested height
        while len(lines) < height:
            lines.append("")

        return lines[:height]


_global_pet: Optional[TerminalPet] = None


def get_terminal_pet() -> TerminalPet:
    """Return application-wide TerminalPet singleton."""
    global _global_pet
    if _global_pet is None:
        _global_pet = TerminalPet()
    return _global_pet
