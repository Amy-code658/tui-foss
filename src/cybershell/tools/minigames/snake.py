"""Terminal Snake Game for Byte's Linux Adventure.

Features:
- Classic Snake gameplay inside terminal
- Score counter and high score
- Linux-themed food items: 'kernel', 'daemon', 'pipe', 'socket', 'packet'
- Funny terminal-style game over messages (Kernel panic, Segfault, etc.)
- Targets remaining tracker
- Real-time play loop: the snake advances on its own clock and you steer with
  hjkl / wasd / arrow keys. No Enter needed to advance turns.
- Zero emojis
"""

from typing import List, Optional, Tuple, Dict, Any
import random
import select
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

FOOD_TYPES = [
    {"name": "kernel", "glyph": "K", "points": 30, "color": FG_PURPLE},
    {"name": "daemon", "glyph": "D", "points": 20, "color": FG_CYAN},
    {"name": "pipe", "glyph": "P", "points": 15, "color": FG_GREEN},
    {"name": "socket", "glyph": "S", "points": 15, "color": FG_YELLOW},
    {"name": "packet", "glyph": "p", "points": 10, "color": FG_WHITE},
]

GAME_OVER_MESSAGES = [
    "Kernel Panic - not syncing: Fatal exception in snake loop.",
    "Segmentation fault (core dumped): Snake hit the memory wall.",
    "Process terminated: SIGSEGV (Snake bit itself).",
    "Out Of Memory (OOM Killer): Terminated python-snake process.",
    "Connection reset by peer: Socket severed unexpectedly.",
]


class TerminalSnake:
    """Terminal Snake game logic and rendering."""

    def __init__(self, width: int = 30, height: int = 15, target_goals: int = 10) -> None:
        self.width: int = max(15, width)
        self.height: int = max(10, height)
        self.target_goals: int = target_goals
        self.targets_remaining: int = target_goals
        self.score: int = 0
        self.high_score: int = 0
        self.game_over: bool = False
        self.win: bool = False
        self.game_over_reason: str = ""
        
        # Snake representation: list of (x, y) tuples, head is snake[0]
        start_x = self.width // 2
        start_y = self.height // 2
        self.snake: List[Tuple[int, int]] = [
            (start_x, start_y),
            (start_x - 1, start_y),
            (start_x - 2, start_y),
        ]
        self.direction: str = "right"  # up, down, left, right
        self.food: Optional[Dict[str, Any]] = None
        self.food_pos: Tuple[int, int] = (0, 0)
        self._spawn_food()

    def _spawn_food(self) -> None:
        """Place new food at a random position not occupied by snake."""
        open_cells = [
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (x, y) not in self.snake
        ]
        if not open_cells:
            self.win = True
            self.game_over = True
            self.game_over_reason = "Mission Complete: Mainframe buffer fully cleared!"
            return

        self.food_pos = random.choice(open_cells)
        self.food = random.choice(FOOD_TYPES)

    def change_direction(self, new_dir: str) -> None:
        """Update direction if not directly reversing."""
        opposites = {"up": "down", "down": "up", "left": "right", "right": "left"}
        if opposites.get(new_dir) != self.direction:
            self.direction = new_dir

    def step(self, command: str = "") -> bool:
        """Advance one tick, optionally applying a steering command first.

        Returns True while the snake is alive, False once the game ends.
        """
        if self.game_over:
            return False

        cmd = command.strip().lower()
        if cmd in ("w", "k", "up"):
            self.change_direction("up")
        elif cmd in ("s", "j", "down"):
            self.change_direction("down")
        elif cmd in ("a", "h", "left"):
            self.change_direction("left")
        elif cmd in ("d", "l", "right"):
            self.change_direction("right")

        return self._advance()

    def turn(self, command: str) -> None:
        """Change direction without advancing a tick (used by real-time play)."""
        cmd = command.strip().lower()
        if cmd in ("w", "k", "up"):
            self.change_direction("up")
        elif cmd in ("s", "j", "down"):
            self.change_direction("down")
        elif cmd in ("a", "h", "left"):
            self.change_direction("left")
        elif cmd in ("d", "l", "right"):
            self.change_direction("right")

    def _advance(self) -> bool:
        """Move the snake one cell in the current direction."""
        head_x, head_y = self.snake[0]
        dx, dy = 0, 0
        if self.direction == "up":
            dy = -1
        elif self.direction == "down":
            dy = 1
        elif self.direction == "left":
            dx = -1
        elif self.direction == "right":
            dx = 1

        new_head = (head_x + dx, head_y + dy)

        # Check wall collision
        if not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height):
            self.game_over = True
            self.game_over_reason = "Segmentation fault: Hit mainframe boundary wall."
            return False

        # Check self collision (the tail cell frees up unless we are growing)
        will_grow = new_head == self.food_pos
        body = self.snake if will_grow else self.snake[:-1]
        if new_head in body:
            self.game_over = True
            self.game_over_reason = "Fatal: Snake collided with own memory segment."
            return False

        self.snake.insert(0, new_head)

        # Check food eaten
        if will_grow:
            points = self.food.get("points", 10) if self.food else 10
            self.score += points
            if self.score > self.high_score:
                self.high_score = self.score

            if self.targets_remaining > 0:
                self.targets_remaining -= 1
                if self.targets_remaining == 0:
                    self.win = True
                    self.game_over = True
                    self.game_over_reason = "Success: All targets harvested! Sector stable."
                    return False

            self._spawn_food()
        else:
            # Move tail forward
            self.snake.pop()

        return True

    def render(self, styled: bool = True) -> str:
        """Render ASCII board representation."""
        lines: List[str] = []

        # Header info
        food_name = self.food["name"] if self.food else "none"
        header = f"Score: {self.score:<4} | Targets Left: {self.targets_remaining:<2} | Next Food: {food_name}"
        lines.append(f"{BOLD}{FG_CYAN}{header}{RESET}" if styled else header)

        # Top border
        top_border = "┌" + ("─" * (self.width * 2)) + "┐"
        lines.append(f"{FG_PURPLE}{top_border}{RESET}" if styled else top_border)

        grid: List[List[str]] = [["  " for _ in range(self.width)] for _ in range(self.height)]

        # Place food
        if self.food:
            fx, fy = self.food_pos
            glyph = self.food["glyph"]
            col = self.food.get("color", FG_YELLOW) if styled else ""
            rst = RESET if styled else ""
            grid[fy][fx] = f"{col}{glyph} {rst}"

        # Place snake
        for idx, (sx, sy) in enumerate(self.snake):
            if 0 <= sx < self.width and 0 <= sy < self.height:
                if idx == 0:
                    # Head
                    head_char = "@ " if idx == 0 else "o "
                    col = FG_GREEN if styled else ""
                else:
                    head_char = "o "
                    col = FG_CYAN if styled else ""
                rst = RESET if styled else ""
                grid[sy][sx] = f"{col}{head_char}{rst}"

        for row in grid:
            row_str = "".join(row)
            b_vert = f"{FG_PURPLE}│{RESET}" if styled else "│"
            lines.append(f"{b_vert}{row_str}{b_vert}")

        # Bottom border
        bot_border = "└" + ("─" * (self.width * 2)) + "┘"
        lines.append(f"{FG_PURPLE}{bot_border}{RESET}" if styled else bot_border)

        # Controls hint
        controls = "Steer: [h/j/k/l] or [w/a/s/d] or arrows | 'q' to quit"
        lines.append(f"{DIM}{controls}{RESET}" if styled else controls)

        if self.game_over:
            reason = self.game_over_reason or random.choice(GAME_OVER_MESSAGES)
            status_col = FG_GREEN if self.win else FG_RED
            res_line = f"{status_col}[GAME OVER] {reason}{RESET}" if styled else f"[GAME OVER] {reason}"
            lines.append(res_line)

        return "\n".join(lines)


def play_snake_interactive() -> int:
    """Run a real-time session of Terminal Snake.

    The snake advances on its own clock; hjkl / wasd / arrow keys steer it and
    'q' quits. No Enter is required to advance a turn.
    """
    game = TerminalSnake(width=24, height=12, target_goals=8)
    tick = 0.16  # seconds per step
    interactive = sys.stdin.isatty()

    def read_key() -> str:
        """Read one steering key without blocking. Returns '' when none pending."""
        if not interactive:
            return ""
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 0)
        except (OSError, ValueError):
            return ""
        if not ready:
            return ""
        try:
            return sys.stdin.read(1)
        except (OSError, ValueError):
            return ""

    while not game.game_over:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(game.render(styled=True) + "\n")
        sys.stdout.write("Steer [h/j/k/l or w/a/s/d, arrows] - q to quit: ")
        sys.stdout.flush()

        key = read_key()
        if key.lower() in ("q", "Q"):
            break
        if key in ("\x1b",):
            # Possible arrow escape sequence: read the remaining bytes.
            seq = ""
            for _ in range(2):
                try:
                    ready, _, _ = select.select([sys.stdin], [], [], 0.001)
                except (OSError, ValueError):
                    break
                if not ready:
                    break
                try:
                    seq += sys.stdin.read(1)
                except (OSError, ValueError):
                    break
            key = {"[A": "k", "[B": "j", "[C": "l", "[D": "h"}.get(seq, "")

        if key:
            game.turn(key)

        # Advance on the game clock, regardless of whether a key arrived.
        deadline = time.monotonic() + tick
        while time.monotonic() < deadline and not game.game_over:
            time.sleep(0.01)
        game.step("")

    # Final screen
    sys.stdout.write("\033[H\033[J")
    sys.stdout.write(game.render(styled=True) + "\n")
    if interactive:
        sys.stdout.write("\nPress Enter to return...")
        sys.stdout.flush()
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

    return game.score
