"""Day 1 Architecture Contracts for CyberShell RPG v2.0.

Author: Amy (Project Lead & Master Integrator)
Status: FROZEN ON DAY 1 (Zero-Conflict Contract Rule)

This module defines the immutable shared Data Transfer Objects (DTOs) and
Protocols implemented and consumed across all sub-team modules:
- Engine (Rudra & Aniket)
- UI (Poornendhu & Gautham)
- Game & Quests (Neha & Aswin)
- Tools & Minigames (Akash)
- Master Integration & Launcher (Amy)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable

# =============================================================================
# Constants & Defaults
# =============================================================================

DEFAULT_MAX_HP: int = 100
DEFAULT_BACKLASH_DAMAGE: int = 15
DEFAULT_HINT_PENALTY: int = 5

RANKS: List[Tuple[int, str]] = [
    (1, "Script Kiddie"),
    (2, "Junior Operative"),
    (3, "Cyber Mercenary"),
    (4, "Netrunner"),
    (5, "Daemon Infiltrator"),
    (6, "Root Architect"),
]


def calculate_rank(level: int) -> str:
    """Determine the operative rank title based on player level."""
    current_rank = RANKS[0][1]
    for lvl, title in RANKS:
        if level >= lvl:
            current_rank = title
        else:
            break
    return current_rank


# =============================================================================
# Core Shared DTOs
# =============================================================================

@dataclass
class Item:
    """Inventory item representing hardware chips, exploits, keys, or consumables."""

    id: str
    name: str
    description: str
    category: str = "hardware"  # hardware, exploit, cipher, key, consumable
    rarity: str = "common"      # common, rare, epic, legendary
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize item to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Item:
        """Construct Item instance from a dictionary."""
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "Unknown Item")),
            description=str(data.get("description", "")),
            category=str(data.get("category", "hardware")),
            rarity=str(data.get("rarity", "common")),
            properties=dict(data.get("properties", {})),
        )


@dataclass
class Objective:
    """Single quest objective evaluated against VFS or player state."""

    id: str
    description: str
    hint: str = ""
    command: str = ""
    syntax: str = ""
    explanation: str = ""
    predicate_type: str = "file_exists"  # file_exists, file_not_exists, file_contains, permission_equals, cwd_equals, file_read, pipeline_used
    predicate_target: str = ""
    predicate_expected: Any = True
    completed: bool = False
    xp_reward: int = 50
    hints: List[str] = field(default_factory=list)
    scenario: str = ""
    question: str = ""
    options: List[str] = field(default_factory=list)
    correct_option: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize objective to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Objective:
        """Construct Objective from a dictionary."""
        return cls(
            id=str(data.get("id", "")),
            description=str(data.get("description", "")),
            hint=str(data.get("hint", "")),
            command=str(data.get("command", "")),
            syntax=str(data.get("syntax", "")),
            explanation=str(data.get("explanation", "")),
            predicate_type=str(data.get("predicate_type", "file_exists")),
            predicate_target=str(data.get("predicate_target", "")),
            predicate_expected=data.get("predicate_expected", True),
            completed=bool(data.get("completed", False)),
            xp_reward=int(data.get("xp_reward", 50)),
            hints=list(data.get("hints", [])),
            scenario=str(data.get("scenario", "")),
            question=str(data.get("question", "")),
            options=list(data.get("options", [])),
            correct_option=str(data.get("correct_option", "")),
        )


@dataclass
class Quest:
    """Narrative mission representing a sector briefing, dialogue, and objectives."""

    id: str
    sector_id: int
    sector_name: str
    npc_name: str
    lore: str
    dialogue: List[str] = field(default_factory=list)
    objectives: List[Objective] = field(default_factory=list)
    reward_item: Optional[Item] = None
    reward_xp: int = 100
    completed: bool = False
    environment_tree: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_completed(self) -> bool:
        """Return True if all objectives in the quest are marked completed."""
        if not self.objectives:
            return self.completed
        return all(obj.completed for obj in self.objectives)

    @property
    def current_objective(self) -> Optional[Objective]:
        """Return the first uncompleted objective, or None if all are done."""
        for obj in self.objectives:
            if not obj.completed:
                return obj
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize quest to a dictionary."""
        return {
            "id": self.id,
            "sector_id": self.sector_id,
            "sector_name": self.sector_name,
            "npc_name": self.npc_name,
            "lore": self.lore,
            "dialogue": list(self.dialogue),
            "objectives": [obj.to_dict() for obj in self.objectives],
            "reward_item": self.reward_item.to_dict() if self.reward_item else None,
            "reward_xp": self.reward_xp,
            "completed": self.completed,
            "environment_tree": dict(self.environment_tree),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Quest:
        """Construct Quest instance from a dictionary."""
        raw_reward = data.get("reward_item")
        reward_item = Item.from_dict(raw_reward) if raw_reward else None
        objectives = [
            Objective.from_dict(obj_data)
            for obj_data in data.get("objectives", [])
        ]
        return cls(
            id=str(data.get("id", "")),
            sector_id=int(data.get("sector_id", 0)),
            sector_name=str(data.get("sector_name", "Unknown Sector")),
            npc_name=str(data.get("npc_name", "Handler")),
            lore=str(data.get("lore", "")),
            dialogue=list(data.get("dialogue", [])),
            objectives=objectives,
            reward_item=reward_item,
            reward_xp=int(data.get("reward_xp", 100)),
            completed=bool(data.get("completed", False)),
            environment_tree=dict(data.get("environment_tree", {})),
        )


@dataclass
class PlayerStats:
    """Player state, health, XP progression, inventory, and gamification stats."""

    character_name: str = "Byte"
    hp: int = DEFAULT_MAX_HP
    max_hp: int = DEFAULT_MAX_HP
    xp: int = 0
    level: int = 1
    rank: str = "Script Kiddie"
    inventory: List[Item] = field(default_factory=list)
    current_sector: int = 0
    completed_sectors: List[int] = field(default_factory=list)
    score: int = 0
    streak: int = 0
    max_streak: int = 0
    badges: List[str] = field(default_factory=list)
    hints_used: int = 0
    secrets_found: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure rank matches initial level."""
        self.rank = calculate_rank(self.level)

    def take_damage(self, amount: int) -> int:
        """Inflict damage upon player, clamped at 0 HP. Returns actual damage taken."""
        if amount <= 0:
            return 0
        actual = min(self.hp, amount)
        self.hp = max(0, self.hp - amount)
        return actual

    def heal(self, amount: int) -> int:
        """Restore HP up to max_hp. Returns amount healed."""
        if amount <= 0:
            return 0
        missing = self.max_hp - self.hp
        restored = min(missing, amount)
        self.hp += restored
        return restored

    def gain_xp(self, amount: int) -> bool:
        """Add XP and compute level up. Returns True if level increased."""
        if amount <= 0:
            return False
        self.xp += amount
        self.score += amount
        leveled_up = False

        # Threshold formula: Level N requires N * 100 cumulative or incremental XP
        while self.xp >= self.level * 100:
            self.level += 1
            self.max_hp += 10
            self.hp = self.max_hp
            self.rank = calculate_rank(self.level)
            leveled_up = True

        return leveled_up

    def add_badge(self, badge: str) -> bool:
        """Award an achievement badge if not already unlocked."""
        if badge not in self.badges:
            self.badges.append(badge)
            return True
        return False

    def increase_streak(self) -> int:
        """Increment current solve streak and update max streak."""
        self.streak += 1
        if self.streak > self.max_streak:
            self.max_streak = self.streak
        return self.streak

    def reset_streak(self) -> None:
        """Reset current streak counter."""
        self.streak = 0

    def add_secret(self, secret_id: str) -> bool:
        """Record an exploration secret discovery."""
        if secret_id not in self.secrets_found:
            self.secrets_found.append(secret_id)
            return True
        return False

    def add_item(self, item: Item) -> bool:
        """Add an item to inventory if not already present. Returns True if added."""
        if any(existing.id == item.id for existing in self.inventory):
            return False
        self.inventory.append(item)
        return True

    def has_item(self, item_id: str) -> bool:
        """Check if an item ID exists in inventory."""
        return any(item.id == item_id for item in self.inventory)

    def mark_sector_completed(self, sector_id: int) -> None:
        """Add sector_id to completed_sectors safely whether backed by list or set."""
        if isinstance(self.completed_sectors, set):
            self.completed_sectors.add(sector_id)
        elif sector_id not in self.completed_sectors:
            self.completed_sectors.append(sector_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize player state for local JSON persistence."""
        return {
            "character_name": self.character_name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "xp": self.xp,
            "level": self.level,
            "rank": self.rank,
            "inventory": [item.to_dict() for item in self.inventory],
            "current_sector": self.current_sector,
            "completed_sectors": list(self.completed_sectors),
            "score": self.score,
            "streak": self.streak,
            "max_streak": self.max_streak,
            "badges": list(self.badges),
            "hints_used": self.hints_used,
            "secrets_found": list(self.secrets_found),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PlayerStats:
        """Deserialize player state from saved JSON data."""
        inventory = [
            Item.from_dict(item_data)
            for item_data in data.get("inventory", [])
        ]
        return cls(
            character_name=str(data.get("character_name", "Byte")),
            hp=int(data.get("hp", DEFAULT_MAX_HP)),
            max_hp=int(data.get("max_hp", DEFAULT_MAX_HP)),
            xp=int(data.get("xp", 0)),
            level=int(data.get("level", 1)),
            rank=str(data.get("rank", "Script Kiddie")),
            inventory=inventory,
            current_sector=int(data.get("current_sector", 0)),
            completed_sectors=list(data.get("completed_sectors", [])),
            score=int(data.get("score", 0)),
            streak=int(data.get("streak", 0)),
            max_streak=int(data.get("max_streak", 0)),
            badges=list(data.get("badges", [])),
            hints_used=int(data.get("hints_used", 0)),
            secrets_found=list(data.get("secrets_found", [])),
        )


@dataclass
class CommandResult:
    """Result returned by the shell interpreter after executing a command."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    backlash_damage: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Return True if command executed with zero exit code."""
        return self.exit_code == 0

    @property
    def has_backlash(self) -> bool:
        """Return True if command caused electrical feedback damage."""
        return self.backlash_damage > 0


@dataclass
class CodexEntry:
    """Spellbook encyclopedia entry for shell commands and combos."""

    command: str
    syntax: str
    description: str
    flags: Dict[str, str] = field(default_factory=dict)
    combos: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize codex entry."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CodexEntry:
        """Construct CodexEntry from dictionary."""
        return cls(
            command=str(data.get("command", "")),
            syntax=str(data.get("syntax", "")),
            description=str(data.get("description", "")),
            flags=dict(data.get("flags", {})),
            combos=list(data.get("combos", [])),
        )


@dataclass
class SectorNode:
    """Mainframe network map topology node."""

    sector_id: int
    name: str
    status: str = "LOCKED"  # ACTIVE, LIBERATED, LOCKED
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize sector node."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SectorNode:
        """Construct SectorNode from dictionary."""
        return cls(
            sector_id=int(data.get("sector_id", 0)),
            name=str(data.get("name", "")),
            status=str(data.get("status", "LOCKED")),
            description=str(data.get("description", "")),
        )


# =============================================================================
# Interfaces and Protocols
# =============================================================================

@runtime_checkable
class EngineProtocol(Protocol):
    """Execution engine interface provided by Aniket/Rudra and mocked by Amy."""

    def execute(self, command_line: str) -> CommandResult:
        """Execute a raw shell command or pipeline and return execution results."""
        ...

    def get_cwd(self) -> str:
        """Return current working directory path string."""
        ...

    def reset_sector(self, sector_dict: Optional[Dict[str, Any]] = None) -> None:
        """Reset filesystem layout to the initial structure for a sector."""
        ...


@runtime_checkable
class EvaluatorProtocol(Protocol):
    """Quest evaluation interface implemented by Neha and consumed by RPGApp."""

    def evaluate_objective(self, objective: Objective, vfs: Any, state: PlayerStats) -> bool:
        """Check if an individual objective predicate is satisfied."""
        ...

    def check_quest_progress(
        self, quest: Quest, vfs: Any, state: PlayerStats
    ) -> Tuple[bool, List[str]]:
        """Evaluate quest objectives and return (is_fully_completed, newly_completed_ids)."""
        ...


@runtime_checkable
class VFSProtocol(Protocol):
    """Filesystem query interface implemented by Rudra's VirtualFileSystem."""

    def get_cwd_path(self) -> str:
        """Return current working directory path."""
        ...

    def exists(self, path: str) -> bool:
        """Check whether a path exists."""
        ...

    def read_file(self, path: str) -> str:
        """Read content of a file at given path."""
        ...

    def get_node(self, path: str) -> Optional[Any]:
        """Retrieve node at given path."""
        ...


@runtime_checkable
class UIProtocol(Protocol):
    """UI controller interface implemented by Poornendhu and Gautham."""

    def render(self) -> str:
        """Render active screen to terminal string."""
        ...

    def set_screen(self, screen_id: int) -> None:
        """Switch active screen view."""
        ...

    def update_stats(self, hp: int, max_hp: int, xp: int) -> None:
        """Update HUD stats values."""
        ...

    def log_ticker(self, message: str) -> None:
        """Push a message to the bottom combat ticker."""
        ...
