from __future__ import annotations

import io
import math
import os
import sys
import unittest
from unittest.mock import patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from cybershell.ui.animation import (
    CelebrationEffect,
    DOT_PULSE_FRAMES,
    SPARKLE_CHARS,
    SPINNER_FRAMES,
    ScreenTransition,
    Spinner,
    Typewriter,
    pulse_color,
)
from cybershell.ui.renderer import (
    draw_breadcrumb,
    draw_floating_modal,
    draw_overthewire_card,
    draw_progress_bar,
    draw_statusline,
    visual_len,
)
from cybershell.ui.search import (
    fuzzy_score,
    fuzzy_search_commands,
    render_telescope_results,
)
from cybershell.ui.theme import (
    BOLD,
    DIM,
    FG_BLUE,
    FG_CYAN,
    FG_GREEN,
    FG_PURPLE,
    FG_RED,
    FG_TEXT,
    FG_YELLOW,
    HEX_BG_DARK,
    HEX_BLUE,
    HEX_CYAN,
    HEX_GREEN,
    HEX_PURPLE,
    HEX_YELLOW,
    RESET,
    badge,
    bg_hex,
    bg_rgb,
    fg_hex,
    fg_rgb,
    gradient_text,
    hex_to_rgb,
    interpolate_color,
    pill,
    rgb_to_ansi256,
    strip_ansi,
    styled,
    supports_truecolor,
)


class TestModernThemeEngine(unittest.TestCase):
    """Verify TrueColor palette, color converters, gradients, and pill tags."""

    def test_hex_to_rgb(self) -> None:
        self.assertEqual(hex_to_rgb("#7aa2f7"), (122, 162, 247))
        self.assertEqual(hex_to_rgb("7aa2f7"), (122, 162, 247))
        self.assertEqual(hex_to_rgb("#fff"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("invalid"), (200, 200, 200))

    def test_rgb_to_ansi256(self) -> None:
        code_grey = rgb_to_ansi256(128, 128, 128)
        self.assertTrue(16 <= code_grey <= 255)
        code_color = rgb_to_ansi256(255, 0, 0)
        self.assertTrue(16 <= code_color <= 255)

    def test_supports_truecolor(self) -> None:
        self.assertTrue(supports_truecolor())

    def test_fg_and_bg_rgb_and_hex(self) -> None:
        fg_seq = fg_rgb(122, 162, 247)
        self.assertIn("122;162;247", fg_seq)
        bg_seq = bg_rgb(26, 27, 38)
        self.assertIn("26;27;38", bg_seq)

        fg_h = fg_hex("#7aa2f7")
        self.assertIn("122;162;247", fg_h)
        bg_h = bg_hex("#1a1b26")
        self.assertIn("26;27;38", bg_h)

    def test_styled_text(self) -> None:
        plain = "Hello World"
        styled_str = styled(plain, fg=HEX_CYAN, bold=True, dim=True)
        self.assertIn(plain, styled_str)
        self.assertEqual(strip_ansi(styled_str), plain)
        self.assertEqual(visual_len(styled_str), len(plain))

        # Tuple RGB support
        tuple_styled = styled(plain, fg=(100, 200, 100), bg=(20, 20, 20))
        self.assertEqual(strip_ansi(tuple_styled), plain)

    def test_pill_tags(self) -> None:
        # Styled pill with powerline caps
        tag = pill("SHELL", bg_hex_color=HEX_BLUE, styled_mode=True)
        self.assertIn("SHELL", tag)
        self.assertIn("", tag)
        self.assertIn("", tag)
        self.assertEqual(strip_ansi(tag).replace("", "").replace("", "").strip(), "SHELL")

        # Unstyled fallback
        unstyled_pill = pill("SHELL", styled_mode=False)
        self.assertEqual(unstyled_pill, "[SHELL]")

    def test_badge(self) -> None:
        b = badge("ADMIN", color_hex=HEX_PURPLE, styled_mode=True)
        self.assertIn("ADMIN", b)
        self.assertEqual(strip_ansi(b), "[ADMIN]")

        unstyled_b = badge("ADMIN", styled_mode=False)
        self.assertEqual(unstyled_b, "[ADMIN]")

    def test_interpolate_color(self) -> None:
        c1 = (0, 0, 0)
        c2 = (200, 100, 50)
        mid = interpolate_color(c1, c2, 0.5)
        self.assertEqual(mid, (100, 50, 25))

        # Clamping
        self.assertEqual(interpolate_color(c1, c2, -1.0), (0, 0, 0))
        self.assertEqual(interpolate_color(c1, c2, 2.0), (200, 100, 50))

    def test_gradient_text(self) -> None:
        text = "CYBERSHELL RPG"
        grad = gradient_text(text, start_hex=HEX_CYAN, end_hex=HEX_PURPLE, bold=True)
        self.assertEqual(strip_ansi(grad), text)
        self.assertEqual(visual_len(grad), len(text))

        # Empty and single char
        self.assertEqual(gradient_text(""), "")
        self.assertEqual(strip_ansi(gradient_text("A")), "A")
        self.assertEqual(gradient_text("Plain", styled_mode=False), "Plain")


class TestAnimationEngine(unittest.TestCase):
    """Verify Braille spinners, typewriter streamer, celebration and transitions."""

    def test_spinner_frames_and_ticks(self) -> None:
        spinner = Spinner(message="Processing", color_hex=HEX_GREEN)
        frame1 = spinner.tick()
        self.assertIn("Processing", frame1)
        self.assertIn(SPINNER_FRAMES[0], frame1)

        frame2 = spinner.tick()
        self.assertIn(SPINNER_FRAMES[1], frame2)

        # get_frame without mutating state
        idx_frame = spinner.get_frame(5)
        self.assertIn(SPINNER_FRAMES[5], idx_frame)

    def test_typewriter_stream_text(self) -> None:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            Typewriter.stream_text("Testing 123", delay=0.0)
        self.assertIn("Testing 123", buf.getvalue())

        # Empty string safe
        buf_empty = io.StringIO()
        with patch("sys.stdout", buf_empty):
            Typewriter.stream_text("", delay=0.0)
        self.assertEqual(buf_empty.getvalue(), "")

    def test_celebration_frames(self) -> None:
        frames = CelebrationEffect.get_frames(title="LEVEL 1 COMPLETE", subtitle="+100 XP", width=60)
        self.assertGreaterEqual(len(frames), 3)
        for frame in frames:
            self.assertTrue(len(frame) > 0)

    def test_celebration_render(self) -> None:
        card = CelebrationEffect.render_celebration(
            title="QUEST CLEARED!",
            subtitle="+50 XP",
            width=70,
            animate=False,
        )
        self.assertIn("QUEST CLEARED!", card)
        self.assertIn("+50 XP", card)
        for line in card.splitlines():
            self.assertLessEqual(visual_len(line), 70)

    def test_screen_transition_wipe(self) -> None:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            ScreenTransition.wipe_screen(lines=5, delay=0.0)
        self.assertIn("\033[2J\033[H", buf.getvalue())

    def test_pulse_color_oscillation(self) -> None:
        color0 = pulse_color(start_hex=HEX_CYAN, end_hex=HEX_PURPLE, step=0, period=20)
        self.assertTrue(color0.startswith("#"))
        self.assertEqual(len(color0), 7)

        color5 = pulse_color(start_hex=HEX_CYAN, end_hex=HEX_PURPLE, step=5, period=20)
        self.assertTrue(color5.startswith("#"))


class TestModernRenderComponents(unittest.TestCase):
    """Verify modern Lualine statusline, floating modal dialogs, and breadcrumbs."""

    def test_draw_statusline_layout_and_containment(self) -> None:
        statusline = draw_statusline(
            mode="COMMAND",
            breadcrumb="~ › sector-01 › pwd",
            objective="Inspect directory",
            xp=150,
            level=2,
            width=80,
            styled=True,
        )
        self.assertIn("COMMAND", statusline)
        self.assertIn("sector-01", statusline)
        self.assertIn("150 XP", statusline)
        self.assertLessEqual(visual_len(statusline), 80)

        # Unstyled statusline
        unstyled = draw_statusline(
            mode="SHELL",
            breadcrumb="~",
            objective="Explore",
            xp=50,
            level=1,
            width=60,
            styled=False,
        )
        self.assertIn("[SHELL]", unstyled)
        self.assertLessEqual(visual_len(unstyled), 60)

    def test_draw_floating_modal(self) -> None:
        modal = draw_floating_modal(
            title="SECRET UNLOCKED",
            content=[
                "You discovered an easter egg folder!",
                "Reward: +25 XP & Master Explorer Badge",
            ],
            width=50,
            styled=True,
            shadow=True,
        )
        self.assertIn("SECRET UNLOCKED", modal)
        self.assertIn("easter egg", modal)
        for line in modal.splitlines():
            self.assertLessEqual(visual_len(line), 50)

    def test_draw_breadcrumb(self) -> None:
        crumb = draw_breadcrumb(["~", "levels", "level-01", "notes.txt"], styled=True)
        self.assertIn("›", crumb)
        self.assertIn("notes.txt", crumb)

        plain_crumb = draw_breadcrumb(["root", "etc"], styled=False)
        self.assertEqual(plain_crumb, "root › etc")

    def test_draw_progress_bar(self) -> None:
        bar_50 = draw_progress_bar(current=5, total=10, width=10, styled=False)
        self.assertEqual(bar_50, "█████░░░░░")

        bar_100 = draw_progress_bar(current=10, total=10, width=8, styled=False)
        self.assertEqual(bar_100, "████████")

        bar_styled = draw_progress_bar(current=3, total=10, width=10, styled=True)
        self.assertEqual(visual_len(bar_styled), 10)


class TestFuzzySearch(unittest.TestCase):
    """Verify subsequence fuzzy score, ranked command search, and Telescope UI rendering."""

    def test_fuzzy_score_exact_match(self) -> None:
        matched, score = fuzzy_score("grep", "grep")
        self.assertTrue(matched)
        self.assertEqual(score, 1000)

    def test_fuzzy_score_substring_prefix(self) -> None:
        matched, score = fuzzy_score("gre", "grep")
        self.assertTrue(matched)
        self.assertGreater(score, 500)

    def test_fuzzy_score_subsequence(self) -> None:
        matched, score = fuzzy_score("gp", "grep")
        self.assertTrue(matched)
        self.assertGreater(score, 0)

    def test_fuzzy_score_no_match(self) -> None:
        matched, score = fuzzy_score("xyz", "grep")
        self.assertFalse(matched)
        self.assertEqual(score, 0)

    def test_fuzzy_score_empty_pattern(self) -> None:
        matched, score = fuzzy_score("", "grep")
        self.assertTrue(matched)

    def test_fuzzy_search_commands_ranking(self) -> None:
        commands = [
            {"name": "grep", "description": "Search text patterns using regex", "flags": {"-r": "Recursive"}},
            {"name": "find", "description": "Search files in a directory hierarchy", "flags": {"-name": "Name pattern"}},
            {"name": "cat", "description": "Concatenate files and print on stdout"},
            {"name": "ls", "description": "List directory contents"},
        ]

        # Searching 'grep' should rank grep first
        results = fuzzy_search_commands("grep", commands)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "grep")

        # Searching 'search' should match both grep and find by description
        results_desc = fuzzy_search_commands("search", commands)
        matched_names = [r["name"] for r in results_desc]
        self.assertIn("grep", matched_names)
        self.assertIn("find", matched_names)

        # Empty query returns original commands up to limit
        all_results = fuzzy_search_commands("", commands, limit=2)
        self.assertEqual(len(all_results), 2)

    def test_render_telescope_results(self) -> None:
        sample_results = [
            {"name": "grep", "description": "Print lines matching a pattern"},
            {"name": "find", "description": "Search for files in a directory"},
        ]
        lines = render_telescope_results("gr", sample_results, width=76, styled=True)
        self.assertGreater(len(lines), 4)

        # First line should be top border
        self.assertTrue(lines[0].startswith("\033[") or lines[0].startswith("╭") or lines[0].startswith("┏"))

        # Telescope header should be present
        combined = "\n".join(lines)
        self.assertIn("TELESCOPE", combined)
        self.assertIn("grep", combined)
        self.assertIn("find", combined)

        # Width containment test
        for line in lines:
            self.assertLessEqual(visual_len(line), 76)

        # Empty results handling
        empty_lines = render_telescope_results("nonexistent", [], width=70, styled=False)
        empty_combined = "\n".join(empty_lines)
        self.assertIn("No matching commands found", empty_combined)
        for line in empty_lines:
            self.assertLessEqual(visual_len(line), 70)


class TestOverTheWireBriefing(unittest.TestCase):
    """Verify OverTheWire Bandit style wargame mission briefing cards."""

    def test_draw_overthewire_card_contents(self) -> None:
        card = draw_overthewire_card(
            sector_id=0,
            sector_name="Filesystem Basics",
            target_text="Find the hidden flag in the current directory.",
            scenario="A secret token was left behind by the prior admin.",
            suggested_commands=["pwd", "ls", "cat"],
            current_hint="Use ls -la to reveal hidden files.",
            width=80,
            styled=False,
        )
        self.assertIn("LEVEL 01", card)
        self.assertIn("FILESYSTEM BASICS", card)
        self.assertIn("TARGET   :", card)
        self.assertIn("SCENARIO :", card)
        self.assertIn("COMMANDS :", card)
        self.assertIn("pwd, ls, cat", card)
        self.assertIn("HINT     :", card)
        self.assertIn("Use ls -la", card)

        # Verify no ABCD multiple-choice options are rendered
        self.assertNotIn("[A]", card)
        self.assertNotIn("[B]", card)
        self.assertNotIn("[C]", card)
        self.assertNotIn("[D]", card)

    def test_draw_overthewire_card_width_containment(self) -> None:
        card_styled = draw_overthewire_card(
            sector_id=2,
            sector_name="Permissions & Ownership",
            target_text="Gain read access to the encrypted payload in /secure/vault.",
            scenario="File permissions are restricted to user root:root.",
            suggested_commands=["chmod", "chown", "sudo"],
            width=80,
            styled=True,
        )
        for line in card_styled.splitlines():
            self.assertLessEqual(visual_len(line), 80, f"Line exceeded width 80: {line}")


if __name__ == "__main__":
    unittest.main()
