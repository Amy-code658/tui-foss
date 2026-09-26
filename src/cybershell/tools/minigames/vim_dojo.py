"""Vim Dojo Target Practice Mini-game for Byte's Linux Adventure.

Focuses on building fast Vim muscle memory:
- Practice keys: h, j, k, l, x, dd, yy, p, w, b, 0, $
- Whack-a-mole style targets appearing in terminal arena
- Live metrics:
  * Targets remaining
  * Hits (deletes/strikes)
  * Misses
  * Accuracy percentage
  * Timer
- Zero emojis
"""

from typing import List, Dict, Optional, Any
import random
import sys
import time

try:
    from cybershell.ui.theme import (
        FG_CYAN,
        FG_GREEN,
        FG_YELLOW,
        FG_PURPLE,
        FG_RED,
        FG_MUTED,
        FG_WHITE,
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
    FG_WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


VIM_TARGETS = [
    {"key": "h", "name": "Move Left", "type": "motion", "hint": "Step cursor left"},
    {"key": "j", "name": "Move Down", "type": "motion", "hint": "Step cursor down"},
    {"key": "k", "name": "Move Up", "type": "motion", "hint": "Step cursor up"},
    {"key": "l", "name": "Move Right", "type": "motion", "hint": "Step cursor right"},
    {"key": "w", "name": "Next Word", "type": "motion", "hint": "Jump forward to start of next word"},
    {"key": "b", "name": "Back Word", "type": "motion", "hint": "Jump backward to start of previous word"},
    {"key": "0", "name": "Line Start", "type": "motion", "hint": "Jump to beginning of current line"},
    {"key": "$", "name": "Line End", "type": "motion", "hint": "Jump to end of current line"},
    {"key": "x", "name": "Delete Char", "type": "edit", "hint": "Delete character under cursor"},
    {"key": "dd", "name": "Delete Line", "type": "edit", "hint": "Cut/delete the entire line"},
    {"key": "yy", "name": "Yank Line", "type": "edit", "hint": "Copy/yank the current line"},
    {"key": "p", "name": "Put / Paste", "type": "edit", "hint": "Paste clipboard text below cursor"},
]


class VimDojo:
    """Whack-a-mole style Vim muscle-memory game."""

    def __init__(self, target_count: int = 10) -> None:
        self.total_targets: int = target_count
        self.targets_remaining: int = target_count
        self.hits: int = 0
        self.misses: int = 0
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.current_target: Dict[str, str] = random.choice(VIM_TARGETS)
        self.feedback: str = "Press the key matching the target prompt!"
        self.completed: bool = False

    @property
    def accuracy(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 100.0
        return (self.hits / total) * 100.0

    @property
    def elapsed_seconds(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def step(self, key_input: str) -> bool:
        """Process one player attempt. Returns True if correct, False otherwise."""
        if self.completed:
            return False

        clean_input = key_input.strip()
        expected = self.current_target["key"]

        if clean_input == expected:
            self.hits += 1
            self.targets_remaining -= 1
            self.feedback = f"Hit! Struck '{expected}' cleanly."
            if self.targets_remaining <= 0:
                self.completed = True
                self.end_time = time.time()
                self.feedback = f"Dojo cleared in {self.elapsed_seconds:.1f}s with {self.accuracy:.1f}% accuracy!"
            else:
                self.current_target = random.choice(VIM_TARGETS)
            return True
        else:
            self.misses += 1
            self.feedback = f"Miss! Entered '{clean_input}', expected '{expected}' ({self.current_target['hint']})."
            return False

    def render(self, styled: bool = True) -> str:
        """Render Vim Dojo arena and metrics."""
        lines: List[str] = []

        # Top border
        width = 62
        b_col = FG_PURPLE if styled else ""
        b_rst = RESET if styled else ""
        top_bar = f"{b_col}┌{'─' * (width - 2)}┐{b_rst}"
        bot_bar = f"{b_col}└{'─' * (width - 2)}┘{b_rst}"
        divider = f"{b_col}├{'─' * (width - 2)}┤{b_rst}"

        lines.append(top_bar)

        def add_row(text: str) -> None:
            # Simple line wrapping
            raw_len = len(text)
            pad = max(0, width - 4 - raw_len)
            lines.append(f"{b_col}│{b_rst} {text}{' ' * pad} {b_col}│{b_rst}")

        title = "VIM DOJO // MUSCLE MEMORY ARENA"
        title_styled = f"{BOLD}{FG_CYAN}{title.center(width - 4)}{RESET}" if styled else title.center(width - 4)
        add_row(title_styled)
        lines.append(divider)

        # Status row
        timer_str = f"{self.elapsed_seconds:.1f}s"
        acc_str = f"{self.accuracy:.1f}%"
        status_text = (
            f"Targets Left: {self.targets_remaining:<2} | Hits: {self.hits:<2} | "
            f"Misses: {self.misses:<2} | Acc: {acc_str:<5} | Time: {timer_str}"
        )
        add_row(f"{FG_YELLOW}{status_text}{RESET}" if styled else status_text)
        lines.append(divider)

        if not self.completed:
            # Active target presentation
            target_key = self.current_target["key"]
            target_name = self.current_target["name"]
            target_hint = self.current_target["hint"]

            add_row(f"{BOLD}INCOMING TARGET:{RESET}" if styled else "INCOMING TARGET:")
            target_display = f"   >>> [ {target_key} ] <<<   ({target_name})"
            add_row(f"{BOLD}{FG_GREEN}{target_display}{RESET}" if styled else target_display)
            add_row(f"   Hint: {target_hint}")
            add_row("")
            add_row("Type the exact Vim motion/key and press Enter (or 'q' to quit)")
        else:
            add_row(f"{BOLD}{FG_GREEN}DOJO MASTERY ACHIEVED!{RESET}" if styled else "DOJO MASTERY ACHIEVED!")
            add_row(f"Total Targets : {self.total_targets}")
            add_row(f"Final Accuracy: {self.accuracy:.1f}%")
            add_row(f"Elapsed Time  : {self.elapsed_seconds:.1f} seconds")
            add_row("")
            add_row("Press Enter to return to menu...")

        lines.append(divider)
        add_row(f"{DIM}{self.feedback}{RESET}" if styled else self.feedback)
        lines.append(bot_bar)

        return "\n".join(lines)


def play_vim_dojo_interactive() -> int:
    """Run an interactive session of Vim Dojo."""
    dojo = VimDojo(target_count=10)

    while not dojo.completed:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(dojo.render(styled=True) + "\n")
        sys.stdout.write("Vim key: ")
        sys.stdout.flush()

        try:
            key_input = input().strip()
        except (KeyboardInterrupt, EOFError):
            break

        if key_input.lower() in ("q", "quit", ":q"):
            break

        dojo.step(key_input)

    # Show completion
    sys.stdout.write("\033[H\033[J")
    sys.stdout.write(dojo.render(styled=True) + "\n")
    sys.stdout.flush()
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

    return dojo.hits
