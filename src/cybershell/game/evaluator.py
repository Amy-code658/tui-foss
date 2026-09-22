"""Quest Evaluator Logic for Byte's Linux Adventure.

Evaluates friendly quest objectives against VFS and player state.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from cybershell.contracts import Objective, PlayerStats, Quest


class QuestEvaluator:
    """Evaluates adventure objectives against VFS and player state."""

    def evaluate_objective(
        self,
        objective: Objective,
        vfs: Any,
        state: PlayerStats,
        last_command: Optional[str] = None,
    ) -> bool:
        """Check if an individual objective predicate is satisfied.
        
        Args:
            objective: The objective to evaluate.
            vfs: The virtual file system conforming to VFSProtocol.
            state: The player's current stats.
            last_command: Optional shell command string executed in this turn.
            
        Returns:
            True if the objective is met, False otherwise.
        """
        if last_command is None and hasattr(vfs, "last_command"):
            last_command = getattr(vfs, "last_command", None)

        if last_command is not None and objective.command:
            cmd_stripped = last_command.strip()
            if not cmd_stripped:
                return False
            tokens = cmd_stripped.split()
            first_token = tokens[0] if tokens else ""
            allowed = [c.strip() for c in objective.command.replace("|", ",").split(",") if c.strip()]
            if not any(a == first_token or a in tokens for a in allowed):
                return False

        ptype = objective.predicate_type
        target = objective.predicate_target
        expected = objective.predicate_expected

        try:
            home_dir = getattr(vfs, "home_dir", "/home/operative")

            def _resolve_target(t: str) -> List[str]:
                if not t:
                    return []
                candidates = [t]
                if t in ("~", "$HOME"):
                    candidates.append(home_dir)
                elif not t.startswith("/"):
                    candidates.append(f"{home_dir}/{t}")
                elif t.startswith("/home/"):
                    parts = t.split("/", 3)
                    # ['', 'home', '<user>', '<rest>']
                    if len(parts) >= 4:
                        candidates.append(f"{home_dir}/{parts[3]}")
                    elif len(parts) == 3:
                        candidates.append(home_dir)
                return candidates

            if ptype == "file_exists":
                exists = any(vfs.exists(c) for c in _resolve_target(target))
                return exists == bool(expected)

            elif ptype == "file_not_exists":
                exists = any(vfs.exists(c) for c in _resolve_target(target))
                return (not exists) == bool(expected)

            elif ptype == "file_contains":
                read_target = None
                for c in _resolve_target(target):
                    if vfs.exists(c):
                        read_target = c
                        break
                if read_target is None:
                    return False
                content = vfs.read_file(read_target)
                return str(expected) in content

            elif ptype == "permission_equals":
                node = None
                for c in _resolve_target(target):
                    node = vfs.get_node(c)
                    if node is not None:
                        break
                if node is None:
                    return False
                mode = str(getattr(node, "mode_octal", ""))
                if str(expected) in ("755", "+x"):
                    return mode == "755" or bool(node.permissions & 0o111)
                return mode == str(expected)

            elif ptype == "cwd_equals":
                cwd = vfs.get_cwd_path()
                target_str = str(target)
                if cwd == target_str or any(cwd == c for c in _resolve_target(target_str)):
                    return True
                if target_str.startswith("/home/"):
                    sub_parts = target_str.split("/")
                    if len(sub_parts) > 3:
                        sub = "/".join(sub_parts[3:])
                        if cwd.endswith(sub):
                            return True
                    elif cwd.startswith("/home/"):
                        return True
                return False

            elif ptype == "file_read":
                read_target = None
                for c in _resolve_target(target):
                    if vfs.exists(c):
                        read_target = c
                        break
                if read_target is None:
                    return False
                if last_command:
                    target_name = target.split("/")[-1]
                    read_cmds = {"cat", "head", "tail", "grep", "less", "more"}
                    tokens = last_command.split()
                    if any(c in tokens for c in read_cmds) and (target in last_command or target_name in last_command):
                        return True
                return False

            elif ptype == "pipeline_used":
                if last_command and ("|" in last_command or "<" in last_command or ">" in last_command):
                    low_cmd = last_command.lower()
                    target_name = target.split("/")[-1] if target else ""
                    if target and (target.lower() not in low_cmd and target_name.lower() not in low_cmd):
                        return False
                    if expected is not True and str(expected).lower() not in low_cmd:
                        return False
                    return True
                return False

            elif ptype == "pattern_matched":
                if last_command:
                    low_cmd = last_command.lower()
                    low_exp = str(expected).lower()
                    target_name = target.split("/")[-1] if target else ""
                    if (low_exp in low_cmd) or (target_name and target_name.lower() in low_cmd):
                        return True
                if vfs.exists(target):
                    try:
                        return str(expected) in vfs.read_file(target)
                    except Exception:
                        return False
                return False

            else:
                return False

        except Exception:
            return False

    def check_quest_progress(
        self,
        quest: Quest,
        vfs: Any,
        state: PlayerStats,
        last_command: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """Evaluate adventure objectives sequentially and grant friendly rewards.
        
        Args:
            quest: The active level quest.
            vfs: The virtual file system instance.
            state: The player's stats to update.
            last_command: Optional last command executed by player.
            
        Returns:
            A tuple of (is_fully_completed, newly_completed_ids).
        """
        if last_command is None and hasattr(vfs, "last_command"):
            last_command = getattr(vfs, "last_command", None)

        # Exploration secrets
        if last_command:
            secrets = {
                ".easter_egg": "Easter Egg Discovered (+50 XP)",
                ".secret_recipe": "Secret Recipe Discovered (+50 XP)",
                ".hidden_clue": "Hidden Attic Clue Discovered (+50 XP)",
                "star.txt": "Golden Star Spotted (+50 XP)",
            }
            for sec_key, sec_title in secrets.items():
                if sec_key in last_command and hasattr(state, "add_secret"):
                    if state.add_secret(sec_key):
                        state.gain_xp(50)
                        if hasattr(state, "add_badge"):
                            state.add_badge("Secret Hunter 🎁")

        newly_completed_ids = []

        # Evaluate the active objective
        current = quest.current_objective
        if current is not None:
            if self.evaluate_objective(current, vfs, state, last_command=last_command):
                current.completed = True
                state.gain_xp(current.xp_reward)
                if hasattr(state, "increase_streak"):
                    state.increase_streak()
                newly_completed_ids.append(current.id)

        # Check if entire level is completed
        if quest.is_completed and not quest.completed:
            quest.completed = True
            state.gain_xp(quest.reward_xp)
            if quest.reward_item:
                state.add_item(quest.reward_item)
            
            level_badges = {
                0: "First Steps 🌱",
                1: "Pathfinder 🧭",
                2: "Curious Reader 📖",
                3: "Dotfile Detective 🔍",
                4: "Treasure Hunter 💎",
                5: "Pattern Spotter 🔎",
                6: "Organizer 🧰",
                7: "Clean & Tidy 🧹",
                8: "Permission Pal 🛡️",
                9: "Counter & Sorter 🧮",
                10: "Pipeline Connecter ⚡",
                11: "Stream Director 🖋️",
                12: "Master Searcher 🔭",
                13: "Attic Conqueror 🏆",
                14: "Master Explorer 👑",
            }
            if hasattr(state, "add_badge"):
                badge = level_badges.get(quest.sector_id, f"Level {quest.sector_id + 1} Star ⭐")
                state.add_badge(badge)

            if hasattr(state, "mark_sector_completed"):
                state.mark_sector_completed(quest.sector_id)
            elif quest.sector_id not in state.completed_sectors:
                if isinstance(state.completed_sectors, set):
                    state.completed_sectors.add(quest.sector_id)
                else:
                    state.completed_sectors.append(quest.sector_id)

        return (quest.completed, newly_completed_ids)
