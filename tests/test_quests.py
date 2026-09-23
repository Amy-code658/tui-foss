"""Tests for CyberShell quest data and sector configuration.

Author: Neha (Narrative & Quests)
Compatible with standard library unittest and pytest.
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

from cybershell.contracts import Item, Objective, Quest
from cybershell.game.quests import get_sector_quests


class TestQuests(unittest.TestCase):
    """Verify sector quest configurations and objectives."""

    def setUp(self) -> None:
        self.quests = get_sector_quests()

    def test_fifteen_levels_in_order(self) -> None:
        """Verify all 15 adventure levels (0-14) are present."""
        self.assertEqual(len(self.quests), 15)
        self.assertEqual(sorted(self.quests.keys()), list(range(15)))

    def test_unique_quest_and_objective_ids(self) -> None:
        """Ensure all quest and objective IDs are unique across sectors."""
        quest_ids = [q.id for q in self.quests.values()]
        self.assertEqual(len(quest_ids), len(set(quest_ids)))

        obj_ids = [obj.id for q in self.quests.values() for obj in q.objectives]
        self.assertEqual(len(obj_ids), len(set(obj_ids)))

    def test_quest_contract_attributes(self) -> None:
        """Verify each Quest has valid attributes conforming to contracts."""
        for sector_id, quest in self.quests.items():
            self.assertEqual(quest.sector_id, sector_id)
            self.assertTrue(quest.sector_name)
            self.assertTrue(quest.npc_name)
            self.assertTrue(quest.lore)
            self.assertIsInstance(quest.dialogue, list)
            self.assertGreater(len(quest.dialogue), 0)
            self.assertGreater(len(quest.objectives), 0)
            self.assertIsInstance(quest.reward_item, Item)
            self.assertGreater(quest.reward_xp, 0)

    def test_objective_contract_attributes(self) -> None:
        """Verify each Objective conforms to evaluator predicate contracts."""
        valid_predicates = {
            "file_exists",
            "file_not_exists",
            "file_contains",
            "permission_equals",
            "cwd_equals",
            "file_read",
            "pipeline_used",
            "pattern_matched",
        }
        for quest in self.quests.values():
            for obj in quest.objectives:
                self.assertTrue(obj.id)
                self.assertTrue(obj.description)
                self.assertTrue(obj.hint)
                self.assertIn(obj.predicate_type, valid_predicates)
                self.assertTrue(obj.predicate_target)
                self.assertGreater(obj.xp_reward, 0)

    def test_four_options_per_objective(self) -> None:
        """Verify each objective across all 15 levels has 4 options and valid correct_option."""
        for q_idx, quest in self.quests.items():
            for obj in quest.objectives:
                self.assertTrue(obj.question, f"Objective {obj.id} in quest {q_idx} is missing a question")
                self.assertEqual(
                    len(obj.options), 4,
                    f"Objective {obj.id} in quest {q_idx} must have exactly 4 options, found {len(obj.options)}"
                )
                self.assertIn(
                    obj.correct_option.upper(), {"A", "B", "C", "D"},
                    f"Objective {obj.id} has invalid correct_option {obj.correct_option}"
                )


if __name__ == "__main__":
    unittest.main()
