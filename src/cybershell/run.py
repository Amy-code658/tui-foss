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
import random
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
    get_foss_penguin,
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
    draw_overthewire_card,
    draw_statusline,
    draw_progress_bar,
    draw_split_panels,
    draw_opencode_layout,
    pad_to_width,
    terminal_size,
    visual_len,
)
from cybershell.ui.search import fuzzy_search_commands, render_telescope_results
from cybershell.ui.rpg_app import RPGApp
from cybershell.ui.animation import CelebrationEffect, ScreenTransition, Typewriter, animate_tux_welcome
from cybershell.ui.theme import (
    get_active_theme,
    set_theme,
    list_themes,
    THEMES,
    gradient_text,
    pill,
    HEX_CYAN,
    HEX_PURPLE,
    HEX_GREEN,
    HEX_YELLOW,
    HEX_BG_DARK,
    HEX_BLUE,
    FG_BORDER,
    RESET,
    BOLD,
    FG_WHITE,
    FG_MUTED,
)
from cybershell.ui.pet import get_terminal_pet
from cybershell.ui.ambience import get_ambience_manager
from cybershell.ui.dashboard import view_progress_dashboard, render_progress_dashboard
from cybershell.ui.command_center import run_command_center, run_theme_selector
from cybershell.tools.minigames.hub import view_minigames_hub
from cybershell.tools.codex import format_field_manual_entry, get_contextual_commands


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


def get_save_path(username: Optional[str] = None) -> str:
    """Return user-specific save path or default save path."""
    if not username:
        return SAVE_FILE_PATH
    clean = "".join(c for c in username.lower() if c.isalnum() or c in ("-", "_")).strip()
    if not clean or clean in ("explorer", "byte", "default"):
        return SAVE_FILE_PATH
    return os.path.expanduser(f"~/.cybershell_save_{clean}.json")


def get_last_saved_username() -> Optional[str]:
    """Retrieve the username from the most recent save file if available."""
    default_path = os.path.expanduser("~/.cybershell_save.json")
    candidates: List[Tuple[float, str]] = []
    if os.path.isfile(default_path):
        candidates.append((os.path.getmtime(default_path), default_path))

    import glob
    for p in glob.glob(os.path.expanduser("~/.cybershell_save_*.json")):
        if os.path.isfile(p):
            candidates.append((os.path.getmtime(p), p))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    most_recent = candidates[0][1]
    try:
        with open(most_recent, "r", encoding="utf-8") as f:
            data = json.load(f)
        name = str(data.get("character_name", "")).strip()
        if name:
            return name
    except Exception:
        pass
    return None


def save_game(
    player: PlayerStats,
    cadet_mode: bool = True,
    filepath: Optional[str] = None,
) -> bool:
    """Save player progression to JSON checkpoint file."""
    if filepath is None:
        filepath = get_save_path(player.character_name)
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

        default_file = os.path.expanduser("~/.cybershell_save.json")
        if filepath != default_file:
            try:
                with open(default_file, "w", encoding="utf-8") as f_def:
                    json.dump(data, f_def, indent=2)
            except Exception:
                pass
        return True
    except Exception:
        return False


def load_saved_game(
    filepath: Optional[str] = None,
    username: Optional[str] = None,
) -> Optional[Tuple[PlayerStats, bool]]:
    """Load player progression from checkpoint file."""
    target_path = filepath
    if target_path is None:
        if username:
            candidate = get_save_path(username)
            if os.path.isfile(candidate):
                target_path = candidate
            else:
                default_file = os.path.expanduser("~/.cybershell_save.json")
                if os.path.isfile(default_file):
                    try:
                        with open(default_file, "r", encoding="utf-8") as f:
                            d = json.load(f)
                        if str(d.get("character_name", "")).strip().lower() == username.strip().lower():
                            target_path = default_file
                    except Exception:
                        pass
                if target_path is None:
                    return None
        else:
            default_file = os.path.expanduser("~/.cybershell_save.json")
            if os.path.isfile(default_file):
                target_path = default_file
            else:
                return None

    if not os.path.isfile(target_path):
        return None

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        saved_name = str(data.get("character_name", username or "Byte"))
        player = PlayerStats(
            character_name=username if username else saved_name,
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


def delete_saved_game(
    filepath: Optional[str] = None,
    username: Optional[str] = None,
) -> bool:
    """Remove checkpoint save file."""
    deleted_any = False
    targets = []
    if filepath:
        targets.append(filepath)
    else:
        if username:
            targets.append(get_save_path(username))
        targets.append(SAVE_FILE_PATH)

    for p in targets:
        try:
            if os.path.isfile(p):
                os.remove(p)
                deleted_any = True
        except Exception:
            pass
    return deleted_any


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


def configure_readline_bindings() -> None:
    """Register readline shortcuts, enabling Ctrl+Space & Ctrl+P for Command Center."""
    if not READLINE_AVAILABLE or readline is None:
        return
    bindings = [
        r'"\C-@": "\C-u:cmd\n"',        # Ctrl+Space (standard NUL \x00 in Linux terminals)
        r'"\C- ": "\C-u:cmd\n"',        # Ctrl+Space alternative readline syntax
        r'"\C-p": "\C-u:cmd\n"',        # Ctrl+P (Neovim / VSCode palette fallback)
        r'"\e[32;5u": "\C-u:cmd\n"',    # CSI u keyboard protocol for Ctrl+Space
        r'"\e[27;5;32~": "\C-u:cmd\n"', # Xterm modifyOtherKeys for Ctrl+Space
    ]
    for b in bindings:
        try:
            readline.parse_and_bind(b)
        except Exception:
            pass


# Configure initial bindings on load
if READLINE_AVAILABLE and readline is not None:
    configure_readline_bindings()


def setup_tab_completion(vfs: VirtualFileSystem) -> None:
    """Configure readline tab completion and keybindings for shell commands and VFS files."""
    if not READLINE_AVAILABLE or readline is None:
        return
    completer = VFSTabCompleter(vfs)
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")
    try:
        readline.set_completer_delims(" \t\n")
    except Exception:
        pass
    configure_readline_bindings()


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
# PERSONALIZED ONBOARDING & OPENING HERO SCREEN
# =============================================================================

def prompt_player_onboarding(width: int = 80, current_name: str = "Explorer") -> str:
    """Personalized onboarding card asking user's name with clean web-app aesthetics."""
    if not sys.stdin.isatty():
        return current_name if current_name else "Explorer"

    term_w = max(40, width)
    box_w = max(44, min(term_w - 4, 76))
    inner_w = box_w - 4
    theme = get_active_theme()

    sys.stdout.write("\033[H\033[J")
    tux_raw = get_foss_penguin(styled=True, frame="wave")
    for line in tux_raw.splitlines():
        print(pad_to_width(line, term_w, align="center"))
    print()

    b_col = theme.fg_blue
    b_rst = RESET
    border_line = PANEL_HORIZONTAL * (box_w - 2)
    top_border = f"{b_col}{PANEL_TOP_LEFT}{border_line}{PANEL_TOP_RIGHT}{b_rst}"
    bot_border = f"{b_col}{PANEL_BOTTOM_LEFT}{border_line}{PANEL_BOTTOM_RIGHT}{b_rst}"
    div_border = f"{b_col}{PANEL_DIVIDER_LEFT}{border_line}{PANEL_DIVIDER_RIGHT}{b_rst}"
    side_char = f"{b_col}{PANEL_VERTICAL}{b_rst}"

    def card_line(txt: str = "") -> str:
        pad = max(0, (box_w - 2) - visual_len(txt) - 2)
        return f"{side_char} {txt}{' ' * pad} {side_char}"

    print(pad_to_width(top_border, term_w, align="center"))
    print(pad_to_width(card_line(f"{BOLD}{theme.fg_cyan}{'WELCOME TO FOSS CYBERSHELL'.center(inner_w)}{RESET}"), term_w, align="center"))
    print(pad_to_width(div_border, term_w, align="center"))
    print(pad_to_width(card_line(""), term_w, align="center"))
    print(pad_to_width(card_line(f"{WHITE}{'A friendly, modern playground for mastering Linux commands.'.center(inner_w)}{RESET}"), term_w, align="center"))
    print(pad_to_width(card_line(f"{theme.fg_muted}{'Safe hands-on sandbox • Real-time feedback • Zero damage'.center(inner_w)}{RESET}"), term_w, align="center"))
    print(pad_to_width(card_line(""), term_w, align="center"))
    print(pad_to_width(card_line(f"{BOLD}{theme.fg_yellow}{'Before we start, what is your name, explorer?'.center(inner_w)}{RESET}"), term_w, align="center"))
    if current_name and current_name != "Explorer":
        print(pad_to_width(card_line(f"{theme.fg_cyan}{f'Active Profile: {current_name}'.center(inner_w)}{RESET}"), term_w, align="center"))
    print(pad_to_width(card_line(""), term_w, align="center"))
    print(pad_to_width(bot_border, term_w, align="center"))
    print()

    indent = " " * max(2, (term_w - box_w) // 2)
    if current_name and current_name != "Explorer":
        sys.stdout.write(f"{indent}{BOLD}{theme.fg_cyan}Enter your name (press [ENTER] for {current_name}, or type new name): {RESET}")
    else:
        sys.stdout.write(f"{indent}{BOLD}{theme.fg_cyan}Enter your name (default: Explorer): {RESET}")
    sys.stdout.flush()

    try:
        raw_name = input().strip()
    except (KeyboardInterrupt, EOFError):
        return current_name if current_name else "Explorer"

    clean_name = "".join(c for c in raw_name if c.isalnum() or c in ("-", "_", " ")).strip()
    if not clean_name:
        clean_name = current_name if current_name else "Explorer"
    clean_name = clean_name[:16]

    sys.stdout.write("\033[H\033[J")
    tux_happy = get_foss_penguin(styled=True, frame="happy")
    for line in tux_happy.splitlines():
        print(pad_to_width(line, term_w, align="center"))
    print()
    print(pad_to_width(f"{BOLD}{theme.fg_green}[✓] Welcome aboard, {clean_name}! Tux is excited to train with you.{RESET}", term_w, align="center"))
    print(pad_to_width(f"{theme.fg_muted}Initializing your personal Linux sandbox...{RESET}", term_w, align="center"))
    if sys.stdout.isatty():
        time.sleep(0.4)
    return clean_name


def render_opening_screen(
    player: PlayerStats,
    width: int = 80,
    cadet_mode: bool = True,
    has_save: bool = False,
) -> str:
    """Render the primary adventure opening screen with clean web-app aesthetics."""
    term_w = max(40, width)
    card_w = max(44, min(term_w - 2, 78))

    # 1. FOSS Penguin Tux & Title Logo
    penguin_raw = get_foss_penguin(styled=True, frame="normal")
    penguin_lines = [
        pad_to_width(line, term_w, align="center")
        for line in penguin_raw.splitlines()
    ]

    logo_raw = get_logo(styled=True)
    logo_lines = [
        pad_to_width(line, term_w, align="center")
        for line in logo_raw.strip("\n").splitlines()
    ]

    # 2. Player summary line
    total_levels = 15
    curr_lvl = min(total_levels, player.current_sector + 1)
    status_text_1 = (
        f"{CYAN}Explorer:{RESET} {WHITE}{BOLD}{player.character_name}{RESET}  |  "
        f"{YELLOW}Progress:{RESET} Level {curr_lvl}/{total_levels}  |  "
        f"{YELLOW}{player.xp} XP{RESET}  |  "
        f"{MAGENTA}Badges: {len(getattr(player, 'badges', []))}{RESET}"
    )
    status_line_1 = pad_to_width(status_text_1, term_w, align="center")

    # 3. System Highlights (Concise 3-line web-card overview instead of overwhelming 14-line box)
    from cybershell.ui.renderer import draw_panel
    from cybershell.ui.theme import fg_hex

    func_title = "FOSS CYBERSHELL // SYSTEM HIGHLIGHTS"
    func_content = [
        f"  {CYAN}Shell Missions{RESET} (15 OverTheWire-style challenges) • {YELLOW}Fuzzy Docs{RESET} ('search <query>')",
        f"  {GREEN}Command Center{RESET} (Ctrl+Space or ':cmd') • {MAGENTA}Chmod Decoder{RESET} ('chmod 755')",
        f"  {BLUE}Arcade Dojo{RESET} (Snake, Vim, Typing) • {CYAN}Tux Penguin Pet{RESET} • {YELLOW}18 Color Themes{RESET}",
    ]
    func_panel_lines = draw_panel(func_title, func_content, card_w, styled=True, border_color=fg_hex(HEX_BLUE))

    # 4. Minimal Boxy Menu Layout
    menu_title = "MAIN DIRECTORY • CHOOSE A DESTINATION"
    th = get_active_theme()

    if has_save:
        options = [
            ("1", "Continue Adventure", f"Resume Level {curr_lvl}/15"),
            ("2", "Start New Game", "Begin fresh adventure from Level 1"),
            ("3", "Adventure Map", "See all 15 levels and your progress"),
            ("4", "Command Guide", "Browse Linux command handbook"),
            ("5", "Backpack & Items", "Inspect collected goodies and badges"),
            ("6", "Chmod Perm Decoder", "Decode permissions & solve security doors"),
            ("7", "Arcade Mini-Games", "Terminal Snake, Vim Dojo, Typing Dojo"),
            ("8", "Field Manual & Rules", "Read the adventure manual & rules"),
            ("T", "Theme Selector", f"Active: {th.display_name} (type 'foss', 'sakura', etc.)"),
            ("0", "Exit Adventure", "Save and exit"),
        ]
    else:
        options = [
            ("1", "Start Adventure", "Begin Level 1: Look Around (pwd & ls)"),
            ("2", "Adventure Map", "See all 15 levels of the journey"),
            ("3", "Command Guide", "Browse Linux command handbook"),
            ("4", "Backpack & Items", "Inspect collected goodies and badges"),
            ("5", "Chmod Perm Decoder", "Decode permissions & solve security doors"),
            ("6", "Arcade Mini-Games", "Terminal Snake, Vim Dojo, Typing Dojo"),
            ("7", "Field Manual & Rules", "Read the adventure manual & rules"),
            ("T", "Theme Selector", f"Active: {th.display_name} (type 'foss', 'sakura', etc.)"),
            ("0", "Exit Adventure", "Exit the game"),
        ]

    menu_content = []
    menu_content.append("")
    colors = [HEX_PURPLE, HEX_CYAN, HEX_PURPLE, HEX_GREEN, HEX_BLUE, HEX_YELLOW, HEX_CYAN, HEX_PURPLE, HEX_BLUE]
    for num, label, summary in options:
        c = colors[int(num) % len(colors)] if num.isdigit() else HEX_PURPLE
        prefix = f"{pill(num, HEX_BG_DARK, c)}  {CYAN}{BOLD}{label:<22}{RESET}"
        menu_content.append(f"  {prefix} {WHITE}{summary}{RESET}")
    menu_content.append("")
    menu_content.append(f"  {BOLD}{th.fg_yellow}Pro-tip:{RESET} {th.fg_white}Type any theme name directly (e.g. 'foss', 'sakura', 'mint', 'dracula') to switch instantly!{RESET}")
    menu_content.append("")

    menu_panel_lines = draw_panel(menu_title, menu_content, card_w, styled=True, border_color=fg_hex(HEX_PURPLE))

    all_lines = (
        penguin_lines
        + [""]
        + logo_lines
        + ["", status_line_1, ""]
        + [pad_to_width(line, term_w, align="center") for line in func_panel_lines]
        + [""]
        + [pad_to_width(line, term_w, align="center") for line in menu_panel_lines]
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
        input(f"  {YELLOW}{BOLD}[ Press ENTER to enter the wargame shell! ]{RESET} ")
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
        print(f"  {GREEN}{BOLD}[ LINUX COMMAND GUIDE ]{RESET}")
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
    print(f"  {YELLOW}{BOLD}[ YOUR BACKPACK & GOODIES ]{RESET}")
    desc = "Special items, stars, and badges collected during your Linux journey."
    for line in textwrap.wrap(desc, width=card_w - 4):
        print(f"  {WHITE}{line}{RESET}")
    print()
    if not player.inventory:
        print(f"  {DIM}Your backpack is currently empty.{RESET}")
        print(f"  {GREEN}Complete sectors and discover secrets to collect credentials.{RESET}")
    else:
        for idx, itm in enumerate(player.inventory, start=1):
            rarity_col = MAGENTA if itm.rarity in ("epic", "legendary", "mythic") else GREEN
            print(f"  [{idx}] [+] {WHITE}{BOLD}{itm.name}{RESET} [{rarity_col}{itm.rarity.upper()}{RESET}]")
            print(f"       {CYAN}{itm.description}{RESET}")
            print()

    raw_badges = getattr(player, "badges", [])
    if raw_badges:
        print(f"\n  {YELLOW}{BOLD}BADGES EARNED:{RESET}")
        for b in raw_badges:
            print(f"    [*] {b}")

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
        print(f"  {YELLOW}{BOLD}[ PERMISSIONS FORMULA ]{RESET}")
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
            f"  {p_row(f'  {YELLOW}{BOLD}PUZZLE #{puzzle.door_number:02d} • Convert to 3-Digit Octal Code{RESET}')}",
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
                f"  {YELLOW}Enter a 3-digit octal number (like 755 or 644) to test your answer!{RESET}",
                f"  {DIM}Type 'h' for a hint, 'n' to skip to next puzzle, or '0' to exit.{RESET}",
            ]
            continue

        if guess_lower in ("h", "hint", "?"):
            u_r = 4 if u_sym[0] == "r" else 0
            u_w = 2 if u_sym[1] == "w" else 0
            u_x = 1 if u_sym[2] == "x" else 0
            u_val = u_r + u_w + u_x
            feedback = [
                f"  {CYAN}{BOLD}STEP-BY-STEP HINT:{RESET}",
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
                f"  {YELLOW}{BOLD}[ PERMISSIONS FORMULA ]{RESET}",
                f"  {WHITE}Triads : {GREEN}[User/Owner]{WHITE} {CYAN}[Group]{WHITE} {MAGENTA}[Others]{RESET}",
                f"  {WHITE}Values : {BOLD}r (read) = 4{RESET}  |  {BOLD}w (write) = 2{RESET}  |  {BOLD}x (execute) = 1{RESET}  |  {DIM}- = 0{RESET}",
                f"  {DIM}Example: rwxr-xr-x -> User: 4+2+1=7 | Group: 4+0+1=5 | Others: 4+0+1=5  =>  755{RESET}",
            ]:
                print(rl)
            print()
            for pl in p_lines:
                print(pl)
            print()
            print(f"  {GREEN}{BOLD}[+] CORRECT! {puzzle.permission} = {puzzle.answer}!{RESET}")
            print(f"  {GREEN}   Breakdown: User={u_val} ({u_sym}), Group={g_val} ({g_sym}), Others={o_val} ({o_sym}){RESET}")
            if result.xp_awarded > 0:
                print(f"  {YELLOW}+{result.xp_awarded} XP awarded to {player.character_name}! Total XP: {player.xp}{RESET}")
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
                f"  {RED}{BOLD}[X] '{guess}' is not correct for '{puzzle.permission}'.{RESET}",
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
        msg = f"[{chosen_letter}] Correct! Running: {cmd_str}"
        return cmd_str, msg
    else:
        meaning = selected_opt.split(" - ")[1].strip() if " - " in selected_opt else selected_opt
        msg = f"[{chosen_letter}] '{cmd_str}' is for {meaning}. Try looking for what solves our current task!"
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
        terminal_logs: List[str] = [
            f"{GREEN}[+] Initializing Level 1: Look Around...{RESET}",
            f"{CYAN}Solve the challenge question above by typing the command or option letter!{RESET}",
            f"{DIM}Tip: Type '?' for a hint, 'map' for level map.{RESET}",
        ]
    else:
        lvl_display = player.current_sector + 1
        terminal_logs = [
            f"{GREEN}[+] Entering Level {lvl_display}/15: {quest.sector_name}{RESET}",
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
        u_name = (player.character_name or "explorer").lower().replace(" ", "-")
        prompt_prefix = f"{GREEN}{u_name}@cybershell:{cwd_short}$"

        # Usable dimensions for 4-pane layout
        usable_w = max(40, width - 2) if width > 42 else max(40, width - 1)
        left_w = int(usable_w * 0.65)
        right_w = usable_w - left_w - 1
        task_inner_w = max(10, left_w - 4)
        docs_inner_w = max(10, right_w - 4)

        # 1. Top-Left Pane: OverTheWire Mission Task (No ABCD quiz)
        total_challenges = 27 if not all_quests else max(27, len(all_quests))
        completed_count = len(getattr(player, "completed_sectors", []))
        pct_prog = int((completed_count / total_challenges) * 100) if total_challenges > 0 else 0

        # Dynamically resolve active theme and ambience
        theme = get_active_theme()
        ambience = get_ambience_manager()

        task_content: List[str] = []
        task_content.append(f"{theme.fg_yellow}LEVEL {player.current_sector + 1:02d} // {quest.sector_name.upper()}{RESET}  {DIM}({completed_count} of {total_challenges} complete - {pct_prog}%){RESET}")
        if active_obj:
            task_content.append("")
            # 1. Question (Clean wrapping)
            q_text = getattr(active_obj, "question", "") or active_obj.description
            q_lines = textwrap.wrap(f"QUESTION : {q_text}", width=task_inner_w, subsequent_indent="           ")
            for i, line in enumerate(q_lines):
                task_content.append(f"{BOLD}{theme.fg_white}{line}{RESET}" if i == 0 else f"{theme.fg_white}{line}{RESET}")

            # 2. Progress bar just below the question
            bar_w = min(16, max(6, task_inner_w - 20))
            prog_bar = draw_progress_bar(completed_count, total_challenges, width=bar_w, styled=True)
            task_content.append(f"{theme.fg_yellow}PROGRESS : {RESET}{prog_bar} {theme.fg_white}{completed_count}/{total_challenges}{RESET} {DIM}({pct_prog}%){RESET}")

            # 3. 4 Options (No commands list in question box!)
            opt_labels = ["A", "B", "C", "D"]
            if getattr(active_obj, "options", None):
                task_content.append("")
                for i, opt in enumerate(active_obj.options[:4]):
                    lbl = opt_labels[i] if i < len(opt_labels) else str(i + 1)
                    task_content.append(f"  {theme.fg_cyan}[{lbl}]{RESET} {theme.fg_white}{opt}{RESET}")

            # 4. Intel (Only question, options, intel, and progress needed)
            task_content.append("")
            intel_lines = textwrap.wrap("INTEL    : Type command or [A-D] | 'hint' for clues | ':cmd' for menu", width=task_inner_w, subsequent_indent="           ")
            for line in intel_lines:
                task_content.append(f"{DIM}{line}{RESET}")

            # Compute suggested for local docs in right pane without showing in question box
            suggested = []
            if getattr(active_obj, "command", None):
                for c in active_obj.command.replace("|", ",").split(","):
                    c_clean = c.strip()
                    if c_clean and c_clean not in suggested:
                        suggested.append(c_clean)
            if getattr(active_obj, "options", None):
                for opt in active_obj.options:
                    c_opt = opt.split(" - ")[0].strip().split()[0]
                    if c_opt not in suggested:
                        suggested.append(c_opt)
            for c in ["pwd", "ls", "cd", "cat", "man"]:
                if c not in suggested and len(suggested) < 4:
                    suggested.append(c)
        else:
            suggested = []
            task_content.append("")
            task_content.append(f"{theme.fg_green}[+] Sector objectives complete! Type 'next' or explore freely.{RESET}")

        # 2. Top-Right Pane: Local Docs (Context-Aware & Fuzzy Searchable)
        docs_content: List[str] = []
        if docs_filter_term:
            filtered_cmds = fuzzy_search_commands(docs_filter_term, app.codex.list_commands(), limit=16)
            docs_content.append(f"{theme.fg_yellow}Search: '{docs_filter_term}' ({len(filtered_cmds)} matches){RESET}")
        else:
            quest_cmds = suggested if active_obj else []
            filtered_cmds = app.codex.get_contextual_commands(
                relevant_cmds=quest_cmds,
                limit=16,
            )
            docs_content.append(f"{DIM}Commands Codex (:cmd / 'search'){RESET}")

        for cmd in filtered_cmds[:14]:
            name = cmd.get("name", "")
            desc = cmd.get("purpose") or cmd.get("description", "")
            avail_desc = max(8, docs_inner_w - 8)
            desc_part = desc[:avail_desc] if len(desc) > avail_desc else desc
            docs_content.append(f"{theme.fg_cyan}{name:<7}{RESET} {DIM}{desc_part}{RESET}")

        if not filtered_cmds:
            docs_content.append(f"{theme.fg_red}No matching commands.{RESET}")
            docs_content.append(f"{DIM}Type 'search' to reset.{RESET}")

        # 3. Bottom-Right Pane: Terminal Pet (Byte)
        pet = get_terminal_pet()
        pet.set_player_name(player.character_name)
        mascot_content = pet.render(width=docs_inner_w + 2, height=6, styled=True)

        # 4. Render 4-Pane Opencode Layout with commandline inside the TERMINAL pane
        layout_h = max(14, height - (4 if ambience.rain_enabled else 3))
        active_prompt = f"{BOLD}{theme.fg_green}{u_name}@cybershell{RESET}:{BOLD}{theme.fg_blue}{cwd_short}{RESET}$ "
        display_term_logs = list(terminal_logs) + [active_prompt]

        layout = draw_opencode_layout(
            task_title="YOUR TASK", task_content=task_content,
            term_title="TERMINAL", term_content=display_term_logs,
            docs_title="LOCAL DOCS", docs_content=docs_content,
            mascot_content=mascot_content,
            width=width, height=layout_h, gap=1, styled=True
        )

        footer = draw_control_footer(screen_type="terminal", width=width, styled=True)
        if ambience.rain_enabled:
            footer += f"  [{theme.fg_cyan}RAIN: ON{RESET}]"

        sys.stdout.write("\033[H\033[J")
        if ambience.rain_enabled:
            sys.stdout.write(ambience.render_rain_line(usable_w, density=0.08, color=theme.fg_cyan, row=0) + "\n")
        sys.stdout.write(layout + "\n")
        sys.stdout.write(pad_to_width(footer, usable_w, align="center") + "\n")
        sys.stdout.flush()

        # Calculate exact row and col of the active prompt inside the TERMINAL pane
        needed_task_height = len(task_content) + 3
        max_task_height = max(5, layout_h - 8)
        task_height = max(5, min(needed_task_height, max_task_height))
        term_height = layout_h - task_height
        term_max_content = term_height - 3
        sliced_term = display_term_logs[-term_max_content:] if len(display_term_logs) > term_max_content else display_term_logs
        prompt_idx = len(sliced_term) - 1
        rain_offset = 1 if ambience.rain_enabled else 0
        prompt_row = rain_offset + task_height + 3 + prompt_idx
        prompt_col = 3 + visual_len(active_prompt)

        try:
            if sys.stdin.isatty():
                sys.stdout.write(f"\033[{prompt_row};{prompt_col}H")
                sys.stdout.flush()
                user_input = input("").strip()
            else:
                user_input = input("").strip()
        except (KeyboardInterrupt, EOFError):
            save_game(player, cadet_mode)
            print(f"\n{theme.fg_cyan}Returning to Main Menu...{RESET}")
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

        # Command Center palette (Ctrl+Space / \x00, :cmd, :menu, :space, cmd)
        if user_input in ("\x00", "\x00\x00") or input_lower in (
            ":cmd", ":space", ":menu", "cmd", ":center", ":p", "palette",
            "ctrl+space", "ctrl-space", "ctrl space", "<c-space>", "^space",
        ):
            action = run_command_center(player, all_quests, width)
            if action == "search_docs":
                terminal_logs.append(f"{CYAN}[+] Type 'search <query>' to filter local documentation.{RESET}")
            elif action == "choose_challenge":
                view_map(app.mainframe, player, all_quests, width)
            elif action == "reset_challenge":
                vfs.load_sector(quest.sector_id, quest)
                for o in quest.objectives:
                    o.completed = False
                pet.react_error()
                terminal_logs.append(f"{YELLOW}[!] Challenge reset. Sector filesystem restored to initial state.{RESET}")
            elif action == "open_manual":
                terminal_logs.append(f"{CYAN}[+] Type 'man <command>' for context-aware field manual pages.{RESET}")
            continue

        if input_lower in (":progress", "progress", ":dashboard"):
            view_progress_dashboard(player, all_quests, width=width)
            continue

        if input_lower in (":games", "games", ":arcade", "arcade", "minigame", "puzzle"):
            view_minigames_hub(player, app.minigame, width=width)
            continue

        if input_lower in (":reset", "reset"):
            vfs.load_sector(quest.sector_id, quest)
            for o in quest.objectives:
                o.completed = False
            pet.react_error()
            terminal_logs.append(f"{prompt_prefix} reset{RESET}")
            terminal_logs.append(f"{CYAN}[!] Current challenge reset. Sector filesystem restored to fresh state.{RESET}")
            continue

        if input_lower in (":pet", "pet"):
            new_state = pet.toggle()
            status_txt = "awake & active" if new_state else "resting"
            terminal_logs.append(f"{prompt_prefix} pet{RESET}")
            terminal_logs.append(f"{CYAN}[+] Terminal Pet Byte is now {status_txt}.{RESET}")
            continue

        if input_lower in (":rain", "rain"):
            ambience = get_ambience_manager()
            r_on = ambience.toggle_rain()
            terminal_logs.append(f"{prompt_prefix} rain{RESET}")
            terminal_logs.append(f"{CYAN}[+] Ambient rain effect is now {'ON' if r_on else 'OFF'} (light shaded).{RESET}")
            continue

        if input_lower in (":rain play", "rain watch", ":rain watch", "rain play"):
            ambience = get_ambience_manager()
            ambience.watch_falling_rain(width=usable_w, height=18, duration=2.5)
            continue

        if input_lower in (":chmod", ":perm", ":decoder"):
            from cybershell.tools.minigames.chmod_decoder import play_chmod_decoder_interactive
            play_chmod_decoder_interactive(player, width=width)
            continue

        if input_lower.startswith("decode ") or input_lower.startswith("perm ") or input_lower.startswith("chmod --decode "):
            from cybershell.tools.minigames.chmod_decoder import format_decoded_permission
            parts = user_input.split(maxsplit=2)
            perm_val = parts[1].strip() if len(parts) > 1 else ""
            if perm_val == "--decode" and len(parts) > 2:
                perm_val = parts[2].strip()
            terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
            if perm_val:
                decoded_txt = format_decoded_permission(perm_val, styled=True)
                for d_line in decoded_txt.splitlines():
                    terminal_logs.append(d_line)
            else:
                terminal_logs.append(f"{YELLOW}Usage: decode <mode> (e.g. decode 755, decode rwxr-xr-x){RESET}")
            continue

        if (input_lower.startswith("chmod ") or input_lower == "chmod") and len(user_input.split()) <= 2:
            parts = user_input.split()
            if len(parts) == 1:
                from cybershell.tools.minigames.chmod_decoder import play_chmod_decoder_interactive
                play_chmod_decoder_interactive(player, width=width)
                continue
            elif len(parts) == 2 and not vfs.exists(parts[1]):
                from cybershell.tools.minigames.chmod_decoder import format_decoded_permission
                perm_candidate = parts[1]
                terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
                decoded_txt = format_decoded_permission(perm_candidate, styled=True)
                for d_line in decoded_txt.splitlines():
                    terminal_logs.append(d_line)
                terminal_logs.append(f"{DIM}To apply to a file, run: chmod {perm_candidate} <filename>{RESET}")
                continue

        if input_lower in (":anim", "anim"):
            ambience = get_ambience_manager()
            a_on = ambience.toggle_calm_animations()
            terminal_logs.append(f"{prompt_prefix} anim{RESET}")
            terminal_logs.append(f"{CYAN}[+] Calm animations are now {'ON' if a_on else 'OFF'}.{RESET}")
            continue

        # Direct theme switching (e.g. ':theme foss', 'theme dracula', or typing 'foss', 'sakura', 'nord' directly)
        theme_cand = ""
        if input_lower.startswith(":theme ") or input_lower.startswith("theme "):
            theme_cand = user_input.split(maxsplit=1)[1].strip()
        else:
            all_theme_names = set(THEMES.keys()) | {t.display_name.lower() for t in THEMES.values()} | {"pastel", "lavender", "sakura", "mint", "peach", "catppuccin"}
            if input_lower in all_theme_names:
                theme_cand = input_lower

        if theme_cand:
            if set_theme(theme_cand):
                new_th = get_active_theme()
                terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
                terminal_logs.append(f"{BOLD}{new_th.fg_green}[✓] Active theme switched to {new_th.display_name}!{RESET}")
                continue

        if input_lower in (":theme", "theme", "themes"):
            run_theme_selector(width=width)
            continue

        if input_lower.startswith(":man ") or input_lower.startswith("man "):
            parts = user_input.split(maxsplit=1)
            cmd_name = parts[1].strip() if len(parts) > 1 else ""
            terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
            if cmd_name:
                field_manual_text = format_field_manual_entry(cmd_name)
                for fm_line in field_manual_text.splitlines():
                    terminal_logs.append(f"{WHITE}{fm_line}{RESET}")
            else:
                terminal_logs.append(f"{YELLOW}Usage: man <command> (e.g. man ls, man mkdir, man chmod){RESET}")
            continue

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

        if input_lower == "clear":
            terminal_logs = []
            continue

        if input_lower.startswith("search "):
            query = input_lower[7:].strip()
            terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
            if query in ("*", "all", "clear", "reset"):
                docs_filter_term = ""
                terminal_logs.append(f"{CYAN}[+] Local docs search filter cleared.{RESET}")
            else:
                docs_filter_term = query
                results = fuzzy_search_commands(query, app.codex.list_commands(), limit=6)
                terminal_logs.append(f"{CYAN}[+] Filtered local docs for '{query}' ({len(results)} matches).{RESET}")
                for t_line in render_telescope_results(query, results, width=min(task_inner_w + 2, 65), styled=True):
                    terminal_logs.append(t_line)
            continue
        elif input_lower == "search":
            terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
            docs_filter_term = ""
            terminal_logs.append(f"{CYAN}[+] Local docs search filter reset. Showing all commands.{RESET}")
            continue

        if input_lower == "save":
            saved = save_game(player, cadet_mode)
            terminal_logs.append(f"{prompt_prefix} save{RESET}")
            if saved:
                terminal_logs.append(f"{GREEN}[OK] Progress saved successfully!{RESET}")
            else:
                terminal_logs.append(f"{RED}Failed to write save file.{RESET}")
            continue

        if input_lower in ("status", "badges", "stats"):
            terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
            terminal_logs.append(f"{CYAN}{BOLD}[ EXPLORER STATS ]{RESET}")
            terminal_logs.append(
                f"  {WHITE}Explorer:{RESET} {CYAN}{player.character_name}{RESET}  "
                f"{YELLOW}Level:{RESET} {player.current_sector + 1}/15  "
                f"{YELLOW}XP:{RESET} {player.xp}  "
                f"{GREEN}Streak:{RESET} {getattr(player, 'streak', 0)}"
            )
            raw_badges = getattr(player, "badges", [])
            badges_str = " ".join(f"[{b}]" for b in raw_badges) if raw_badges else "None yet"
            terminal_logs.append(f"  {YELLOW}Badges:{RESET} {badges_str}")
            continue

        if input_lower.startswith("tree"):
            terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
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
            terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
            for el in explain_command(user_input, active_obj):
                terminal_logs.append(el)
            continue

        if input_lower in ("hint", "?"):
            terminal_logs.append(f"{prompt_prefix} {user_input}{RESET}")
            if not active_obj:
                terminal_logs.append(f"{GREEN}All goals in this level are complete! Great job!{RESET}")
            else:
                pet.react_hint()
                if hasattr(player, "use_hint"):
                    player.use_hint()
                h_msg, _ = get_progressive_hint(active_obj, hint_tier, cadet_mode=True)
                terminal_logs.append(f"{YELLOW}{BOLD}[HINT {hint_tier}/3] {h_msg}{RESET}")
                hint_tier = min(3, hint_tier + 1)
            continue

        cmd_start_index = len(terminal_logs)

        # Check for option selection [A/B/C/D] or [1/2/3/4]
        opt_cmd, opt_msg = resolve_option_choice(user_input, active_obj)
        if opt_cmd is not None:
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
                terminal_logs.append(f"{prompt_prefix} {cmd_to_show}{RESET}")
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
                terminal_logs.append(f"{DIM}[TIP] Output shown above. Review mission briefing to find the required command.{RESET}")
            continue
        else:
            actual_cmd = user_input

        # Check for beginner typo before execution
        typo = check_typo_or_syntax(actual_cmd)

        # Execute command in VFS
        terminal_logs.append(f"{prompt_prefix} {actual_cmd}{RESET}")
        if opt_cmd is not None and opt_msg:
            terminal_logs.append(f"{CYAN}{opt_msg}{RESET}")
        result = interpreter.execute(actual_cmd)

        if typo:
            sugg, expl = typo
            
            terminal_logs.append(f"{YELLOW}[TIP] Detected '{actual_cmd}'. Did you mean '{sugg}'? {expl}{RESET}")

        if result.stdout:
            first_cmd = actual_cmd.split()[0] if actual_cmd.split() else ""
            if first_cmd == "ls":
                for out_line in colorize_ls_output(result.stdout):
                    terminal_logs.append(out_line)
            else:
                for out_line in result.stdout.splitlines():
                    terminal_logs.append(f"{WHITE}{out_line}{RESET}")

        if result.stderr:
            pet.react_error(result.stderr)
            for err_line in result.stderr.splitlines():
                terminal_logs.append(f"{RED}{err_line}{RESET}")
            feedback_errs = [
                "✗ Not quite. Check the path and try again.",
                "✗ Command failed. Double-check your syntax.",
                "✗ Target not found. Check files with 'ls -la'.",
            ]
            terminal_logs.append(f"{YELLOW}{random.choice(feedback_errs)}{RESET}")
            if not typo:
                terminal_logs.append(f"{DIM}Type 'hint' or 'search <cmd>' for tactical guidance.{RESET}")

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
            pet.react_success(actual_cmd)
            feedback_oks = [
                "✓ Nice. The shell approves.",
                "✓ Clean execution. Moving to next sector.",
                "✓ Filesystem verified. Well done.",
            ]
            terminal_logs.append(f"{GREEN}{random.choice(feedback_oks)}{RESET}")
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

                # Store item in player inventory without crowded screen spam
                if quest.reward_item and hasattr(player, "inventory") and quest.reward_item not in player.inventory:
                    player.inventory.append(quest.reward_item)

                terminal_logs.append(f"{GREEN}{BOLD}[✓] Level {quest.sector_id + 1} completed! (+{reward_sum} XP){RESET}")

                next_sector = player.current_sector + 1
                if next_sector in all_quests:
                    player.current_sector = next_sector
                    quest = all_quests[next_sector]
                    vfs.load_sector(next_sector, quest)
                    save_game(player, cadet_mode)
                    terminal_logs.append(f"{CYAN}Entering Level {next_sector + 1}: {quest.sector_name}{RESET}")
                else:
                    save_game(player, cadet_mode)
                    terminal_logs.append(f"{GREEN}{BOLD}[✓] All 15 levels completed! Congratulations!{RESET}")
            else:
                terminal_logs.append(f"{GREEN}[✓] Objective cleared! (+{reward_sum} XP){RESET}")

        if player.level > old_level:
            terminal_logs.append(f"{MAGENTA}{BOLD}[+] LEVEL UP! You reached Level {player.level}! Title: {player.rank}{RESET}")


# =============================================================================
# MAIN MENU CONTROLLER LOOP
# =============================================================================

def main_menu_loop(character_name: str = "Byte", start_sector: int = 0) -> None:
    """Main menu loop with navigation, profile switching, and first-time field manual."""
    width, _ = terminal_size()
    last_user = get_last_saved_username() or (character_name if character_name != "Byte" else "Explorer")

    # Prompt user on launch to confirm active explorer or switch to a new user
    if sys.stdin.isatty():
        active_user = prompt_player_onboarding(width=width, current_name=last_user)
    else:
        active_user = character_name or "Explorer"

    saved_data = load_saved_game(username=active_user)
    cadet_mode = True
    first_launch = saved_data is None

    if saved_data is not None:
        player, cadet_mode = saved_data
        player.character_name = active_user
    else:
        player = PlayerStats(
            character_name=active_user,
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

    # First launch for this specific user shows onboarding animation & mandatory Field Manual!
    if first_launch:
        save_game(player, cadet_mode)
        animate_tux_welcome(character_name=player.character_name, width=width, quick=False)
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

    # Initial startup splash prompt before revealing Tux penguin and menu
    if sys.stdin.isatty():
        width, _ = terminal_size()
        sys.stdout.write("\033[H\033[J")
        box_w = min(max(50, width - 4), 68)
        inner_bw = box_w - 2
        theme = get_active_theme()
        b_col = theme.fg_blue
        b_rst = RESET
        top_b = f"{b_col}{PANEL_TOP_LEFT}{PANEL_HORIZONTAL * inner_bw}{PANEL_TOP_RIGHT}{b_rst}"
        bot_b = f"{b_col}{PANEL_BOTTOM_LEFT}{PANEL_HORIZONTAL * inner_bw}{PANEL_BOTTOM_RIGHT}{b_rst}"
        div_b = f"{b_col}{PANEL_DIVIDER_LEFT}{PANEL_HORIZONTAL * inner_bw}{PANEL_DIVIDER_RIGHT}{b_rst}"
        side_b = f"{b_col}{PANEL_VERTICAL}{b_rst}"

        def splash_row(txt: str = "") -> str:
            pad = max(0, inner_bw - visual_len(txt) - 2)
            return f"{side_b} {txt}{' ' * pad} {side_b}"

        hero_name = player.character_name.upper() if player.character_name and player.character_name != "Byte" else "FOSS"
        splash_lines = [
            "",
            top_b,
            splash_row(f"{BOLD}{theme.fg_cyan}{f'{hero_name} LINUX ADVENTURE // FOSS EDITION'.center(inner_bw - 2)}{RESET}"),
            div_b,
            splash_row(""),
            splash_row(f"{WHITE}{'Learn real-world Linux command mastery safely.'.center(inner_bw - 2)}{RESET}"),
            splash_row(f"{DIM}{theme.fg_yellow}{'15 Quests • Real Shell • OverTheWire Style • Zero Damage'.center(inner_bw - 2)}{RESET}"),
            splash_row(""),
            splash_row(f"{BOLD}{YELLOW}{'Press [ENTER] to initialize FOSS CyberShell...'.center(inner_bw - 2)}{RESET}"),
            splash_row(""),
            bot_b,
        ]
        for s_l in splash_lines:
            print(pad_to_width(s_l, width, align="center"))
        print()
        try:
            splash_in = input().strip()
            if splash_in:
                s_cand = splash_in.lower()
                for pfx in (":theme ", "theme ", ":theme", "theme"):
                    if s_cand.startswith(pfx):
                        s_cand = s_cand[len(pfx):].strip()
                        break
                all_theme_names = set(THEMES.keys()) | {t.display_name.lower() for t in THEMES.values()} | {"pastel", "lavender", "sakura", "mint", "peach", "catppuccin"}
                if s_cand in all_theme_names or splash_in.lower() in all_theme_names:
                    set_theme(s_cand if s_cand in all_theme_names else splash_in.lower())
        except (KeyboardInterrupt, EOFError):
            return

        animate_tux_welcome(character_name=player.character_name, width=width, quick=True)

    while True:
        user_save = get_save_path(player.character_name)
        has_save = os.path.isfile(user_save) or os.path.isfile(SAVE_FILE_PATH)
        width, _ = terminal_size()
        sys.stdout.write("\033[H\033[J")
        print(render_opening_screen(player, width, cadet_mode=cadet_mode, has_save=has_save))

        max_option = 8 if has_save else 7
        try:
            choice = input(f"\n{YELLOW}Choose an option [0-{max_option}, T] (default: 1): {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{CYAN}See you next time! Session closed.{RESET}\n")
            break

        if not choice:
            choice = "1"

        choice_lower = choice.lower()
        if choice_lower in ("0", "exit", "quit", "q"):
            print(f"\n{CYAN}See you next time! Session closed.{RESET}\n")
            break

        # Switch active profile / user directly in menu
        if choice_lower in ("user", "profile", "switch", ":user", ":profile"):
            p_name = prompt_player_onboarding(width, current_name=player.character_name)
            if p_name and p_name != player.character_name:
                active_user = p_name
                saved_data = load_saved_game(username=active_user)
                if saved_data is not None:
                    player, cadet_mode = saved_data
                    player.character_name = active_user
                else:
                    player = PlayerStats(
                        character_name=active_user,
                        hp=100,
                        max_hp=100,
                        xp=0,
                        current_sector=0,
                    )
                    save_game(player, cadet_mode)
                app.character_name = active_user
            continue

        # Direct theme switching in the first interface
        direct_theme_target = choice_lower
        for pfx in (":theme ", "theme ", ":theme", "theme"):
            if direct_theme_target.startswith(pfx):
                direct_theme_target = direct_theme_target[len(pfx):].strip()
                break

        all_theme_names = set(THEMES.keys()) | {t.display_name.lower() for t in THEMES.values()} | {"pastel", "lavender", "sakura", "mint", "peach", "catppuccin"}
        if direct_theme_target in all_theme_names or choice_lower in all_theme_names:
            target_to_set = direct_theme_target if direct_theme_target in all_theme_names else choice_lower
            if set_theme(target_to_set):
                new_theme = get_active_theme()
                print(f"\n{BOLD}{new_theme.fg_green}[✓] Active theme switched to {new_theme.display_name}!{RESET}")
                import time
                time.sleep(0.35)
                continue

        if choice_lower in ("t", "theme", ":theme"):
            run_theme_selector(width)
            continue

        if has_save:
            if choice_lower in ("1", "continue", "resume", "c", "start", "e"):
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
            elif choice_lower in ("2", "new", "reset", "n"):
                delete_saved_game(username=player.character_name)
                p_name = prompt_player_onboarding(width, current_name=player.character_name) if sys.stdin.isatty() else player.character_name
                player = PlayerStats(
                    character_name=p_name,
                    hp=100,
                    max_hp=100,
                    xp=0,
                    current_sector=0,
                )
                app.character_name = p_name
                vfs = VirtualFileSystem(default_user="byte")
                interpreter = Interpreter(vfs=vfs)
                all_quests = get_sector_quests()
                save_game(player, cadet_mode)
                animate_tux_welcome(character_name=player.character_name, width=width, quick=False)
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
            elif choice_lower in ("3", "map", "m"):
                view_map(app.mainframe, player, all_quests, width)
            elif choice_lower in ("4", "codex", "guide", "find"):
                view_codex(app.codex, player, width)
            elif choice_lower in ("5", "items", "inventory", "backpack", "b"):
                view_inventory(player, width)
            elif choice_lower in ("6", "chmod", "perm", "decoder", "puzzle"):
                from cybershell.tools.minigames.chmod_decoder import play_chmod_decoder_interactive
                play_chmod_decoder_interactive(player, width=width)
            elif choice_lower in ("7", "arcade", "minigame", "games"):
                from cybershell.tools.minigames.hub import view_minigames_hub
                view_minigames_hub(player, width=width)
            elif choice_lower in ("8", "manual", "help", "rules", "h", "?"):
                view_field_manual(width)
            else:
                print(f"\n{RED}That's not a valid option. Please choose [0-{max_option}].{RESET}")
                try:
                    input(f"{YELLOW}Press Enter to continue...{RESET}")
                except (KeyboardInterrupt, EOFError):
                    break
        else:
            if choice_lower in ("1", "start", "play", "e", "explore"):
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
            elif choice_lower in ("2", "map", "m"):
                view_map(app.mainframe, player, all_quests, width)
            elif choice_lower in ("3", "codex", "guide", "find"):
                view_codex(app.codex, player, width)
            elif choice_lower in ("4", "items", "inventory", "backpack", "b"):
                view_inventory(player, width)
            elif choice_lower in ("5", "chmod", "perm", "decoder", "puzzle"):
                from cybershell.tools.minigames.chmod_decoder import play_chmod_decoder_interactive
                play_chmod_decoder_interactive(player, width=width)
            elif choice_lower in ("6", "arcade", "minigame", "games"):
                from cybershell.tools.minigames.hub import view_minigames_hub
                view_minigames_hub(player, width=width)
            elif choice_lower in ("7", "manual", "help", "rules", "h", "?"):
                view_field_manual(width)
            else:
                print(f"\n{RED}That's not a valid option. Please choose [0-{max_option}].{RESET}")
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
