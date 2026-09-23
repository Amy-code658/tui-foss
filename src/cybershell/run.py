#!/usr/bin/env python3
"""Byte's Linux Adventure - Main Executable Launcher.

CLI launcher, argument parser, environment bootstrapper,
and interactive adventure loop controller.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import sys
import textwrap
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    readline = None
    READLINE_AVAILABLE = False

# Ensure src/ and project root are on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "cybershell":
    SRC_DIR = os.path.dirname(SCRIPT_DIR)
else:
    SRC_DIR = os.path.join(SCRIPT_DIR, "src")
PROJECT_ROOT = os.path.dirname(SRC_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cybershell import __version__
from cybershell.contracts import (
    DEFAULT_BACKLASH_DAMAGE,
    CommandResult,
    Item,
    Objective,
    PlayerStats,
    Quest,
)
from cybershell.engine.node import DirectoryNode, FSNode
from cybershell.engine.vfs import VirtualFileSystem
from cybershell.engine.interpreter import Interpreter
from cybershell.game.evaluator import QuestEvaluator
from cybershell.game.quests import get_sector_quests
from cybershell.tools.chmod_minigame import ChmodMinigame
from cybershell.tools.codex import Codex
from cybershell.tools.map import MainframeMap, render_adventure_map
from cybershell.ui.ascii_art import (
    ADVENTURE_LOGO,
    BLUE,
    BOLD,
    CYAN,
    CYBER_LOGO,
    DIM,
    FIELD_MANUAL_HEADER,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    WHITE,
    YELLOW,
    format_boss_hp_bar,
    get_access_granted_banner,
    get_level_unlocked_banner,
    get_logo,
    get_portrait,
    get_siren_banner,
    get_victory_banner,
)
from cybershell.ui.renderer import (
    PANEL_BOTTOM_LEFT,
    PANEL_BOTTOM_RIGHT,
    PANEL_DIVIDER_LEFT,
    PANEL_DIVIDER_RIGHT,
    PANEL_HORIZONTAL,
    PANEL_TOP_LEFT,
    PANEL_TOP_RIGHT,
    PANEL_VERTICAL,
    draw_compact_hud,
    draw_control_footer,
    draw_double_header,
    draw_field_manual_card,
    draw_panel,
    draw_question_card,
    draw_split_panels,
    draw_opencode_layout,
    pad_to_width,
    terminal_size,
    visual_len,
)
from cybershell.ui.rpg_app import RPGApp
from cybershell.ui.animation import CelebrationEffect, ScreenTransition, Typewriter
from cybershell.ui.theme import gradient_text, pill, HEX_CYAN, HEX_PURPLE, HEX_GREEN, HEX_YELLOW, HEX_BG_DARK, HEX_BLUE, FG_BORDER, RESET, BOLD


def wrap_text(text: str, width: int, prefix: str = "", style: str = "") -> List[str]:
    """Wrap text into readable complete sentences fitting width."""
    width = max(10, width)
    raw_text = str(text).strip()
    if not raw_text:
        return []
    lines = textwrap.wrap(raw_text, width=max(10, width - len(prefix)))
    if not lines:
        return [f"{style}{prefix}{RESET}"]
    reset = RESET if style else ""
    return [
        f"{style}{prefix if i == 0 else ' ' * len(prefix)}{line}{reset}"
        for i, line in enumerate(lines)
    ]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="cybershell",
        description="Byte's Linux Adventure - A Friendly Terminal Journey",
    )
    parser.add_argument(
        "--name", "-n",
        default="Byte",
        help="Explorer name (default: Byte)",
    )
    parser.add_argument(
        "--sector", "-s",
        type=int,
        default=0,
        help="Starting level ID (0-14, default: 0)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run UI showcase and exit",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run quick architectural smoke tests and exit",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"Byte's Linux Adventure v{__version__}",
    )
    return parser.parse_args()


def run_smoke_test() -> int:
    """Execute test suite as a diagnostic pre-flight check."""
    import unittest
    tests_dir = os.path.join(PROJECT_ROOT, "tests")
    if not os.path.isdir(tests_dir):
        tests_dir = "tests"
    suite = unittest.defaultTestLoader.discover(tests_dir, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


# =============================================================================
# PERSISTENCE & BEGINNER-FRIENDLY ASSIST TOOLS
# =============================================================================

SAVE_FILE_PATH = os.path.expanduser("~/.cybershell_save.json")


def save_game(
    player: PlayerStats,
    cadet_mode: bool = True,
    filepath: str = SAVE_FILE_PATH,
) -> bool:
    """Save player progression to JSON checkpoint file."""
    try:
        data = {
            "character_name": player.character_name,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "xp": player.xp,
            "level": player.level,
            "rank": player.rank,
            "current_sector": player.current_sector,
            "completed_sectors": list(player.completed_sectors),
            "inventory": [item.to_dict() for item in player.inventory],
            "badges": list(getattr(player, "badges", [])),
            "streak": getattr(player, "streak", 0),
            "max_streak": getattr(player, "max_streak", 0),
            "secrets_found": list(getattr(player, "secrets_found", [])),
            "cadet_mode": cadet_mode,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def load_saved_game(
    filepath: str = SAVE_FILE_PATH,
) -> Optional[Tuple[PlayerStats, bool]]:
    """Load player progression from checkpoint file."""
    if not os.path.isfile(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        player = PlayerStats(
            character_name=str(data.get("character_name", "Byte")),
            hp=int(data.get("hp", 100)),
            max_hp=int(data.get("max_hp", 100)),
            xp=int(data.get("xp", 0)),
            current_sector=int(data.get("current_sector", 0)),
        )
        player.level = int(data.get("level", 1))
        player.rank = str(data.get("rank", "Novice Explorer"))
        player.completed_sectors = set(data.get("completed_sectors", []))
        player.badges = list(data.get("badges", []))
        player.streak = int(data.get("streak", 0))
        player.max_streak = int(data.get("max_streak", 0))
        player.secrets_found = list(data.get("secrets_found", []))
        raw_inv = data.get("inventory", [])
        for item_dict in raw_inv:
            if isinstance(item_dict, dict):
                player.add_item(Item.from_dict(item_dict))
        cadet_mode = bool(data.get("cadet_mode", True))
        return player, cadet_mode
    except Exception:
        return None


def delete_saved_game(filepath: str = SAVE_FILE_PATH) -> bool:
    """Remove checkpoint save file."""
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
            return True
    except Exception:
        pass
    return False


KNOWN_COMMANDS = [
    "pwd", "ls", "cd", "cat", "less", "touch", "mkdir", "chmod", "grep",
    "find", "sort", "wc", "echo", "head", "tail", "cp", "mv", "rm",
    "man", "lookup", "help", "hint", "status", "badges",
    "clear", "tree", "explain", "menu", "codex",
    "items", "inventory", "map", "minigame", "cadet", "operative",
    "save", "exit", "quit",
]


def check_typo_or_syntax(cmd_str: str) -> Optional[Tuple[str, str]]:
    """Analyze command input for common beginner typos and missing spaces.

    Returns (suggested_command, coaching_explanation) if detected, else None.
    """
    raw = cmd_str.strip()
    if not raw:
        return None

    # Missing space after cd: cd.., cd/, cd~
    if raw.startswith("cd") and len(raw) > 2 and raw[2] in (".", "/", "~", "$"):
        suggested = f"cd {raw[2:]}"
        return (
            suggested,
            "In Linux, 'cd' requires a space before the destination folder (e.g. 'cd ..').",
        )

    # Missing space after ls: ls-la, ls-l, ls-a
    if raw.startswith("ls-"):
        suggested = f"ls -{raw[3:]}"
        return (
            suggested,
            "Command options require a space after 'ls' (e.g., 'ls -la' or 'ls -a').",
        )

    # Missing space after cat: catfile.txt -> cat file.txt
    if raw.startswith("cat") and len(raw) > 3 and raw[3] not in (" ", "-"):
        suggested = f"cat {raw[3:]}"
        return (
            suggested,
            "'cat' requires a space before the filename (e.g. 'cat note.txt').",
        )

    # Common command misspellings
    typo_map = {
        "pdw": ("pwd", "'pwd' stands for Print Working Directory."),
        "pwd.": ("pwd", "No dot needed after 'pwd'."),
        "sl": ("ls", "'ls' lists files in the current folder."),
        "lss": ("ls", "'ls' lists files in the current folder."),
        "cpt": ("cat", "'cat' prints file contents."),
        "caat": ("cat", "'cat' prints file contents."),
        "toush": ("touch", "'touch' creates a new empty file."),
        "touh": ("touch", "'touch' creates a new empty file."),
        "mrdir": ("mkdir", "'mkdir' creates a new folder."),
        "mdkir": ("mkdir", "'mkdir' creates a new folder."),
        "chomd": ("chmod", "'chmod' changes file permissions."),
        "chmdo": ("chmod", "'chmod' changes file permissions."),
        "gerp": ("grep", "'grep' searches for text inside files."),
        "grpe": ("grep", "'grep' searches for text inside files."),
        "gtrep": ("grep", "'grep' searches for text inside files."),
        "srot": ("sort", "'sort' sorts lines of text alphabetically."),
        "clera": ("clear", "'clear' clears the terminal screen."),
        "claer": ("clear", "'clear' clears the terminal screen."),
        "clea": ("clear", "'clear' clears the terminal screen."),
        "exlpain": ("explain", "'explain' shows how a command works."),
        "explayn": ("explain", "'explain' shows how a command works."),
    }
    first_token = raw.split()[0].lower()
    if first_token in typo_map:
        corr, explanation = typo_map[first_token]
        rest = raw[len(first_token):]
        return (f"{corr}{rest}", explanation)

    # Check 1-character edit distance against known commands
    if len(first_token) >= 3 and first_token not in KNOWN_COMMANDS:
        for known in KNOWN_COMMANDS:
            if abs(len(first_token) - len(known)) <= 1:
                diffs = sum(
                    1 for a, b in zip(first_token, known) if a != b
                ) + abs(len(first_token) - len(known))
                if diffs == 1:
                    rest = raw[len(first_token):]
                    return (
                        f"{known}{rest}",
                        f"Command '{first_token}' is not recognized.",
                    )

    return None


def render_vfs_tree(
    start_node: DirectoryNode,
    max_depth: int = 3,
) -> List[str]:
    """Render a visual directory tree of VFS folders and files with Unicode branches."""
    root_name = start_node.name or "/"
    lines: List[str] = [f"{BLUE}{BOLD}{root_name}{RESET}"]

    def _walk(dir_node: DirectoryNode, prefix: str, current_depth: int) -> None:
        if current_depth > max_depth:
            return
        items = sorted(
            dir_node.children.items(),
            key=lambda x: (not x[1].is_directory, x[0]),
        )
        total = len(items)
        for i, (name, child) in enumerate(items):
            is_last = (i == total - 1)
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "
            if child.is_directory:
                lines.append(f"{prefix}{connector}{BLUE}{BOLD}{name}/{RESET}")
                _walk(child, prefix + child_prefix, current_depth + 1)
            else:
                color = GREEN if (child.permissions & 0o111) else WHITE
                lines.append(f"{prefix}{connector}{color}{name}{RESET}")

    _walk(start_node, "", 1)
    return lines


def colorize_ls_output(stdout: str) -> List[str]:
    """Colorize directory contents in 'ls' and 'ls -la' output."""
    lines: List[str] = []
    for line in stdout.splitlines():
        if not line.strip():
            lines.append("")
            continue
        parts = line.split()
        if len(parts) >= 6 and len(parts[0]) in (9, 10):
            perms = parts[0]
            filename = " ".join(parts[5:])
            prefix_str = " ".join(parts[:5])
            if perms.startswith("d"):
                colored_name = f"{BLUE}{BOLD}{filename}/{RESET}"
            elif "x" in perms:
                colored_name = f"{GREEN}{BOLD}{filename}{RESET}"
            elif filename.startswith("."):
                colored_name = f"{DIM}{filename}{RESET}"
            else:
                colored_name = f"{WHITE}{filename}{RESET}"
            lines.append(f"{prefix_str} {colored_name}")
        else:
            colored_tokens: List[str] = []
            for token in parts:
                if token.endswith("/"):
                    colored_tokens.append(f"{BLUE}{BOLD}{token}{RESET}")
                elif token.startswith("."):
                    colored_tokens.append(f"{DIM}{token}{RESET}")
                else:
                    colored_tokens.append(f"{WHITE}{token}{RESET}")
            lines.append("  ".join(colored_tokens) if colored_tokens else line)
    return lines


class VFSTabCompleter:
    """Interactive command and path autocompleter using readline."""

    def __init__(self, vfs: VirtualFileSystem):
        self.vfs = vfs
        self.commands = list(KNOWN_COMMANDS)

    def complete(self, text: str, state: int) -> Optional[str]:
        """Return match for text at given state index."""
        begidx = readline.get_begidx() if readline else 0

        if begidx == 0:
            matches = [c for c in self.commands if c.startswith(text)]
        else:
            try:
                prefix = text
                dirname, basename = posixpath.split(prefix)
                target_node = self.vfs.cwd
                if dirname:
                    resolved = self.vfs.resolve_path(dirname)
                    if resolved and resolved.is_directory:
                        target_node = resolved
                matches = []
                for name, child in target_node.children.items():
                    if name.startswith(basename):
                        full_match = posixpath.join(dirname, name) if dirname else name
                        if child.is_directory:
                            full_match += "/"
                        matches.append(full_match)
            except Exception:
                matches = []

        if state < len(matches):
            return matches[state]
        return None


def setup_tab_completion(vfs: VirtualFileSystem) -> None:
    """Configure readline tab completion for shell commands and VFS files."""
    if not READLINE_AVAILABLE or readline is None:
        return
    completer = VFSTabCompleter(vfs)
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")
    try:
        readline.set_completer_delims(" \t\n")
    except Exception:
        pass


def get_progressive_hint(
    active_obj: Objective,
    tier: int,
    cadet_mode: bool = True,
) -> Tuple[str, int]:
    """Return progressive 3-tier hint with zero HP penalty.

    - Tier 1: General concept guidance.
    - Tier 2: Expected command syntax pattern.
    - Tier 3: Direct command solution.
    """
    hints = getattr(active_obj, "hints", None) or []
    if hints:
        idx = max(0, min(tier - 1, len(hints) - 1))
        tier_names = {1: "Concept Clue", 2: "Syntax Pattern", 3: "Direct Solution"}
        name = tier_names.get(tier, "Hint")
        msg = f"[Hint {tier}/3 • {name}] {hints[idx]}"
    else:
        if tier == 1:
            msg = f"[Hint 1/3 • Concept Clue] Your goal is: {active_obj.description}"
        elif tier == 2:
            syntax_tip = active_obj.syntax if active_obj.syntax else active_obj.command
            msg = f"[Hint 2/3 • Syntax Pattern] Try using: {syntax_tip}"
        else:
            sol = active_obj.command if active_obj.command else (active_obj.hint or "Execute command.")
            msg = f"[Hint 3/3 • Direct Solution] Type: {sol}"

    return msg, 0


def explain_command(
    cmd_input: str,
    active_obj: Optional[Objective] = None,
) -> List[str]:
    """Provide an interactive, beginner-friendly breakdown of command syntax."""
    tokens = cmd_input.strip().split()
    if len(tokens) <= 1:
        if active_obj and active_obj.command:
            return [
                f"{YELLOW}{BOLD}[ ACTIVE LEVEL COMMAND EXPLANATION ]{RESET}",
                f"  {CYAN}Command:{RESET} {WHITE}{BOLD}{active_obj.command}{RESET}",
                f"  {CYAN}Syntax:{RESET}  {YELLOW}{active_obj.syntax}{RESET}",
                f"  {CYAN}Purpose:{RESET} {WHITE}{active_obj.explanation}{RESET}",
                f"  {DIM}Type 'explain <cmd>' to inspect any other command (e.g. 'explain grep -i apple notes.txt').{RESET}",
            ]
        return [
            f"{YELLOW}[ COMMAND EXPLAINER ]{RESET}",
            f"{WHITE}Type 'explain <command>' to break down syntax, options, and arguments.{RESET}",
            f"{DIM}Examples: 'explain ls -a', 'explain chmod 755 run.sh', 'explain grep apple items.txt'{RESET}",
        ]

    cmd = tokens[1].lower()
    args = tokens[2:]

    lines = [f"{YELLOW}{BOLD}[ COMMAND BREAKDOWN: {' '.join(tokens[1:])} ]{RESET}"]

    if cmd == "pwd":
        lines.append(f"  {CYAN}pwd{RESET} : 'Print Working Directory'. Shows the full path of where you currently are.")
    elif cmd == "ls":
        lines.append(f"  {CYAN}ls{RESET} : 'List'. Displays files and folders in your current directory.")
        if any("-a" in a for a in args) or any("a" in a for a in args if a.startswith("-")):
            lines.append(f"  {YELLOW}-a{RESET} : Show all files, including hidden files that start with a dot (e.g. .hidden).")
        if any("-l" in a for a in args) or any("l" in a for a in args if a.startswith("-")):
            lines.append(f"  {YELLOW}-l{RESET} : Long format with details like permissions, size, and date.")
    elif cmd == "cd":
        lines.append(f"  {CYAN}cd{RESET} : 'Change Directory'. Moves you into another folder.")
        dest = args[0] if args else "~"
        if dest == "..":
            lines.append(f"  {YELLOW}..{RESET} : Go up one level to the parent folder.")
        elif dest in ("~", ""):
            lines.append(f"  {YELLOW}~{RESET}  : Go home to your main directory.")
    elif cmd == "cat":
        lines.append(f"  {CYAN}cat{RESET} : 'Concatenate / Print'. Reads and prints the text inside a file.")
    elif cmd == "grep":
        lines.append(f"  {CYAN}grep{RESET} : Searches text for lines matching a word or pattern.")
        if "-i" in args:
            lines.append(f"  {YELLOW}-i{RESET} : Case-insensitive search (matches uppercase or lowercase).")
    elif cmd == "chmod":
        lines.append(f"  {CYAN}chmod{RESET} : 'Change Mode' - Changes file permissions (who can read, write, or run a file).")
        if any("755" in a for a in args):
            lines.append(f"  {YELLOW}755{RESET} : Read, write, execute for owner; read and execute for others.")
    elif cmd == "sort":
        lines.append(f"  {CYAN}sort{RESET} : Sorts text lines alphabetically or numerically.")
    elif cmd == "wc":
        lines.append(f"  {CYAN}wc{RESET} : 'Word Count'. Counts lines (-l), words (-w), or characters (-m).")
    else:
        lines.append(f"  {CYAN}{cmd}{RESET} : Linux command. Type 'man {cmd}' for detailed examples.")

    return lines


# =============================================================================
# DEDICATED OPENING SCREEN & NAVIGATION
# =============================================================================

def render_opening_screen(
    player: PlayerStats,
    width: int = 80,
    cadet_mode: bool = True,
    has_save: bool = False,
) -> str:
    """Render the primary adventure opening screen."""
    width = max(60, width)
    inner_w = max(40, width - 4)

    # 1. Title Logo
    logo_raw = get_logo(styled=True)
    logo_lines = [
        pad_to_width(line, width, align="center")
        for line in logo_raw.strip("\n").splitlines()
    ]

    # 2. Player summary line
    total_levels = 15
    curr_lvl = min(total_levels, player.current_sector + 1)
    status_text_1 = (
        f"{CYAN}Explorer:{RESET} {WHITE}{BOLD}{player.character_name}{RESET}  |  "
        f"{YELLOW}Progress:{RESET} Level {curr_lvl}/{total_levels}  |  "
        f"{YELLOW}⭐ {player.xp} XP{RESET}  |  "
        f"{MAGENTA}🏆 {len(getattr(player, 'badges', []))} Badges{RESET}"
    )
    status_line_1 = pad_to_width(status_text_1, width, align="center")

    # 3. Minimal Boxy Menu Layout
    menu_title = "MAIN DIRECTORY • CHOOSE A DESTINATION"

    if has_save:
        options = [
            ("1", "Continue Adventure", f"Resume Level {curr_lvl}/15"),
            ("2", "Start New Game", "Begin fresh adventure from Level 1"),
            ("3", "Adventure Map", "See all 15 levels and your progress"),
            ("4", "Command Guide", "Browse Linux command handbook"),
            ("5", "Backpack & Items", "Inspect collected goodies and badges"),
            ("6", "Permissions Puzzle", "Practice chmod permissions minigame"),
            ("7", "Field Manual & Rules", "Read the adventure manual & rules"),
            ("0", "Exit Adventure", "Save and exit"),
        ]
    else:
        options = [
            ("1", "Start Adventure", "Begin Level 1: Look Around (pwd & ls)"),
            ("2", "Adventure Map", "See all 15 levels of the journey"),
            ("3", "Command Guide", "Browse Linux command handbook"),
            ("4", "Backpack & Items", "Inspect collected goodies and badges"),
            ("5", "Permissions Puzzle", "Practice chmod permissions minigame"),
            ("6", "Field Manual & Rules", "Read the adventure manual & rules"),
            ("0", "Exit Adventure", "Exit the game"),
        ]

    menu_content = []
    menu_content.append("")
    colors = [HEX_PURPLE, HEX_CYAN, HEX_PURPLE, HEX_GREEN, HEX_BLUE, HEX_YELLOW, HEX_CYAN, HEX_PURPLE]
    for num, label, summary in options:
        c = colors[int(num)] if num.isdigit() else HEX_PURPLE
        prefix = f"{pill(num, HEX_BG_DARK, c)}  {CYAN}{BOLD}{label:<22}{RESET}"
        menu_content.append(f"  {prefix} {WHITE}{summary}{RESET}")
    menu_content.append("")

    from cybershell.ui.renderer import draw_panel
    from cybershell.ui.theme import fg_hex
    menu_panel_lines = draw_panel(menu_title, menu_content, inner_w, styled=True, border_color=fg_hex(HEX_PURPLE))
    
    all_lines = (
        logo_lines
        + ["", status_line_1, ""]
        + [pad_to_width(line, width, align="center") for line in menu_panel_lines]
        + [""]
    )
    return "\n".join(all_lines)


# =============================================================================
# MANDATORY FIELD MANUAL & RULES SCREEN
# =============================================================================

def show_mandatory_field_manual(width: int = 80) -> None:
    """Display the short, mandatory Field Manual & Rules screen on first launch."""
    sys.stdout.write("\033[H\033[J")
    card = draw_field_manual_card(page=1, width=width, styled=True)
    for line in card.splitlines():
        print(f"  {line}")
    print()
    try:
        input(f"  {YELLOW}{BOLD}[ Press ENTER to start your adventure! 🌱 ]{RESET} ")
    except (KeyboardInterrupt, EOFError):
        pass


# =============================================================================
# DEDICATED SCREEN VIEWERS
# =============================================================================

def view_codex(codex: Codex, player: PlayerStats, width: int) -> None:
    """Display the friendly command guide with search capability."""
    card_w = min(max(40, width - 4), 74)
    while True:
        sys.stdout.write("\033[H\033[J")
        header = draw_double_header(
            player.character_name,
            player.hp,
            player.max_hp,
            player.xp,
            "COMMAND GUIDE",
            card_w,
            styled=True,
        )
        for h_line in header.splitlines():
            print(f"  {h_line}")
        print()
        print(f"  {GREEN}{BOLD}[ 🌱 LINUX COMMAND GUIDE ]{RESET}")
        desc = (
            "Browse handy Linux commands or search for what you want to do. "
            "Type a command name (e.g. 'cat', 'ls', 'grep', 'chmod') to see how it works!"
        )
        for line in textwrap.wrap(desc, width=card_w - 4):
            print(f"  {WHITE}{line}{RESET}")
        print()
        print(f"  {CYAN}{BOLD}AVAILABLE COMMANDS:{RESET}")
        cmds = [entry["name"] for entry in codex.list_commands()]
        chunk_size = 5
        for i in range(0, len(cmds), chunk_size):
            chunk = cmds[i : i + chunk_size]
            formatted = "    ".join(f"{GREEN}{cmd:<8}{RESET}" for cmd in chunk)
            print(f"    {formatted}")
        print()
        print(f"  {DIM}{'─' * card_w}{RESET}")
        try:
            term = input(
                f"  {YELLOW}Enter command or keyword (or press Enter / '0' to return to menu): {RESET}"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not term or term in ("0", "q", "quit", "exit", "back", "menu"):
            break

        entry_text = codex.display_command(term)
        if "Unknown command" not in entry_text:
            print()
            print(f"  {MAGENTA}{BOLD}=== GUIDE: {term.upper()} ==={RESET}")
            for e_line in entry_text.splitlines():
                print(f"  {WHITE}{e_line}{RESET}")
        else:
            term_lower = term.lower()
            matches = [
                entry for entry in codex.list_commands()
                if term_lower in entry["name"].lower()
                or term_lower in entry.get("description", "").lower()
            ]
            if matches:
                print()
                print(f"  {YELLOW}{BOLD}=== MATCHES FOR '{term}' ({len(matches)}) ==={RESET}")
                for m in matches:
                    print(f"    • {GREEN}{BOLD}{m['name']:<8}{RESET} : {WHITE}{m.get('description', '')}{RESET}")
            else:
                print(f"\n  {RED}No commands matching '{term}' found. Try 'ls', 'cat', or 'grep'!{RESET}")

        try:
            input(f"\n  {YELLOW}Press Enter to return to command list...{RESET}")
        except (KeyboardInterrupt, EOFError):
            break


def view_inventory(player: PlayerStats, width: int) -> None:
    """Display the player's backpack and collected goodies."""
    card_w = min(max(40, width - 4), 74)
    sys.stdout.write("\033[H\033[J")
    header = draw_double_header(
        player.character_name,
        player.hp,
        player.max_hp,
        player.xp,
        "BACKPACK & ITEMS",
        card_w,
        styled=True,
    )
    for h_line in header.splitlines():
        print(f"  {h_line}")
    print()
    print(f"  {YELLOW}{BOLD}[ 🎒 YOUR BACKPACK & GOODIES ]{RESET}")
    desc = "Special items, stars, and badges collected during your Linux journey."
    for line in textwrap.wrap(desc, width=card_w - 4):
        print(f"  {WHITE}{line}{RESET}")
    print()
    if not player.inventory:
        print(f"  {DIM}Your backpack is currently empty.{RESET}")
        print(f"  {GREEN}Complete levels and discover secrets to earn items and stars! 🌱{RESET}")
    else:
        for idx, itm in enumerate(player.inventory, start=1):
            rarity_col = MAGENTA if itm.rarity in ("epic", "legendary", "mythic") else GREEN
            print(f"  [{idx}] 🎁 {WHITE}{BOLD}{itm.name}{RESET} [{rarity_col}{itm.rarity.upper()}{RESET}]")
            print(f"       {CYAN}{itm.description}{RESET}")
            print()

    raw_badges = getattr(player, "badges", [])
    if raw_badges:
        print(f"\n  {YELLOW}{BOLD}BADGES EARNED:{RESET}")
        for b in raw_badges:
            print(f"    🏆 {b}")

    print(f"\n  {DIM}{'─' * card_w}{RESET}")
    try:
        input(f"  {YELLOW}Press Enter to return to Main Menu...{RESET}")
    except (KeyboardInterrupt, EOFError):
        pass


def view_map(mainframe: MainframeMap, player: PlayerStats, all_quests: Dict[int, Quest], width: int) -> None:
    """Display the friendly 15-level Adventure Map."""
    card_w = min(max(40, width - 4), 74)
    sys.stdout.write("\033[H\033[J")
    header = draw_double_header(
        player.character_name,
        player.hp,
        player.max_hp,
        player.xp,
        "ADVENTURE MAP (15 LEVELS)",
        card_w,
        styled=True,
    )
    for h_line in header.splitlines():
        print(f"  {h_line}")
    print()
    for m_line in render_adventure_map(player, all_quests, width=card_w).splitlines():
        print(f"  {m_line}")
    print(f"\n  {DIM}{'─' * card_w}{RESET}")
    try:
        input(f"  {YELLOW}Press Enter to return to Main Menu...{RESET}")
    except (KeyboardInterrupt, EOFError):
        pass


def view_minigame(minigame: ChmodMinigame, player: PlayerStats, width: int) -> None:
    """Run the interactive Chmod Permissions Minigame with learning lab and answer validation."""
    minigame.set_player(player)
    puzzle = minigame.active_puzzle or minigame.generate_puzzle()
    feedback: List[str] = []

    card_w = min(max(40, width - 4), 74)

    while True:
        sys.stdout.write("\033[H\033[J")
        header = draw_double_header(
            player.character_name,
            player.hp,
            player.max_hp,
            player.xp,
            "PERMISSIONS PUZZLE & LEARNING LAB",
            card_w,
            styled=True,
        )
        for h_line in header.splitlines():
            print(f"  {h_line}")
        print()

        # Permissions Learning Reference Card (compact 3 lines)
        print(f"  {YELLOW}{BOLD}[ 📖 PERMISSIONS FORMULA ]{RESET}")
        print(f"  {WHITE}Triads : {GREEN}[User/Owner]{WHITE} {CYAN}[Group]{WHITE} {MAGENTA}[Others]{RESET}")
        print(f"  {WHITE}Values : {BOLD}r (read) = 4{RESET}  |  {BOLD}w (write) = 2{RESET}  |  {BOLD}x (execute) = 1{RESET}  |  {DIM}- = 0{RESET}")
        print(f"  {DIM}Example: rwxr-xr-x -> User: 4+2+1=7 | Group: 4+0+1=5 | Others: 4+0+1=5  =>  755{RESET}")
        print()

        # Current Puzzle Card
        u_sym = puzzle.permission[0:3]
        g_sym = puzzle.permission[3:6]
        o_sym = puzzle.permission[6:9]

        inner_w = card_w - 2
        p_top = f"\033[92m{PANEL_TOP_LEFT}{PANEL_HORIZONTAL * inner_w}{PANEL_TOP_RIGHT}\033[0m"
        p_bot = f"\033[92m{PANEL_BOTTOM_LEFT}{PANEL_HORIZONTAL * inner_w}{PANEL_BOTTOM_RIGHT}\033[0m"
        p_div = f"\033[92m{PANEL_DIVIDER_LEFT}{PANEL_HORIZONTAL * inner_w}{PANEL_DIVIDER_RIGHT}\033[0m"

        def p_row(styled_content: str) -> str:
            pad = max(0, inner_w - visual_len(styled_content))
            return f"\033[92m{PANEL_VERTICAL}\033[0m{styled_content}{' ' * pad}\033[92m{PANEL_VERTICAL}\033[0m"

        p_lines = [
            f"  {p_top}",
            f"  {p_row(f'  {YELLOW}{BOLD}🚪 PUZZLE #{puzzle.door_number:02d} • Convert to 3-Digit Octal Code{RESET}')}",
            f"  {p_div}",
            f"  {p_row(f'  Symbolic Pattern : {BOLD}{WHITE}{puzzle.permission}{RESET}')}",
            f"  {p_row(f'    • {GREEN}User   (u){RESET}   : {WHITE}{u_sym}{RESET}   (r=4, w=2, x=1, -=0)')}",
            f"  {p_row(f'    • {CYAN}Group  (g){RESET}   : {WHITE}{g_sym}{RESET}   (r=4, w=2, x=1, -=0)')}",
            f"  {p_row(f'    • {MAGENTA}Others (o){RESET}   : {WHITE}{o_sym}{RESET}   (r=4, w=2, x=1, -=0)')}",
            f"  {p_bot}",
        ]
        for pl in p_lines:
            print(pl)
        print()

        if feedback:
            for fb in feedback:
                print(fb)
            print()

        try:
            guess = input(
                f"  {YELLOW}{BOLD}Enter 3-digit code (e.g. 755) ['h'=hint, 'n'=next, '0'=exit]: {RESET}"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            break

        guess_lower = guess.lower()
        if guess_lower in ("0", "q", "quit", "exit", "menu", "back"):
            break

        if not guess:
            feedback = [
                f"  {YELLOW}💡 Enter a 3-digit octal number (like 755 or 644) to test your answer!{RESET}",
                f"  {DIM}Type 'h' for a hint, 'n' to skip to next puzzle, or '0' to exit.{RESET}",
            ]
            continue

        if guess_lower in ("h", "hint", "?"):
            u_r = 4 if u_sym[0] == "r" else 0
            u_w = 2 if u_sym[1] == "w" else 0
            u_x = 1 if u_sym[2] == "x" else 0
            u_val = u_r + u_w + u_x
            feedback = [
                f"  {CYAN}{BOLD}💡 STEP-BY-STEP HINT:{RESET}",
                f"     1. User '{u_sym}' has values {u_r} + {u_w} + {u_x} = {BOLD}{u_val}{RESET} (1st digit).",
                f"     2. Next calculate Group '{g_sym}' and Others '{o_sym}' the same way!",
            ]
            continue

        if guess_lower in ("n", "next", "skip"):
            feedback = [
                f"  {DIM}Skipped puzzle #{puzzle.door_number:02d}. The correct code was {puzzle.answer}.{RESET}"
            ]
            puzzle = minigame.generate_puzzle()
            continue

        result = minigame.validate_answer(guess)
        if result.correct:
            u_val = (4 if u_sym[0] == "r" else 0) + (2 if u_sym[1] == "w" else 0) + (1 if u_sym[2] == "x" else 0)
            g_val = (4 if g_sym[0] == "r" else 0) + (2 if g_sym[1] == "w" else 0) + (1 if g_sym[2] == "x" else 0)
            o_val = (4 if o_sym[0] == "r" else 0) + (2 if o_sym[1] == "w" else 0) + (1 if o_sym[2] == "x" else 0)

            # Redraw screen with success celebration
            sys.stdout.write("\033[H\033[J")
            for h_line in header.splitlines():
                print(f"  {h_line}")
            print()
            for rl in [
                f"  {YELLOW}{BOLD}[ 📖 PERMISSIONS FORMULA ]{RESET}",
                f"  {WHITE}Triads : {GREEN}[User/Owner]{WHITE} {CYAN}[Group]{WHITE} {MAGENTA}[Others]{RESET}",
                f"  {WHITE}Values : {BOLD}r (read) = 4{RESET}  |  {BOLD}w (write) = 2{RESET}  |  {BOLD}x (execute) = 1{RESET}  |  {DIM}- = 0{RESET}",
                f"  {DIM}Example: rwxr-xr-x -> User: 4+2+1=7 | Group: 4+0+1=5 | Others: 4+0+1=5  =>  755{RESET}",
            ]:
                print(rl)
            print()
            for pl in p_lines:
                print(pl)
            print()
            print(f"  {GREEN}{BOLD}🎉 CORRECT! {puzzle.permission} = {puzzle.answer}!{RESET}")
            print(f"  {GREEN}   Breakdown: User={u_val} ({u_sym}), Group={g_val} ({g_sym}), Others={o_val} ({o_sym}){RESET}")
            if result.xp_awarded > 0:
                print(f"  {YELLOW}⭐ +{result.xp_awarded} XP awarded to {player.character_name}! Total XP: {player.xp}{RESET}")
            print()
            try:
                nxt = input(f"  {YELLOW}[ Press Enter for next puzzle, or 0 to exit ]{RESET} ").strip()
                if nxt in ("0", "q", "quit", "exit", "menu"):
                    break
            except (KeyboardInterrupt, EOFError):
                break
            feedback = [f"  {GREEN}✓ Solved puzzle #{puzzle.door_number:02d}! Here is your next puzzle:{RESET}"]
            puzzle = minigame.generate_puzzle()
        else:
            u_r = 4 if u_sym[0] == "r" else 0
            u_w = 2 if u_sym[1] == "w" else 0
            u_x = 1 if u_sym[2] == "x" else 0
            u_val = u_r + u_w + u_x

            g_r = 4 if g_sym[0] == "r" else 0
            g_w = 2 if g_sym[1] == "w" else 0
            g_x = 1 if g_sym[2] == "x" else 0
            g_val = g_r + g_w + g_x

            o_r = 4 if o_sym[0] == "r" else 0
            o_w = 2 if o_sym[1] == "w" else 0
            o_x = 1 if o_sym[2] == "x" else 0
            o_val = o_r + o_w + o_x

            feedback = [
                f"  {RED}{BOLD}❌ '{guess}' is not correct for '{puzzle.permission}'.{RESET}",
                f"  {YELLOW}Let's calculate step by step:{RESET}",
                f"    • {GREEN}User   '{u_sym}'{RESET} : {u_r} + {u_w} + {u_x} = {BOLD}{u_val}{RESET}",
                f"    • {CYAN}Group  '{g_sym}'{RESET} : {g_r} + {g_w} + {g_x} = {BOLD}{g_val}{RESET}",
                f"    • {MAGENTA}Others '{o_sym}'{RESET} : {o_r} + {o_w} + {o_x} = {BOLD}{o_val}{RESET}",
                f"  {WHITE}The matching code is {BOLD}{puzzle.answer}{RESET}.",
                f"  {DIM}Type the correct code, or press 'n' for a new puzzle, or '0' to exit.{RESET}",
            ]


def view_field_manual(width: int) -> None:
    """Display the Field Manual & Rules screen with compact 2-page navigation."""
    page = 1
    while True:
        sys.stdout.write("\033[H\033[J")
        card = draw_field_manual_card(page=page, width=width, styled=True)
        for line in card.splitlines():
            print(f"  {line}")
        print()
        if page == 1:
            prompt = f"  {YELLOW}{BOLD}[ Enter: Next Page (Commands) | 0 or q: Main Menu ]{RESET} "
        else:
            prompt = f"  {YELLOW}{BOLD}[ Enter: Main Menu | 1: Page 1 (Rules) | 0 or q: Main Menu ]{RESET} "
        try:
            choice = input(prompt).strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if choice in ("0", "q", "quit", "exit", "menu"):
            break
        if page == 1:
            if choice in ("1",):
                page = 1
            elif choice in ("", "n", "next", "2", "c", "cmd", "commands"):
                page = 2
            else:
                break
        else:
            if choice in ("2",):
                page = 2
            elif choice in ("1", "p", "prev", "back", "r", "rules"):
                page = 1
            else:
                break


# =============================================================================
# INTERACTIVE ADVENTURE GAME LOOP
# =============================================================================

def resolve_option_choice(
    user_input: str,
    active_obj: Optional[Objective],
) -> Tuple[Optional[str], Optional[str]]:
    """Check if user entered an option letter (A/B/C/D) or number (1/2/3/4).

    Returns:
        (command_to_execute, feedback_message)
    """
    if not active_obj or not getattr(active_obj, "options", None):
        return None, None

    choice = user_input.strip().upper()
    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3, "1": 0, "2": 1, "3": 2, "4": 3}
    if choice not in letter_map:
        return None, None

    idx = letter_map[choice]
    options = active_obj.options
    if idx >= len(options):
        return None, None

    selected_opt = options[idx]
    cmd_part = selected_opt.split(" - ")[0].strip()
    cmd_str = " ".join(cmd_part.split())

    correct_letter = getattr(active_obj, "correct_option", "A").upper()
    correct_idx = letter_map.get(correct_letter, 0)
    chosen_letter = ["A", "B", "C", "D"][idx]

    if idx == correct_idx:
        msg = f"💡 [{chosen_letter}] Correct! Running: {cmd_str}"
        return cmd_str, msg
    else:
        meaning = selected_opt.split(" - ")[1].strip() if " - " in selected_opt else selected_opt
        msg = f"💡 [{chosen_letter}] '{cmd_str}' is for {meaning}. Try looking for what solves our current task!"
        return None, msg


def interactive_game_loop(
    character_name: str = "Byte",
    start_sector: int = 0,
    player: Optional[PlayerStats] = None,
    vfs: Optional[VirtualFileSystem] = None,
    interpreter: Optional[Interpreter] = None,
    evaluator: Optional[QuestEvaluator] = None,
    all_quests: Optional[Dict[int, Quest]] = None,
    app: Optional[RPGApp] = None,
    cadet_mode: bool = True,
) -> None:
    """Interactive adventure terminal loop with compact rounded HUD."""
    if player is None:
        player = PlayerStats(
            character_name=character_name,
            hp=100,
            max_hp=100,
            xp=0,
            current_sector=start_sector,
        )
    if vfs is None:
        vfs = VirtualFileSystem(default_user="byte")
    if interpreter is None:
        interpreter = Interpreter(vfs=vfs)
    if evaluator is None:
        evaluator = QuestEvaluator()
    if all_quests is None:
        all_quests = get_sector_quests()
    if app is None:
        app = RPGApp(
            character_name=player.character_name,
            hp=player.hp,
            max_hp=player.max_hp,
            xp=player.xp,
        )

    app.set_screen(RPGApp.SCREEN_LAB)
    setup_tab_completion(vfs)

    quest = all_quests.get(player.current_sector)
    if not quest:
        quest = all_quests[0]

    # Preload level environment files into VFS
    vfs.load_sector(player.current_sector, quest)

    init_w, _ = terminal_size()
    box_w = min(init_w - 4, 68)

    # Initial logs
    ScreenTransition.wipe_screen(delay=0.005)
    if player.current_sector == 0 and not quest.is_completed:
        Typewriter.stream_text("🌱 Welcome to Level 1: Look Around!", styled_prefix=GREEN, delay=0.015)
        Typewriter.stream_text("Solve the challenge question above by typing the command or option letter!", styled_prefix=CYAN, delay=0.015)
        Typewriter.stream_text("Tip: Type '?' for a hint, 'map' for level map.", styled_prefix=DIM, delay=0.015)
        terminal_logs: List[str] = [
            f"{GREEN}🌱 Welcome to Level 1: Look Around!{RESET}",
            f"{CYAN}Solve the challenge question above by typing the command or option letter!{RESET}",
            f"{DIM}Tip: Type '?' for a hint, 'map' for level map.{RESET}",
        ]
    else:
        lvl_display = player.current_sector + 1
        Typewriter.stream_text(f"🌱 Entering Level {lvl_display}/15: {quest.sector_name}!", styled_prefix=GREEN, delay=0.015)
        terminal_logs = [
            f"{GREEN}🌱 Entering Level {lvl_display}/15: {quest.sector_name}!{RESET}",
            f"{DIM}Type 'help' for commands, '?' for a hint, 'map' for level map.{RESET}",
        ]

    hint_tier = 1
    last_objective_id: Optional[str] = None
    level_start_badges = list(getattr(player, "badges", []))
    docs_filter_term = ""

    while True:
        width, height = terminal_size()
        app.hp = player.hp
        app.max_hp = player.max_hp
        app.xp = player.xp
        app.inventory = player.inventory

        # Active objective tracking
        active_obj = quest.current_objective
        if active_obj:
            obj_desc = active_obj.description
        else:
            obj_desc = "All level goals complete! Type 'next' or explore freely."

        if active_obj and active_obj.id != last_objective_id:
            last_objective_id = active_obj.id
            hint_tier = 1

        cwd_path = vfs.get_cwd_path()
        cwd_short = cwd_path.replace(f"/home/{vfs.user}", "~")

        task_inner_w = int(width * 0.70) - 4
        # Compact task content
        task_content = []
        task_content.append(f"{YELLOW}Level {player.current_sector + 1}/15: {quest.sector_name}{RESET}")
        if active_obj:
            task_content.append("")
            desc = getattr(active_obj, 'question', '') or active_obj.description
            for line in textwrap.wrap(desc, width=task_inner_w):
                task_content.append(f"{BOLD}{line}{RESET}")
            if getattr(active_obj, "options", None):
                task_content.append("")
                for idx, opt in enumerate(active_obj.options):
                    letter = ["A", "B", "C", "D"][idx]
                    for i, opt_line in enumerate(textwrap.wrap(opt, width=task_inner_w - 6)):
                        if i == 0:
                            task_content.append(f"  [{letter}] {opt_line}")
                        else:
                            task_content.append(f"      {opt_line}")
        else:
            task_content.append("")
            task_content.append("All level goals complete! Type 'next'.")

        docs_inner_w = int(width * 0.30) - 4
        # Docs content
        docs_content = []
        if docs_filter_term:
            filtered_cmds = []
            term = docs_filter_term.lower()
            for cmd in app.codex.list_commands():
                matches = term in cmd['name'].lower() or term in cmd['description'].lower()
                match_extra = None
                
                if not matches and 'flags' in cmd:
                    for f_name, f_desc in cmd['flags'].items():
                        if term in f_name.lower() or term in f_desc.lower():
                            matches = True
                            match_extra = f"Flag {f_name}: {f_desc}"
                            break
                            
                if not matches and 'examples' in cmd:
                    for ex in cmd['examples']:
                        if term in ex.lower():
                            matches = True
                            match_extra = f"Ex: {ex}"
                            break
                            
                if not matches and 'combos' in cmd:
                    for cb in cmd['combos']:
                        if term in cb.lower():
                            matches = True
                            match_extra = f"Combo: {cb}"
                            break
                
                if matches:
                    cmd_copy = dict(cmd)
                    if match_extra:
                        cmd_copy['_match_extra'] = match_extra
                    filtered_cmds.append(cmd_copy)
            docs_content.append(f"{YELLOW}Search: '{docs_filter_term}'{RESET}")
        else:
            filtered_cmds = app.codex.list_commands()
            
        for cmd in filtered_cmds[:15]:
            desc_lines = textwrap.wrap(cmd['description'], width=docs_inner_w - 9)
            if not desc_lines:
                desc_lines = [""]
            docs_content.append(f"{CYAN}{cmd['name']:<8}{RESET} {DIM}{desc_lines[0]}{RESET}")
            for extra_line in desc_lines[1:]:
                docs_content.append(f"         {DIM}{extra_line}{RESET}")
                
            if '_match_extra' in cmd:
                match_lines = textwrap.wrap(cmd['_match_extra'], width=docs_inner_w - 4)
                for ml in match_lines:
                    docs_content.append(f"    {GREEN}{ml}{RESET}")
                
        if not filtered_cmds:
            docs_content.append(f"{RED}No results found.{RESET}")
            
        docs_content.append("")
        docs_content.append(f"{DIM}Type 'search <term>' to filter{RESET}")

        # Mascot content
        mascot_content = get_portrait(player.character_name, styled=True)
        quotes = ["You got this! 🌱", "Keep exploring!", "Every error is a lesson!"]
        mascot_content.append("")
        mascot_content.append(f"{GREEN}{quotes[player.xp % len(quotes)]}{RESET}".center(30))

        layout = draw_opencode_layout(
            task_title="YOUR TASK", task_content=task_content,
            term_title="TERMINAL", term_content=terminal_logs,
            docs_title="LOCAL DOCS", docs_content=docs_content,
            mascot_content=mascot_content,
            width=width, height=height - 2, # leaving room for prompt
            gap=1, styled=True
        )

        footer = draw_control_footer(screen_type="terminal", width=width, styled=True)

        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(layout + "\n")
        sys.stdout.write(pad_to_width(footer, width, align="center") + "\n")
        sys.stdout.flush()

        try:
            prompt = f"\033[1;92mbyte@adventure\033[0m:\033[1;94m{cwd_short}\033[0m$ "
            user_input = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            save_game(player, cadet_mode)
            print(f"\n{CYAN}Returning to Main Menu...{RESET}")
            break

        if not user_input:
            continue

        input_lower = user_input.lower()

        # Return to main menu
        if input_lower in ("0", "menu", "main", "back", "title"):
            save_game(player, cadet_mode)
            break

        if input_lower in ("exit", "quit"):
            save_game(player, cadet_mode)
            break

        # In-game viewers
        if input_lower in ("codex",):
            view_codex(app.codex, player, width)
            continue

        if input_lower in ("items", "inventory", "backpack"):
            view_inventory(player, width)
            continue

        if input_lower in ("map",):
            view_map(app.mainframe, player, all_quests, width)
            continue

        if input_lower in ("minigame", "puzzle"):
            view_minigame(app.minigame, player, width)
            continue

        if input_lower == "clear":
            terminal_logs = []
            continue

        if input_lower.startswith("search "):
            docs_filter_term = input_lower[7:].strip()
            terminal_logs.append(f"{GREEN}byte@adventure:{cwd_short}$ {user_input}{RESET}")
            terminal_logs.append(f"{CYAN}Filtered LOCAL DOCS by '{docs_filter_term}'{RESET}")
            continue
        elif input_lower == "search":
            docs_filter_term = ""
            terminal_logs.append(f"{GREEN}byte@adventure:{cwd_short}$ {user_input}{RESET}")
            terminal_logs.append(f"{CYAN}Cleared LOCAL DOCS filter.{RESET}")
            continue

        if input_lower == "save":
            saved = save_game(player, cadet_mode)
            terminal_logs.append(f"{GREEN}byte@adventure:{cwd_short}$ save{RESET}")
            if saved:
                terminal_logs.append(f"{GREEN}💾 Progress saved successfully!{RESET}")
            else:
                terminal_logs.append(f"{RED}Failed to write save file.{RESET}")
            continue

        if input_lower in ("status", "badges", "stats"):
            terminal_logs.append(f"{GREEN}byte@adventure:{cwd_short}$ {user_input}{RESET}")
            terminal_logs.append(f"{CYAN}{BOLD}[ EXPLORER STATS ]{RESET}")
            terminal_logs.append(
                f"  {WHITE}Explorer:{RESET} {CYAN}{player.character_name}{RESET}  "
                f"{YELLOW}Level:{RESET} {player.current_sector + 1}/15  "
                f"{YELLOW}⭐ XP:{RESET} {player.xp}  "
                f"{GREEN}Streak:{RESET} {getattr(player, 'streak', 0)}"
            )
            raw_badges = getattr(player, "badges", [])
            badges_str = " ".join(f"[{b}]" for b in raw_badges) if raw_badges else "None yet"
            terminal_logs.append(f"  {YELLOW}Badges:{RESET} {badges_str}")
            continue

        if input_lower.startswith("tree"):
            terminal_logs.append(f"{GREEN}byte@adventure:{cwd_short}$ {user_input}{RESET}")
            parts = user_input.split(maxsplit=1)
            target_path = parts[1] if len(parts) > 1 else "."
            node = vfs.resolve_path(target_path)
            if node is None:
                terminal_logs.append(f"{RED}tree: {target_path}: No such file or directory{RESET}")
            elif not node.is_directory:
                terminal_logs.append(f"{WHITE}{node.name}{RESET}")
                terminal_logs.append(f"{DIM}0 directories, 1 file{RESET}")
            else:
                for tl in render_vfs_tree(node):
                    terminal_logs.append(tl)
            continue

        if input_lower.startswith("explain"):
            terminal_logs.append(f"{GREEN}byte@adventure:{cwd_short}$ {user_input}{RESET}")
            for el in explain_command(user_input, active_obj):
                terminal_logs.append(el)
            continue

        if input_lower in ("hint", "?"):
            terminal_logs.append(f"{GREEN}byte@adventure:{cwd_short}$ {user_input}{RESET}")
            if not active_obj:
                terminal_logs.append(f"{GREEN}All goals in this level are complete! Great job! 🌱{RESET}")
            else:
                if hasattr(player, "use_hint"):
                    player.use_hint()
                h_msg, _ = get_progressive_hint(active_obj, hint_tier, cadet_mode=True)
                terminal_logs.append(f"{YELLOW}{BOLD}💡 {h_msg}{RESET}")
                hint_tier = min(3, hint_tier + 1)
            continue

        cmd_start_index = len(terminal_logs)

        # Check for option selection [A/B/C/D] or [1/2/3/4]
        opt_cmd, opt_msg = resolve_option_choice(user_input, active_obj)
        if opt_cmd is not None:
            terminal_logs.append(f"{GREEN}{opt_msg}{RESET}")
            actual_cmd = opt_cmd
        elif opt_msg is not None:
            terminal_logs.append(f"{YELLOW}{opt_msg}{RESET}")
            # Also execute the selected command so the player sees the output!
            choice = user_input.strip().upper()
            letter_map = {"A": 0, "B": 1, "C": 2, "D": 3, "1": 0, "2": 1, "3": 2, "4": 3}
            idx = letter_map.get(choice, 0)
            if active_obj and getattr(active_obj, "options", None) and idx < len(active_obj.options):
                opt_str = active_obj.options[idx]
                cmd_to_show = opt_str.split(" - ")[0].strip()
                terminal_logs.append(f"{GREEN}byte@adventure:{cwd_short}$ {cmd_to_show}{RESET}")
                res = interpreter.execute(cmd_to_show)
                if res.stdout:
                    first_cmd = cmd_to_show.split()[0] if cmd_to_show.split() else ""
                    if first_cmd == "ls":
                        for out_line in colorize_ls_output(res.stdout):
                            terminal_logs.append(out_line)
                    else:
                        for out_line in res.stdout.splitlines():
                            terminal_logs.append(f"{WHITE}{out_line}{RESET}")
                if res.stderr:
                    for err_line in res.stderr.splitlines():
                        terminal_logs.append(f"{RED}{err_line}{RESET}")
                terminal_logs.append(f"{DIM}💡 Output shown above. Review the question card to find the command needed for this task!{RESET}")
            continue
        else:
            actual_cmd = user_input

        # Check for beginner typo before execution
        typo = check_typo_or_syntax(actual_cmd)

        # Execute command in VFS
        terminal_logs.append(f"{GREEN}byte@adventure:{cwd_short}$ {actual_cmd}{RESET}")
        result = interpreter.execute(actual_cmd)

        if typo:
            sugg, expl = typo
            
            terminal_logs.append(f"{YELLOW}💡 [TIP] Detected '{actual_cmd}'. Did you mean '{sugg}'? {expl}{RESET}")

        if result.stdout:
            first_cmd = actual_cmd.split()[0] if actual_cmd.split() else ""
            if first_cmd == "ls":
                for out_line in colorize_ls_output(result.stdout):
                    terminal_logs.append(out_line)
            else:
                for out_line in result.stdout.splitlines():
                    terminal_logs.append(f"{WHITE}{out_line}{RESET}")

        if result.stderr:
            for err_line in result.stderr.splitlines():
                terminal_logs.append(f"{RED}{err_line}{RESET}")
            if not typo:
                terminal_logs.append(f"{DIM}💡 Type '?' or 'help' if you'd like a hint.{RESET}")

        # Objective evaluation
        old_level = player.level
        is_completed, newly_completed = evaluator.check_quest_progress(
            quest, vfs, player, last_command=actual_cmd
        )

        if not result.stderr and result.exit_code == 0 and not newly_completed and not result.stdout:
            first_cmd = actual_cmd.strip().split()[0] if actual_cmd.strip() else ""
            if first_cmd in ("touch", "mkdir", "cd", "chmod", "cp", "mv", "rm"):
                terminal_logs.append(f"{DIM}✓ Done!{RESET}")

        if newly_completed:
            hint_tier = 1
            reward_sum = sum(
                (next((o.xp_reward for o in quest.objectives if o.id == item), 50) if isinstance(item, str) else item.xp_reward)
                for item in newly_completed
            )
            save_game(player, cadet_mode)

            # Preserve current command output, while clearing older clutter from previous attempts
            recent_logs = list(terminal_logs[cmd_start_index:])
            terminal_logs.clear()
            terminal_logs.extend(recent_logs)

            if is_completed:
                if hasattr(player, "mark_sector_completed"):
                    player.mark_sector_completed(quest.sector_id)
                elif isinstance(player.completed_sectors, set):
                    player.completed_sectors.add(quest.sector_id)
                elif quest.sector_id not in player.completed_sectors:
                    player.completed_sectors.append(quest.sector_id)

                celebration = CelebrationEffect.render_celebration(
                    title=f"LEVEL {quest.sector_id + 1} COMPLETED!",
                    subtitle=f"Sector: {quest.sector_name.upper()} | +{reward_sum} XP",
                    width=width,
                    animate=False,
                )
                for c_line in celebration.splitlines():
                    terminal_logs.append(c_line)

                # Show badge status change only after level completion (not in between tasks)
                curr_badges = list(getattr(player, "badges", []))
                level_badges = [b for b in curr_badges if b not in level_start_badges]
                if level_badges:
                    for nb in level_badges:
                        terminal_logs.append(f"{YELLOW}🏆 BADGE UNLOCKED: [{nb}]{RESET}")
                    terminal_logs.append(f"{CYAN}Explorer Badges: {len(curr_badges)}/15 Unlocked ⭐{RESET}")
                level_start_badges = list(curr_badges)

                if quest.reward_item:
                    terminal_logs.append(f"{YELLOW}🎁 GOODIE ACQUIRED: {quest.reward_item.name} - {quest.reward_item.description}{RESET}")

                next_sector = player.current_sector + 1
                if next_sector in all_quests:
                    player.current_sector = next_sector
                    quest = all_quests[next_sector]
                    vfs.load_sector(next_sector, quest)
                    save_game(player, cadet_mode)

                    unlock_banner = get_level_unlocked_banner(
                        sector_num=next_sector + 1,
                        sector_name=quest.sector_name,
                        width=min(width - 4, 60),
                        styled=True,
                    )
                    for u_line in unlock_banner.splitlines():
                        terminal_logs.append(u_line)
                    Typewriter.stream_text(f'"{quest.lore[:80]}..."', delay=0.02, styled_prefix=f"{GREEN}Guide {quest.npc_name}: ")
                    terminal_logs.append(f"{GREEN}Guide {quest.npc_name}: \"{quest.lore[:80]}...\"{RESET}")
                else:
                    save_game(player, cadet_mode)
                    for v_line in get_victory_banner(styled=True).splitlines():
                        terminal_logs.append(v_line)
            else:
                # Clean slate for next question in this level! ("one task kazhiyumbo")
                completed_names = []
                for item in newly_completed:
                    matched_obj = next((o for o in quest.objectives if o.id == item), None) if isinstance(item, str) else item
                    desc = matched_obj.description if matched_obj else str(item)
                    completed_names.append(desc)
                summary_text = " & ".join(completed_names)
                terminal_logs.append(f"{GREEN}✓ Task Cleared: {summary_text} (+{reward_sum} XP ⭐){RESET}")
                terminal_logs.append(f"{CYAN}Here is your next challenge question! Check the card above. 🌱{RESET}")

        if player.level > old_level:
            terminal_logs.append(f"{MAGENTA}{BOLD}🌟 LEVEL UP! You reached Level {player.level}! Title: {player.rank}{RESET}")
            Typewriter.stream_text(f"🌟 LEVEL UP! You reached Level {player.level}! Title: {player.rank}", delay=0.015, styled_prefix=f"{MAGENTA}{BOLD}")


# =============================================================================
# MAIN MENU CONTROLLER LOOP
# =============================================================================

def main_menu_loop(character_name: str = "Byte", start_sector: int = 0) -> None:
    """Main menu loop with navigation and first-time field manual."""
    saved_data = load_saved_game()
    cadet_mode = True
    first_launch = saved_data is None

    if saved_data is not None:
        player, cadet_mode = saved_data
    else:
        player = PlayerStats(
            character_name=character_name,
            hp=100,
            max_hp=100,
            xp=0,
            current_sector=start_sector,
        )

    vfs = VirtualFileSystem(default_user="byte")
    interpreter = Interpreter(vfs=vfs)
    evaluator = QuestEvaluator()
    all_quests = get_sector_quests()

    app = RPGApp(
        character_name=player.character_name,
        hp=player.hp,
        max_hp=player.max_hp,
        xp=player.xp,
    )

    # First launch shows the mandatory Field Manual & Rules screen!
    if first_launch:
        width, _ = terminal_size()
        show_mandatory_field_manual(width)
        interactive_game_loop(
            character_name=player.character_name,
            start_sector=0,
            player=player,
            vfs=vfs,
            interpreter=interpreter,
            evaluator=evaluator,
            all_quests=all_quests,
            app=app,
            cadet_mode=cadet_mode,
        )

    while True:
        has_save = os.path.isfile(SAVE_FILE_PATH)
        width, _ = terminal_size()
        sys.stdout.write("\033[H\033[J")
        print(render_opening_screen(player, width, cadet_mode=cadet_mode, has_save=has_save))

        max_option = 7 if has_save else 6
        try:
            choice = input(f"\n{YELLOW}Choose an option [0-{max_option}] (default: 1): {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{CYAN}See you next time! Happy exploring 🌱{RESET}\n")
            break

        if not choice:
            choice = "1"

        choice_lower = choice.lower()
        if choice_lower in ("0", "exit", "quit", "q"):
            print(f"\n{CYAN}See you next time! Happy exploring 🌱{RESET}\n")
            break

        if has_save:
            if choice_lower in ("1", "continue", "resume", "c", "start"):
                interactive_game_loop(
                    character_name=player.character_name,
                    start_sector=player.current_sector,
                    player=player,
                    vfs=vfs,
                    interpreter=interpreter,
                    evaluator=evaluator,
                    all_quests=all_quests,
                    app=app,
                    cadet_mode=cadet_mode,
                )
            elif choice_lower in ("2", "new", "reset"):
                delete_saved_game()
                player = PlayerStats(
                    character_name=character_name,
                    hp=100,
                    max_hp=100,
                    xp=0,
                    current_sector=0,
                )
                vfs = VirtualFileSystem(default_user="byte")
                interpreter = Interpreter(vfs=vfs)
                all_quests = get_sector_quests()
                show_mandatory_field_manual(width)
                interactive_game_loop(
                    character_name=player.character_name,
                    start_sector=0,
                    player=player,
                    vfs=vfs,
                    interpreter=interpreter,
                    evaluator=evaluator,
                    all_quests=all_quests,
                    app=app,
                    cadet_mode=cadet_mode,
                )
            elif choice_lower in ("3", "map"):
                view_map(app.mainframe, player, all_quests, width)
            elif choice_lower in ("4", "codex", "guide"):
                view_codex(app.codex, player, width)
            elif choice_lower in ("5", "items", "inventory", "backpack"):
                view_inventory(player, width)
            elif choice_lower in ("6", "minigame", "puzzle", "chmod"):
                view_minigame(app.minigame, player, width)
            elif choice_lower in ("7", "manual", "help", "rules"):
                view_field_manual(width)
            else:
                print(f"\n{RED}That's not an option here 🙂 Please choose [0-{max_option}].{RESET}")
                try:
                    input(f"{YELLOW}Press Enter to continue...{RESET}")
                except (KeyboardInterrupt, EOFError):
                    break
        else:
            if choice_lower in ("1", "start", "play"):
                show_mandatory_field_manual(width)
                interactive_game_loop(
                    character_name=player.character_name,
                    start_sector=player.current_sector,
                    player=player,
                    vfs=vfs,
                    interpreter=interpreter,
                    evaluator=evaluator,
                    all_quests=all_quests,
                    app=app,
                    cadet_mode=cadet_mode,
                )
            elif choice_lower in ("2", "map"):
                view_map(app.mainframe, player, all_quests, width)
            elif choice_lower in ("3", "codex", "guide"):
                view_codex(app.codex, player, width)
            elif choice_lower in ("4", "items", "inventory", "backpack"):
                view_inventory(player, width)
            elif choice_lower in ("5", "minigame", "puzzle", "chmod"):
                view_minigame(app.minigame, player, width)
            elif choice_lower in ("6", "manual", "help", "rules"):
                view_field_manual(width)
            else:
                print(f"\n{RED}That's not an option here 🙂 Please choose [0-{max_option}].{RESET}")
                try:
                    input(f"{YELLOW}Press Enter to continue...{RESET}")
                except (KeyboardInterrupt, EOFError):
                    break


def run_demo(character_name: str = "Byte") -> None:
    """Showcase UI rendering across screens."""
    width, _ = terminal_size()
    app = RPGApp(character_name=character_name, hp=100, max_hp=100, xp=45)
    player = PlayerStats(character_name=character_name, hp=100, max_hp=100, xp=45)

    screens = [
        ("TITLE & OPENING SCREEN", lambda: render_opening_screen(player, width, cadet_mode=True, has_save=False)),
        ("PLAYGROUND SCREEN", lambda: app.render_lab(width)),
        ("COMMAND GUIDE SCREEN", lambda: app.render_codex(width)),
        ("ADVENTURE MAP SCREEN", lambda: app.render_map(width)),
    ]

    for title, render_fn in screens:
        sys.stdout.write("\033[H\033[J")
        print("=" * width)
        print(f"--- {title} ---".center(width))
        print(render_fn())
        if sys.stdin.isatty():
            try:
                input(f"\n{YELLOW}Press Enter to view next screen (or Ctrl+C to exit demo)...{RESET}")
            except (KeyboardInterrupt, EOFError):
                break


def main() -> int:
    """Main program entrypoint."""
    args = parse_args()

    if args.smoke_test:
        return run_smoke_test()

    if args.demo:
        run_demo(args.name)
        return 0

    try:
        # Enter alternate screen buffer to prevent scrollback bleeding
        sys.stdout.write("\033[?1049h\033[H")
        sys.stdout.flush()
        main_menu_loop(args.name, args.sector)
    finally:
        # Exit alternate screen buffer safely
        sys.stdout.write("\033[?1049l")
        sys.stdout.flush()
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
