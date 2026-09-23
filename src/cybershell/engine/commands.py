"""Shell command implementations for the CyberShell virtual filesystem.

This module deliberately contains no command-line parsing.  ``ShellInterpreter``
turns a user command into an argument vector and passes it here, which makes the
individual commands straightforward to test and reusable by the game UI.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple

from cybershell.contracts import CommandResult
from cybershell.engine.node import DirectoryNode, FSNode
from cybershell.engine.vfs import VirtualFileSystem


class ShellCommands:
    """Execute supported Linux-like commands against a :class:`VirtualFileSystem`."""

    def __init__(self, vfs: VirtualFileSystem) -> None:
        self.vfs = vfs
        self._commands: Dict[str, Callable[[Sequence[str], str], CommandResult]] = {
            "pwd": self.pwd,
            "cd": self.cd,
            "ls": self.ls,
            "echo": self.echo,
            "touch": self.touch,
            "mkdir": self.mkdir,
            "cat": self.cat,
            "head": self.head,
            "tail": self.tail,
            "cp": self.cp,
            "mv": self.mv,
            "rm": self.rm,
            "chmod": self.chmod,
            "grep": self.grep,
            "wc": self.wc,
            "sort": self.sort,
            "less": self.less,
            "find": self.find,
            "man": self.man,
            "lookup": self.lookup,
            "help": self.help,
        }

    @property
    def command_names(self) -> Tuple[str, ...]:
        """Return the commands provided by this shell implementation."""
        return tuple(self._commands)

    def execute(self, argv: Sequence[str], stdin: str = "") -> CommandResult:
        """Run one already-tokenized command, optionally consuming piped input."""
        if not argv:
            return CommandResult(stderr="cybershell: syntax error near unexpected token `|`\n", exit_code=2)
        command = argv[0]
        handler = self._commands.get(command)
        if handler is None:
            return CommandResult(stderr=f"cybershell: command not found: {command}\n", exit_code=127)
        try:
            return handler(argv[1:], stdin)
        except (FileNotFoundError, NotADirectoryError, IsADirectoryError, FileExistsError, PermissionError) as error:
            return self._filesystem_error(command, error)
        except ValueError as error:
            return CommandResult(stderr=f"{command}: {error}\n", exit_code=1)

    @staticmethod
    def _filesystem_error(command: str, error: Exception) -> CommandResult:
        """Translate VFS exceptions into concise, familiar shell diagnostics."""
        message = str(error)
        target = ""
        if "'" in message:
            pieces = message.split("'")
            if len(pieces) >= 2:
                target = pieces[-2]
        if isinstance(error, FileNotFoundError):
            detail = "No such file or directory"
        elif isinstance(error, NotADirectoryError):
            detail = "Not a directory"
        elif isinstance(error, IsADirectoryError):
            detail = "Is a directory"
        elif isinstance(error, FileExistsError):
            detail = "File exists"
        else:
            detail = "Permission denied"
        prefix = f"{command}: {target}: " if target else f"{command}: "
        return CommandResult(stderr=f"{prefix}{detail}\n", exit_code=1)

    def pwd(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        if args:
            return CommandResult(stderr="pwd: too many arguments\n", exit_code=1)
        return CommandResult(stdout=f"{self.vfs.get_cwd_path()}\n")

    def cd(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        if len(args) > 1:
            return CommandResult(stderr="cd: too many arguments\n", exit_code=1)
        destination = args[0] if args else "~"
        new_path = self.vfs.cd(destination)
        return CommandResult(metadata={"cwd": new_path})

    def ls(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        show_hidden = False
        long_format = False
        paths: List[str] = []
        for arg in args:
            if arg == "--":
                paths.extend(args[args.index(arg) + 1 :])
                break
            if arg.startswith("-") and arg != "-":
                flags = arg[1:]
                if not flags or any(flag not in "al" for flag in flags):
                    return CommandResult(stderr=f"ls: invalid option -- '{flags[:1]}'\n", exit_code=2)
                show_hidden = show_hidden or "a" in flags
                long_format = long_format or "l" in flags
            else:
                paths.append(arg)
        paths = paths or ["."]

        output: List[str] = []
        for index, path in enumerate(paths):
            node = self.vfs.resolve_path(path)
            if len(paths) > 1:
                if index:
                    output.append("")
                output.append(f"{path}:")
            if show_hidden and isinstance(node, DirectoryNode):
                output.append(self._format_ls_node(node, long_format, "."))
                output.append(self._format_ls_node(node.parent or node, long_format, ".."))
            nodes = self._ls_nodes(node, show_hidden)
            output.extend(self._format_ls_node(item, long_format) for item in nodes)
        return CommandResult(stdout="\n".join(output) + ("\n" if output else ""))

    def _ls_nodes(self, node: FSNode, show_hidden: bool) -> List[FSNode]:
        if not isinstance(node, DirectoryNode):
            return [node]
        nodes = node.list_children(show_hidden=show_hidden)
        return nodes

    @staticmethod
    def _format_ls_node(node: FSNode, long_format: bool, display_name: Optional[str] = None) -> str:
        name = node.name if display_name is None else display_name
        if not long_format:
            return name or "."
        return f"{node.mode_str}  1 {node.owner:<10} {node.group:<10} {node.size:>6} {name or '.'}"

    @staticmethod
    def echo(args: Sequence[str], stdin: str = "") -> CommandResult:
        newline = True
        words = list(args)
        if words and words[0] == "-n":
            newline = False
            words = words[1:]
        return CommandResult(stdout=" ".join(words) + ("\n" if newline else ""))

    def touch(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        if not args:
            return CommandResult(stderr="touch: missing file operand\n", exit_code=1)
        for path in args:
            self.vfs.touch(path)
        return CommandResult()

    def mkdir(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        parents = False
        paths: List[str] = []
        for arg in args:
            if arg == "-p":
                parents = True
            elif arg.startswith("-"):
                return CommandResult(stderr=f"mkdir: invalid option -- '{arg[1:2]}'\n", exit_code=2)
            else:
                paths.append(arg)
        if not paths:
            return CommandResult(stderr="mkdir: missing operand\n", exit_code=1)
        for path in paths:
            if parents:
                self.vfs.mkdir_p(path)
            else:
                self.vfs.mkdir(path)
        return CommandResult()

    def cat(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        if not args:
            return CommandResult(stdout=stdin)
        return CommandResult(stdout="".join(self.vfs.read_file(path) for path in args))

    def head(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        count, paths, error = self._line_options("head", args)
        if error:
            return error
        content = self._read_inputs(paths, stdin, "head")
        if isinstance(content, CommandResult):
            return content
        return CommandResult(stdout="".join(content.splitlines(keepends=True)[:count]))

    def tail(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        count, paths, error = self._line_options("tail", args)
        if error:
            return error
        content = self._read_inputs(paths, stdin, "tail")
        if isinstance(content, CommandResult):
            return content
        return CommandResult(stdout="".join(content.splitlines(keepends=True)[-count:]))

    @staticmethod
    def _line_options(command: str, args: Sequence[str]) -> Tuple[int, List[str], Optional[CommandResult]]:
        words = list(args)
        count = 10
        if words[:1] == ["-n"]:
            if len(words) < 2 or not words[1].isdigit():
                return count, [], CommandResult(stderr=f"{command}: invalid number of lines\n", exit_code=1)
            count = int(words[1])
            words = words[2:]
        return count, words, None

    def _read_inputs(self, paths: Sequence[str], stdin: str, command: str):
        if not paths:
            return stdin
        try:
            return "".join(self.vfs.read_file(path) for path in paths)
        except (FileNotFoundError, NotADirectoryError, IsADirectoryError, FileExistsError, PermissionError) as error:
            return self._filesystem_error(command, error)

    def cp(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        recursive = False
        words = [arg for arg in args if arg not in ("-r", "-R")]
        recursive = len(words) != len(args)
        if len(words) != 2:
            return CommandResult(stderr="cp: missing destination file operand\n", exit_code=1)
        self.vfs.copy(words[0], words[1], recursive=recursive)
        return CommandResult()

    def mv(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        if len(args) != 2:
            return CommandResult(stderr="mv: missing destination file operand\n", exit_code=1)
        self.vfs.move(args[0], args[1])
        return CommandResult()

    def rm(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        recursive = any(arg in ("-r", "-R", "-rf", "-fr") for arg in args)
        force = any(arg in ("-f", "-rf", "-fr") for arg in args)
        paths = [arg for arg in args if not arg.startswith("-")]
        if not paths:
            return CommandResult(stderr="rm: missing operand\n", exit_code=1)
        for path in paths:
            try:
                self.vfs.remove(path, recursive=recursive)
            except FileNotFoundError:
                if not force:
                    raise
        return CommandResult()

    def chmod(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        if len(args) < 2:
            return CommandResult(stderr="chmod: missing operand\n", exit_code=1)
        mode, paths = args[0], args[1:]
        for path in paths:
            if mode in ("+x", "a+x", "u+x"):
                node = self.vfs.get_node(path)
                if node is not None:
                    node.permissions = (node.permissions | 0o111) & 0o777
                else:
                    self.vfs.chmod(path, "755")
            else:
                self.vfs.chmod(path, mode)
        return CommandResult()

    def grep(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        ignore_case = False
        invert = False
        words: List[str] = []
        for arg in args:
            if arg.startswith("-") and arg != "-" and not words:
                flags = arg[1:]
                if any(flag not in "iv" for flag in flags):
                    return CommandResult(stderr=f"grep: invalid option -- '{flags[:1]}'\n", exit_code=2)
                ignore_case = ignore_case or "i" in flags
                invert = invert or "v" in flags
            else:
                words.append(arg)
        if not words:
            return CommandResult(stderr="grep: missing search pattern\n", exit_code=2)
        pattern, paths = words[0], words[1:]
        content = self._read_inputs(paths, stdin, "grep")
        if isinstance(content, CommandResult):
            return content
        comparable_pattern = pattern.lower() if ignore_case else pattern
        selected = []
        for line in content.splitlines(keepends=True):
            comparable_line = line.lower() if ignore_case else line
            matches = comparable_pattern in comparable_line
            if matches != invert:
                selected.append(line)
        return CommandResult(stdout="".join(selected), exit_code=0 if selected else 1)

    def wc(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        if args and args[0] != "-l":
            return CommandResult(stderr="wc: only -l is supported\n", exit_code=2)
        paths = args[1:] if args else []
        content = self._read_inputs(paths, stdin, "wc")
        if isinstance(content, CommandResult):
            return content
        return CommandResult(stdout=f"{content.count(chr(10))}\n")

    def sort(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        reverse = False
        numeric = False
        unique = False
        paths: List[str] = []
        for arg in args:
            if arg.startswith("-") and arg != "-":
                flags = arg[1:]
                if "r" in flags:
                    reverse = True
                if "n" in flags:
                    numeric = True
                if "u" in flags:
                    unique = True
            else:
                paths.append(arg)
        content = self._read_inputs(paths, stdin, "sort")
        if isinstance(content, CommandResult):
            return content
        lines = [line for line in content.splitlines(keepends=True)]
        if unique:
            lines = list(dict.fromkeys(lines))
        if numeric:
            def _num_key(line: str):
                parts = line.strip().split()
                if parts:
                    try:
                        return (0, float(parts[0]))
                    except ValueError:
                        return (1, parts[0])
                return (2, "")
            lines.sort(key=_num_key, reverse=reverse)
        else:
            lines.sort(reverse=reverse)
        return CommandResult(stdout="".join(lines), exit_code=0)

    def less(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        return self.cat(args, stdin)

    def find(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        import fnmatch
        import posixpath
        start_path = "."
        name_pattern = "*"
        type_filter = None

        idx = 0
        if args and not args[0].startswith("-"):
            start_path = args[0]
            idx = 1

        while idx < len(args):
            arg = args[idx]
            if arg == "-name" and idx + 1 < len(args):
                name_pattern = args[idx + 1].strip("'\"")
                idx += 2
            elif arg == "-type" and idx + 1 < len(args):
                type_filter = args[idx + 1].lower()
                idx += 2
            else:
                idx += 1

        try:
            start_node = self.vfs.resolve_path(start_path)
        except Exception:
            return CommandResult(stderr=f"find: '{start_path}': No such file or directory\n", exit_code=1)

        results: List[str] = []

        def _traverse(node: FSNode, current_display: str) -> None:
            matches_name = fnmatch.fnmatch(node.name, name_pattern) or (name_pattern == "*" and not node.name)
            matches_type = True
            if type_filter == "f":
                matches_type = not node.is_directory
            elif type_filter == "d":
                matches_type = node.is_directory

            if matches_name and matches_type and current_display:
                results.append(current_display)

            if isinstance(node, DirectoryNode):
                for child_name, child in sorted(node.children.items()):
                    child_display = posixpath.join(current_display, child_name) if current_display != "/" else f"/{child_name}"
                    _traverse(child, child_display)

        base_display = start_path if start_path != "." else "."
        _traverse(start_node, base_display)

        output = "\n".join(results) + ("\n" if results else "")
        return CommandResult(stdout=output, exit_code=0)

    def man(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        if not args:
            return CommandResult(
                stdout="What manual page do you want?\nFor example, try 'man ls', 'man grep', or 'man find'.\n",
                exit_code=0,
            )
        from cybershell.tools.codex import format_man_page
        text = format_man_page(args[0])
        return CommandResult(stdout=text + "\n", exit_code=0)

    def lookup(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        return self.man(args, stdin)

    def help(self, args: Sequence[str], stdin: str = "") -> CommandResult:
        if args:
            return self.man(args, stdin)
        commands = sorted(self._commands.keys())
        lines = [
            "🌱 BYTE'S LINUX COMMAND GUIDE",
            "Available commands:",
            f"  {', '.join(commands[:11])}",
            f"  {', '.join(commands[11:])}",
            "",
            "Helpful Tools:",
            "  man <cmd>     - Short friendly guide for a command (e.g. 'man ls')",
            "  ? / hint      - Friendly hints for your current objective",
            "  map           - Show your adventure progress across all 15 levels",
            "  clear         - Clear the screen",
            "",
            "Explore freely! Mistakes are completely okay and safe 🌱",
        ]
        return CommandResult(stdout="\n".join(lines) + "\n", exit_code=0)
