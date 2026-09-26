"""Full End-to-End Integration and Smoke Test Suite for CyberShell RPG v2.0.

Author: Amy (Project Lead & Master Integrator)
Role: Validates contracts, engine protocols, player progression, VFS integration,
      UI lifecycle, and end-to-end quest completion simulation.
Compatible with both standard library unittest and pytest.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

# Ensure 'src' and project root are on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cybershell.contracts import (  # noqa: E402
    DEFAULT_BACKLASH_DAMAGE,
    DEFAULT_MAX_HP,
    CodexEntry,
    CommandResult,
    EngineProtocol,
    Item,
    Objective,
    PlayerStats,
    Quest,
    SectorNode,
    calculate_rank,
)
from cybershell.engine.vfs import VirtualFileSystem  # noqa: E402
from cybershell.ui.rpg_app import RPGApp  # noqa: E402
from tests.conftest import MockEngine, MockGameState  # noqa: E402


class TestCyberShellIntegration(unittest.TestCase):
    """Amy's master integration test suite."""

    def setUp(self) -> None:
        """Initialize fresh test state before each test case."""
        self.player = MockGameState.create_player(name="Cipher", hp=100)
        self.engine = MockEngine()
        self.vfs = VirtualFileSystem(default_user="operative")

    # -------------------------------------------------------------------------
    # 1. Contracts & Serialization Validation
    # -------------------------------------------------------------------------

    def test_contracts_serialization_roundtrip(self) -> None:
        """Verify that all frozen DTOs serialize and deserialize without loss."""
        # 1. Item
        item = Item(
            id="item_exploit_01",
            name="Buffer Overflow Exploit",
            description="Bypasses Sector 1 gatekeeper daemon.",
            category="exploit",
            rarity="epic",
            properties={"damage": 50, "single_use": True},
        )
        item_dict = item.to_dict()
        reconstructed_item = Item.from_dict(item_dict)
        self.assertEqual(item, reconstructed_item)

        # 2. Objective
        objective = Objective(
            id="obj_test_1",
            description="Run ls -la in root",
            hint="Try typing ls -la /",
            predicate_type="cwd_equals",
            predicate_target="/",
            completed=False,
            xp_reward=75,
        )
        obj_dict = objective.to_dict()
        reconstructed_obj = Objective.from_dict(obj_dict)
        self.assertEqual(objective, reconstructed_obj)

        # 3. Quest
        quest = Quest(
            id="quest_sector_1",
            sector_id=1,
            sector_name="The File Vault",
            npc_name="Cipher",
            lore="Infiltrate the secure archival cluster.",
            dialogue=["Break the encryption on the primary ledger."],
            objectives=[objective],
            reward_item=item,
            reward_xp=150,
            completed=False,
        )
        quest_dict = quest.to_dict()
        reconstructed_quest = Quest.from_dict(quest_dict)
        self.assertEqual(quest.id, reconstructed_quest.id)
        self.assertEqual(quest.sector_name, reconstructed_quest.sector_name)
        self.assertEqual(len(quest.objectives), len(reconstructed_quest.objectives))
        self.assertEqual(quest.reward_item, reconstructed_quest.reward_item)

        # 4. PlayerStats
        self.player.add_item(item)
        player_dict = self.player.to_dict()
        # Verify JSON serializability
        serialized_json = json.dumps(player_dict)
        deserialized_data = json.loads(serialized_json)
        reconstructed_player = PlayerStats.from_dict(deserialized_data)
        self.assertEqual(self.player.character_name, reconstructed_player.character_name)
        self.assertEqual(self.player.hp, reconstructed_player.hp)
        self.assertEqual(self.player.level, reconstructed_player.level)
        self.assertEqual(len(self.player.inventory), len(reconstructed_player.inventory))

        # 5. CodexEntry & SectorNode
        codex = CodexEntry(
            command="chmod",
            syntax="chmod [mode] [file]",
            description="Alter file security permissions.",
            flags={"-R": "Recursive"},
            combos=["chmod 755 run.sh && ./run.sh"],
        )
        self.assertEqual(codex, CodexEntry.from_dict(codex.to_dict()))

        sector_node = SectorNode(
            sector_id=2,
            name="Data Interception Grid",
            status="ACTIVE",
            description="Intercept corporate telemetries.",
        )
        self.assertEqual(sector_node, SectorNode.from_dict(sector_node.to_dict()))

    # -------------------------------------------------------------------------
    # 2. Player Progression & Combat Mechanics
    # -------------------------------------------------------------------------

    def test_player_damage_healing_and_leveling(self) -> None:
        """Verify health clamping, healing, XP gain, level up, and rank titles."""
        p = PlayerStats(character_name="ZeroCool", hp=100, max_hp=100, xp=0, level=1)
        self.assertEqual(p.rank, "Script Kiddie")

        # Take damage
        taken = p.take_damage(30)
        self.assertEqual(taken, 30)
        self.assertEqual(p.hp, 70)

        # Take overkill damage - should clamp at 0
        overkill = p.take_damage(150)
        self.assertEqual(overkill, 70)
        self.assertEqual(p.hp, 0)

        # Healing
        restored = p.heal(50)
        self.assertEqual(restored, 50)
        self.assertEqual(p.hp, 50)

        # Over-heal - should cap at max_hp
        p.heal(200)
        self.assertEqual(p.hp, 100)

        # Gain XP and level up
        leveled = p.gain_xp(50)
        self.assertFalse(leveled)
        self.assertEqual(p.level, 1)

        # Level up threshold: 100 XP triggers level 2
        leveled = p.gain_xp(60)
        self.assertTrue(leveled)
        self.assertEqual(p.level, 2)
        self.assertEqual(p.rank, "Junior Operative")
        self.assertEqual(p.max_hp, 110)
        self.assertEqual(p.hp, 110)

        # Test rank scaling helper
        self.assertEqual(calculate_rank(1), "Script Kiddie")
        self.assertEqual(calculate_rank(3), "Cyber Mercenary")
        self.assertEqual(calculate_rank(4), "Netrunner")
        self.assertEqual(calculate_rank(6), "Root Architect")

    def test_inventory_duplicate_protection(self) -> None:
        """Verify that duplicate items cannot be accidentally stacked in inventory."""
        chip = Item(id="chip_01", name="ROM Chip", description="Read only memory")
        self.assertTrue(self.player.add_item(chip))
        self.assertTrue(self.player.has_item("chip_01"))

        # Second addition of same ID must return False
        self.assertFalse(self.player.add_item(chip))
        self.assertEqual(len(self.player.inventory), 1)

    # -------------------------------------------------------------------------
    # 3. Engine Protocol & Electrical Backlash
    # -------------------------------------------------------------------------

    def test_engine_protocol_and_backlash(self) -> None:
        """Verify EngineProtocol conformance and syntax backlash damage (-15 HP)."""
        self.assertTrue(isinstance(self.engine, EngineProtocol))

        # Successful command
        res_pwd = self.engine.execute("pwd")
        self.assertTrue(res_pwd.is_success)
        self.assertEqual(res_pwd.stdout.strip(), "/home/operative")
        self.assertEqual(res_pwd.backlash_damage, 0)

        # Simulated cd
        self.engine.execute("cd /tmp")
        self.assertEqual(self.engine.get_cwd(), "/tmp")

        # Invalid command syntax causing electrical backlash
        bad_res = self.engine.execute("corrupted_daemon_call --inject")
        self.assertFalse(bad_res.is_success)
        self.assertEqual(bad_res.exit_code, 127)
        self.assertEqual(bad_res.backlash_damage, DEFAULT_BACKLASH_DAMAGE)
        self.assertTrue(bad_res.has_backlash)

    # -------------------------------------------------------------------------
    # 4. Virtual Filesystem (VFS) Integration
    # -------------------------------------------------------------------------

    def test_vfs_interaction_and_path_resolution(self) -> None:
        """Verify real VFS methods integrate with game requirements."""
        self.assertEqual(self.vfs.get_cwd_path(), "/home/operative")

        # Create a mission target file
        node = self.vfs.touch("/home/operative/flag.txt")
        self.assertIsNotNone(node)
        self.assertTrue(self.vfs.exists("/home/operative/flag.txt"))

        # Write data to file
        self.vfs.write_file("/home/operative/flag.txt", "CYBER_KEY{ROOT_ACCESS_GRANTED}")
        content = self.vfs.read_file("/home/operative/flag.txt")
        self.assertEqual(content, "CYBER_KEY{ROOT_ACCESS_GRANTED}")

        # Test chmod permission changes
        self.vfs.chmod("/home/operative/flag.txt", 0o600)
        flag_node = self.vfs.get_node("/home/operative/flag.txt")
        self.assertIsNotNone(flag_node)
        self.assertEqual(flag_node.permissions, 0o600)

    # -------------------------------------------------------------------------
    # 5. UI App Lifecycle Integration
    # -------------------------------------------------------------------------

    def test_ui_app_lifecycle(self) -> None:
        """Verify RPGApp initializes, changes screens, and renders cleanly."""
        app = RPGApp(
            character_name=self.player.character_name,
            hp=self.player.hp,
            max_hp=self.player.max_hp,
            xp=self.player.xp,
        )

        # Verify title screen rendering
        title_render = app.render_title(80)
        self.assertIn("MAIN DIRECTORY", title_render)

        # Switch to Playground
        app.set_screen(RPGApp.SCREEN_LAB)
        self.assertEqual(app.get_screen_name(), "ADVENTURE PLAYGROUND")
        lab_render = app.render_lab(80)
        from cybershell.ui.theme import strip_ansi
        lab_clean = strip_ansi(lab_render)
        self.assertIn("GUIDE & OBJECTIVE", lab_clean)
        self.assertIn("TERMINAL", lab_clean)

        # Switch to Codex
        app.set_screen(RPGApp.SCREEN_CODEX)
        codex_render = app.render()
        codex_clean = strip_ansi(codex_render)
        self.assertIn("COMMAND GUIDE", codex_clean)

        # Switch to Map
        app.set_screen(RPGApp.SCREEN_MAP)
        map_render = app.render()
        map_clean = strip_ansi(map_render)
        self.assertIn("CORE NODE", map_clean)

    # -------------------------------------------------------------------------
    # 6. End-to-End Quest Progression Simulation
    # -------------------------------------------------------------------------

    def test_full_quest_lifecycle_simulation(self) -> None:
        """Simulate an operative completing Sector 0 objectives and acquiring loot."""
        quest = MockGameState.create_quest(sector_id=0)
        self.assertEqual(len(quest.objectives), 2)
        self.assertFalse(quest.is_completed)

        # Step 1: Player mistakenly executes invalid command -> takes backlash damage
        res1 = self.engine.execute("cat /missing_core")
        # In mock engine this is valid command, let's run an unknown command:
        res_bad = self.engine.execute("pwdd")
        self.assertEqual(res_bad.exit_code, 127)
        self.assertEqual(res_bad.backlash_damage, 15)
        self.player.take_damage(res_bad.backlash_damage)
        self.assertEqual(self.player.hp, 85)

        # Step 2: Operative checks location with 'pwd' -> completes Objective 1
        res_pwd = self.engine.execute("pwd")
        self.assertTrue(res_pwd.is_success)
        obj1 = quest.objectives[0]
        obj1.completed = True
        self.player.gain_xp(obj1.xp_reward)
        self.assertEqual(self.player.xp, 50)

        # Step 3: Operative checks directory with 'ls' -> completes Objective 2
        res_ls = self.engine.execute("ls -la")
        self.assertTrue(res_ls.is_success)
        obj2 = quest.objectives[1]
        obj2.completed = True
        leveled = self.player.gain_xp(obj2.xp_reward)

        # Player hits 100 XP -> Leveled up to Level 2!
        self.assertTrue(leveled)
        self.assertEqual(self.player.level, 2)
        self.assertEqual(self.player.rank, "Junior Operative")
        self.assertEqual(self.player.hp, 110)

        # Verify Quest completion & Loot drop
        self.assertTrue(quest.is_completed)
        quest.completed = True
        if quest.reward_item:
            added = self.player.add_item(quest.reward_item)
            self.assertTrue(added)
            self.assertTrue(self.player.has_item("item_quarantine_chip"))

        # Sector 0 complete, record progress
        self.player.completed_sectors.append(0)
        self.player.current_sector = 1

        # Final state verification
        self.assertIn(0, self.player.completed_sectors)
        self.assertEqual(self.player.current_sector, 1)
        self.assertEqual(len(self.player.inventory), 1)

    def test_full_six_sector_campaign_progression(self) -> None:
        """Verify seamless quest completion and level advancement across levels."""
        from cybershell.engine.interpreter import Interpreter
        from cybershell.game.evaluator import QuestEvaluator
        from cybershell.game.quests import get_sector_quests

        vfs = VirtualFileSystem(default_user="byte")
        interpreter = Interpreter(vfs=vfs)
        evaluator = QuestEvaluator()
        player = PlayerStats(character_name="Byte", hp=100, max_hp=100, xp=0, current_sector=0)
        all_quests = get_sector_quests()

        # Step through first 3 levels sequentially
        # Level 0: Look Around
        vfs.load_sector(0, all_quests[0])
        interpreter.execute("pwd")
        evaluator.check_quest_progress(all_quests[0], vfs, player)
        interpreter.execute("ls")
        evaluator.check_quest_progress(all_quests[0], vfs, player)
        self.assertTrue(all_quests[0].is_completed)
        player.completed_sectors.append(0)

        # Level 1: Moving In
        player.current_sector = 1
        vfs.load_sector(1, all_quests[1])
        interpreter.execute("cd garden")
        evaluator.check_quest_progress(all_quests[1], vfs, player)
        interpreter.execute("cd ..")
        evaluator.check_quest_progress(all_quests[1], vfs, player)
        self.assertTrue(all_quests[1].is_completed)
        player.completed_sectors.append(1)

        # Level 2: Reading Notes
        player.current_sector = 2
        vfs.load_sector(2, all_quests[2])
        interpreter.execute("cat welcome.txt")
        evaluator.check_quest_progress(all_quests[2], vfs, player)
        self.assertTrue(all_quests[2].is_completed)
        player.completed_sectors.append(2)

        self.assertGreater(player.xp, 100)
        self.assertIn(0, player.completed_sectors)
        self.assertIn(1, player.completed_sectors)
        self.assertIn(2, player.completed_sectors)

    # -------------------------------------------------------------------------
    # 8. Beginner Assist Toolkit & Persistence Validation
    # -------------------------------------------------------------------------

    def test_persistence_save_load_and_delete(self) -> None:
        """Verify checkpoint save, load, and deletion preserve operative progression."""
        import tempfile
        from cybershell.run import delete_saved_game, load_saved_game, save_game

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            player = PlayerStats(
                character_name="Nova",
                hp=85,
                max_hp=100,
                xp=275,
                current_sector=2,
            )
            player.level = 3
            player.rank = "Specialist"
            player.completed_sectors = {0, 1}
            player.add_item(
                Item(id="chip_1", name="Data Chip", description="Encrypted", category="token")
            )

            # 1. Save state
            saved = save_game(player, cadet_mode=True, filepath=tmp_path)
            self.assertTrue(saved)
            self.assertTrue(os.path.isfile(tmp_path))

            # 2. Load state
            loaded = load_saved_game(filepath=tmp_path)
            self.assertIsNotNone(loaded)
            loaded_player, cadet_mode = loaded
            self.assertEqual(loaded_player.character_name, "Nova")
            self.assertEqual(loaded_player.hp, 85)
            self.assertEqual(loaded_player.xp, 275)
            self.assertEqual(loaded_player.current_sector, 2)
            self.assertEqual(loaded_player.completed_sectors, {0, 1})
            self.assertTrue(loaded_player.has_item("chip_1"))
            self.assertTrue(cadet_mode)

            # 3. Delete save
            deleted = delete_saved_game(filepath=tmp_path)
            self.assertTrue(deleted)
            self.assertFalse(os.path.isfile(tmp_path))
        finally:
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)

    def test_typo_and_syntax_coach(self) -> None:
        """Verify typo coach detects common missing spaces and misspellings."""
        from cybershell.run import check_typo_or_syntax

        # Missing spaces after commands
        t1 = check_typo_or_syntax("cd..")
        self.assertIsNotNone(t1)
        self.assertEqual(t1[0], "cd ..")

        t2 = check_typo_or_syntax("cd/")
        self.assertIsNotNone(t2)
        self.assertEqual(t2[0], "cd /")

        t3 = check_typo_or_syntax("ls-la")
        self.assertIsNotNone(t3)
        self.assertEqual(t3[0], "ls -la")

        t4 = check_typo_or_syntax("catfirewall.log")
        self.assertIsNotNone(t4)
        self.assertEqual(t4[0], "cat firewall.log")

        # Misspelled commands
        t5 = check_typo_or_syntax("pdw")
        self.assertIsNotNone(t5)
        self.assertEqual(t5[0], "pwd")

        t6 = check_typo_or_syntax("sl")
        self.assertIsNotNone(t6)
        self.assertEqual(t6[0], "ls")

        # Valid commands should return None
        self.assertIsNone(check_typo_or_syntax("pwd"))
        self.assertIsNone(check_typo_or_syntax("ls -la"))
        self.assertIsNone(check_typo_or_syntax("cd .."))

    def test_directory_tree_rendering(self) -> None:
        """Verify visual directory tree generates Unicode branches and color-coded nodes."""
        from cybershell.run import render_vfs_tree

        tree_lines = render_vfs_tree(self.vfs.root, max_depth=2)
        combined = "\n".join(tree_lines)
        self.assertIn("/", tree_lines[0])
        self.assertTrue(any("bin/" in line for line in tree_lines))
        self.assertTrue(any("home/" in line for line in tree_lines))
        self.assertTrue("├──" in combined or "└──" in combined)

    def test_command_explainer(self) -> None:
        """Verify interactive command explainer breaks down syntax and flags."""
        from cybershell.run import explain_command

        obj = Objective(
            id="obj_test",
            description="Verify working coordinates.",
            command="pwd",
            syntax="pwd",
            explanation="Prints absolute directory path coordinates.",
        )

        # Active objective explainer
        expl_active = explain_command("explain", active_obj=obj)
        self.assertTrue(any("pwd" in line for line in expl_active))
        self.assertTrue(any("Prints absolute directory path" in line for line in expl_active))

        # Explicit command explainer
        expl_chmod = explain_command("explain chmod 755 script.sh")
        self.assertTrue(any("Change Mode" in line for line in expl_chmod))
        self.assertTrue(any("755" in line for line in expl_chmod))

    def test_progressive_hints(self) -> None:
        """Verify 3-tier progressive hints provide clues without HP penalties."""
        from cybershell.run import get_progressive_hint

        obj = Objective(
            id="obj_hint",
            description="Identify filesystem coordinates.",
            command="pwd",
            syntax="pwd",
            explanation="Prints current directory path.",
            hint="Type 'pwd' and press Enter.",
        )

        # Hints are friendly and free
        h1, c1 = get_progressive_hint(obj, tier=1, cadet_mode=True)
        self.assertIn("Hint 1/3", h1)
        self.assertEqual(c1, 0)

        h2, c2 = get_progressive_hint(obj, tier=2, cadet_mode=True)
        self.assertIn("Hint 2/3", h2)
        self.assertEqual(c2, 0)

        h3, c3 = get_progressive_hint(obj, tier=3, cadet_mode=True)
        self.assertIn("Hint 3/3", h3)
        self.assertEqual(c3, 0)

    def test_colorize_ls_output(self) -> None:
        """Verify colorize_ls_output formats directory and file entries with ANSI colors."""
        from cybershell.run import colorize_ls_output

        raw_ls = "drwxr-xr-x 2 root root 4096 Sep 20 21:00 bin\n-rw-r--r-- 1 operative operative 128 Sep 20 21:00 notes.txt\n"
        colored = colorize_ls_output(raw_ls)
        self.assertEqual(len(colored), 2)
        self.assertTrue(any("\033[" in line for line in colored))

        # Also test 6-column VFS output
        raw_vfs = "drwxr-xr-x  1 operative  operative  4096 .\n-rw-r--r--  1 operative  operative  78 firewall.log\n"
        colored_vfs = colorize_ls_output(raw_vfs)
        self.assertEqual(len(colored_vfs), 2)
        self.assertTrue(any("\033[" in line for line in colored_vfs))

    def test_sector_0_step_by_step_no_skip(self) -> None:
        """Verify that typing pwd only completes Task 1 and does NOT skip Task 2 (1/2 -> 2/2)."""
        from cybershell.engine.interpreter import Interpreter
        from cybershell.game.evaluator import QuestEvaluator
        from cybershell.game.quests import get_sector_quests

        vfs = VirtualFileSystem(default_user="byte")
        interpreter = Interpreter(vfs=vfs)
        evaluator = QuestEvaluator()
        player = PlayerStats(character_name="Byte", hp=100, max_hp=100, xp=0, current_sector=0)
        quests = get_sector_quests()
        quest = quests[0]

        # Initial: Task 1 of 2
        self.assertEqual(quest.current_objective.id, "obj_1_1")

        # Running a non-matching utility command (e.g. help or ls) must NOT complete Task 1 (pwd)
        interpreter.execute("help")
        comp, newly = evaluator.check_quest_progress(quest, vfs, player)
        self.assertFalse(comp)
        self.assertEqual(newly, [])
        self.assertEqual(quest.current_objective.id, "obj_1_1")

        # Step 1: Type 'pwd' -> completes ONLY obj_1_1, advancing to Task 2 (obj_1_2)
        interpreter.execute("pwd")
        comp, newly = evaluator.check_quest_progress(quest, vfs, player)
        self.assertFalse(comp)
        self.assertEqual(newly, ["obj_1_1"])
        self.assertEqual(quest.current_objective.id, "obj_1_2")
        self.assertEqual(quest.current_objective.command, "ls")

        # Running 'pwd' again while on Task 2 must NOT complete Task 2
        interpreter.execute("pwd")
        comp, newly = evaluator.check_quest_progress(quest, vfs, player)
        self.assertFalse(comp)
        self.assertEqual(newly, [])
        self.assertEqual(quest.current_objective.id, "obj_1_2")

        # Step 2: Type 'ls' -> completes obj_1_2 and finishes the level
        interpreter.execute("ls")
        comp, newly = evaluator.check_quest_progress(quest, vfs, player)
        self.assertTrue(comp)
        self.assertEqual(newly, ["obj_1_2"])
        self.assertIsNone(quest.current_objective)
        self.assertTrue(quest.is_completed)

    def test_split_panels_balanced_borders(self) -> None:
        """Verify draw_split_panels balances inner content so outer borders align at bottom."""
        from cybershell.ui.renderer import draw_split_panels

        left_lines = [f"Line {i}" for i in range(20)]
        right_lines = [f"Log {i}" for i in range(5)]

        rendered = draw_split_panels("LEFT", left_lines, "RIGHT", right_lines, width=80)
        lines = rendered.splitlines()

        # Both boxes must end on the same line with bottom border characters (╰ and ╯)
        last_line = lines[-1]
        self.assertIn("╰", last_line)
        self.assertIn("╯", last_line)
        self.assertEqual(last_line.count("╰"), 2)
        self.assertEqual(last_line.count("╯"), 2)

    def test_render_opening_screen_layout(self) -> None:
        """Verify opening screen renders clean description, complete sentences, and station options."""
        from cybershell.run import render_opening_screen

        player = PlayerStats(character_name="Cipher", hp=100, max_hp=100, xp=50, current_sector=1)
        screen_text = render_opening_screen(player, width=80, cadet_mode=True, has_save=False)

        # Verify key sections
        self.assertIn("MAIN DIRECTORY", screen_text)
        self.assertIn("Explorer:", screen_text)
        self.assertIn("CHOOSE A DESTINATION", screen_text)
        self.assertIn("Start Adventure", screen_text)
        self.assertIn("Adventure Map", screen_text)
        self.assertIn("Command Guide", screen_text)

        # Verify with saved game
        save_screen = render_opening_screen(player, width=80, cadet_mode=False, has_save=True)
        self.assertIn("Continue Adventure", save_screen)
        self.assertIn("Start New Game", save_screen)

    def test_wargame_discovery_tools(self) -> None:
        """Verify man, lookup, help, and find commands in interpreter."""
        from cybershell.engine.interpreter import Interpreter

        interpreter = Interpreter(vfs=self.vfs)

        # man ls
        res_man = interpreter.execute("man ls")
        self.assertEqual(res_man.exit_code, 0)
        self.assertIn("NAME", res_man.stdout)
        self.assertIn("ls", res_man.stdout)

        # lookup grep
        res_lookup = interpreter.execute("lookup grep")
        self.assertEqual(res_lookup.exit_code, 0)
        self.assertIn("grep", res_lookup.stdout)

        # help
        res_help = interpreter.execute("help")
        self.assertEqual(res_help.exit_code, 0)
        self.assertIn("Available commands:", res_help.stdout)

        # find
        self.vfs.mkdir_p("/home/operative/logs")
        self.vfs.touch("/home/operative/logs/secret.log")
        res_find = interpreter.execute("find . -name secret.log")
        self.assertEqual(res_find.exit_code, 0)
        self.assertIn("secret.log", res_find.stdout)

    def test_wargame_hints_and_streaks(self) -> None:
        """Verify progressive hints, streak tracking, and badges."""
        from cybershell.run import get_progressive_hint

        obj = Objective(
            id="obj_custom",
            description="Inspect firewall logs.",
            command="cat",
            hints=[
                "Check the logs folder.",
                "Inspect firewall.log with cat.",
                "Execute 'cat firewall.log'",
            ],
        )

        h1, c1 = get_progressive_hint(obj, tier=1, cadet_mode=True)
        self.assertIn("Check the logs folder", h1)
        self.assertEqual(c1, 0)

        h2, c2 = get_progressive_hint(obj, tier=2, cadet_mode=True)
        self.assertIn("Inspect firewall.log with cat", h2)

        h3, c3 = get_progressive_hint(obj, tier=3, cadet_mode=True)
        self.assertIn("Execute 'cat firewall.log'", h3)

        # Streak & badges
        p = PlayerStats(character_name="Ghost", hp=100, max_hp=100, xp=0)
        self.assertEqual(p.streak, 0)
        p.increase_streak()
        self.assertEqual(p.streak, 1)
        p.increase_streak()
        self.assertEqual(p.streak, 2)
        self.assertEqual(p.max_streak, 2)
        p.reset_streak()
        self.assertEqual(p.streak, 0)
        self.assertEqual(p.max_streak, 2)

        added = p.add_badge("Terminal Ninja 🥷")
        self.assertTrue(added)
        self.assertFalse(p.add_badge("Terminal Ninja 🥷"))
        self.assertIn("Terminal Ninja 🥷", p.badges)

    def test_wargame_easter_egg_secret_hunter(self) -> None:
        """Verify discovering hidden filesystem easter eggs awards bonus XP and Secret Hunter badge."""
        from cybershell.game.evaluator import QuestEvaluator
        from cybershell.game.quests import get_sector_quests

        evaluator = QuestEvaluator()
        p = PlayerStats(character_name="Shadow", hp=100, max_hp=100, xp=0)
        quests = get_sector_quests()
        quest = quests[0]

        evaluator.check_quest_progress(quest, self.vfs, p, last_command="cat .easter_egg")
        self.assertEqual(p.xp, 50)
        self.assertIn("Secret Hunter 🎁", p.badges)
        self.assertIn(".easter_egg", p.secrets_found)

    def test_compact_hud_and_celebration_banners(self) -> None:
        """Verify draw_compact_hud, access granted banner, and level unlocked banner format cleanly."""
        from cybershell.ui.ascii_art import (
            get_access_granted_banner,
            get_level_unlocked_banner,
        )
        from cybershell.ui.renderer import draw_compact_hud

        hud = draw_compact_hud(
            character_name="Neo",
            level_num=1,
            sector_name="File Vault",
            xp=250,
            streak=3,
            objective_desc="Recover the encrypted note.",
            hp=100,
            max_hp=100,
            width=80,
            styled=False,
            total_levels=15,
        )
        hud_lines = hud.splitlines()
        self.assertEqual(len(hud_lines), 5)
        self.assertIn("Neo's Adventure", hud_lines[1])
        self.assertIn("Level 01/15", hud_lines[1])
        self.assertIn("File Vault", hud_lines[2])
        self.assertIn("250 XP", hud_lines[2])
        self.assertIn("Recover the encrypted note.", hud_lines[3])

        granted = get_access_granted_banner("NOTE RECOVERED", 100, streak=3, badge="Vault Master", styled=False)
        self.assertIn("OBJECTIVE COMPLETE", granted)
        self.assertIn("NOTE RECOVERED", granted)
        self.assertIn("+100 XP", granted)
        self.assertIn("Vault Master", granted)

        unlocked = get_level_unlocked_banner(2, "Data Garden", styled=False)
        self.assertIn("LEVEL 02 UNLOCKED", unlocked)
        self.assertIn("Data Garden", unlocked)

    def test_interactive_game_loop_stream_simulation(self) -> None:
        """Simulate interactive game loop with commands, ensuring zero typo damage and progression."""
        import io
        from unittest.mock import patch
        from cybershell.run import interactive_game_loop

        player = PlayerStats(character_name="Zero", hp=100, max_hp=100, xp=0, current_sector=0)
        vfs = VirtualFileSystem(default_user="byte")

        mock_inputs = [
            "man ls",           # manual page
            "lookup grep",      # command lookup
            "status",           # telemetry & badges
            "hint",             # progressive clue
            "pwd",              # complete obj 1
            "sl",               # typo test: must NOT deduct HP!
            "ls",               # complete obj 2 & level 0
            "menu",             # exit cleanly
        ]

        captured_stdout = io.StringIO()
        with patch("builtins.input", side_effect=mock_inputs), patch("sys.stdout", captured_stdout):
            interactive_game_loop(
                character_name=player.character_name,
                start_sector=0,
                player=player,
                vfs=vfs,
                cadet_mode=False,
            )

        # Verify progression
        self.assertEqual(player.hp, player.max_hp)  # No HP damage from 'sl' typo!
        self.assertGreater(player.xp, 0)
        self.assertIn(0, player.completed_sectors)
        self.assertEqual(player.current_sector, 1)

    def test_resolve_option_choice_and_question_answering(self) -> None:
        """Verify option selection maps to command, and invalid option gives friendly tip."""
        from cybershell.run import resolve_option_choice
        from cybershell.game.quests import get_sector_quests

        quests = get_sector_quests()
        q0 = quests[0]
        obj1 = q0.objectives[0]

        # Valid choice B or 2 -> executes pwd
        cmd, msg = resolve_option_choice("B", obj1)
        self.assertEqual(cmd, "pwd")
        self.assertIn("Correct!", msg)

        cmd2, msg2 = resolve_option_choice("2", obj1)
        self.assertEqual(cmd2, "pwd")
        self.assertIn("Correct!", msg2)

        # Invalid choice A -> returns None command with friendly tip
        cmd_wrong, msg_wrong = resolve_option_choice("A", obj1)
        self.assertIsNone(cmd_wrong)
        self.assertIn("Try looking for", msg_wrong)

        # Regular command -> returns None so command executes normally
        cmd_plain, msg_plain = resolve_option_choice("pwd", obj1)
        self.assertIsNone(cmd_plain)
        self.assertIsNone(msg_plain)

    def test_minigame_answer_checking_and_learning_feedback(self) -> None:
        """Verify minigame checks answers, provides math breakdowns, and awards XP."""
        from unittest.mock import patch
        import io
        from cybershell.tools.chmod_minigame import ChmodMinigame
        from cybershell.run import view_minigame
        from cybershell.contracts import PlayerStats

        player = PlayerStats(character_name="Byte", hp=100, max_hp=100, xp=0)
        minigame = ChmodMinigame(difficulty="easy")

        # Mock sequence:
        # 1. "" (blank enter - should give tip, stay on puzzle)
        # 2. "h" (hint - should show step-by-step User triad math)
        # 3. "777" (wrong answer - should show step-by-step arithmetic)
        # 4. correct answer (should celebrate, award XP)
        # 5. "0" (exit after correct answer)
        # 6. "0" (exit main loop)
        door_puz = minigame.generate_puzzle()
        correct_code = door_puz.answer
        # reset active_puzzle to door_puz
        minigame.active_puzzle = door_puz

        out_stream = io.StringIO()
        with patch("sys.stdout", out_stream):
            with patch("builtins.input", side_effect=["", "h", "000", correct_code, "0"]):
                view_minigame(minigame, player, 80)

        output = out_stream.getvalue()
        # Verify formula card present
        self.assertIn("PERMISSIONS FORMULA", output)
        self.assertIn("r (read) = 4", output)
        # Verify hint present
        self.assertIn("STEP-BY-STEP HINT", output)
        # Verify step-by-step error math present
        self.assertIn("not correct", output)
        self.assertIn("Let's calculate step by step", output)
        # Verify XP awarded on correct answer
        self.assertIn("CORRECT!", output)
        self.assertGreater(player.xp, 0)

    def test_gameplay_output_preserved_after_option_selection(self) -> None:
        """Verify command output is preserved when options are entered and tasks complete."""
        from cybershell.engine.vfs import VirtualFileSystem
        from cybershell.engine.interpreter import Interpreter
        from cybershell.game.evaluator import QuestEvaluator
        from cybershell.game.quests import get_sector_quests
        from cybershell.contracts import PlayerStats

        vfs = VirtualFileSystem(default_user="byte")
        interpreter = Interpreter(vfs=vfs)
        evaluator = QuestEvaluator()
        quests = get_sector_quests()
        q0 = quests[0]
        vfs.load_sector(0, q0)
        player = PlayerStats(character_name="Byte", hp=100, max_hp=100, xp=0)

        # Simulate option B (pwd) execution
        terminal_logs = ["initial welcome log"]
        cmd_start_index = len(terminal_logs)

        # Run pwd
        terminal_logs.append("💡 [B] Correct! Running: pwd")
        terminal_logs.append("byte@adventure:~$ pwd")
        res = interpreter.execute("pwd")
        for line in res.stdout.splitlines():
            terminal_logs.append(line)

        # Verify output exists
        self.assertIn("/home/byte", terminal_logs)

        # Progress check
        is_comp, newly_comp = evaluator.check_quest_progress(q0, vfs, player, last_command="pwd")
        self.assertTrue(newly_comp)

        # Apply new clean slate preservation
        recent_logs = list(terminal_logs[cmd_start_index:])
        terminal_logs.clear()
        terminal_logs.extend(recent_logs)
        terminal_logs.append("✓ Task Cleared: Location (+50 XP)")

        # Verify output is STILL in terminal_logs after task clearance!
        self.assertIn("/home/byte", terminal_logs)
        self.assertIn("byte@adventure:~$ pwd", terminal_logs)
        self.assertIn("✓ Task Cleared", terminal_logs[-1])

    def test_all_fifteen_levels_progression_with_byte_user(self) -> None:
        """Verify all 15 levels advance and complete seamlessly with default user 'byte'."""
        from cybershell.engine.vfs import VirtualFileSystem
        from cybershell.engine.interpreter import Interpreter
        from cybershell.game.evaluator import QuestEvaluator
        from cybershell.game.quests import get_sector_quests
        from cybershell.contracts import PlayerStats

        quests = get_sector_quests()
        evaluator = QuestEvaluator()

        for sid in range(15):
            q = quests[sid]
            vfs = VirtualFileSystem(default_user="byte")
            vfs.load_sector(sid, q)
            interp = Interpreter(vfs=vfs)
            player = PlayerStats(character_name="Byte", hp=100, max_hp=100, xp=0)

            for idx, obj in enumerate(q.objectives):
                corr_letter = obj.correct_option.upper()
                opt_idx = ord(corr_letter) - ord("A")
                cmd = obj.options[opt_idx].split(" - ")[0].strip()

                interp.execute(cmd)
                evaluator.check_quest_progress(q, vfs, player, last_command=cmd)
                self.assertTrue(
                    obj.completed,
                    f"Level {sid + 1} objective {idx + 1} ({obj.id}) failed on command '{cmd}'",
                )

            self.assertTrue(
                q.is_completed,
                f"Level {sid + 1} ({q.sector_name}) should be completed after all objectives cleared",
            )


if __name__ == "__main__":
    unittest.main()
