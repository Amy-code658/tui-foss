"""CyberShell RPG - Telescope-style Fuzzy Finder for Command Codex & Docs.

Provides fast subsequence fuzzy matching and Neovim Telescope-style UI rendering.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from cybershell.ui.theme import (
    BOLD,
    DIM,
    FG_BLUE,
    FG_CYAN,
    FG_GREEN,
    FG_MUTED,
    FG_PURPLE,
    FG_TEXT,
    FG_YELLOW,
    RESET,
    strip_ansi,
    visual_len,
)


def fuzzy_score(pattern: str, candidate: str) -> Tuple[bool, int]:
    """Calculate subsequence fuzzy match score between pattern and candidate string.

    Returns:
        (matched, score): True with positive score if pattern is a subsequence,
        False with 0 otherwise.
    """
    pattern = pattern.strip().lower()
    candidate_lower = candidate.lower()

    if not pattern:
        return True, 100

    if pattern == candidate_lower:
        return True, 1000

    if pattern in candidate_lower:
        idx = candidate_lower.find(pattern)
        base = 500 - (idx * 5)
        if idx == 0:
            base += 100
        return True, base

    p_idx = 0
    p_len = len(pattern)
    score = 0
    prev_matched_idx = -2

    for c_idx, char in enumerate(candidate_lower):
        if p_idx < p_len and char == pattern[p_idx]:
            # Matched a character in sequence
            match_score = 10

            # Bonus for match at start of word or boundary
            if c_idx == 0 or candidate_lower[c_idx - 1] in " _-./":
                match_score += 25

            # Bonus for consecutive matches
            if c_idx == prev_matched_idx + 1:
                match_score += 20

            score += match_score
            prev_matched_idx = c_idx
            p_idx += 1

    if p_idx == p_len:
        # Full subsequence matched
        # Small length penalty so shorter/closer matches rank higher
        length_penalty = min(50, len(candidate_lower) - p_len)
        return True, max(1, score - length_penalty)

    return False, 0


def fuzzy_search_commands(
    query: str,
    commands: List[Dict[str, Any]],
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Fuzzy search a list of command dictionaries.

    Searches command name (weight 4x), description (weight 1.5x),
    flags, and examples. Returns sorted list of matching dicts with
    an added '_fuzzy_score' key.
    """
    query = query.strip()
    if not query:
        return commands[:limit]

    scored_results: List[Tuple[int, Dict[str, Any]]] = []

    for cmd in commands:
        name = str(cmd.get("name", ""))
        desc = str(cmd.get("description", ""))
        flags = cmd.get("flags", {})
        examples = cmd.get("examples", [])
        combos = cmd.get("combos", [])

        # Score name
        name_matched, name_score = fuzzy_score(query, name)
        final_score = (name_score * 4) if name_matched else 0

        # Score description
        desc_matched, desc_score = fuzzy_score(query, desc)
        if desc_matched:
            final_score = max(final_score, int(desc_score * 1.5))

        # Check flags
        for f_name, f_desc in flags.items():
            f_matched, f_score = fuzzy_score(query, f"{f_name} {f_desc}")
            if f_matched:
                final_score = max(final_score, f_score + 30)

        # Check examples
        for ex in examples:
            e_matched, e_score = fuzzy_score(query, str(ex))
            if e_matched:
                final_score = max(final_score, e_score + 20)

        # Check combos
        for cb in combos:
            c_matched, c_score = fuzzy_score(query, str(cb))
            if c_matched:
                final_score = max(final_score, c_score + 20)

        if final_score > 0:
            cmd_copy = dict(cmd)
            cmd_copy["_fuzzy_score"] = final_score
            scored_results.append((final_score, cmd_copy))

    # Sort descending by score, then alphabetically by command name
    scored_results.sort(key=lambda item: (-item[0], item[1].get("name", "")))
    return [item[1] for item in scored_results[:limit]]


def render_telescope_results(
    query: str,
    results: List[Dict[str, Any]],
    width: int = 76,
    styled: bool = True,
) -> List[str]:
    """Render a Neovim Telescope-style floating results card."""
    width = max(40, width)
    inner_w = width - 2
    content_w = inner_w - 2

    b_col = FG_PURPLE if styled else ""
    b_rst = RESET if styled else ""

    top_border = f"{b_col}╭{'─' * inner_w}╮{b_rst}"
    bot_border = f"{b_col}╰{'─' * inner_w}╯{b_rst}"
    div_border = f"{b_col}├{'─' * inner_w}┤{b_rst}"

    title_text = f" TELESCOPE // COMMAND CODEX "
    match_count = len(results)
    count_text = f"[{match_count} matches] "
    gap = inner_w - len(title_text) - len(count_text)
    if gap < 1:
        header_line = f" {title_text[:inner_w - 2]} "
    else:
        header_line = f"{title_text}{' ' * gap}{count_text}"

    if styled:
        h_rendered = f"{BOLD}{FG_PURPLE}{header_line}{RESET}"
    else:
        h_rendered = header_line

    prompt_label = "> "
    query_display = query if query else "*"
    if styled:
        prompt_line = f" {FG_GREEN}{prompt_label}{FG_TEXT}{query_display}{RESET}"
    else:
        prompt_line = f" {prompt_label}{query_display}"

    pad_p = max(0, inner_w - visual_len(prompt_line))
    p_row = f"{b_col}│{b_rst}{prompt_line}{' ' * pad_p}{b_col}│{b_rst}"

    pad_h = max(0, inner_w - visual_len(h_rendered))
    h_row = f"{b_col}│{b_rst}{h_rendered}{' ' * pad_h}{b_col}│{b_rst}"

    lines = [top_border, h_row, div_border, p_row, div_border]

    if not results:
        no_match = " No matching commands found. Try another search pattern."
        if styled:
            no_match = f"{FG_MUTED}{no_match}{RESET}"
        pad = max(0, inner_w - visual_len(no_match))
        lines.append(f"{b_col}│{b_rst}{no_match}{' ' * pad}{b_col}│{b_rst}")
    else:
        for idx, cmd in enumerate(results[:7]):
            name = cmd.get("name", "")
            desc = cmd.get("description", "")
            pointer = "::" if idx == 0 else "  "

            left_part = f" {pointer} {name:<8} "
            avail_desc = content_w - len(left_part)
            desc_part = desc[:avail_desc] if len(desc) > avail_desc else desc

            if styled:
                pointer_col = FG_CYAN if idx == 0 else FG_MUTED
                name_col = f"{BOLD}{FG_GREEN if idx == 0 else FG_TEXT}"
                desc_col = FG_MUTED
                rendered_item = (
                    f" {pointer_col}{pointer}{RESET} "
                    f"{name_col}{name:<8}{RESET} "
                    f"{desc_col}{desc_part}{RESET}"
                )
            else:
                rendered_item = f" {pointer} {name:<8} {desc_part}"

            pad = max(0, inner_w - visual_len(rendered_item))
            lines.append(f"{b_col}│{b_rst}{rendered_item}{' ' * pad}{b_col}│{b_rst}")

    lines.append(bot_border)
    return lines
