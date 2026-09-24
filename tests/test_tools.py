"""Unit Test Suite for Akash's Hacker Codex, Chmod Calc, Map & Minigame tools.

Author: Akash (Hacker Codex & Chmod Minigame)
Coverage: codex.py, chmod_calc.py, map.py, chmod_minigame.py.
Compatible with both the standard library unittest runner and pytest.
"""

from __future__ import annotations

import os
import random
import sys
import unittest

# Ensure 'src' is on sys.path for direct test execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from cybershell.contracts import CodexEntry, PlayerStats  # noqa: E402
from cybershell.tools.chmod_calc import (  # noqa: E402
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
from cybershell.tools.chmod_minigame import (  # noqa: E402
    DIFFICULTIES,
    EASY_CODES,
    MEDIUM_CODES,
    XP_REWARDS,
    ChmodMinigame,
)
from cybershell.tools.codex import (  # noqa: E402
    CODEX,
    COMMANDS,
    REQUIRED_KEYS,
    Codex,
    display_command,
    get_combos,
    get_command,
    get_flags,
    list_commands,
    search_commands,
)
from cybershell.tools.map import (  # noqa: E402
    ACTIVE,
    LIBERATED,
    LOCKED,
    STATUS_GLYPHS,
    VALID_STATUSES,
    MainframeMap,
    MapError,
    default_mainframe_map,
)

# =============================================================================
# 1. Hacker Codex
# =============================================================================

REQUIRED_COMMAND_NAMES = (
    "ls", "cd", "cat", "grep", "chmod", "rm", "touch", "mkdir",
    "pwd", "find", "cp", "mv", "head", "tail", "wc", "echo",
    "man", "lookup", "help", "hint", "sort", "less",
    "tree", "whoami", "rmdir", "clear", "ps", "kill", "git", "vim", "nano",
)


class TestCodex(unittest.TestCase):
    """Tests for the codex command encyclopedia."""

    def setUp(self) -> None:
        """Fresh codex per test."""
        self.codex = Codex()

    def test_all_required_commands_exist(self) -> None:
        """Every required command must be registered in the default database."""
        for name in REQUIRED_COMMAND_NAMES:
            self.assertIn(name, COMMANDS, f"missing command: {name}")
        self.assertIn(name := "ls", self.codex.command_names())
        self.assertTrue(set(REQUIRED_COMMAND_NAMES).issubset(self.codex.command_names()))

    def test_command_lookup(self) -> None:
        """get_command returns the correctly structured record for a command."""
        entry = self.codex.get_command("chmod")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["name"], "chmod")
        self.assertIsInstance(entry["flags"], dict)
        self.assertTrue(len(entry["flags"]) > 0)
        self.assertIsInstance(entry["examples"], list)
        self.assertIsInstance(entry["combos"], list)

    def test_unknown_command_handling(self) -> None:
        """Unknown commands are handled cleanly (None, no crash)."""
        self.assertIsNone(self.codex.get_command("sudo"))
        self.assertIsNone(self.codex.get_command(""))
        self.assertFalse(self.codex.has_command("nottacommand"))

    def test_command_lookup_is_case_insensitive_and_strips(self) -> None:
        """Lookups tolerate whitespace and case."""
        self.assertIsNotNone(self.codex.get_command("  Ls "))
        self.assertIsNotNone(self.codex.get_command("CAT"))

    def test_flags_retrieval(self) -> None:
        """Flags can be retrieved for known commands."""
        flags = self.codex.get_flags("ls")
        self.assertIn("-l", flags)
        self.assertIn("-a", flags)
        self.assertEqual(self.codex.get_flags("unknown"), {})

    def test_combos_retrieval(self) -> None:
        """Tactical combos can be retrieved."""
        combos = self.codex.get_combos("grep")
        self.assertTrue(len(combos) > 0)
        self.assertIsInstance(combos, list)
        self.assertEqual(self.codex.get_combos("unknown"), [])

    def test_search_commands(self) -> None:
        """Search matches on names, descriptions, and flag content."""
        by_name = self.codex.search_commands("grep")
        self.assertTrue(any(c["name"] == "grep" for c in by_name))
        by_keyword = self.codex.search_commands("password")
        matches = {c["name"] for c in by_keyword}
        self.assertTrue(matches, "expected at least one command to match 'password'")
        self.assertEqual(self.codex.search_commands(""), [])
        self.assertEqual(self.codex.search_commands("zzz_nothing_here"), [])

    def test_command_data_structure(self) -> None:
        """Every entry carries the expected structured keys."""
        for entry in self.codex.list_commands():
            for key in REQUIRED_KEYS:
                self.assertIn(key, entry, f"{entry.get('name')} missing {key}")
            self.assertEqual(entry["name"], self.codex.get_command(entry["name"])["name"])

    def test_list_commands(self) -> None:
        """Listing returns all commands in sorted order."""
        names = [c["name"] for c in self.codex.list_commands()]
        self.assertEqual(names, sorted(names))
        self.assertEqual(len(names), len(REQUIRED_COMMAND_NAMES))

    def test_display_command(self) -> None:
        """Display output is human readable and contains the entry details."""
        rendered = display_command("chmod")
        self.assertIn("chmod", rendered)
        self.assertIn("Syntax:", rendered)
        self.assertIn("Flags:", rendered)
        rendered_unknown = display_command("nope")
        self.assertIn("UNKNOWN", rendered_unknown)

    def test_module_level_functions(self) -> None:
        """Module-level convenience helpers mirror the class API."""
        self.assertIsNotNone(get_command("ls"))
        self.assertIn("ls", [c["name"] for c in list_commands()])
        self.assertIn("-l", get_flags("ls"))
        self.assertIsInstance(get_combos("ls"), list)
        self.assertIsInstance(search_commands("cat"), list)

    def test_codex_entry_dto_integration(self) -> None:
        """Commands can be exposed via the shared CodexEntry contract DTO."""
        dto = self.codex.to_codex_entry("grep")
        self.assertIsInstance(dto, CodexEntry)
        self.assertEqual(dto.command, "grep")
        self.assertEqual(dto.to_dict()["command"], "grep")
        self.assertIsNone(self.codex.to_codex_entry("unknown"))

    def test_invalid_entry_schema_rejected(self) -> None:
        """Registered entries must follow the documented schema."""
        bad_entries = {"tmp": {"name": "tmp", "syntax": "tmp", "description": "x"}}
        with self.assertRaises(ValueError):
            Codex(bad_entries)

    def test_default_codex_is_shared(self) -> None:
        """The module-level CODEX instance is functional."""
        self.assertTrue(CODEX.has_command("ls"))


# =============================================================================
# 2. Chmod Calculator
# =============================================================================

ROUND_TRIPS = {
    "755": "rwxr-xr-x",
    "644": "rw-r--r--",
    "700": "rwx------",
    "777": "rwxrwxrwx",
}


class TestChmodCalc(unittest.TestCase):
    """Tests for the chmod permission calculator."""

    def test_octal_to_symbolic(self) -> None:
        """Octal modes convert to their expected symbolic strings."""
        for octal, symbolic in ROUND_TRIPS.items():
            self.assertEqual(octal_to_symbolic(octal), symbolic, f"octal {octal}")

    def test_symbolic_to_octal(self) -> None:
        """Symbolic modes convert back to their expected octal strings."""
        for octal, symbolic in ROUND_TRIPS.items():
            self.assertEqual(symbolic_to_octal(symbolic), octal, f"symbolic {symbolic}")

    def test_round_trip_bidirectional(self) -> None:
        """Octal <-> symbolic conversions round trip losslessly."""
        for octal in ("000", "400", "640", "664", "754", "764", "740", "700", "777", "600"):
            self.assertEqual(symbolic_to_octal(octal_to_symbolic(octal)), octal)
        for symbolic in ("rwxr-xr--", "rw-rw-r--", "r--------", "---------"):
            self.assertEqual(octal_to_symbolic(symbolic_to_octal(symbolic)), symbolic)

    def test_int_octal_input_supported(self) -> None:
        """Octal digits given as integers (e.g. 755) are accepted."""
        self.assertEqual(octal_to_symbolic(755), "rwxr-xr-x")
        self.assertEqual(octal_to_symbolic(644), "rw-r--r--")

    def test_type_prefixed_symbolic_accepted(self) -> None:
        """ls -l style prefixes ('-', 'd') are tolerated."""
        self.assertEqual(symbolic_to_octal("-rwxr-xr-x"), "755")
        self.assertEqual(symbolic_to_octal("drwxr-xr-x"), "755")

    def test_invalid_octal_values(self) -> None:
        """Non-octal, non-numeric, and wrong-length values are rejected."""
        for bad in ("888", "999", "12a", "abc", "12.5", "", "   "):
            with self.assertRaises(ChmodError, msg=f"octal {bad!r}"):
                validate_octal(bad)
        for bad in ("7555", "77", "7"):
            with self.assertRaises(ChmodError, msg=f"octal {bad!r}"):
                validate_octal(bad)

    def test_invalid_symbolic_permissions(self) -> None:
        """Malformed symbolic permissions, wrong lengths, and odd chars rejected."""
        for bad in ("rwxr-xr", "rwxr-xr-xr", "rwxrwxrw", ""):
            with self.assertRaises(ChmodError, msg=f"symbolic {bad!r}"):
                validate_symbolic(bad)
        for bad in ("rwzr-xr-x", "rwxr-xr-x!", "rwxr:x-x"):
            with self.assertRaises(ChmodError, msg=f"symbolic {bad!r}"):
                validate_symbolic(bad)
        # Duplicate / out-of-order letters within a triad are invalid.
        with self.assertRaises(ChmodError):
            validate_symbolic("rrxr-xr-x")

    def test_conversion_rejects_invalid_input(self) -> None:
        """Conversion helpers surface ChmodError rather than corrupting output."""
        with self.assertRaises(ChmodError):
            octal_to_symbolic("8ff")
        with self.assertRaises(ChmodError):
            symbolic_to_octal("rwxr-xr-")

    def test_security_info(self) -> None:
        """Security info exposes oct/symbolic/triplets/capabilities."""
        info = security_info("755")
        self.assertEqual(info["octal"], "755")
        self.assertEqual(info["symbolic"], "rwxr-xr-x")
        self.assertEqual(info["triplets"]["owner"], "rwx")
        self.assertEqual(info["triplets"]["group"], "r-x")
        self.assertEqual(info["triplets"]["others"], "r-x")
        self.assertIn("Owner", info["capabilities"])

    def test_security_report(self) -> None:
        """Security report is human readable and shows each triad."""
        report = security_report("755")
        for expected in ("755", "Owner:  rwx", "Group:  r-x", "Others:  r-x", "Security:"):
            self.assertIn(expected, report)
        self.assertIn("Owner can read, write and execute.", report)
        self.assertIn("Others can read and execute.", report)

    def test_get_triplets(self) -> None:
        """Triplet decomposition orders owner/group/others correctly."""
        owner, group, others = get_triplets("754")
        self.assertEqual(owner, "rwx")
        self.assertEqual(group, "r-x")
        self.assertEqual(others, "r--")

    def test_describe_triad(self) -> None:
        """Triad capabilities read naturally in English."""
        self.assertEqual(describe_triad("rwx"), "can read, write and execute.")
        self.assertEqual(describe_triad("r--"), "can read.")
        self.assertEqual(describe_triad("-w-"), "can write.")
        self.assertEqual(describe_triad("---"), "has no access permissions.")
        self.assertEqual(describe_triad("r-x", "Group"), "Group can read and execute.")

    def test_parse_permission_accepts_both_forms(self) -> None:
        """Unified parser handles octal or symbolic strings / ints."""
        self.assertEqual(parse_permission("755"), 0o755)
        self.assertEqual(parse_permission("rwxr-xr-x"), 0o755)
        self.assertEqual(parse_permission(755), 0o755)
        with self.assertRaises(ChmodError):
            parse_permission("bonk")

    def test_zero_permissions(self) -> None:
        """000 maps to no permissions at all."""
        self.assertEqual(octal_to_symbolic("000"), "---------")
        self.assertEqual(security_report("000").split("Security:")[1].count("no access"), 3)


# =============================================================================
# 3. Tactical Mainframe Map
# =============================================================================


class TestMainframeMap(unittest.TestCase):
    """Tests for the ASCII mainframe topology map."""

    def setUp(self) -> None:
        self.map = MainframeMap(name="TEST GRID")

    def test_node_creation(self) -> None:
        """Nodes can be created and retrieved."""
        node = self.map.add_node(1, "CORE NODE")
        self.assertEqual(node.sector_id, 1)
        self.assertEqual(node.status, LOCKED)
        self.assertIs(self.map.get_node(1), node)
        self.assertIn(1, self.map.node_ids())

    def test_duplicate_node_rejected(self) -> None:
        """Adding the same sector id twice raises MapError."""
        self.map.add_node(1, "CORE NODE")
        with self.assertRaises(MapError):
            self.map.add_node(1, "CORE NODE AGAIN")

    def test_add_or_update_node(self) -> None:
        """Upsert creates then updates an existing node."""
        self.map.add_or_update_node(1, "CORE", status="ACTIVE")
        self.map.add_or_update_node(1, "CORE REBRAND", status="LOCKED")
        self.assertEqual(self.map.get_node(1).name, "CORE REBRAND")

    def test_status_updates(self) -> None:
        """set_status updates and returns updated node state."""
        node = self.map.add_node(2, "SECTOR B", status="LOCKED")
        updated = self.map.set_status(2, "LIBERATED")
        self.assertIs(updated, node)
        self.assertEqual(self.map.get_status(2), "LIBERATED")

    def test_valid_statuses(self) -> None:
        """Each valid status is accepted on node creation and update."""
        for status in VALID_STATUSES:
            node_id = len(VALID_STATUSES) + VALID_STATUSES.index(status)
            node = self.map.add_node(node_id, f"N{status}", status=status)
            self.assertIsInstance(node.status, str)
            self.assertIn(status, STATUS_GLYPHS)

    def test_invalid_status_rejected(self) -> None:
        """Unsupported statuses are rejected with MapError."""
        with self.assertRaises(MapError):
            self.map.add_node(9, "GHOST", status="HACKED")
        self.map.add_node(1, "CORE")
        with self.assertRaises(MapError):
            self.map.set_status(1, "aperant")

    def test_add_node_default_status_is_locked(self) -> None:
        """Nodes default to the locked status when none is given."""
        self.assertEqual(self.map.add_node(3, "VAULT").status, LOCKED)

    def test_get_status_unknown_node(self) -> None:
        """Status lookups for unknown nodes return None."""
        self.assertIsNone(self.map.get_status(404))

    def test_update_missing_node_rejected(self) -> None:
        """Updating a node that does not exist raises MapError."""
        with self.assertRaises(MapError):
            self.map.update_node(5, name="nope")

    def test_connections(self) -> None:
        """Links can be created, queried, and removed."""
        self.map.add_node(0, "CORE")
        self.map.add_node(1, "A")
        self.map.add_node(2, "B")
        self.map.connect(0, 1)
        self.map.connect(0, 2)
        self.assertEqual(self.map.get_connections(0), [1, 2])
        self.assertEqual(self.map.get_edges(), [(0, 1), (0, 2)])
        self.map.disconnect(0, 1)
        self.assertEqual(self.map.get_connections(0), [2])

    def test_connect_unknown_node_rejected(self) -> None:
        """Linking unknown nodes raises MapError."""
        self.map.add_node(0, "CORE")
        with self.assertRaises(MapError):
            self.map.connect(0, 9)
        with self.assertRaises(MapError):
            self.map.connect(9, 0)

    def test_self_loop_rejected(self) -> None:
        """A node cannot link to itself."""
        self.map.add_node(0, "CORE")
        with self.assertRaises(MapError):
            self.map.connect(0, 0)

    def test_map_rendering(self) -> None:
        """Rendered map contains node names, statuses, glyphs, and box art."""
        default = default_mainframe_map()
        rendered = default.render()
        for name in ("CORE NODE", "SECTOR A", "SECTOR B", "ARCHIVE", "SECURITY"):
            self.assertIn(name, rendered)
        for glyph in (STATUS_GLYPHS[ACTIVE], STATUS_GLYPHS[LIBERATED], STATUS_GLYPHS[LOCKED]):
            self.assertIn(glyph, rendered)
        for border in ("┌", "┐", "└", "┘", "│", "▼", "┬"):
            self.assertIn(border, rendered)

    def test_map_render_deterministic(self) -> None:
        """Rendering the same topology twice gives identical output."""
        self.assertEqual(default_mainframe_map().render(), default_mainframe_map().render())

    def test_map_render_empty(self) -> None:
        """An empty map renders a message instead of crashing."""
        self.assertIn("no nodes", MainframeMap().render())

    def test_display_topology(self) -> None:
        """Topology text lists every node with its status and links."""
        rendered = default_mainframe_map().display_topology()
        self.assertIn("CORE NODE", rendered)
        self.assertIn("SECTOR B", rendered)
        self.assertIn("SECTOR A → ARCHIVE", rendered)

    def test_remove_node(self) -> None:
        """Removed nodes drop out of topology and from links."""
        m = default_mainframe_map()
        removed = m.remove_node(3)
        self.assertEqual(removed.sector_id, 3)
        self.assertIsNone(m.get_node(3))
        self.assertNotIn(3, m.get_connections(1))
        with self.assertRaises(MapError):
            m.remove_node(3)

    def test_apply_progression(self) -> None:
        """Player progression syncs LIBERATED + ACTIVE statuses onto the map."""
        m = default_mainframe_map()
        player = PlayerStats(current_sector=2, completed_sectors=[1, 3])
        updated = m.apply_progression(player)
        self.assertGreater(updated, 0)
        self.assertEqual(m.get_status(1), LIBERATED)
        self.assertEqual(m.get_status(3), LIBERATED)
        self.assertEqual(m.get_status(2), ACTIVE)

    def test_serialization_roundtrip(self) -> None:
        """Maps serialize and deserialize without losing structure."""
        m = default_mainframe_map()
        restored = MainframeMap.from_dict(m.to_dict())
        self.assertEqual(restored.name, m.name)
        self.assertEqual(sorted(restored.node_ids()), sorted(m.node_ids()))
        self.assertEqual(restored.get_edges(), m.get_edges())
        self.assertEqual(restored.get_status(2), m.get_status(2))

    def test_bidirectional_connections(self) -> None:
        """connect_bidirectional adds links in both directions."""
        self.map.add_node(1, "A")
        self.map.add_node(2, "B")
        self.map.connect_bidirectional(1, 2)
        self.assertEqual(self.map.get_connections(1), [2])
        self.assertEqual(self.map.get_connections(2), [1])


# =============================================================================
# 4. Chmod Security Minigame
# =============================================================================


def make_player(start_xp: int = 0) -> PlayerStats:
    """Construct a no-op player for deterministic XP tests."""
    return PlayerStats(character_name="TestOp", xp=start_xp)


class TestChmodMinigame(unittest.TestCase):
    """Tests for the chmod door-lockpicking minigame."""

    def test_puzzle_generation(self) -> None:
        """generate_puzzle produces a well-formed, answerable puzzle."""
        game = ChmodMinigame(difficulty="easy", rng=random.Random(1))
        puzzle = game.generate_puzzle()
        self.assertEqual(len(puzzle.answer), 3)
        self.assertEqual(puzzle.difficulty, "easy")
        self.assertEqual(octal_to_symbolic(puzzle.answer), puzzle.permission)
        self.assertEqual(game.active_puzzle, puzzle)

    def test_puzzle_answer_matches_pattern(self) -> None:
        """The converted symbolic pattern matches the generated answer."""
        game = ChmodMinigame(difficulty="medium", rng=random.Random(4))
        for _ in range(20):
            puzzle = game.generate_puzzle()
            self.assertEqual(symbolic_to_octal(puzzle.permission), puzzle.answer)

    def test_valid_answer(self) -> None:
        """A correct octal code is accepted and rewards XP."""
        game = ChmodMinigame(difficulty="easy", rng=random.Random(3))
        game.set_player(make_player(start_xp=10))
        puzzle = game.generate_puzzle()
        result = game.validate_answer(puzzle.answer)
        self.assertTrue(result.correct)
        self.assertEqual(result.xp_awarded, XP_REWARDS["easy"])
        self.assertEqual(game.player.xp, 10 + XP_REWARDS["easy"])
        self.assertEqual(game.xp_earned, XP_REWARDS["easy"])
        self.assertEqual(game.doors_solved, 1)

    def test_invalid_answer_no_xp(self) -> None:
        """A wrong octal code is rejected without awarding XP."""
        game = ChmodMinigame(difficulty="easy", rng=random.Random(3))
        game.set_player(make_player())
        game.generate_puzzle()
        result = game.validate_answer("000")
        self.assertFalse(result.correct)
        self.assertEqual(result.xp_awarded, 0)
        self.assertEqual(game.player.xp, 0)
        self.assertEqual(game.doors_solved, 0)

    def test_malformed_input_no_crash(self) -> None:
        """Garbage input fails gracefully without exceptions or XP."""
        game = ChmodMinigame(difficulty="medium", rng=random.Random(2))
        game.set_player(make_player())
        game.generate_puzzle()
        for garbage in ("abc", "888", "9", "", "  ", "7545", None, 999):
            result = game.validate_answer(garbage)
            self.assertFalse(result.correct, msg=f"garbage {garbage!r}")
            self.assertEqual(result.xp_awarded, 0)
        self.assertEqual(game.player.xp, 0)
        self.assertEqual(game.doors_solved, 0)

    def test_validate_answer_without_active_puzzle(self) -> None:
        """Validating before generating a puzzle is safe."""
        game = ChmodMinigame()
        result = game.validate_answer("755")
        self.assertFalse(result.correct)
        self.assertEqual(result.xp_awarded, 0)

    def test_xp_awarded_exactly_once(self) -> None:
        """Re-solving the same door never awards XP a second time."""
        game = ChmodMinigame(difficulty="easy", rng=random.Random(5))
        game.set_player(make_player())
        puzzle = game.generate_puzzle()
        first = game.validate_answer(puzzle.answer)
        second = game.validate_answer(puzzle.answer)
        self.assertTrue(first.correct)
        self.assertTrue(second.correct)
        self.assertGreater(first.xp_awarded, 0)
        self.assertEqual(second.xp_awarded, 0)
        self.assertEqual(game.player.xp, first.xp_awarded)
        self.assertEqual(game.doors_solved, 1)

    def test_easy_pool(self) -> None:
        """Easy puzzles draw only from simple common permission codes."""
        game = ChmodMinigame(difficulty="easy", rng=random.Random(8))
        for _ in range(50):
            puzzle = game.generate_puzzle()
            self.assertIn(puzzle.answer, EASY_CODES)

    def test_medium_pool(self) -> None:
        """Medium puzzles draw only from the less obvious combination codes."""
        game = ChmodMinigame(difficulty="medium", rng=random.Random(8))
        for _ in range(50):
            puzzle = game.generate_puzzle()
            self.assertIn(puzzle.answer, MEDIUM_CODES)

    def test_hard_pool(self) -> None:
        """Hard puzzles are random valid 3-digit octal codes."""
        game = ChmodMinigame(difficulty="hard", rng=random.Random(9))
        seen = {game.generate_puzzle().answer for _ in range(100)}
        self.assertGreater(len(seen), 1, "expected variety in hard puzzles")
        for code in seen:
            self.assertTrue(code.isdecimal())
            self.assertEqual(len(code), 3)
            self.assertLessEqual(max(int(d) for d in code), 7)

    def test_difficulty_validation(self) -> None:
        """Invalid difficulty levels are rejected; valid ones accepted."""
        for level in DIFFICULTIES:
            self.assertEqual(ChmodMinigame(difficulty=level).difficulty, level)
        self.assertEqual(ChmodMinigame(difficulty="HARD").difficulty, "hard")
        self.assertEqual(ChmodMinigame(difficulty=" EASY ").difficulty, "easy")
        for level in ("impossible", " ", "9"):
            with self.assertRaises(ValueError):
                ChmodMinigame(difficulty=level)

    def test_difficulty_setter(self) -> None:
        """Difficulty can be changed mid-session and affects the reward."""
        game = ChmodMinigame(difficulty="easy")
        game.set_difficulty("hard")
        self.assertEqual(game.difficulty, "hard")
        self.assertEqual(game.reward_for(), XP_REWARDS["hard"])
        with self.assertRaises(ValueError):
            game.set_difficulty("nightmare")

    def test_difficulty_affects_reward(self) -> None:
        """Harder doors award more XP; medium matches the +50 spec example."""
        self.assertEqual(XP_REWARDS["medium"], 50)
        for level in ("easy", "medium", "hard"):
            game = ChmodMinigame(difficulty=level, rng=random.Random(1))
            game.set_player(make_player())
            game.generate_puzzle().answer
            result = game.validate_answer(game.active_puzzle.answer)
            self.assertEqual(result.xp_awarded, XP_REWARDS[level], msg=level)

    def test_rng_determinism(self) -> None:
        """Seeded RNG yields identical puzzle sequences."""
        game_a = ChmodMinigame(difficulty="hard", rng=random.Random(42))
        game_b = ChmodMinigame(difficulty="hard", rng=random.Random(42))
        seq_a = [game_a.generate_puzzle().answer for _ in range(10)]
        seq_b = [game_b.generate_puzzle().answer for _ in range(10)]
        self.assertEqual(seq_a, seq_b)

    def test_solve_without_player_is_safe(self) -> None:
        """Solving a door without a bound player never crashes or leaks XP."""
        game = ChmodMinigame(difficulty="easy", rng=random.Random(6))
        puzzle = game.generate_puzzle()
        result = game.validate_answer(puzzle.answer)
        self.assertTrue(result.correct)
        self.assertEqual(game.doors_solved, 1)
        self.assertEqual(result.xp_awarded, XP_REWARDS["easy"])
        self.assertIsNone(game.player)

    def test_door_numbers_increment(self) -> None:
        """Each generated puzzle gets a fresh, incrementing door number."""
        game = ChmodMinigame(difficulty="easy", rng=random.Random(7))
        numbers = [game.generate_puzzle().door_number for _ in range(5)]
        self.assertEqual(numbers, [1, 2, 3, 4, 5])

    def test_door_rendering(self) -> None:
        """The ASCII door displays the pattern and an entry prompt."""
        game = ChmodMinigame(difficulty="medium", rng=random.Random(11))
        puzzle = game.generate_puzzle()
        rendered = game.render_door()
        self.assertIn(f"SECURITY DOOR #{puzzle.door_number:02d}", rendered)
        self.assertIn(f"Permission pattern: {puzzle.permission}", rendered)
        self.assertIn("Enter security code", rendered)
        self.assertEqual(len(rendered.splitlines()), 7)

    def test_door_rendering_without_puzzle(self) -> None:
        """Rendering a door before generation gives a helper message."""
        game = ChmodMinigame()
        self.assertIn("Generate a puzzle", game.render_door())

    def test_reward_for(self) -> None:
        """reward_for reflects configured rewards without a player."""
        game = ChmodMinigame(difficulty="easy")
        self.assertEqual(game.reward_for("hard"), XP_REWARDS["hard"])
        self.assertEqual(game.reward_for(), XP_REWARDS["easy"])


# =============================================================================
# 5. Cross-module integration (calc powers the minigame)
# =============================================================================


class TestToolIntegration(unittest.TestCase):
    """The minigame reuses chmod_calc (no duplicated conversion logic)."""

    def test_minigame_uses_calc_conversions(self) -> None:
        """Every generated pattern matches chmod_calc's canonical output."""
        game = ChmodMinigame(difficulty="hard", rng=random.Random(20))
        for _ in range(30):
            puzzle = game.generate_puzzle()
            self.assertEqual(octal_to_symbolic(puzzle.answer), puzzle.permission)
            self.assertEqual(symbolic_to_octal(puzzle.permission), puzzle.answer)

    def test_rpg_app_renders_tool_screens(self) -> None:
        """The RPGApp controller wires the new tools into screens 2/4/5."""
        from unittest.mock import patch

        from cybershell.ui.rpg_app import RPGApp

        app = RPGApp()
        with patch("cybershell.ui.rpg_app.terminal_size", return_value=(80, 24)):
            app.set_screen(RPGApp.SCREEN_CODEX)
            codex_render = app.render()
            self.assertIn("CODEX", codex_render)
            self.assertIn("chmod", codex_render)

            app.set_screen(RPGApp.SCREEN_MAP)
            map_render = app.render()
            self.assertIn("MAP", map_render)
            self.assertIn("CORE NODE", map_render)

            app.set_screen(RPGApp.SCREEN_MINIGAME)
            mini_render = app.render()
            self.assertIn("MINIGAME", mini_render)
            self.assertIn("SECURITY DOOR", mini_render)

    def test_rpg_app_minigame_awards_xp(self) -> None:
        """Playing the minigame through the app advances the bound player."""
        from unittest.mock import patch

        from cybershell.ui.rpg_app import RPGApp

        app = RPGApp()
        player = make_player()
        app.minigame.set_difficulty("easy")
        app.minigame.set_player(player)
        with patch("cybershell.ui.rpg_app.terminal_size", return_value=(80, 24)):
            app.set_screen(RPGApp.SCREEN_MINIGAME)
            app.render()
            puzzle = app.minigame.active_puzzle
            result = app.minigame.validate_answer(puzzle.answer)
            self.assertTrue(result.correct)
            self.assertEqual(player.xp, XP_REWARDS["easy"])


if __name__ == "__main__":
    unittest.main()
