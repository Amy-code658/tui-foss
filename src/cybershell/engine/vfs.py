"""In-Memory Linux Virtual Filesystem (VFS) Engine.

Author: Rudra (VFS Architect)
Role: Implements path resolution, directory traversal, node creation,
      file read/write, permissions enforcement, and instant sector loading.
"""

from __future__ import annotations

import posixpath
from typing import Any, Dict, List, Optional, Union

from cybershell.engine.node import (
    DirectoryNode,
    FileNode,
    FSNode,
    parse_permissions,
)


class VirtualFileSystem:
    """In-memory Linux filesystem tree and navigation engine."""

    def __init__(self, default_user: str = "operative") -> None:
        self.user: str = default_user
        self.home_dir: str = f"/home/{default_user}"

        # Initialize the root node
        self.root: DirectoryNode = DirectoryNode(
            name="",
            parent=None,
            permissions=0o755,
            owner="root",
            group="root",
        )

        # Set default current working directory
        self.cwd: DirectoryNode = self.root

        # Bootstrap standard Unix filesystem layout
        self._init_standard_layout()

        # Set operative home as initial CWD
        self.cd(self.home_dir)

        # Track the last executed shell command for quest evaluation
        self.last_command: Optional[str] = None

    def _init_standard_layout(self) -> None:
        """Create basic Linux directories: /bin, /etc, /home/operative, /root, /tmp, /var, /var/log."""
        for path in [
            "/bin",
            "/etc",
            "/home",
            self.home_dir,
            "/root",
            "/tmp",
            "/var",
            "/var/log",
        ]:
            self.mkdir_p(path)

        # Pre-seed mission target files for narrative quest continuity
        run_script = self.touch(f"{self.home_dir}/run.sh")
        run_script.write('#!/bin/bash\necho "Execution Core operational."\n')
        run_script.chmod(0o644)

        fw_log = self.touch(f"{self.home_dir}/firewall.log")
        fw_log.write("ERROR: Security perimeter breached.\nALERT: Sentinel Overlord daemon detected.\n")

    # -------------------------------------------------------------------------
    # Path Normalization and Resolution
    # -------------------------------------------------------------------------

    def normalize_path(self, path: str) -> str:
        """Convert any relative, home-expanded, or redundant path into canonical absolute path.

        Examples:
            '~'             -> '/home/operative'
            '~/notes.txt'   -> '/home/operative/notes.txt'
            '../var/./log'  -> '/var/log'
            '///bin///'     -> '/bin'
            '/../../'       -> '/' (cannot escape root)
        """
        if not path:
            return self.get_cwd_path()

        clean_path = path.strip()

        # Tilde expansion
        if clean_path == "~":
            clean_path = self.home_dir
        elif clean_path.startswith("~/"):
            clean_path = posixpath.join(self.home_dir, clean_path[2:])

        # Relative path resolution against CWD
        if not clean_path.startswith("/"):
            clean_path = posixpath.join(self.get_cwd_path(), clean_path)

        # posixpath.normpath resolves '.' and '..', drops duplicate slashes,
        # and guarantees that root '/..' resolves safely back to '/'
        normalized = posixpath.normpath(clean_path)
        return normalized

    def resolve_path(self, path: str) -> FSNode:
        """Traverse the tree and return the FSNode at path.

        Raises:
            FileNotFoundError: If any path component does not exist.
            NotADirectoryError: If an intermediate path component is a regular file.
        """
        norm = self.normalize_path(path)
        if norm == "/":
            return self.root

        # Split components (e.g. '/home/operative/file' -> ['home', 'operative', 'file'])
        parts = [p for p in norm.split("/") if p]
        current: FSNode = self.root

        for part in parts:
            if not isinstance(current, DirectoryNode):
                raise NotADirectoryError(f"Not a directory: '{current.path}'")
            child = current.get_child(part)
            if child is None:
                raise FileNotFoundError(f"No such file or directory: '{path}'")
            current = child

        return current

    def get_node(self, path: str) -> Optional[FSNode]:
        """Safe non-throwing lookup. Returns None if node does not exist or error occurs."""
        try:
            return self.resolve_path(path)
        except (FileNotFoundError, NotADirectoryError):
            return None

    # -------------------------------------------------------------------------
    # Basic Status and Introspection
    # -------------------------------------------------------------------------

    def exists(self, path: str) -> bool:
        """Return True if path exists in VFS."""
        return self.get_node(path) is not None

    def is_dir(self, path: str) -> bool:
        """Return True if path exists and is a directory."""
        node = self.get_node(path)
        return node is not None and node.is_directory

    def is_file(self, path: str) -> bool:
        """Return True if path exists and is a regular file."""
        node = self.get_node(path)
        return node is not None and node.is_file

    def get_cwd_path(self) -> str:
        """Return current working directory path string."""
        return self.cwd.path

    def pwd(self) -> str:
        """Return current working directory path string (bash 'pwd')."""
        return self.get_cwd_path()

    # -------------------------------------------------------------------------
    # Directory Navigation & Listing
    # -------------------------------------------------------------------------

    def cd(self, path: str = "~") -> str:
        """Change current working directory. Returns new path.

        Raises:
            FileNotFoundError: If directory does not exist.
            NotADirectoryError: If target path is a file.
        """
        node = self.resolve_path(path)
        if not node.is_directory:
            raise NotADirectoryError(f"Not a directory: '{path}'")
        self.cwd = node  # type: ignore[assignment]
        return self.get_cwd_path()

    def list_dir(self, path: str = ".", show_hidden: bool = False) -> List[FSNode]:
        """List files and subdirectories at path.

        If path is a file, returns [file].
        If path is a directory, returns sorted children.
        """
        node = self.resolve_path(path)
        if node.is_file:
            return [node]
        if isinstance(node, DirectoryNode):
            return node.list_children(show_hidden=show_hidden)
        return []

    def ls(self, path: str = ".", show_hidden: bool = False) -> List[FSNode]:
        """Alias for list_dir."""
        return self.list_dir(path=path, show_hidden=show_hidden)

    # -------------------------------------------------------------------------
    # Node Creation and Modification
    # -------------------------------------------------------------------------

    def touch(self, path: str) -> FileNode:
        """Create an empty file or update timestamp if it already exists.

        Raises:
            FileNotFoundError: If parent directory does not exist.
            NotADirectoryError: If parent is not a directory.
        """
        node = self.get_node(path)
        if node is not None:
            node.touch()
            if isinstance(node, FileNode):
                return node
            # If already a directory, touch it and return (touch on dir updates timestamp)
            return node  # type: ignore[return-value]

        norm = self.normalize_path(path)
        parent_path, filename = posixpath.split(norm)
        parent_node = self.resolve_path(parent_path)

        if not isinstance(parent_node, DirectoryNode):
            raise NotADirectoryError(f"Not a directory: '{parent_path}'")

        new_file = FileNode(
            name=filename,
            content="",
            parent=parent_node,
            permissions=0o644,
            owner=self.user,
            group=self.user,
        )
        parent_node.add_child(new_file)
        return new_file

    def mkdir(self, path: str, permissions: Union[int, str] = 0o755) -> DirectoryNode:
        """Create a directory. Parent must exist.

        Raises:
            FileExistsError: If directory or file already exists.
            FileNotFoundError: If parent directory does not exist.
            NotADirectoryError: If parent is not a directory.
        """
        if self.exists(path):
            raise FileExistsError(f"File exists: '{path}'")

        norm = self.normalize_path(path)
        parent_path, dirname = posixpath.split(norm)
        parent_node = self.resolve_path(parent_path)

        if not isinstance(parent_node, DirectoryNode):
            raise NotADirectoryError(f"Not a directory: '{parent_path}'")

        new_dir = DirectoryNode(
            name=dirname,
            parent=parent_node,
            permissions=permissions,
            owner=self.user,
            group=self.user,
        )
        parent_node.add_child(new_dir)
        return new_dir

    def mkdir_p(self, path: str, permissions: Union[int, str] = 0o755) -> DirectoryNode:
        """Create a directory and all non-existent parent directories (mkdir -p)."""
        norm = self.normalize_path(path)
        if norm == "/":
            return self.root

        parts = [p for p in norm.split("/") if p]
        current = self.root

        for part in parts:
            child = current.get_child(part)
            if child is None:
                new_dir = DirectoryNode(
                    name=part,
                    parent=current,
                    permissions=permissions,
                    owner=self.user,
                    group=self.user,
                )
                current.add_child(new_dir)
                current = new_dir
            elif isinstance(child, DirectoryNode):
                current = child
            else:
                raise NotADirectoryError(f"Cannot create directory, file exists in path: '{part}'")

        return current

    def read_file(self, path: str) -> str:
        """Read and return string content of a file.

        Raises:
            FileNotFoundError: If file not found.
            IsADirectoryError: If target path is a directory.
        """
        node = self.resolve_path(path)
        if isinstance(node, DirectoryNode):
            raise IsADirectoryError(f"Is a directory: '{path}'")
        if isinstance(node, FileNode):
            return node.read()
        return ""

    def write_file(self, path: str, content: str, append: bool = False) -> FileNode:
        """Write or append text content to a file. Creates file if missing.

        Raises:
            IsADirectoryError: If target path is an existing directory.
            FileNotFoundError: If parent directory does not exist.
        """
        node = self.get_node(path)
        if node is not None:
            if isinstance(node, DirectoryNode):
                raise IsADirectoryError(f"Is a directory: '{path}'")
            if isinstance(node, FileNode):
                if append:
                    node.append(content)
                else:
                    node.write(content)
                return node

        # File does not exist yet -> create it
        norm = self.normalize_path(path)
        parent_path, filename = posixpath.split(norm)
        parent_node = self.resolve_path(parent_path)

        if not isinstance(parent_node, DirectoryNode):
            raise NotADirectoryError(f"Not a directory: '{parent_path}'")

        new_file = FileNode(
            name=filename,
            content=content,
            parent=parent_node,
            permissions=0o644,
            owner=self.user,
            group=self.user,
        )
        parent_node.add_child(new_file)
        return new_file

    def remove(self, path: str, recursive: bool = False) -> None:
        """Remove file or directory (rm / rm -r).

        Raises:
            FileNotFoundError: If path does not exist.
            PermissionError: If attempting to delete root '/' or active CWD.
            IsADirectoryError: If deleting directory without recursive=True.
        """
        node = self.resolve_path(path)

        # Protect root directory
        if node is self.root:
            raise PermissionError("Cannot remove root directory '/'")

        # Protect current working directory and its parents
        cwd_path = self.get_cwd_path()
        if node.path == cwd_path or cwd_path.startswith(node.path + "/"):
            raise PermissionError(f"Cannot remove directory currently in use: '{path}'")

        if isinstance(node, DirectoryNode) and not recursive:
            raise IsADirectoryError(f"Is a directory: '{path}' (use -r to delete directories)")

        if node.parent is not None:
            node.parent.remove_child(node.name)

    def chmod(self, path: str, mode: Union[int, str]) -> None:
        """Change permissions of node at path.

        Accepts octal int (0o755), octal str ('755'), or symbolic ('rwxr-xr-x').
        """
        node = self.resolve_path(path)
        node.chmod(mode)

    def copy(self, src_path: str, dst_path: str, recursive: bool = True) -> FSNode:
        """Copy a file or directory tree (cp / cp -r)."""
        src_node = self.resolve_path(src_path)

        if isinstance(src_node, DirectoryNode) and not recursive:
            raise IsADirectoryError(f"omitting directory '{src_path}'")

        dst_node = self.get_node(dst_path)

        if dst_node is not None:
            if isinstance(dst_node, DirectoryNode):
                # Copy into existing directory
                cloned = src_node.copy()
                dst_node.add_child(cloned)
                return cloned
            elif isinstance(dst_node, FileNode):
                if isinstance(src_node, DirectoryNode):
                    raise FileExistsError(f"Cannot overwrite non-directory '{dst_path}' with directory")
                # Overwrite existing file
                dst_node.write(src_node.read())
                return dst_node

        # Destination does not exist -> copy with new name in parent
        norm_dst = self.normalize_path(dst_path)
        dst_parent_path, dst_name = posixpath.split(norm_dst)
        parent = self.resolve_path(dst_parent_path)

        if not isinstance(parent, DirectoryNode):
            raise NotADirectoryError(f"Not a directory: '{dst_parent_path}'")

        cloned = src_node.copy(new_name=dst_name)
        parent.add_child(cloned)
        return cloned

    def move(self, src_path: str, dst_path: str) -> FSNode:
        """Move or rename a file or directory (mv)."""
        src_node = self.resolve_path(src_path)
        if src_node is self.root:
            raise PermissionError("Cannot move root directory '/'")

        dst_node = self.get_node(dst_path)

        # Case 1: Destination is an existing directory -> move inside it
        if dst_node is not None and isinstance(dst_node, DirectoryNode):
            src_node.parent.remove_child(src_node.name)  # type: ignore[union-attr]
            dst_node.add_child(src_node)
            return src_node

        # Case 2: Destination is an existing file
        if dst_node is not None and isinstance(dst_node, FileNode):
            if isinstance(src_node, DirectoryNode):
                raise FileExistsError(f"Cannot overwrite file '{dst_path}' with directory")
            # Overwrite destination file
            dst_node.parent.remove_child(dst_node.name)  # type: ignore[union-attr]
            src_node.parent.remove_child(src_node.name)  # type: ignore[union-attr]
            src_node.name = dst_node.name
            dst_node.parent.add_child(src_node)  # type: ignore[union-attr]
            return src_node

        # Case 3: Destination does not exist -> rename in new parent
        norm_dst = self.normalize_path(dst_path)
        dst_parent_path, new_name = posixpath.split(norm_dst)
        parent = self.resolve_path(dst_parent_path)

        if not isinstance(parent, DirectoryNode):
            raise NotADirectoryError(f"Not a directory: '{dst_parent_path}'")

        src_node.parent.remove_child(src_node.name)  # type: ignore[union-attr]
        src_node.name = new_name
        parent.add_child(src_node)
        return src_node

    # -------------------------------------------------------------------------
    # Sector Loading & Snapshotting (Day 5 & Quests Integration)
    # -------------------------------------------------------------------------

    def reset_from_dict(
        self,
        tree: Dict[str, Any],
        default_cwd: str = "/home/operative",
        preserve_standard_layout: bool = True,
    ) -> None:
        """Instantly build or reset the entire VFS layout from a nested dictionary in <1ms.

        Dictionary values can be:
          - str: creates a FileNode with that text content.
          - dict:
              If has 'content' key: creates FileNode with custom metadata (permissions, owner).
              Otherwise: creates DirectoryNode and recursively builds child items.

        Example:
            {
                "home": {
                    "operative": {
                        "README.md": "Sector 0: Quarantine Zone",
                        ".token": {"content": "SECRET_KEY_123", "permissions": "600"}
                    }
                },
                "var": {
                    "log": {
                        "syslog": "kernel: corrupted sector identified"
                    }
                }
            }
        """
        # Recreate root
        self.root = DirectoryNode(
            name="",
            parent=None,
            permissions=0o755,
            owner="root",
            group="root",
        )
        self.cwd = self.root

        if preserve_standard_layout:
            self._init_standard_layout()

        self._populate_dict_node(self.root, tree)

        # Set operative CWD
        if self.exists(default_cwd) and self.is_dir(default_cwd):
            self.cd(default_cwd)
        else:
            self.mkdir_p(default_cwd)
            self.cd(default_cwd)

    def _populate_dict_node(self, current_dir: DirectoryNode, subtree: Dict[str, Any]) -> None:
        """Recursively populate DirectoryNode from dictionary."""
        for name, item in subtree.items():
            if isinstance(item, str):
                # Simple string content file
                file_node = FileNode(
                    name=name,
                    content=item,
                    parent=current_dir,
                    permissions=0o644,
                    owner=self.user,
                    group=self.user,
                )
                current_dir.add_child(file_node)
            elif isinstance(item, dict):
                if "content" in item:
                    # File with explicit attributes
                    content = str(item.get("content", ""))
                    perms = parse_permissions(item.get("permissions", 0o644))
                    owner = item.get("owner", self.user)
                    group = item.get("group", self.user)
                    file_node = FileNode(
                        name=name,
                        content=content,
                        parent=current_dir,
                        permissions=perms,
                        owner=owner,
                        group=group,
                    )
                    current_dir.add_child(file_node)
                else:
                    # Directory node
                    perms = parse_permissions(item.get("__permissions__", 0o755))
                    owner = item.get("__owner__", self.user)
                    group = item.get("__group__", self.user)

                    # Filter out metadata keys if any
                    sub_children = {k: v for k, v in item.items() if not k.startswith("__")}

                    existing = current_dir.get_child(name)
                    if existing is not None and isinstance(existing, DirectoryNode):
                        dir_node = existing
                    else:
                        dir_node = DirectoryNode(
                            name=name,
                            parent=current_dir,
                            permissions=perms,
                            owner=owner,
                            group=group,
                        )
                        current_dir.add_child(dir_node)

                    self._populate_dict_node(dir_node, sub_children)

    def dump_tree(self, start_path: str = "/") -> Dict[str, Any]:
        """Serialize subtree into a nested dictionary (useful for debugging and tests)."""
        node = self.resolve_path(start_path)
        if isinstance(node, FileNode):
            return {"__file__": True, "content": node.read(), "permissions": node.mode_octal}

        def _dump(d_node: DirectoryNode) -> Dict[str, Any]:
            result: Dict[str, Any] = {}
            for child_name, child in d_node.children.items():
                if isinstance(child, FileNode):
                    result[child_name] = child.read()
                elif isinstance(child, DirectoryNode):
                    result[child_name] = _dump(child)
            return result

        return _dump(node)  # type: ignore[arg-type]

    def load_sector(self, sector_id: int, quest: Optional[Any] = None) -> None:
        """Load specific files and environment tree for a sector into VFS."""
        if quest is None:
            try:
                from cybershell.game.quests import get_sector_quests
                all_q = get_sector_quests()
                quest = all_q.get(sector_id)
            except Exception:
                quest = None
        if quest is not None and hasattr(quest, "environment_tree") and quest.environment_tree:
            def _populate(current_path: str, node_data: Any) -> None:
                if isinstance(node_data, str):
                    f = self.touch(current_path)
                    f.write(node_data)
                elif isinstance(node_data, dict):
                    if "content" in node_data:
                        f = self.touch(current_path)
                        f.write(str(node_data.get("content", "")))
                        if "permissions" in node_data:
                            f.chmod(node_data["permissions"])
                    else:
                        self.mkdir_p(current_path)
                        for child_name, child_val in node_data.items():
                            child_path = posixpath.join(current_path, child_name)
                            _populate(child_path, child_val)

            for item_name, item_val in quest.environment_tree.items():
                if item_name.startswith("/"):
                    full_path = item_name
                else:
                    full_path = posixpath.join(self.home_dir, item_name)
                _populate(full_path, item_val)

