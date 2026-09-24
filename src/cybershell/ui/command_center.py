"""Central Command Center / Palette for Byte's Linux Adventure.

A polished developer-style command palette accessible from anywhere via:
- Ctrl+Space (or \\x00)
- Command shortcuts: :cmd, :menu, :space, cmd

Features:
- Search local documentation
- Choose challenge / quick switch
- View progress dashboard
- Open mini-games hub
- Open Field Manual
- Reset current challenge
- Toggle terminal pet
- Toggle background effects (rain)
- Toggle calm animations
- Theme selector (12 developer themes)
- Settings & diagnostics

Zero emojis, clean developer styling.
"""

from typing import List, Dict, Optional, Tuple, Any
import sys

from cybershell.contracts import PlayerStats, Quest
from cybershell.ui.theme import (
    FG_CYAN,
    FG_BLUE,
    FG_GREEN,
    FG_YELLOW,
    FG_PURPLE,
    FG_RED,
    FG_MUTED,
    FG_WHITE,
    RESET,
    BOLD,
    DIM,
    list_themes,
    get_active_theme,
    set_theme,
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
from cybershell.ui.pet import get_terminal_pet
from cybershell.ui.ambience import get_ambience_manager


PALETTE_ACTIONS = [
    {
        "id": "search_docs",
        "key": "1",
        "title": "Search Local Documentation",
        "detail": "Search Linux commands, flags, and tactical combos",
    },
    {
        "id": "choose_challenge",
        "key": "2",
        "title": "Choose Challenge",
        "detail": "Quick switch to any available level or sector",
    },
    {
        "id": "view_progress",
        "key": "3",
        "title": "View Progress Dashboard",
        "detail": "Inspect completion %, level, streaks & topic breakdown",
    },
    {
        "id": "open_minigames",
        "key": "4",
        "title": "Open Mini-Games Hub",
        "detail": "Play Terminal Snake, Vim Dojo, Typing Dojo, or Chmod",
    },
    {
        "id": "open_manual",
        "key": "5",
        "title": "Open Field Manual",
        "detail": "Linux command manual and syntax reference",
    },
    {
        "id": "reset_challenge",
        "key": "6",
        "title": "Reset Current Challenge",
        "detail": "Restore current sector filesystem to clean state",
    },
    {
        "id": "toggle_pet",
        "key": "7",
        "title": "Toggle Terminal Pet",
        "detail": "Toggle ASCII companion Byte on/off",
    },
    {
        "id": "toggle_rain",
        "key": "8",
        "title": "Toggle Background Rain",
        "detail": "Toggle ambient matrix rain effect",
    },
    {
        "id": "toggle_anim",
        "key": "9",
        "title": "Toggle Calm Animations",
        "detail": "Toggle subtle breathing/pulse indicator",
    },
    {
        "id": "chmod_decoder",
        "key": "C",
        "title": "Chmod Permission Decoder",
        "detail": "Octal & symbolic conversion + security door puzzle",
    },
    {
        "id": "theme_selector",
        "key": "T",
        "title": "Color Theme Selector",
        "detail": "FOSS, Tokyo Night, Dracula, Catppuccin, Nord, etc. (13 themes)",
    },
    {
        "id": "settings",
        "key": "S",
        "title": "System Settings & Diagnostics",
        "detail": "Inspect terminal dimensions, cadet mode, save status",
    },
]


def render_command_center(
    player: PlayerStats,
    width: int = 74,
    styled: bool = True,
    status_msg: str = "",
) -> str:
    """Render the developer command palette."""
    width = max(45, min(width - 2, 74))
    inner_w = width - 2
    content_w = inner_w - 4

    theme = get_active_theme()
    pet = get_terminal_pet()
    ambience = get_ambience_manager()

    b_col = theme.fg_blue if styled else ""
    b_rst = RESET if styled else ""
    top = f"{b_col}{PANEL_TOP_LEFT}{PANEL_HORIZONTAL * inner_w}{PANEL_TOP_RIGHT}{b_rst}"
    bot = f"{b_col}{PANEL_BOTTOM_LEFT}{PANEL_HORIZONTAL * inner_w}{PANEL_BOTTOM_RIGHT}{b_rst}"
    divider = f"{b_col}{PANEL_VERTICAL}{b_rst}{PANEL_HORIZONTAL * inner_w}{b_col}{PANEL_VERTICAL}{b_rst}"

    lines: List[str] = [top]

    def add_line(text: str = "") -> None:
        pad = max(0, inner_w - visual_len(text) - 2)
        lines.append(f"{b_col}{PANEL_VERTICAL}{b_rst} {text}{' ' * pad} {b_col}{PANEL_VERTICAL}{b_rst}")

    # Header
    title = "COMMAND CENTER // PALETTE"
    if styled:
        add_line(f"{BOLD}{theme.fg_cyan}{title.center(content_w)}{RESET}")
    else:
        add_line(title.center(content_w))

    lines.append(divider)

    # Sub-status bar with live theme colors
    pet_status = f"{theme.fg_green}ON{RESET}" if pet.enabled else f"{theme.fg_muted}OFF{RESET}"
    rain_status = f"{theme.fg_cyan}ON{RESET}" if ambience.rain_enabled else f"{theme.fg_muted}OFF{RESET}"
    anim_status = f"{theme.fg_yellow}ON{RESET}" if ambience.calm_animations else f"{theme.fg_muted}OFF{RESET}"
    if styled:
        status_bar = f"Theme: {BOLD}{theme.fg_purple}{theme.display_name}{RESET} | Pet: {pet_status} | Rain: {rain_status} | Anim: {anim_status}"
    else:
        status_bar = f"Theme: {theme.display_name} | Pet: {'ON' if pet.enabled else 'OFF'} | Rain: {'ON' if ambience.rain_enabled else 'OFF'} | Anim: {'ON' if ambience.calm_animations else 'OFF'}"
    add_line(f"{status_bar.center(content_w)}")
    add_line("")

    for item in PALETTE_ACTIONS:
        key = item["key"]
        k_fmt = f"{BOLD}{theme.fg_yellow}[{key}]{RESET}" if styled else f"[{key}]"
        name_fmt = f"{BOLD}{theme.fg_white}{item['title']:<28}{RESET}" if styled else f"{item['title']:<28}"
        det_fmt = f"{DIM}{item['detail']}{RESET}" if styled else item["detail"]
        add_line(f"  {k_fmt} {name_fmt} {det_fmt}")

    add_line(f"  {BOLD}{theme.fg_yellow}[0]{RESET if styled else ''} {BOLD}{theme.fg_white}{'Return to Terminal':<28}{RESET if styled else ''} {DIM}{'Close command palette'}{RESET if styled else ''}")

    if status_msg:
        lines.append(divider)
        add_line(f"{BOLD}{theme.fg_green}{status_msg.center(content_w)}{RESET}" if styled else status_msg.center(content_w))

    lines.append(divider)
    footer = "Type key or command name to trigger [0/Esc to close]"
    add_line(f"{DIM}{footer.center(content_w)}{RESET}" if styled else footer.center(content_w))
    lines.append(bot)

    return "\n".join(lines)


def run_theme_selector(width: int = 70) -> None:
    """Sub-palette to choose one of the 12 developer themes."""
    themes = list_themes()
    status_msg = ""
    while True:
        sys.stdout.write("\033[H\033[J")
        current = get_active_theme()
        sep_line = "=" * 64
        sub_sep = "-" * 64
        print("\n" + f"{current.fg_blue}{sep_line}{RESET}")
        print(f"  {BOLD}{current.fg_cyan}THEME SELECTOR // 13 DEVELOPER COLOR THEMES{RESET}")
        print(f"{current.fg_blue}{sep_line}{RESET}")
        print(f"  Active: {BOLD}{current.fg_purple}{current.display_name}{RESET}  (preview live swatches below)\n")

        for idx, t in enumerate(themes, 1):
            is_active = (t.id == current.id)
            marker = f" {BOLD}{current.fg_green}[ACTIVE]{RESET}" if is_active else ""
            swatch = f"{t.fg_purple}■ {t.fg_blue}■ {t.fg_cyan}■ {t.fg_green}■ {t.fg_yellow}■ {t.fg_red}■{RESET}"
            print(f"  {current.fg_yellow}[{idx:2d}]{RESET} {BOLD}{t.display_name:<20}{RESET} {swatch}{marker}")

        print(f"\n  {current.fg_yellow}[ 0]{RESET} Return to Command Center")
        print(f"{current.fg_blue}{sub_sep}{RESET}")
        if status_msg:
            print(f"  {status_msg}")
            print(f"{current.fg_blue}{sub_sep}{RESET}")
        sys.stdout.write(f"{BOLD}{current.fg_cyan}theme> {RESET}")
        sys.stdout.flush()

        try:
            choice = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if choice in ("0", "q", "exit", "back"):
            break

        selected = None
        if choice.isdigit():
            val = int(choice)
            if 1 <= val <= len(themes):
                selected = themes[val - 1]
        if not selected:
            for t in themes:
                if choice in (t.id.lower(), t.display_name.lower()):
                    selected = t
                    break

        if selected:
            set_theme(selected.id)
            new_theme = get_active_theme()
            status_msg = f"{new_theme.fg_green}[✓] Theme changed to {new_theme.display_name}!{RESET}"
        else:
            status_msg = f"{current.fg_red}[!] Unknown theme '{choice}'. Select 1-12 or 0.{RESET}"


def run_settings_view(player: PlayerStats, width: int = 70) -> None:
    """View game diagnostic settings."""
    import shutil
    cols, lines = shutil.get_terminal_size((80, 24))
    pet = get_terminal_pet()
    ambience = get_ambience_manager()
    theme = get_active_theme()

    sys.stdout.write("\033[H\033[J")
    sep_line = "=" * 60
    print("\n" + f"{theme.fg_blue}{sep_line}{RESET}")
    print(f"  {BOLD}{theme.fg_cyan}SYSTEM SETTINGS & DIAGNOSTICS{RESET}")
    print(f"{theme.fg_blue}{sep_line}{RESET}")
    print(f"  Terminal Size      : {cols} cols x {lines} lines")
    print(f"  Player Profile     : {player.character_name} (Level {player.level}, {player.rank})")
    print(f"  Active Theme       : {theme.fg_purple}{theme.display_name}{RESET} (ID: {theme.id})")
    print(f"  Terminal Pet       : {'Enabled' if pet.enabled else 'Disabled'}")
    print(f"  Matrix Rain        : {'Enabled' if ambience.rain_enabled else 'Disabled'}")
    print(f"  Calm Animations    : {'Enabled' if ambience.calm_animations else 'Disabled'}")
    print(f"  Sectors Liberated  : {len(player.completed_sectors)} / 27")
    print(f"  Save File Location : ~/.cybershell_save.json")
    print(f"{theme.fg_blue}{'-' * 60}{RESET}")
    print("Press Enter to return...")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass


def run_command_center(
    player: PlayerStats,
    all_quests: Optional[Dict[int, Quest]] = None,
    width: int = 80,
) -> Optional[str]:
    """Interactive loop for the Command Center.

    Returns an action string if an action requires handling in the main loop,
    or None if fully handled.
    """
    status_banner = ""
    while True:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(render_command_center(player, width=width, styled=True, status_msg=status_banner) + "\n")
        sys.stdout.write("cmd> ")
        sys.stdout.flush()
        status_banner = ""

        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            return None

        if not choice or choice in ("0", "q", "exit", "quit", "back"):
            return None

        choice_lower = choice.lower()

        if choice in ("1",) or "search" in choice_lower or "doc" in choice_lower:
            return "search_docs"

        if choice in ("2",) or "choose" in choice_lower or "challenge" in choice_lower or "level" in choice_lower:
            return "choose_challenge"

        if choice in ("3",) or "progress" in choice_lower or "dashboard" in choice_lower:
            from cybershell.ui.dashboard import view_progress_dashboard
            view_progress_dashboard(player, all_quests, width=width)
            continue

        if choice in ("4",) or "game" in choice_lower or "minigame" in choice_lower or "arcade" in choice_lower:
            from cybershell.tools.minigames.hub import view_minigames_hub
            view_minigames_hub(player, width=width)
            continue

        if choice in ("5",) or "manual" in choice_lower or "man" in choice_lower:
            return "open_manual"

        if choice in ("6",) or "reset" in choice_lower:
            return "reset_challenge"

        if choice in ("7",) or "pet" in choice_lower:
            pet = get_terminal_pet()
            new_s = pet.toggle()
            status_banner = f"[✓] Terminal Pet Byte is now {'ON' if new_s else 'OFF'}."
            continue

        if choice in ("8",) or "rain" in choice_lower:
            ambience = get_ambience_manager()
            new_r = ambience.toggle_rain()
            status_banner = f"[✓] Background Rain effect is now {'ON' if new_r else 'OFF'}."
            continue

        if choice in ("9",) or "anim" in choice_lower:
            ambience = get_ambience_manager()
            new_a = ambience.toggle_calm_animations()
            status_banner = f"[✓] Calm Animations are now {'ON' if new_a else 'OFF'}."
            continue

        if choice_lower in ("t", "theme", "themes", "color"):
            run_theme_selector(width=width)
            current_t = get_active_theme()
            status_banner = f"[✓] Active theme is {current_t.display_name}."
            continue

        if choice_lower in ("c", "chmod", "perm", "decoder"):
            from cybershell.tools.minigames.chmod_decoder import play_chmod_decoder_interactive
            play_chmod_decoder_interactive(player, width=width)
            continue

        if choice_lower in ("s", "setting", "settings", "diag"):
            run_settings_view(player, width=width)
            continue

        status_banner = f"[!] Unknown command '{choice}'. Enter 1-9, C, T, S, or 0."
