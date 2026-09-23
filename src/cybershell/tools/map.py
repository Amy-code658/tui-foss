"""Tactical Mainframe Map - network topology renderer for CyberShell RPG v2.0.

Author: Akash (Hacker Codex & Chmod Minigame)
Role: A structured representation of mainframe sector nodes, their links, and
      live security status, rendered as an ASCII network map. Nodes are
      stored as the shared ``SectorNode`` DTO so the map can be driven by
      game progression (``PlayerStats``) without a second state system.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from cybershell.contracts import PlayerStats, SectorNode

# Status vocabulary & glyphs
ACTIVE: str = "ACTIVE"
LIBERATED: str = "LIBERATED"
LOCKED: str = "LOCKED"
VALID_STATUSES: Tuple[str, str, str] = (ACTIVE, LIBERATED, LOCKED)
STATUS_GLYPHS: Dict[str, str] = {
    ACTIVE: "🟢",
    LIBERATED: "🔵",
    LOCKED: "🔒",
}

_H_GAP = 8  # horizontal gap between sibling subtrees in the ASCII layout


class MapError(ValueError):
    """Raised for invalid mainframe map operations."""


def _validate_status(status: str) -> str:
    """Return a validated status; raise MapError for unsupported values."""
    value = str(status).strip().upper()
    if value not in VALID_STATUSES:
        raise MapError(
            f"Invalid node status {status!r}: expected one of {', '.join(VALID_STATUSES)}"
        )
    return value


class MainframeMap:
    """A mainframe topology of sector nodes and their connections."""

    def __init__(
        self,
        name: str = "MAINFRAME",
        nodes: Optional[Dict[int, SectorNode]] = None,
        connections: Optional[Dict[int, List[int]]] = None,
    ) -> None:
        self.name: str = name
        self._nodes: Dict[int, SectorNode] = dict(nodes or {})
        self._connections: Dict[int, List[int]] = {}
        for node_id, targets in (connections or {}).items():
            self._connections[int(node_id)] = list(targets)

    # -- node mutation ------------------------------------------------------

    def add_node(
        self,
        sector_id: int,
        name: str,
        status: str = LOCKED,
        description: str = "",
    ) -> SectorNode:
        """Create and register a new sector node. Raises on duplicate ids."""
        node_id = int(sector_id)
        if node_id in self._nodes:
            raise MapError(f"A node with sector_id {node_id} already exists")
        node = SectorNode(
            sector_id=node_id,
            name=str(name),
            status=_validate_status(status),
            description=str(description),
        )
        self._nodes[node_id] = node
        self._connections.setdefault(node_id, [])
        return node

    def add_or_update_node(
        self,
        sector_id: int,
        name: str,
        status: str = LOCKED,
        description: str = "",
    ) -> SectorNode:
        """Create a node or overwrite an existing one with the same id."""
        node_id = int(sector_id)
        if node_id in self._nodes:
            return self.update_node(node_id, name=name, status=status, description=description)
        return self.add_node(node_id, name, status=status, description=description)

    def update_node(
        self,
        sector_id: int,
        name: Optional[str] = None,
        status: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SectorNode:
        """Update fields of an existing node. Raises MapError when missing."""
        node_id = int(sector_id)
        node = self._nodes.get(node_id)
        if node is None:
            raise MapError(f"No node with sector_id {sector_id} exists")
        if name is not None:
            node.name = str(name)
        if status is not None:
            node.status = _validate_status(status)
        if description is not None:
            node.description = str(description)
        return node

    def remove_node(self, sector_id: int) -> SectorNode:
        """Remove a node and all links that reference it."""
        node_id = int(sector_id)
        node = self._nodes.pop(node_id, None)
        if node is None:
            raise MapError(f"No node with sector_id {sector_id} exists")
        self._connections.pop(node_id, None)
        for targets in self._connections.values():
            if node_id in targets:
                targets.remove(node_id)
        return node

    def set_status(self, sector_id: int, status: str) -> SectorNode:
        """Update a node's status, returning the updated node."""
        return self.update_node(sector_id, status=status)

    # -- lookup -------------------------------------------------------------

    def get_node(self, sector_id: int) -> Optional[SectorNode]:
        """Return a node, or None when it is not registered."""
        return self._nodes.get(int(sector_id))

    def get_status(self, sector_id: int) -> Optional[str]:
        """Return a node's current status, or None for unknown nodes."""
        node = self._nodes.get(int(sector_id))
        return node.status if node else None

    def node_ids(self) -> List[int]:
        """Return all registered node ids, sorted."""
        return sorted(self._nodes)

    def list_nodes(self) -> List[SectorNode]:
        """Return all nodes ordered by their sector_id."""
        return [self._nodes[node_id] for node_id in self.node_ids()]

    def get_description(self, sector_id: int) -> Optional[str]:
        """Return a node's description, or None for unknown nodes."""
        node = self._nodes.get(int(sector_id))
        return node.description if node else None

    # -- connections --------------------------------------------------------

    def _require_node(self, node_id: int) -> None:
        if node_id not in self._nodes:
            raise MapError(f"No node with sector_id {node_id} exists")

    def connect(self, src: int, dst: int) -> None:
        """Add a directed link from node ``src`` toward node ``dst``."""
        src_id, dst_id = int(src), int(dst)
        self._require_node(src_id)
        self._require_node(dst_id)
        if src_id == dst_id:
            raise MapError("A node cannot be linked to itself")
        links = self._connections.setdefault(src_id, [])
        if dst_id not in links:
            links.append(dst_id)
            self._connections[src_id] = sorted(links)

    def connect_bidirectional(self, first: int, second: int) -> None:
        """Link two nodes in both directions (secure two-way conduit)."""
        self.connect(first, second)
        self.connect(second, first)

    def disconnect(self, src: int, dst: int) -> None:
        """Remove a directed link between two nodes."""
        src_id, dst_id = int(src), int(dst)
        self._require_node(src_id)
        links = self._connections.get(src_id, [])
        if dst_id in links:
            links.remove(dst_id)

    def get_connections(self, sector_id: int) -> List[int]:
        """Return the sorted list of nodes directly linked from a node."""
        return sorted(self._connections.get(int(sector_id), []))

    def get_edges(self) -> List[Tuple[int, int]]:
        """Return all directed edges, sorted for determinism."""
        edges = [
            (src_id, dst_id)
            for src_id in sorted(self._connections)
            for dst_id in self._connections[src_id]
        ]
        return edges

    # -- game state integration ---------------------------------------------

    def apply_progression(self, player: PlayerStats) -> int:
        """Sync node statuses from a player's progression.

        Nodes whose sector_id was completed become LIBERATED; the node
        matching the player's current sector becomes ACTIVE. Returns the
        number of nodes whose status changed.
        """
        updated = 0
        for node in self.list_nodes():
            if node.sector_id in player.completed_sectors and node.status != LIBERATED:
                node.status = LIBERATED
                updated += 1
            elif node.sector_id == player.current_sector and node.status != ACTIVE:
                node.status = ACTIVE
                updated += 1
        return updated

    # -- rendering ----------------------------------------------------------

    def display_topology(self) -> str:
        """Render a textual topology summary of nodes and links."""
        lines = [f"[ MAINFRAME TOPOLOGY // {self.name} ]"]
        for node in self.list_nodes():
            glyph = STATUS_GLYPHS[node.status]
            lines.append(f"  [{node.sector_id}] {node.name:<20} {glyph} {node.status}")
        if self.get_edges():
            lines.append("  -- LINKS --")
            for src, dst in self.get_edges():
                lines.append(f"    {self._name_of(src)} → {self._name_of(dst)}")
        else:
            lines.append("  -- LINKS --  (none)")
        return "\n".join(lines)

    def _name_of(self, node_id: int) -> str:
        node = self._nodes.get(node_id)
        return node.name if node else f"<sector {node_id}>"

    # -- ASCII tree renderer ------------------------------------------------

    def render(self) -> str:
        """Render the topology as an ASCII network map."""
        self._levels = self._depth_levels()
        if not self._levels:
            return "[ MAINFRAME MAP ] no nodes registered."

        self._positions: Dict[int, int] = {}
        self._left: Dict[int, int] = {}
        self._right: Dict[int, int] = {}
        self._cursor = 0
        for root in self._roots():
            self._measure(root)

        rendered: List[str] = []
        for depth, level in enumerate(self._levels):
            if depth > 0:
                rendered.extend(self._connector_lines(depth))
            rendered.extend(self._box_rows(level))
        return "\n".join(rendered)

    def _roots(self) -> List[int]:
        """All nodes with no inbound link (the top of the tree)."""
        inbound: Set[int] = set()
        for targets in self._connections.values():
            inbound.update(targets)
        roots = [node_id for node_id in self.node_ids() if node_id not in inbound]
        return roots or ([self.node_ids()[0]] if self.node_ids() else [])

    def _depth_levels(self) -> List[List[int]]:
        """Group node ids by their BFS depth from the roots."""
        depth_map: Dict[int, int] = {}
        queue: List[Tuple[int, int]] = []
        seen: Set[int] = set()
        for root in self._roots():
            queue.append((root, 0))
            seen.add(root)
        while queue:
            node_id, depth = queue.pop(0)
            depth_map[node_id] = depth
            for child in self._connections.get(node_id, []):
                if child not in seen:
                    seen.add(child)
                    queue.append((child, depth + 1))
        # Stranded nodes (not reachable from any root) float at depth zero.
        for node_id in self.node_ids():
            if node_id not in depth_map:
                depth_map[node_id] = 0
        levels: List[List[int]] = []
        for node_id in self.node_ids():
            depth = depth_map[node_id]
            while len(levels) <= depth:
                levels.append([])
            levels[depth].append(node_id)
        return levels

    def _box_dimensions(self, node: SectorNode) -> int:
        """Return the inner width (excluding border chars) of a node box."""
        status_text = f"{STATUS_GLYPHS[node.status]} {node.status}"
        return max(len(node.name), len(status_text)) + 2

    def _measure(self, node_id: int) -> None:
        """Recursively lay out subtree columns, centring parents over children."""
        children = sorted(self._connections.get(node_id, []))
        node = self._nodes[node_id]
        inner = self._box_dimensions(node)
        if not children:
            start = self._cursor
            self._cursor += inner + 2 + _H_GAP
            self._left[node_id] = start
            self._right[node_id] = start + inner + 2
            self._positions[node_id] = start + 1 + inner // 2
            return
        for child in children:
            self._measure(child)
        left = min(self._left[child] for child in children)
        right = max(self._right[child] for child in children)
        self._left[node_id] = left
        self._right[node_id] = right
        self._positions[node_id] = (left + right) // 2

    def _box_lines(self, node_id: int, depth: int) -> List[str]:
        """Render the 4 border/content lines of a node box."""
        node = self._nodes[node_id]
        inner = self._box_dimensions(node)
        children = [c for c in self._connections.get(node_id, []) if self._depth_of(c) > depth]
        incoming = any(self._depth_of(other) < depth for other in self._ids_linking_to(node_id))

        top = "┌" + "─" * inner + "┐"
        if incoming:
            marker_col = 1 + inner // 2
            top = top[:marker_col] + "▼" + top[marker_col + 1:]
        name_line = "│" + ("  " + node.name).ljust(inner) + "│"
        status_line = "│" + ("  " + f"{STATUS_GLYPHS[node.status]} {node.status}").ljust(inner)
        status_line += "│"
        bottom = "└" + "─" * inner + "┘"
        if children:
            marker_col = 1 + inner // 2
            bottom = bottom[:marker_col] + "┬" + bottom[marker_col + 1:]
        return [top, name_line, status_line, bottom]

    def _ids_linking_to(self, node_id: int) -> List[int]:
        """All nodes that have a direct link toward ``node_id``."""
        return [src for src in self.node_ids() if node_id in self._connections.get(src, [])]

    def _depth_of(self, node_id: int) -> int:
        """Look up the BFS depth of a node from the latest layout."""
        for depth, level in enumerate(getattr(self, "_levels", [])):
            if node_id in level:
                return depth
        return 0

    def _box_rows(self, level: List[int]) -> List[str]:
        """Merge all boxes at one depth into full-width text rows."""
        rows = ["", "", "", ""]
        for node_id in level:
            left = self._positions[node_id] - (1 + self._box_dimensions(self._nodes[node_id]) // 2)
            for index, text in enumerate(self._box_lines(node_id, self._depth_of(node_id))):
                start = max(0, left)
                if start + len(text) > len(rows[index]):
                    rows[index] = rows[index].ljust(start + len(text))
                rows[index] = rows[index][:start] + text + rows[index][start + len(text):]
        return [row.rstrip() for row in rows]

    def _connector_lines(self, depth: int) -> List[str]:
        """Build the ASCII link rows bridging depth-1 boxes to this depth."""
        parent_ids = [nid for nid in self._levels[depth - 1]]
        width = max(self._right.values()) + 2 if self._right else 0
        stem_row = [" "] * width
        bracket_row = [" "] * width
        drop_row = [" "] * width

        for parent in parent_ids:
            children = [
                c for c in self._connections.get(parent, [])
                if self._depth_of(c) == depth
            ]
            if not children:
                continue
            parent_col = self._positions[parent]
            stem_row[parent_col] = "│"
            child_cols = sorted(self._positions[child] for child in children)
            if len(child_cols) == 1:
                bracket_row[parent_col] = "│"
                drop_row[child_cols[0]] = "│"
                continue
            left_col, right_col = child_cols[0], child_cols[-1]
            if not left_col <= parent_col <= right_col:
                parent_col = (left_col + right_col) // 2
            for col in range(left_col, right_col + 1):
                if col == left_col:
                    bracket_row[col] = "┌"
                elif col == right_col:
                    bracket_row[col] = "┐"
                elif col == parent_col:
                    bracket_row[col] = "┴"
                else:
                    bracket_row[col] = "─"
            for col in child_cols:
                drop_row[col] = "│"

        return [
            "".join(stem_row).rstrip(),
            "".join(bracket_row).rstrip(),
            "".join(drop_row).rstrip(),
        ]

    # -- serialization ------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the full topology for persistence."""
        return {
            "name": self.name,
            "nodes": [node.to_dict() for node in self.list_nodes()],
            "connections": {str(src): list(targets) for src, targets in self._connections.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MainframeMap":
        """Reconstruct a map from :meth:`to_dict` output."""
        nodes = {
            int(item["sector_id"]): SectorNode.from_dict(item)
            for item in data.get("nodes", [])
        }
        connections = {
            int(src): [int(t) for t in targets]
            for src, targets in data.get("connections", {}).items()
        }
        return cls(name=str(data.get("name", "MAINFRAME")), nodes=nodes, connections=connections)


def default_mainframe_map() -> MainframeMap:
    """Build the canonical tactical mainframe topology."""
    network = MainframeMap(name="TACTICAL MAINFRAME")
    network.add_node(0, "CORE NODE", status=ACTIVE, description="Primary mainframe nucleus.")
    network.add_node(1, "SECTOR A", status=LIBERATED, description="Perimeter sector A.")
    network.add_node(2, "SECTOR B", status=LOCKED, description="Perimeter sector B.")
    network.add_node(3, "ARCHIVE", status=ACTIVE, description="Data archival silo.")
    network.add_node(4, "SECURITY", status=LOCKED, description="Defensive daemon hub.")
    network.connect(0, 1)
    network.connect(0, 2)
    network.connect(1, 3)
    network.connect(2, 4)
    return network


def render_adventure_map(
    player: PlayerStats,
    quests: Optional[Dict[int, Any]] = None,
    width: int = 60,
) -> str:
    """Render the friendly 15-level adventure progression map."""
    if quests is None:
        try:
            from cybershell.game.quests import get_sector_quests
            quests = get_sector_quests()
        except Exception:
            quests = {}

    lines = [
        "🌱 YOUR ADVENTURE (15 LEVELS)",
        "",
    ]
    completed = set(player.completed_sectors) if hasattr(player, "completed_sectors") else set()
    current = getattr(player, "current_sector", 0)

    for sid in range(15):
        q = quests.get(sid)
        title = q.sector_name if q else f"Level {sid + 1}"
        lvl_num = f"{sid + 1:02d}"
        if sid in completed:
            mark = "\033[92m✓\033[0m"
            state_str = f"\033[92m{lvl_num}  {title:<24} (Completed)\033[0m"
        elif sid == current:
            mark = "\033[93m●\033[0m"
            state_str = f"\033[1;93m{lvl_num}  {title:<24} (Current)\033[0m"
        else:
            mark = "\033[2m○\033[0m"
            state_str = f"\033[2m{lvl_num}  {title:<24}\033[0m"
        lines.append(f"  {mark} {state_str}")

    lines.append("")
    total_completed = len(completed)
    pct = int((total_completed / 15) * 100)
    lines.append(f"Progress: {total_completed}/15 levels completed ({pct}%) ⭐")
    return "\n".join(lines)


__all__ = [
    "ACTIVE",
    "LIBERATED",
    "LOCKED",
    "VALID_STATUSES",
    "STATUS_GLYPHS",
    "MapError",
    "MainframeMap",
    "default_mainframe_map",
    "render_adventure_map",
]
