"""Chmod Permission Decoder & Security Minigame for Byte's Linux Adventure.

Provides:
1. Interactive Permission Decoder (convert 755 <-> rwxr-xr-x with security analysis)
2. Lockpicking Security Door Minigame (solve permission puzzles for XP)
3. Direct terminal helper functions for decoding permissions.

Zero emojis, clean developer styling.
"""

from __future__ import annotations

import sys
from typing import Dict, List, Optional, Tuple, Union

from cybershell.contracts import PlayerStats
from cybershell.tools.chmod_calc import (
    ChmodError,
    describe_triad,
    get_triplets,
    octal_to_symbolic,
    parse_permission,
    security_info,
    security_report,
    symbolic_to_octal,
    validate_octal,
    validate_symbolic,
)
from cybershell.tools.chmod_minigame import ChmodMinigame
from cybershell.ui.theme import (
    BOLD,
    CYAN,
    DIM,
    FG_BLUE,
    FG_CYAN,
    FG_GREEN,
    FG_MUTED,
    FG_PURPLE,
    FG_RED,
    FG_WHITE,
    FG_YELLOW,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    WHITE,
    YELLOW,
    get_active_theme,
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
    pad_to_width,
    visual_len,
)


def decode_permission_details(value: str) -> Dict[str, Any]:
    """Decode an octal (e.g. 755) or symbolic (e.g. rwxr-xr-x) permission string."""
    raw = value.strip()
    if not raw:
        raise ChmodError("Permission is empty.")

    # Remove optional leading '-' or 'd' if 10 chars
    if len(raw) == 10 and raw[0] in ("-", "d", "l"):
        raw = raw[1:]

    is_octal = raw.isdigit()
    if is_octal:
        octal_str = validate_octal(raw)
        sym_str = octal_to_symbolic(octal_str)
    else:
        sym_str = validate_symbolic(raw)
        octal_str = symbolic_to_octal(sym_str)

    owner_sym, group_sym, others_sym = get_triplets(octal_str)
    info = security_info(octal_str)

    # Binary bits
    int_mode = parse_permission(octal_str)
    binary_str = f"{(int_mode >> 6) & 7:03b} {(int_mode >> 3) & 7:03b} {int_mode & 7:03b}"

    return {
        "octal": octal_str,
        "symbolic": sym_str,
        "binary": binary_str,
        "owner": owner_sym,
        "group": group_sym,
        "others": others_sym,
        "capabilities": info["capabilities"],
    }


def format_decoded_permission(value: Union[str, dict], styled: bool = True, width: int = 74) -> str:
    """Format human-readable permission explanation for terminal output."""
    if isinstance(value, dict):
        data = value
    else:
        try:
            data = decode_permission_details(value)
        except ChmodError as e:
            return f"{RED}[!] Permission error: {e}{RESET}" if styled else f"[!] Permission error: {e}"

    theme = get_active_theme()
    c_cyan = theme.fg_cyan if styled else ""
    c_yellow = theme.fg_yellow if styled else ""
    c_green = theme.fg_green if styled else ""
    c_purple = theme.fg_purple if styled else ""
    c_white = theme.fg_white if styled else ""
    c_dim = DIM if styled else ""
    c_rst = RESET if styled else ""
    c_bld = BOLD if styled else ""

    lines = [
        f"{c_bld}{c_yellow}PERMISSION DECODER // {data['octal']} <-> {data['symbolic']}{c_rst}",
        f"  Octal    : {c_bld}{c_yellow}{data['octal']}{c_rst}",
        f"  Symbolic : {c_bld}{c_cyan}{data['symbolic']}{c_rst}",
        f"  Binary   : {c_dim}{data['binary']}{c_rst}",
        f"  Triads   : {c_green}User/Owner [{data['owner']}]{c_rst}  {c_cyan}Group [{data['group']}]{c_rst}  {c_purple}Others [{data['others']}]{c_rst}",
        f"  Security :",
        f"    • {c_green}Owner{c_rst}  : {data['capabilities']['Owner']}",
        f"    • {c_cyan}Group{c_rst}  : {data['capabilities']['Group']}",
        f"    • {c_purple}Others{c_rst} : {data['capabilities']['Others']}",
    ]
    return "\n".join(lines)


def play_chmod_decoder_interactive(player: PlayerStats, width: int = 74) -> None:
    """Interactive loop for the Chmod Permission Decoder & Security Minigame."""
    minigame = ChmodMinigame(difficulty="easy")
    minigame.set_player(player)

    while True:
        sys.stdout.write("\033[H\033[J")
        theme = get_active_theme()
        sep = "=" * min(68, width - 2)
        print(f"\n{theme.fg_blue}{sep}{RESET}")
        print(f"  {BOLD}{theme.fg_cyan}CHMOD PERM DECODER & SECURITY MINIGAME{RESET}")
        print(f"{theme.fg_blue}{sep}{RESET}")
        print(f"  {theme.fg_yellow}[1]{RESET} {BOLD}Decode Any Permission{RESET} (enter 755, 644, rwxr-xr-x, etc.)")
        print(f"  {theme.fg_yellow}[2]{RESET} {BOLD}Play Security Door Puzzle{RESET} (octal lockpicking challenges for XP)")
        print(f"  {theme.fg_yellow}[3]{RESET} {BOLD}View Permission Formula Sheet{RESET} (r=4, w=2, x=1)")
        print(f"  {theme.fg_yellow}[0]{RESET} Return to Arcade")
        print(f"{theme.fg_blue}{'-' * min(68, width - 2)}{RESET}")
        sys.stdout.write(f"{BOLD}{theme.fg_cyan}chmod-lab> {RESET}")
        sys.stdout.flush()

        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice in ("0", "q", "exit", "back", "esc", "escape", "\x1b"):
            break

        if choice == "1":
            _run_interactive_calc(width)
        elif choice == "2":
            _run_interactive_doors(minigame, player, width)
        elif choice == "3":
            _view_formula_sheet(width)


def _run_interactive_calc(width: int = 70) -> None:
    """Prompt user for octal or symbolic permission and display full analysis."""
    theme = get_active_theme()
    while True:
        sys.stdout.write("\033[H\033[J")
        print(f"\n{theme.fg_blue}{'=' * 60}{RESET}")
        print(f"  {BOLD}{theme.fg_cyan}CHMOD DECODER // REAL-TIME PERMISSION ANALYSIS{RESET}")
        print(f"{theme.fg_blue}{'=' * 60}{RESET}")
        print("  Enter any 3-digit octal (e.g. 755, 644, 700, 777)")
        print("  or symbolic string (e.g. rwxr-xr-x, rw-r--r--)")
        print("  [Type '0' or press Enter to return]")
        print(f"{theme.fg_blue}{'-' * 60}{RESET}")
        sys.stdout.write(f"{BOLD}{theme.fg_yellow}perm> {RESET}")
        sys.stdout.flush()

        try:
            val = input().strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not val or val in ("0", "q", "exit", "back"):
            break

        output = format_decoded_permission(val, styled=True)
        print(f"\n{output}\n")
        print(f"{DIM}Press Enter to inspect another permission...{RESET}")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            break


def _run_interactive_doors(minigame: ChmodMinigame, player: PlayerStats, width: int = 70) -> None:
    """Run interactive security door lockpicking puzzle."""
    puzzle = minigame.active_puzzle or minigame.generate_puzzle()
    feedback: List[str] = []
    card_w = min(max(40, width - 4), 74)

    while True:
        sys.stdout.write("\033[H\033[J")
        theme = get_active_theme()
        print(f"\n{theme.fg_blue}{'=' * 64}{RESET}")
        print(f"  {BOLD}{theme.fg_cyan}CHMOD SECURITY PUZZLE // DOOR #{puzzle.door_number:02d}{RESET}  {DIM}(XP: {player.xp}){RESET}")
        print(f"{theme.fg_blue}{'=' * 64}{RESET}")

        u_sym = puzzle.permission[0:3]
        g_sym = puzzle.permission[3:6]
        o_sym = puzzle.permission[6:9]

        print(f"\n  Symbolic Pattern : {BOLD}{WHITE}{puzzle.permission}{RESET}")
        print(f"    • {GREEN}User/Owner (u){RESET} : {WHITE}{u_sym}{RESET}   (r=4, w=2, x=1, -=0)")
        print(f"    • {CYAN}Group      (g){RESET} : {WHITE}{g_sym}{RESET}   (r=4, w=2, x=1, -=0)")
        print(f"    • {MAGENTA}Others     (o){RESET} : {WHITE}{o_sym}{RESET}   (r=4, w=2, x=1, -=0)")
        print(f"\n{theme.fg_blue}{'-' * 64}{RESET}")

        if feedback:
            for fb in feedback:
                print(f"  {fb}")
            print(f"{theme.fg_blue}{'-' * 64}{RESET}")
            feedback = []

        try:
            guess = input(
                f"  {YELLOW}{BOLD}Enter 3-digit code (e.g. 755) ['h'=hint, 'n'=next, '0'=exit]: {RESET}"
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if guess in ("0", "q", "exit", "back"):
            break

        if guess in ("h", "hint"):
            hint_txt = minigame.get_hint()
            feedback.append(f"{CYAN}[💡 HINT] {hint_txt}{RESET}")
            continue

        if guess in ("n", "next", "skip"):
            puzzle = minigame.generate_puzzle()
            feedback.append(f"{YELLOW}[→] Generated new puzzle door.{RESET}")
            continue

        result = minigame.check_solution(guess)
        if result["correct"]:
            xp_gain = result["xp_earned"]
            feedback.append(f"{GREEN}[✓] LOCK DISENGAGED! Correct octal code: {guess}{RESET}")
            feedback.append(f"{GREEN}[+] Earned +{xp_gain} XP!{RESET}")
            puzzle = minigame.generate_puzzle()
        else:
            feedback.append(f"{RED}[✗] Invalid code. Expected 3 octal digits summing user/group/others.{RESET}")
            feedback.append(f"{DIM}Formula: User triad={puzzle.permission[:3]}, Group={puzzle.permission[3:6]}, Others={puzzle.permission[6:]}{RESET}")


def _view_formula_sheet(width: int = 70) -> None:
    """Display quick permission formula reference."""
    theme = get_active_theme()
    sys.stdout.write("\033[H\033[J")
    print(f"\n{theme.fg_blue}{'=' * 64}{RESET}")
    print(f"  {BOLD}{theme.fg_cyan}LINUX FILE PERMISSIONS REFERENCE SHEET{RESET}")
    print(f"{theme.fg_blue}{'=' * 64}{RESET}")
    print(f"  {BOLD}Triad Format:{RESET}  {GREEN}[Owner/User]{RESET} {CYAN}[Group]{RESET} {MAGENTA}[Others]{RESET}")
    print(f"  {BOLD}Values:{RESET}        {BOLD}r (read)    = 4{RESET}")
    print(f"                 {BOLD}w (write)   = 2{RESET}")
    print(f"                 {BOLD}x (execute) = 1{RESET}")
    print(f"                 {DIM}- (no perm) = 0{RESET}")
    print(f"\n  {BOLD}Calculation Examples:{RESET}")
    print(f"  • rwx r-x r-x  ->  (4+2+1) (4+0+1) (4+0+1)  = {BOLD}755{RESET}")
    print(f"  • rw- r-- r--  ->  (4+2+0) (4+0+0) (4+0+0)  = {BOLD}644{RESET}")
    print(f"  • rwx --- ---  ->  (4+2+1) (0+0+0) (0+0+0)  = {BOLD}700{RESET}")
    print(f"  • rwxrwxrwx  ->  (4+2+1) (4+2+1) (4+2+1)  = {BOLD}777{RESET}")
    print(f"{theme.fg_blue}{'-' * 64}{RESET}")
    print("Press Enter to return...")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
