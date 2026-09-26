"""Typing Dojo Command Practice Mini-game for Byte's Linux Adventure.

CRITICAL SAFETY DESIGN:
Commands presented in this typing trainer are evaluated PURELY AS TEXT STRINGS.
They are NEVER passed to a shell, subprocess, exec(), eval(), or VFS runner.

Features:
- Real Linux commands appearing on screen as typing targets
- Real-time performance tracking:
  * WPM (Words Per Minute based on standard 5 chars/word)
  * Accuracy percentage (Levenshtein / character similarity)
  * Total characters typed
  * Elapsed time
  * Best score / high score
- Zero emojis
"""

from typing import List, Dict, Optional, Tuple
import difflib
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


TYPING_PROMPTS = [
    "chmod 755 play.sh",
    "grep -rn 'root' /etc/passwd",
    "find . -name '*.py' -type f",
    "mkdir -p ~/projects/cybershell",
    "ps aux | grep daemon",
    "tar -czvf backup.tar.gz src/",
    "cat /var/log/syslog | tail -n 20",
    "ls -la --color=auto /var/log",
    "git status --short",
    "kill -9 $(pgrep runaway)",
    "echo 'export PATH=$PATH:/opt/bin' >> ~/.bashrc",
    "wc -l < /etc/resolv.conf",
    "df -h | grep '^/dev/'",
    "head -n 5 access.log | sort -u",
]


class TypingDojo:
    """Safe Linux command typing drill trainer."""

    def __init__(self, rounds: int = 5) -> None:
        self.rounds: int = rounds
        self.current_round: int = 0
        self.total_chars_expected: int = 0
        self.total_chars_typed: int = 0
        self.total_chars_correct: int = 0
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.current_prompt: str = random.choice(TYPING_PROMPTS)
        self.feedback: str = "Type the exact command prompt below and press Enter."
        self.completed: bool = False
        self.best_wpm: float = 0.0

    @property
    def elapsed_minutes(self) -> float:
        duration = (self.end_time or time.time()) - self.start_time
        return max(0.001, duration / 60.0)

    @property
    def wpm(self) -> float:
        # Standard: (chars / 5) / minutes
        words = self.total_chars_correct / 5.0
        return max(0.0, words / self.elapsed_minutes)

    @property
    def accuracy(self) -> float:
        if self.total_chars_typed == 0:
            return 100.0
        return max(0.0, min(100.0, (self.total_chars_correct / self.total_chars_typed) * 100.0))

    def step(self, typed_text: str) -> Tuple[bool, float]:
        """Process typed line against current command prompt.

        SAFETY NOTE: Input is strictly string-compared. Never executed!
        """
        if self.completed:
            return False, 0.0

        expected = self.current_prompt
        actual = typed_text

        # Character matching
        matcher = difflib.SequenceMatcher(None, expected, actual)
        correct_chars = sum(match.size for match in matcher.get_matching_blocks())

        self.total_chars_expected += len(expected)
        self.total_chars_typed += len(actual)
        self.total_chars_correct += correct_chars

        exact_match = (actual == expected)
        round_accuracy = (correct_chars / max(1, max(len(expected), len(actual)))) * 100.0

        if exact_match:
            self.feedback = f"Perfect match! (100% accuracy on '{expected}')"
        else:
            self.feedback = f"Close! {round_accuracy:.1f}% accuracy on '{expected}'."

        self.current_round += 1
        current_wpm = self.wpm
        if current_wpm > self.best_wpm:
            self.best_wpm = current_wpm

        if self.current_round >= self.rounds:
            self.completed = True
            self.end_time = time.time()
            self.feedback = (
                f"Drill finished! Final WPM: {self.wpm:.1f} | Accuracy: {self.accuracy:.1f}%"
            )
        else:
            # Pick a new distinct prompt
            available = [p for p in TYPING_PROMPTS if p != self.current_prompt]
            self.current_prompt = random.choice(available)

        return exact_match, round_accuracy

    def render(self, styled: bool = True) -> str:
        """Render Typing Dojo terminal display."""
        width = 68
        b_col = FG_PURPLE if styled else ""
        b_rst = RESET if styled else ""
        top_bar = f"{b_col}┌{'─' * (width - 2)}┐{b_rst}"
        bot_bar = f"{b_col}└{'─' * (width - 2)}┘{b_rst}"
        divider = f"{b_col}├{'─' * (width - 2)}┤{b_rst}"

        lines: List[str] = [top_bar]

        def add_row(text: str) -> None:
            raw_len = len(text)
            pad = max(0, width - 4 - raw_len)
            lines.append(f"{b_col}│{b_rst} {text}{' ' * pad} {b_col}│{b_rst}")

        title = "TYPING DOJO // SAFE LINUX COMMAND SPEED DRILLS"
        title_styled = f"{BOLD}{FG_CYAN}{title.center(width - 4)}{RESET}" if styled else title.center(width - 4)
        add_row(title_styled)
        lines.append(divider)

        # Metrics bar
        wpm_str = f"{self.wpm:.1f}"
        acc_str = f"{self.accuracy:.1f}%"
        chars_str = f"{self.total_chars_typed}"
        status_line = (
            f"Round: {self.current_round}/{self.rounds} | WPM: {wpm_str:<5} | "
            f"Acc: {acc_str:<6} | Chars: {chars_str:<4} | Best WPM: {self.best_wpm:.1f}"
        )
        add_row(f"{FG_YELLOW}{status_line}{RESET}" if styled else status_line)
        lines.append(divider)

        if not self.completed:
            add_row(f"{DIM}Target Command (Safe practice - never executed in shell):{RESET}" if styled else "Target Command (Safe practice - never executed in shell):")
            add_row("")
            cmd_display = f"   $ {self.current_prompt}"
            add_row(f"{BOLD}{FG_GREEN}{cmd_display}{RESET}" if styled else cmd_display)
            add_row("")
            add_row("Type the exact line above and press Enter (or 'q' to quit):")
        else:
            add_row(f"{BOLD}{FG_GREEN}TYPING DRILL COMPLETE!{RESET}" if styled else "TYPING DRILL COMPLETE!")
            add_row(f"Speed         : {self.wpm:.1f} WPM")
            add_row(f"Accuracy      : {self.accuracy:.1f}%")
            add_row(f"Total Chars   : {self.total_chars_typed}")
            add_row(f"Duration      : {self.elapsed_minutes * 60:.1f} seconds")
            add_row("")
            add_row("Press Enter to return to menu...")

        lines.append(divider)
        add_row(f"{DIM}{self.feedback}{RESET}" if styled else self.feedback)
        lines.append(bot_bar)

        return "\n".join(lines)


def play_typing_dojo_interactive() -> float:
    """Run an interactive session of Typing Dojo."""
    dojo = TypingDojo(rounds=5)

    while not dojo.completed:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(dojo.render(styled=True) + "\n")
        sys.stdout.write("Type: ")
        sys.stdout.flush()

        try:
            line = input()
        except (KeyboardInterrupt, EOFError):
            break

        if line.strip().lower() in ("q", "quit", ":q"):
            break

        dojo.step(line)

    sys.stdout.write("\033[H\033[J")
    sys.stdout.write(dojo.render(styled=True) + "\n")
    sys.stdout.flush()
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

    return dojo.wpm
