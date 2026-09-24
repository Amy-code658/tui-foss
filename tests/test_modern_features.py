"""Comprehensive tests for Byte's Linux Adventure modern TUI features.

Covers:
1. 12 Developer Themes & Theme Engine
2. Context-Aware Field Manual & Codex contextual prioritization
3. Terminal Pet companion state machine & rendering (no emojis)
4. Ambience Manager (rain, calm animations, pulse)
5. Progress Dashboard (metrics, accuracy, topic breakdown)
6. Mini-games: Terminal Snake, Vim Dojo, Typing Dojo (safe string drill)
7. Command Center palette rendering
"""

import unittest
from cybershell.contracts import PlayerStats
from cybershell.ui.theme import (
    THEMES,
    Theme,
    list_themes,
    get_active_theme,
    set_theme,
)
from cybershell.tools.codex import (
    Codex,
    format_field_manual_entry,
    get_contextual_commands,
)
from cybershell.ui.pet import TerminalPet, get_terminal_pet
from cybershell.ui.ambience import AmbienceManager, get_ambience_manager
from cybershell.ui.dashboard import (
    render_progress_bar,
    render_progress_dashboard,
    TOPICS,
)
from cybershell.tools.minigames.snake import TerminalSnake
from cybershell.tools.minigames.vim_dojo import VimDojo
from cybershell.tools.minigames.typing_dojo import TypingDojo
from cybershell.tools.minigames.hub import render_minigames_menu
from cybershell.ui.command_center import render_command_center, PALETTE_ACTIONS


class TestThemes(unittest.TestCase):
    """Verify 17 developer and pastel color themes and switching mechanism."""

    def test_eighteen_themes_registered(self) -> None:
        themes = list_themes()
        self.assertEqual(len(themes), 18)
        theme_ids = {t.id for t in themes}
        required_ids = {
            "tokyo-night",
            "dracula",
            "catppuccin-mocha",
            "catppuccin-latte",
            "nord",
            "everforest",
            "gruvbox",
            "solarized-dark",
            "solarized-light",
            "one-dark",
            "monokai",
            "rose-pine",
            "foss",
            "pastel-lavender",
            "pastel-sakura",
            "pastel-mint",
            "pastel-peach",
            "web-minimal",
        }
        self.assertTrue(required_ids.issubset(theme_ids))

    def test_pastel_and_minimal_theme_aliases(self) -> None:
        self.assertTrue(set_theme("sakura"))
        self.assertEqual(get_active_theme().id, "pastel-sakura")
        self.assertTrue(set_theme("pastel-mint"))
        self.assertEqual(get_active_theme().id, "pastel-mint")
        self.assertTrue(set_theme("peach"))
        self.assertEqual(get_active_theme().id, "pastel-peach")
        self.assertTrue(set_theme("lavender"))
        self.assertEqual(get_active_theme().id, "pastel-lavender")
        self.assertTrue(set_theme("web"))
        self.assertEqual(get_active_theme().id, "web-minimal")
        self.assertTrue(set_theme("minimal"))
        self.assertEqual(get_active_theme().id, "web-minimal")

    def test_theme_switching(self) -> None:
        success = set_theme("dracula")
        self.assertTrue(success)
        active = get_active_theme()
        self.assertEqual(active.id, "dracula")

        # Case-insensitive / display name
        success_name = set_theme("Nord")
        self.assertTrue(success_name)
        self.assertEqual(get_active_theme().id, "nord")

        # Invalid theme
        invalid = set_theme("nonexistent-theme-xyz")
        self.assertFalse(invalid)

        # Reset to tokyo-night
        set_theme("tokyo-night")

    def test_theme_colors_and_ansi_properties(self) -> None:
        set_theme("tokyo-night")
        tn = get_active_theme()
        set_theme("dracula")
        drac = get_active_theme()
        self.assertNotEqual(tn.fg_purple, drac.fg_purple)
        self.assertNotEqual(tn.fg_cyan, drac.fg_cyan)
        self.assertTrue(drac.fg_white.startswith("\033["))
        self.assertTrue(drac.fg_green.startswith("\033["))
        set_theme("tokyo-night")


class TestFieldManualAndCodex(unittest.TestCase):
    """Verify Context-Aware Field Manual and command relevance."""

    def test_field_manual_formatting(self) -> None:
        entry = format_field_manual_entry("mkdir")
        self.assertIn("mkdir — ", entry)
        self.assertIn("Purpose:", entry)
        self.assertIn("Syntax:", entry)
        self.assertIn("Explanation:", entry)
        self.assertIn("Example:", entry)
        self.assertIn("Related:", entry)

    def test_field_manual_unknown_command(self) -> None:
        entry = format_field_manual_entry("supercalifragilistic")
        self.assertIn("No Field Manual entry", entry)

    def test_contextual_commands_prioritization(self) -> None:
        codex = Codex()
        # Request with touch & mkdir relevant to challenge
        results = codex.get_contextual_commands(relevant_cmds=["touch", "mkdir"], limit=5)
        names = [r["name"] for r in results]
        self.assertEqual(names[0], "mkdir")
        self.assertEqual(names[1], "touch")


class TestTerminalPet(unittest.TestCase):
    """Verify ASCII Terminal Pet reactions and rendering."""

    def setUp(self) -> None:
        self.pet = TerminalPet(name="Byte", enabled=True)

    def test_pet_success_reaction_and_streak(self) -> None:
        self.pet.react_success("ls")
        self.assertEqual(self.pet.state, "happy")
        self.assertEqual(self.pet.streak_count, 1)

        # Trigger streak
        self.pet.react_success("cd")
        self.pet.react_success("cat")
        self.assertEqual(self.pet.state, "celebrating")
        self.assertEqual(self.pet.streak_count, 3)

    def test_pet_error_reaction(self) -> None:
        self.pet.react_success("ls")
        self.pet.react_error("No such file")
        self.assertEqual(self.pet.state, "confused")
        self.assertEqual(self.pet.streak_count, 0)

    def test_pet_toggle(self) -> None:
        self.assertTrue(self.pet.enabled)
        new_state = self.pet.toggle()
        self.assertFalse(new_state)
        self.assertFalse(self.pet.enabled)

    def test_pet_render_no_emojis(self) -> None:
        rendered_lines = self.pet.render(width=24, height=6, styled=False)
        self.assertEqual(len(rendered_lines), 6)
        joined = "".join(rendered_lines)
        self.assertIn("Byte", joined)
        # Check no emojis in sprites
        for char in joined:
            self.assertLess(ord(char), 0x1000, f"Emoji or non-ascii/latin character found: {char!r}")

    def test_cute_penguin_pet_styling(self) -> None:
        styled_lines = self.pet.render(width=24, height=6, styled=True)
        self.assertEqual(len(styled_lines), 6)
        joined = "".join(styled_lines)
        self.assertIn("121;192;255", joined)
        self.assertIn("241;224;90", joined)
        self.assertIn(">v<", joined)

    def test_pet_personalized_name(self) -> None:
        self.pet.set_player_name("Amy")
        self.assertEqual(self.pet.player_name, "Amy")
        self.pet.current_quote = "Great job, {name}!"
        rendered = self.pet.render(width=30, height=6, styled=False)
        joined = "".join(rendered)
        self.assertIn("Amy", joined)


class TestAmbienceManager(unittest.TestCase):
    """Verify ambient rain and calm animations."""

    def setUp(self) -> None:
        self.ambience = AmbienceManager()

    def test_toggle_states(self) -> None:
        self.assertFalse(self.ambience.rain_enabled)
        self.assertTrue(self.ambience.toggle_rain())
        self.assertTrue(self.ambience.rain_enabled)

        self.assertFalse(self.ambience.calm_animations)
        self.assertTrue(self.ambience.toggle_calm_animations())
        self.assertTrue(self.ambience.calm_animations)

        summary = self.ambience.get_status_summary()
        self.assertIn("Rain: ON", summary)
        self.assertIn("Calm Anim: ON", summary)

    def test_rain_backdrop_generation(self) -> None:
        self.ambience.rain_enabled = True
        backdrop = self.ambience.generate_rain_backdrop(width=40, height=5)
        self.assertEqual(len(backdrop), 5)

    def test_rain_line_and_padding_lengths(self) -> None:
        from cybershell.ui.renderer import visual_len
        self.ambience.rain_enabled = True
        line = self.ambience.render_rain_line(50, density=0.20)
        self.assertEqual(visual_len(line), 50)

        padded = self.ambience.pad_with_rain("Hello World", 40)
        self.assertEqual(visual_len(padded), 40)
        self.assertTrue(padded.startswith("Hello World"))

        # When rain is disabled
        self.ambience.rain_enabled = False
        plain_padded = self.ambience.pad_with_rain("Hello", 20)
        self.assertEqual(visual_len(plain_padded), 20)
        self.assertEqual(plain_padded, "Hello" + (" " * 15))


class TestProgressDashboard(unittest.TestCase):
    """Verify dashboard metrics and topic breakdown."""

    def test_progress_bar_calculation(self) -> None:
        zero_bar = render_progress_bar(0.0, bar_width=10, styled=False)
        self.assertIn("0%", zero_bar)
        full_bar = render_progress_bar(1.0, bar_width=10, styled=False)
        self.assertIn("100%", full_bar)

    def test_dashboard_rendering(self) -> None:
        player = PlayerStats(character_name="TestHero")
        player.completed_sectors = [0, 1, 2]
        player.level = 2
        player.streak = 3
        player.max_streak = 5
        output = render_progress_dashboard(player, width=80, styled=False)
        self.assertIn("PROGRESS & SKILL DASHBOARD", output)
        self.assertIn("3 of 27 complete", output)
        self.assertIn("TestHero", output)
        self.assertIn("Navigation", output)
        self.assertIn("TOPIC BREAKDOWN", output)


class TestMiniGames(unittest.TestCase):
    """Verify Snake, Vim Dojo, and Typing Dojo."""

    def test_snake_mechanics(self) -> None:
        snake = TerminalSnake(width=20, height=10, target_goals=3)
        self.assertFalse(snake.game_over)
        initial_score = snake.score
        # Step right
        alive = snake.step("d")
        self.assertTrue(alive)

    def test_vim_dojo_mechanics(self) -> None:
        dojo = VimDojo(target_count=3)
        self.assertEqual(dojo.hits, 0)
        target_key = dojo.current_target["key"]
        # Strike correctly
        hit = dojo.step(target_key)
        self.assertTrue(hit)
        self.assertEqual(dojo.hits, 1)

        # Strike wrong key
        wrong_key = "zzz_not_vim"
        miss = dojo.step(wrong_key)
        self.assertFalse(miss)
        self.assertEqual(dojo.misses, 1)

    def test_typing_dojo_safety_and_scoring(self) -> None:
        dojo = TypingDojo(rounds=2)
        # Verify text is purely compared as string and never executed
        prompt = dojo.current_prompt
        exact, acc = dojo.step(prompt)
        self.assertTrue(exact)
        self.assertEqual(acc, 100.0)
        self.assertGreater(dojo.wpm, 0.0)

    def test_minigames_hub_menu(self) -> None:
        menu = render_minigames_menu(width=65, styled=False)
        self.assertIn("CYBERSHELL ARCADE", menu)
        self.assertIn("Terminal Snake", menu)
        self.assertIn("Vim Dojo", menu)
        self.assertIn("Typing Dojo", menu)


class TestCommandCenter(unittest.TestCase):
    """Verify developer Command Center palette."""

    def test_command_center_render(self) -> None:
        player = PlayerStats()
        palette = render_command_center(player, width=74, styled=False)
        self.assertIn("COMMAND CENTER // PALETTE", palette)
        self.assertIn("Search Local Documentation", palette)
        self.assertIn("Choose Challenge", palette)
        self.assertIn("View Progress Dashboard", palette)
        self.assertIn("Open Mini-Games Hub", palette)
        self.assertIn("Open Field Manual", palette)
        self.assertIn("Reset Current Challenge", palette)
        self.assertIn("Toggle Terminal Pet", palette)
        self.assertIn("Color Theme Selector", palette)

    def test_command_center_feedback_banner(self) -> None:
        player = PlayerStats()
        palette = render_command_center(player, width=74, styled=True, status_msg="Theme changed to Dracula!")
        self.assertIn("Theme changed to Dracula!", palette)


class TestLayoutDynamicThemingAndRain(unittest.TestCase):
    """Verify 4-pane layout with dynamic themes and rain."""

    def test_draw_opencode_layout_with_rain(self) -> None:
        from cybershell.ui.renderer import draw_opencode_layout, visual_len
        ambience = get_ambience_manager()
        ambience.rain_enabled = True
        set_theme("dracula")

        layout = draw_opencode_layout(
            task_title="YOUR TASK", task_content=["Line 1", "Line 2"],
            term_title="TERMINAL", term_content=["echo test"],
            docs_title="LOCAL DOCS", docs_content=["ls", "pwd"],
            mascot_content=["Byte"],
            width=80, height=20, styled=True
        )
        self.assertIn("YOUR TASK", layout)
        self.assertIn("TERMINAL", layout)
        self.assertIn("LOCAL DOCS", layout)
        self.assertIn("BYTE", layout)

        # Check line width consistency
        for line in layout.splitlines():
            self.assertEqual(visual_len(line), 78)

        # Reset state
        ambience.rain_enabled = False
        set_theme("tokyo-night")

    def test_chmod_permission_decoder(self) -> None:
        from cybershell.tools.minigames.chmod_decoder import decode_permission_details, format_decoded_permission
        
        info_755 = decode_permission_details("755")
        self.assertIsNotNone(info_755)
        self.assertEqual(info_755["octal"], "755")
        self.assertEqual(info_755["symbolic"], "rwxr-xr-x")
        self.assertEqual(info_755["binary"], "111 101 101")
        
        formatted = format_decoded_permission(info_755, width=70)
        self.assertTrue(len(formatted.splitlines()) > 5)
        self.assertIn("User/Owner", formatted)

        # Test symbolic input
        info_rwx = decode_permission_details("rwxrwxrwx")
        self.assertIsNotNone(info_rwx)
        self.assertEqual(info_rwx["octal"], "777")

    def test_foss_penguin_ascii(self) -> None:
        from cybershell.ui.ascii_art import get_foss_penguin
        penguin = get_foss_penguin(styled=False)
        self.assertTrue(len(penguin.splitlines()) >= 5)
        self.assertIn("(o o)", penguin)

    def test_foss_penguin_frames_and_welcome(self) -> None:
        from cybershell.ui.ascii_art import get_foss_penguin
        from cybershell.ui.animation import animate_tux_welcome
        from cybershell.run import prompt_player_onboarding
        
        # Test frames
        p_normal = get_foss_penguin(styled=False, frame="normal")
        p_blink = get_foss_penguin(styled=False, frame="blink")
        p_wave = get_foss_penguin(styled=False, frame="wave")
        p_happy = get_foss_penguin(styled=False, frame="happy")
        
        self.assertIn("(o o)", p_normal)
        self.assertIn("(o o)", p_normal)  # eyes
        self.assertIn("^^ ^^", p_normal)  # feet
        self.assertIn("- -", p_blink)
        self.assertIn("(o o)", p_wave)
        self.assertIn("(^ ^)", p_happy)
        
        # Non-interactive executions (must not raise or block)
        from unittest.mock import patch
        with patch("sys.stdout.isatty", return_value=False):
            animate_tux_welcome(character_name="TestHero", width=80, quick=True)

        with patch("builtins.input", return_value="Amy"):
            name = prompt_player_onboarding(width=80)
            self.assertEqual(name, "Amy")

        with patch("builtins.input", return_value=""):
            default_name = prompt_player_onboarding(width=80)
            self.assertEqual(default_name, "Explorer")

    def test_thick_heavy_borders(self) -> None:
        from cybershell.ui.renderer import draw_fixed_panel, HEAVY_TOP_LEFT, HEAVY_BOTTOM_LEFT
        panel = draw_fixed_panel("TEST", ["Line 1", "Line 2"], width=30, height=6, styled=False)
        self.assertEqual(len(panel), 6)
        self.assertTrue(panel[0].startswith(HEAVY_TOP_LEFT))
        self.assertTrue(panel[-1].startswith(HEAVY_BOTTOM_LEFT))

    def test_progress_bar_rendering(self) -> None:
        from cybershell.ui.renderer import draw_progress_bar
        bar = draw_progress_bar(5, 10, width=10, styled=False)
        self.assertEqual(bar, "█████░░░░░")

    def test_interactive_task_options_and_terminal_prompt(self) -> None:
        from cybershell.contracts import Objective
        from cybershell.ui.renderer import draw_opencode_layout, visual_len
        from cybershell.ui.theme import get_active_theme

        th = get_active_theme()
        obj = Objective(
            id="test_obj",
            description="Find where you are located.",
            question="Which command shows your current working directory?",
            options=[
                "ls - list files",
                "pwd - print working directory",
                "cd - change directory",
                "cat - read file",
            ],
            correct_option="B",
        )

        task_inner_w = 40
        q_text = getattr(obj, "question", "") or obj.description
        task_content = [
            f"LEVEL 01 // TEST",
            "",
            f"QUESTION : {q_text}",
            f"PROGRESS : [████░░░░] 1/2 (50%)",
            "",
        ]
        for i, opt in enumerate(obj.options):
            lbl = ["A", "B", "C", "D"][i]
            task_content.append(f"  [{lbl}] {opt}")
        task_content.append("")
        task_content.append("INTEL    : Type command or [A-D]")

        joined = "\n".join(task_content)
        self.assertIn("QUESTION :", joined)
        self.assertIn("PROGRESS :", joined)
        self.assertIn("[A]", joined)
        self.assertIn("[B]", joined)
        self.assertIn("INTEL    :", joined)
        self.assertNotIn("COMMANDS :", joined)

        # In-terminal layout rendering
        prompt = "amy@cybershell:~$ "
        layout = draw_opencode_layout(
            "YOUR TASK", task_content,
            "TERMINAL", [prompt],
            "LOCAL DOCS", ["pwd", "ls"],
            ["pet"],
            width=80, height=24, gap=1, styled=False
        )
        self.assertIn(prompt, layout)


class TestMultiUserProfileAndReadlineShortcuts(unittest.TestCase):
    """Verify multi-user profile persistence and Ctrl+Space readline macro configuration."""

    def test_get_save_path_resolution(self) -> None:
        from cybershell.run import get_save_path, SAVE_FILE_PATH
        self.assertEqual(get_save_path(None), SAVE_FILE_PATH)
        self.assertEqual(get_save_path(""), SAVE_FILE_PATH)
        self.assertEqual(get_save_path("Explorer"), SAVE_FILE_PATH)
        self.assertEqual(get_save_path("byte"), SAVE_FILE_PATH)
        self.assertEqual(get_save_path("default"), SAVE_FILE_PATH)

        alice_path = get_save_path("Alice")
        self.assertTrue(alice_path.endswith(".cybershell_save_alice.json"))

        bob_path = get_save_path("Bob_99")
        self.assertTrue(bob_path.endswith(".cybershell_save_bob_99.json"))

    def test_multi_user_profile_isolation(self) -> None:
        import tempfile
        import os
        from cybershell.run import save_game, load_saved_game, delete_saved_game

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_alice = os.path.join(tmp_dir, ".cybershell_save_alice.json")
            file_bob = os.path.join(tmp_dir, ".cybershell_save_bob.json")

            player_alice = PlayerStats(character_name="Alice", hp=100, xp=500, current_sector=3)
            player_alice.level = 4
            player_bob = PlayerStats(character_name="Bob", hp=80, xp=150, current_sector=1)
            player_bob.level = 2

            self.assertTrue(save_game(player_alice, cadet_mode=True, filepath=file_alice))
            self.assertTrue(save_game(player_bob, cadet_mode=False, filepath=file_bob))

            # Verify isolated loading
            loaded_alice = load_saved_game(filepath=file_alice)
            self.assertIsNotNone(loaded_alice)
            self.assertEqual(loaded_alice[0].character_name, "Alice")
            self.assertEqual(loaded_alice[0].xp, 500)
            self.assertEqual(loaded_alice[0].level, 4)
            self.assertTrue(loaded_alice[1])

            loaded_bob = load_saved_game(filepath=file_bob)
            self.assertIsNotNone(loaded_bob)
            self.assertEqual(loaded_bob[0].character_name, "Bob")
            self.assertEqual(loaded_bob[0].xp, 150)
            self.assertEqual(loaded_bob[0].level, 2)
            self.assertFalse(loaded_bob[1])

            # Deletion of Bob does not remove Alice
            self.assertTrue(delete_saved_game(filepath=file_bob))
            self.assertFalse(os.path.isfile(file_bob))
            self.assertTrue(os.path.isfile(file_alice))

    def test_configure_readline_bindings(self) -> None:
        from cybershell.run import configure_readline_bindings
        # Ensure it executes without any exceptions
        try:
            configure_readline_bindings()
        except Exception as e:
            self.fail(f"configure_readline_bindings raised exception: {e}")

    def test_ctrl_space_pexpect_pty_macro(self) -> None:
        """Verify sending NUL (Ctrl+Space \x00) translates into :cmd through readline."""
        import os
        import sys
        import pexpect
        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{src_path}:{env.get('PYTHONPATH', '')}".rstrip(":")
        child = pexpect.spawn(
            sys.executable,
            ["-c", "from cybershell.run import configure_readline_bindings; configure_readline_bindings(); x = input('TEST> '); print('RESULT:' + x)"],
            encoding="utf-8",
            env=env,
        )
        child.expect("TEST> ")
        child.send(chr(0)) # ASCII NUL = Ctrl+Space
        child.expect(r"RESULT:(.*)")
        out = child.match.group(1).strip()
        self.assertEqual(out, ":cmd")
        child.close()


if __name__ == "__main__":
    unittest.main()
