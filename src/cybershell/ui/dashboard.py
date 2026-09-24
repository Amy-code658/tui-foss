"""Progress Dashboard for Byte's Linux Adventure.

Renders a comprehensive, developer-style progress dashboard showing:
- Overall completion percentage
- Challenges completed (e.g. "3 of 27 complete")
- Level, Rank, XP
- Streak counter and Max streak
- Accuracy rate & Best performance
- Topic breakdown with individual progress bars:
  * Navigation (pwd, cd, ls)
  * Files & Folders (touch, mkdir, tree, rmdir)
  * File Operations (cat, cp, mv, rm, head, tail)
  * Searching (grep, find, wc)
  * Pipes & Redirection (pipes, redirects, sort, less)
  * Permissions (chmod, octal modes)
  * Processes (ps, kill)
  * Git (status, diff, log)
  * Vim (modal motions, commands)

No emojis - pure clean ASCII/Unicode terminal layout.
"""

from typing import Dict, List, Optional
import math
import sys

from cybershell.contracts import PlayerStats, Quest
from cybershell.ui.theme import (
    FG_CYAN,
    FG_GREEN,
    FG_YELLOW,
    FG_PURPLE,
    FG_RED,
    FG_MUTED,
    FG_TEXT,
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
    truncate_styled,
)


TOPICS = [
    {
        "name": "Navigation",
        "tools": "pwd, cd, ls",
        "sectors": [0, 1],
    },
    {
        "name": "Files & Folders",
        "tools": "touch, mkdir, tree, rmdir",
        "sectors": [2, 3],
    },
    {
        "name": "File Operations",
        "tools": "cat, cp, mv, rm, head, tail",
        "sectors": [4, 5],
    },
    {
        "name": "Searching",
        "tools": "grep, find, wc",
        "sectors": [6, 7],
    },
    {
        "name": "Pipes & Redir",
        "tools": "|, >, >>, sort, less",
        "sectors": [8, 9],
    },
    {
        "name": "Permissions",
        "tools": "chmod, 755, 644",
        "sectors": [10, 11],
    },
    {
        "name": "Processes",
        "tools": "ps, kill, top",
        "sectors": [12],
    },
    {
        "name": "Git Basics",
        "tools": "status, diff, log",
        "sectors": [13],
    },
    {
        "name": "Vim Motions",
        "tools": "hjkl, dd, x, :wq",
        "sectors": [14],
    },
]


def render_progress_bar(pct: float, bar_width: int = 16, styled: bool = True) -> str:
    """Render a clean block progress bar [████░░░░░░]."""
    pct = max(0.0, min(1.0, pct))
    filled_len = int(round(bar_width * pct))
    unfilled_len = bar_width - filled_len
    
    fill_char = "█"
    empty_char = "░"
    
    if styled:
        if pct >= 1.0:
            bar = f"{FG_GREEN}{fill_char * filled_len}{RESET}"
        elif pct >= 0.5:
            bar = f"{FG_CYAN}{fill_char * filled_len}{RESET}{FG_MUTED}{empty_char * unfilled_len}{RESET}"
        else:
            bar = f"{FG_YELLOW}{fill_char * filled_len}{RESET}{FG_MUTED}{empty_char * unfilled_len}{RESET}"
    else:
        bar = (fill_char * filled_len) + (empty_char * unfilled_len)
    
    return f"[{bar}] {int(pct * 100):>3}%"


def render_progress_dashboard(
    player: PlayerStats,
    all_quests: Optional[Dict[int, Quest]] = None,
    width: int = 80,
    styled: bool = True,
) -> str:
    """Render full-screen Progress Dashboard with metrics and topic breakdown."""
    width = max(50, min(width - 2, 78))
    inner_w = width - 2
    content_w = inner_w - 4

    b_col = FG_PURPLE if styled else ""
    b_rst = RESET if styled else ""
    top = f"{b_col}{PANEL_TOP_LEFT}{PANEL_HORIZONTAL * inner_w}{PANEL_TOP_RIGHT}{b_rst}"
    bot = f"{b_col}{PANEL_BOTTOM_LEFT}{PANEL_HORIZONTAL * inner_w}{PANEL_BOTTOM_RIGHT}{b_rst}"
    divider = f"{b_col}{PANEL_VERTICAL}{b_rst}{PANEL_HORIZONTAL * inner_w}{b_col}{PANEL_VERTICAL}{b_rst}"

    lines: List[str] = [top]

    def add_line(text: str = "") -> None:
        pad = max(0, inner_w - visual_len(text) - 2)
        lines.append(f"{b_col}{PANEL_VERTICAL}{b_rst} {text}{' ' * pad} {b_col}{PANEL_VERTICAL}{b_rst}")

    # Header
    title = "PROGRESS & SKILL DASHBOARD"
    if styled:
        add_line(f"{BOLD}{FG_CYAN}{title.center(content_w)}{RESET}")
    else:
        add_line(title.center(content_w))

    lines.append(divider)

    # 1. Summary Metrics
    completed_sectors = set(getattr(player, "completed_sectors", []))
    total_challenges = 27 if not all_quests else max(27, len(all_quests))
    completed_count = len(completed_sectors)
    overall_pct = completed_count / total_challenges if total_challenges > 0 else 0.0

    # Accuracy calculation
    cmd_succeeded = getattr(player, "commands_succeeded", 0)
    cmd_total = getattr(player, "commands_run", 0)
    if cmd_total > 0:
        accuracy = int((cmd_succeeded / cmd_total) * 100)
    else:
        # High default starting baseline
        accuracy = 95 if completed_count > 0 else 100

    col1 = f"Player   : {BOLD}{player.character_name}{RESET if styled else ''}"
    col2 = f"Level : {FG_YELLOW}{player.level}{RESET if styled else ''} ({player.rank})"
    add_line(f"{col1:<32} {col2}")

    col3 = f"XP Total : {FG_GREEN}{player.xp}{RESET if styled else ''}"
    col4 = f"Streak: {FG_CYAN}{player.streak}{RESET if styled else ''} (Best: {player.max_streak})"
    add_line(f"{col3:<32} {col4}")

    col5 = f"Accuracy : {FG_GREEN}{accuracy}%{RESET if styled else ''}"
    col6 = f"Status: {FG_WHITE}{completed_count} of {total_challenges} complete{RESET if styled else ''}"
    add_line(f"{col5:<32} {col6}")

    add_line("")

    # Overall progress bar
    bar_str = render_progress_bar(overall_pct, bar_width=content_w - 20, styled=styled)
    add_line(f"Overall Progress: {bar_str}")

    lines.append(divider)

    # 2. Topic Breakdown
    sec_title = "TOPIC BREAKDOWN"
    if styled:
        add_line(f"{BOLD}{FG_YELLOW}{sec_title}{RESET}")
    else:
        add_line(sec_title)

    for topic in TOPICS:
        t_name = topic["name"]
        t_tools = topic["tools"]
        t_sectors = topic["sectors"]

        # Completion ratio for this topic
        topic_done = sum(1 for s in t_sectors if s in completed_sectors)
        topic_total = len(t_sectors)
        ratio = topic_done / topic_total if topic_total > 0 else 0.0

        bar = render_progress_bar(ratio, bar_width=14, styled=styled)
        row = f"{t_name:<16} {DIM}{t_tools:<24}{RESET if styled else ''} {bar}"
        add_line(row)

    lines.append(divider)
    footer_text = "Press Enter or Esc to return to terminal"
    add_line(f"{DIM}{footer_text.center(content_w)}{RESET if styled else ''}")
    lines.append(bot)

    return "\n".join(lines)


def view_progress_dashboard(
    player: PlayerStats,
    all_quests: Optional[Dict[int, Quest]] = None,
    width: int = 80,
) -> None:
    """Interactive full-screen viewer for Progress Dashboard."""
    output = render_progress_dashboard(player, all_quests, width=width, styled=True)
    sys.stdout.write("\033[H\033[J")
    sys.stdout.write(output + "\n")
    sys.stdout.flush()
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
