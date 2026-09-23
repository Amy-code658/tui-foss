"""Unit Test Suite for Byte's Linux Adventure UI & Visual Assets.

Covers:
- Visual Assets: ASCII logos, friendly character portraits, avatar badges, and celebration banners.
- Terminal Buffer: Command history, scrolling log buffer, and prompt formatting.
- Activity Ticker: Bottom broadcast strip, message categories, and width containment.
- RPGApp Screen Controller: Dual-pane layout, screen routing, zero layout clipping, and UIProtocol conformance.
"""

from __future__ import annotations

import os
import sys
import unittest

# Ensure src/ is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from cybershell.contracts import Item, PlayerStats, UIProtocol
from cybershell.ui.ascii_art import (
    ADVENTURE_LOGO,
    ADVENTURE_LOGO_COMPACT,
    AVATARS,
    CYBER_LOGO,
    CYBER_LOGO_COMPACT,
    DEFEAT_BANNER,
    FIELD_MANUAL_HEADER,
    PORTRAITS,
    VICTORY_BANNER,
    get_avatar_badge,
    get_defeat_banner,
    get_logo,
    get_portrait,
    get_victory_banner,
    strip_ansi,
    visual_len,
)
from cybershell.ui.renderer import (
    draw_compact_hud,
    draw_control_footer,
    draw_double_header,
    draw_field_manual_card,
    draw_panel,
    draw_question_card,
    draw_split_panels,
    pad_to_width,
    truncate_styled,
)
from cybershell.ui.rpg_app import CombatTicker, RPGApp, TerminalBuffer


class TestASCIIArt(unittest.TestCase):
    """Test friendly ASCII logo, character portraits, and visual banners."""

    def test_cyber_logo_dimensions_and_content(self) -> None:
        """Verify adventure logo fits standard 80-col terminal frames and has content."""
        lines = ADVENTURE_LOGO.strip("\n").splitlines()
        self.assertGreater(len(lines), 3)
        for line in lines:
            self.assertLessEqual(visual_len(line), 80, f"Logo line exceeded 80 chars: {line}")

        # Check unstyled and styled get_logo()
        plain = get_logo(styled=False)
        self.assertIn("____", plain)
        self.assertEqual(strip_ansi(plain), plain)

        styled = get_logo(styled=True)
        self.assertIn("\033[", styled)
        self.assertEqual(strip_ansi(styled), plain)

        # Check compact logo
        self.assertIn("BYTE'S LINUX ADVENTURE", ADVENTURE_LOGO_COMPACT)
        self.assertEqual(CYBER_LOGO_COMPACT, ADVENTURE_LOGO_COMPACT)

    def test_all_npc_portraits_exist_and_are_uniform(self) -> None:
        """Verify all guides have complete portraits with uniform line lengths."""
        required_npcs = ["byte", "fern", "penny", "nova", "guide", "player"]
        for npc in required_npcs:
            portrait = get_portrait(npc, styled=False)
            self.assertGreaterEqual(len(portrait), 5, f"Portrait for {npc} has fewer than 5 lines")

            # Check that line widths within each portrait are consistent (prevent jitter)
            widths = [visual_len(line) for line in portrait]
            first_width = widths[0]
            for idx, w in enumerate(widths):
                self.assertEqual(
                    w,
                    first_width,
                    f"Line {idx} of {npc} portrait width ({w}) != first line width ({first_width})",
                )

        # Verify fallback for unknown NPC defaults to Byte
        unknown = get_portrait("unknown_character_xyz")
        byte_portrait = get_portrait("byte")
        self.assertEqual(unknown, byte_portrait)

        # Verify styled portraits preserve text and add ANSI codes
        styled_fern = get_portrait("fern", styled=True)
        plain_fern = get_portrait("fern", styled=False)
        self.assertEqual(len(styled_fern), len(plain_fern))
        for s_line, p_line in zip(styled_fern, plain_fern):
            self.assertEqual(strip_ansi(s_line), p_line)

    def test_avatar_badges(self) -> None:
        """Verify friendly compact avatars for quick attribution."""
        self.assertEqual(get_avatar_badge("byte"), "(・ω・)")
        self.assertEqual(get_avatar_badge("fern"), "(^‿^)")
        self.assertEqual(get_avatar_badge("penny"), "(•‿•)")
        self.assertEqual(get_avatar_badge("nova"), "(★‿★)")
        self.assertEqual(get_avatar_badge("non_existent"), "(・ω・)")

    def test_victory_and_defeat_banners(self) -> None:
        """Verify celebration and encouraging banner formatting."""
        victory = get_victory_banner(styled=False)
        self.assertIn("ADVENTURE COMPLETE", victory)
        self.assertIn("MASTER EXPLORER", victory)
        self.assertEqual(victory, VICTORY_BANNER)

        defeat = get_defeat_banner(styled=False)
        self.assertIn("Mistakes are a great way to learn!", defeat)
        self.assertEqual(defeat, DEFEAT_BANNER)

        # Styled banners preserve clean text
        self.assertEqual(strip_ansi(get_victory_banner(styled=True)), VICTORY_BANNER)
        self.assertEqual(strip_ansi(get_defeat_banner(styled=True)), DEFEAT_BANNER)

    def test_draw_question_card_rendering(self) -> None:
        """Verify draw_question_card formats within 80 columns without clipping."""
        card = draw_question_card(
            question_num=1,
            total_questions=2,
            question_text="Which Linux command displays your current working directory path?",
            options=[
                "ls       - List files in current folder",
                "pwd      - Print working directory path",
                "cd       - Change current directory",
                "whoami   - Display current logged in user",
            ],
            scenario="You just opened a terminal in a new system.",
            width=80,
            styled=True,
        )
        self.assertIn("QUESTION 1/2", card)
        self.assertIn("[A]", card)
        self.assertIn("[B]", card)
        self.assertIn("[C]", card)
        self.assertIn("[D]", card)
        self.assertIn("pwd", card)
        for line in card.splitlines():
            self.assertLessEqual(visual_len(line), 80, f"Question card line exceeded 80 cols: {line}")

        # Empty returns empty string
        self.assertEqual(draw_question_card(question_text="", options=[]), "")


class TestTerminalBufferWidget(unittest.TestCase):
    """Test terminal input widget and scrolling log buffer."""

    def setUp(self) -> None:
        self.buffer = TerminalBuffer(prompt="byte@adventure:~$ ", max_lines=10)

    def test_initial_buffer_state(self) -> None:
        self.assertGreater(len(self.buffer.logs), 0)
        visible = self.buffer.get_visible_logs(5)
        self.assertLessEqual(len(visible), 5)
        self.assertEqual(self.buffer.prompt, "byte@adventure:~$ ")

    def test_scrolling_buffer_capacity(self) -> None:
        """Buffer must cap total lines at max_lines and retain newest entries."""
        for i in range(25):
            self.buffer.add_log(f"log line {i}")

        self.assertEqual(len(self.buffer.logs), 10)
        self.assertEqual(self.buffer.logs[-1], "log line 24")
        self.assertEqual(self.buffer.logs[0], "log line 15")

    def test_add_command_and_history_navigation(self) -> None:
        """Commands must be logged and navigable via history."""
        self.buffer.add_command("pwd")
        self.buffer.add_command("ls -a")
        self.buffer.add_command("cat note.txt")

        self.assertEqual(self.buffer.history, ["pwd", "ls -a", "cat note.txt"])
        self.assertIn("byte@adventure:~$ pwd", self.buffer.logs)

        # History previous (backward)
        self.assertEqual(self.buffer.history_prev(), "cat note.txt")
        self.assertEqual(self.buffer.history_prev(), "ls -a")
        self.assertEqual(self.buffer.history_prev(), "pwd")
        # Clamped at oldest
        self.assertEqual(self.buffer.history_prev(), "pwd")

        # History next (forward)
        self.assertEqual(self.buffer.history_next(), "ls -a")
        self.assertEqual(self.buffer.history_next(), "cat note.txt")
        self.assertEqual(self.buffer.history_next(), "")

    def test_clear_buffer(self) -> None:
        self.buffer.clear()
        self.assertEqual(len(self.buffer.logs), 0)
        visible = self.buffer.get_visible_logs(5)
        self.assertEqual(visible, ["(terminal ready)"])


class TestCombatLogTicker(unittest.TestCase):
    """Test bottom activity broadcast strip and friendly feedback."""

    def setUp(self) -> None:
        self.ticker = CombatTicker()

    def test_ticker_initial_state(self) -> None:
        self.assertIn("Welcome to Byte's Linux Adventure!", self.ticker.active_message)

    def test_ticker_categories_and_formatting(self) -> None:
        # Star / Badge
        self.ticker.log("First Step Badge Earned!", category="badge")
        self.assertEqual(self.ticker.active_message, "⭐ First Step Badge Earned!")

        # Goodie Acquired
        self.ticker.log("Golden Compass acquired", category="loot")
        self.assertEqual(self.ticker.active_message, "🎁 Golden Compass acquired")

        # Level Up / XP
        self.ticker.log("LEVEL UP! Rank: Master Explorer", category="level")
        self.assertEqual(self.ticker.active_message, "🌟 LEVEL UP! Rank: Master Explorer")

        # Objective
        self.ticker.log("OBJECTIVE COMPLETED: +50 XP", category="objective")
        self.assertEqual(self.ticker.active_message, "🎯 OBJECTIVE COMPLETED: +50 XP")

        # Hint
        self.ticker.log("Try typing 'pwd'", category="hint")
        self.assertEqual(self.ticker.active_message, "💡 Try typing 'pwd'")

    def test_ticker_render_width_containment(self) -> None:
        """Rendered ticker must strictly fit terminal width without line breaking."""
        self.ticker.log("Level 10 completed! Great job!", category="level")
        rendered = self.ticker.render(width=80)
        self.assertLessEqual(visual_len(rendered), 80)
        self.assertIn("Level 10 completed", rendered)

        # Narrow terminal truncation
        narrow_rendered = self.ticker.render(width=30)
        self.assertLessEqual(visual_len(narrow_rendered), 30)
        self.assertIn("…", narrow_rendered)


class TestRPGAppGauthamIntegration(unittest.TestCase):
    """Test RPGApp screen controller and UIProtocol compliance."""

    def setUp(self) -> None:
        self.app = RPGApp(character_name="Byte", hp=100, max_hp=100, xp=50)

    def test_ui_protocol_conformance(self) -> None:
        """Verify RPGApp satisfies UIProtocol from contracts.py."""
        self.assertTrue(
            isinstance(self.app, UIProtocol),
            "RPGApp does not satisfy UIProtocol from contracts.py",
        )

    def test_update_stats(self) -> None:
        self.app.update_stats(hp=100, max_hp=100, xp=150)
        self.assertEqual(self.app.xp, 150)

    def test_log_ticker(self) -> None:
        self.app.log_ticker("LEVEL COMPLETE!", category="objective")
        self.assertIn("LEVEL COMPLETE!", self.app.ticker.active_message)
        self.assertIn("🎯", self.app.ticker.active_message)

    def test_title_screen_contains_logo_and_navigation(self) -> None:
        title = strip_ansi(self.app.render_title(80))
        self.assertIn("MAIN DIRECTORY", title)
        self.assertIn("____", title)
        self.assertIn("1 \ue0b4  START ADVENTURE", title)

    def test_zero_layout_clipping_at_80_columns(self) -> None:
        """Strict check: every line rendered at 80 cols must NOT exceed 80 chars."""
        # Title screen
        for line in self.app.render_title(80).splitlines():
            self.assertLessEqual(visual_len(line), 80, f"Title line clipped: {line}")

        # Lab / Playground screen
        for line in self.app.render_lab(80).splitlines():
            self.assertLessEqual(visual_len(line), 80, f"Lab line clipped: {line}")

        # Codex / Guide screen
        for line in self.app.render_codex(80).splitlines():
            self.assertLessEqual(visual_len(line), 80, f"Codex line clipped: {line}")

    def test_victory_and_defeat_screens(self) -> None:
        victory = self.app.render_victory(80)
        self.assertIn("ADVENTURE COMPLETE", victory)

        defeat = self.app.render_defeat(80)
        self.assertIn("Mistakes are a great way to learn!", defeat)

    def test_field_manual_card_dimensions_and_visibility(self) -> None:
        """Field manual card must be strictly <= 16 lines and <= 80 chars wide on all pages."""
        # Page 1: Rules
        card_p1 = draw_field_manual_card(page=1, width=80, styled=False)
        lines_p1 = card_p1.splitlines()
        self.assertLessEqual(len(lines_p1), 16, f"Page 1 has {len(lines_p1)} lines, expected <= 16")
        for line in lines_p1:
            self.assertLessEqual(visual_len(line), 80, f"Page 1 line exceeded 80 cols: {line}")
        self.assertIn("15 Levels", card_p1)
        self.assertIn("Real Shell", card_p1)
        self.assertIn("ZERO damage", card_p1)
        self.assertIn("Easy Hints", card_p1)
        self.assertIn("Progress Map", card_p1)
        self.assertIn("Main Menu", card_p1)
        self.assertIn("Byte", card_p1)

        # Page 2: Commands
        card_p2 = draw_field_manual_card(page=2, width=80, styled=False)
        lines_p2 = card_p2.splitlines()
        self.assertLessEqual(len(lines_p2), 16, f"Page 2 has {len(lines_p2)} lines, expected <= 16")
        for line in lines_p2:
            self.assertLessEqual(visual_len(line), 80, f"Page 2 line exceeded 80 cols: {line}")
        self.assertIn("pwd", card_p2)
        self.assertIn("cd", card_p2)
        self.assertIn("cat", card_p2)
        self.assertIn("grep", card_p2)

    def test_render_manual_visibility(self) -> None:
        """RPGApp.render_manual must fit standard frames without clipping."""
        manual = self.app.render_manual(80)
        lines = manual.splitlines()
        self.assertLessEqual(len(lines), 16)
        for line in lines:
            self.assertLessEqual(visual_len(line), 80, f"Manual line clipped: {line}")
        self.assertIn("FIELD MANUAL & RULES", manual)

    def test_draw_double_header_dimensions(self) -> None:
        """Verify draw_double_header renders within exact specified width."""
        header = draw_double_header(
            character_name="Byte",
            hp=100,
            max_hp=100,
            xp=150,
            sector_title="ADVENTURE MAP",
            width=74,
            styled=True,
        )
        lines = header.splitlines()
        self.assertEqual(len(lines), 4)
        for line in lines:
            self.assertEqual(visual_len(line), 74)
        self.assertIn("BYTE'S LINUX ADVENTURE", header)
        self.assertIn("150 XP", header)
        self.assertIn("ADVENTURE MAP", header)

    def test_view_field_manual_navigation(self) -> None:
        """view_field_manual must support page progression and exit cleanly."""
        from unittest.mock import patch
        from cybershell.run import view_field_manual

        # Press Enter on page 1 -> moves to page 2 -> press Enter on page 2 -> exits
        with patch("builtins.input", side_effect=["", ""]):
            with patch("sys.stdout"):
                view_field_manual(80)

        # Type '0' on page 1 -> exits immediately
        with patch("builtins.input", side_effect=["0"]):
            with patch("sys.stdout"):
                view_field_manual(80)

    def test_view_codex_navigation(self) -> None:
        """view_codex allows searching commands and exits cleanly."""
        from io import StringIO
        from unittest.mock import patch
        from cybershell.run import view_codex
        from cybershell.tools.codex import Codex

        codex = Codex()
        player = PlayerStats(character_name="Byte", hp=100, max_hp=100, xp=50)

        # Search for pwd, then press Enter to return, then 0 to exit
        buf = StringIO()
        with patch("builtins.input", side_effect=["pwd", "", "0"]):
            with patch("sys.stdout", buf):
                view_codex(codex, player, 80)
        output = buf.getvalue()
        self.assertIn("LINUX COMMAND GUIDE", output)
        self.assertIn("GUIDE: PWD", output)

    def test_view_inventory_rendering(self) -> None:
        """view_inventory displays backpack items and badges without errors."""
        from io import StringIO
        from unittest.mock import patch
        from cybershell.run import view_inventory

        player = PlayerStats(character_name="Byte", hp=100, max_hp=100, xp=100)
        player.inventory.append(
            Item(id="star_1", name="Gold Star", description="A shiny star", rarity="legendary")
        )
        player.badges.append("Scout Badge")

        buf = StringIO()
        with patch("builtins.input", side_effect=[""]):
            with patch("sys.stdout", buf):
                view_inventory(player, 80)
        output = buf.getvalue()
        self.assertIn("YOUR BACKPACK & GOODIES", output)
        self.assertIn("Gold Star", output)
        self.assertIn("Scout Badge", output)

    def test_view_map_rendering(self) -> None:
        """view_map displays 15 levels and exits on Enter."""
        from io import StringIO
        from unittest.mock import patch
        from cybershell.run import view_map
        from cybershell.tools.map import MainframeMap
        from cybershell.game.quests import get_sector_quests

        player = PlayerStats(character_name="Byte", hp=100, max_hp=100, xp=100, current_sector=1)
        player.completed_sectors.append(0)
        mainframe = MainframeMap()
        quests = get_sector_quests()

        buf = StringIO()
        with patch("builtins.input", side_effect=[""]):
            with patch("sys.stdout", buf):
                view_map(mainframe, player, quests, 80)
        output = buf.getvalue()
        self.assertIn("ADVENTURE MAP (15 LEVELS)", output)
        self.assertIn("Completed", output)
        self.assertIn("Current", output)


if __name__ == "__main__":
    unittest.main()
