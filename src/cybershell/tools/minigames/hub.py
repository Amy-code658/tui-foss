"""Mini-Games Hub for Byte's Linux Adventure.

Provides interactive selection of:
1. Chmod Perm Decoder (Octal lockpicking puzzle)
2. Terminal Snake (Harvest kernel, daemon, pipe items)
3. Vim Dojo (Muscle-memory whack-a-mole for motions and edits)
4. Typing Dojo (Safe Linux command speed drills)
0. Return to Shell

Zero emojis, clean developer styling.
"""

from typing import Optional
import sys

from cybershell.contracts import PlayerStats
from cybershell.tools.chmod_minigame import ChmodMinigame
from cybershell.tools.minigames.snake import play_snake_interactive
from cybershell.tools.minigames.vim_dojo import play_vim_dojo_interactive
from cybershell.tools.minigames.typing_dojo import play_typing_dojo_interactive
from cybershell.ui.theme import (
    FG_CYAN,
    FG_GREEN,
    FG_YELLOW,
    FG_PURPLE,
    FG_MUTED,
    FG_WHITE,
    RESET,
    BOLD,
    DIM,
)
from cybershell.ui.renderer import (
    PANEL_TOP_LEFT,
    PANEL_TOP_RIGHT,
    PANEL_BOTTOM_LEFT,
    PANEL_BOTTOM_RIGHT,
    PANEL_HORIZONTAL,
    PANEL_VERTICAL,
    visual_len,
    pad_to_width,
)


def render_minigames_menu(width: int = 70, styled: bool = True) -> str:
    """Render rounded mini-games hub menu."""
    width = max(45, min(width - 2, 70))
    inner_w = width - 2
    content_w = inner_w - 4

    b_col = FG_PURPLE if styled else ""
    b_rst = RESET if styled else ""
    top = f"{b_col}{PANEL_TOP_LEFT}{PANEL_HORIZONTAL * inner_w}{PANEL_TOP_RIGHT}{b_rst}"
    bot = f"{b_col}{PANEL_BOTTOM_LEFT}{PANEL_HORIZONTAL * inner_w}{PANEL_BOTTOM_RIGHT}{b_rst}"
    divider = f"{b_col}{PANEL_VERTICAL}{b_rst}{PANEL_HORIZONTAL * inner_w}{b_col}{PANEL_VERTICAL}{b_rst}"

    lines = [top]

    def add_line(text: str = "") -> None:
        pad = max(0, inner_w - visual_len(text) - 2)
        lines.append(f"{b_col}{PANEL_VERTICAL}{b_rst} {text}{' ' * pad} {b_col}{PANEL_VERTICAL}{b_rst}")

    title = "CYBERSHELL ARCADE // PRACTICE & MINIGAMES"
    title_fmt = f"{BOLD}{FG_CYAN}{title.center(content_w)}{RESET}" if styled else title.center(content_w)
    add_line(title_fmt)
    lines.append(divider)

    desc = "Refine muscle memory, terminal reflex, and command speed."
    add_line(f"{DIM}{desc.center(content_w)}{RESET}" if styled else desc.center(content_w))
    add_line("")

    games = [
        ("1", "Chmod Perm Decoder", "Solve octal security doors (755, 644, etc.)"),
        ("2", "Terminal Snake", "Classic snake: eat kernel, daemon, pipe & socket items"),
        ("3", "Vim Dojo", "Fast whack-a-mole target practice for hjkl, x, dd, yy"),
        ("4", "Typing Dojo", "Safe, real Linux command speed drills with WPM & acc"),
        ("0", "Return to Terminal", "Exit arcade and resume current challenge"),
    ]

    for key, name, details in games:
        key_fmt = f"{BOLD}{FG_YELLOW}[{key}]{RESET}" if styled else f"[{key}]"
        name_fmt = f"{BOLD}{FG_WHITE}{name:<20}{RESET}" if styled else f"{name:<20}"
        det_fmt = f"{DIM}{details}{RESET}" if styled else details
        add_line(f"  {key_fmt} {name_fmt} {det_fmt}")

    lines.append(divider)
    footer = "Enter number to start [1-4, 0 to return]"
    add_line(f"{DIM}{footer.center(content_w)}{RESET}" if styled else footer.center(content_w))
    lines.append(bot)

    return "\n".join(lines)


def view_minigames_hub(
    player: PlayerStats,
    chmod_game: Optional[ChmodMinigame] = None,
    width: int = 70,
    ui: Optional[object] = None,
) -> None:
    """Interactive loop for the Mini-Games Hub."""
    while True:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(render_minigames_menu(width=width, styled=True) + "\n")
        sys.stdout.write("arcade> ")
        sys.stdout.flush()

        try:
            choice = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if choice in ("0", "q", "quit", "exit", "back"):
            break
        elif choice == "1":
            from cybershell.tools.minigames.chmod_decoder import play_chmod_decoder_interactive
            play_chmod_decoder_interactive(player, width=width)
        elif choice == "2":
            if ui is not None and hasattr(ui, "play_snake"):
                score = int(ui.play_snake() or 0)
            else:
                score = play_snake_interactive()
            if score > 0:
                player.xp += score // 2
        elif choice == "3":
            hits = play_vim_dojo_interactive()
            if hits > 0:
                player.xp += hits * 5
        elif choice == "4":
            wpm = play_typing_dojo_interactive()
            if wpm > 0:
                player.xp += int(wpm)
