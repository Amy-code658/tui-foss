"""Tests for CyberShell RPG Modern TUI Engine (Theme, Animations, and Components)."""

from __future__ import annotations

import io
import math
import sys
import unittest
from unittest.mock import patch

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
    draw_progress_bar,
    draw_statusline,
    visual_len,
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


if __name__ == "__main__":
    unittest.main()
