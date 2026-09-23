"""Pipeline-aware command interpreter for the CyberShell RPG engine."""

from __future__ import annotations

import shlex
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cybershell.contracts import DEFAULT_BACKLASH_DAMAGE, CommandResult
from cybershell.engine.commands import ShellCommands
from cybershell.engine.vfs import VirtualFileSystem


class ShellInterpreter:
    """Parse shell input and execute commands, pipes, and output redirects."""

    def __init__(self, vfs: Optional[VirtualFileSystem] = None, default_user: str = "operative") -> None:
        self.vfs = vfs if vfs is not None else VirtualFileSystem(default_user=default_user)
        self.commands = ShellCommands(self.vfs)

    def execute(self, command_line: str) -> CommandResult:
        """Execute one command line and apply combat backlash to invalid syntax/commands."""
        self.vfs.last_command = command_line

        tokens, error = self.tokenize(command_line)
        if error is not None:
            return self._with_backlash(error)
        if not tokens:
            return CommandResult()

        stages, redirect, in_redir, parse_error = self._parse(tokens)
        if parse_error is not None:
            return self._with_backlash(parse_error)

        stdin = ""
        if in_redir is not None:
            try:
                stdin = self.vfs.read_file(in_redir)
            except (FileNotFoundError, NotADirectoryError, IsADirectoryError, PermissionError) as exc:
                return CommandResult(stderr=f"{exc}\n", exit_code=1)

        result = CommandResult()
        for stage in stages:
            result = self.commands.execute(stage, stdin)
            if result.exit_code != 0:
                return self._with_backlash(result) if result.exit_code == 127 else result
            stdin = result.stdout

        if redirect is not None:
            path, append = redirect
            try:
                self.vfs.write_file(path, result.stdout, append=append)
            except (FileNotFoundError, NotADirectoryError, IsADirectoryError, PermissionError) as exc:
                return CommandResult(stderr=f"{exc}\n", exit_code=1)
            result = CommandResult(stdout="", metadata={"redirect": path, "append": append})
        return result

    @staticmethod
    def tokenize(command_line: str) -> Tuple[List[str], Optional[CommandResult]]:
        """Tokenize quoted strings while retaining pipeline and redirect operators."""
        try:
            lexer = shlex.shlex(command_line, posix=True, punctuation_chars="|><")
            lexer.whitespace_split = True
            lexer.commenters = ""
            return list(lexer), None
        except ValueError as error:
            return [], CommandResult(stderr=f"syntax error: {error}\n", exit_code=2)

    @staticmethod
    def _parse(tokens: Sequence[str]) -> Tuple[List[List[str]], Optional[Tuple[str, bool]], Optional[str], Optional[CommandResult]]:
        redirect: Optional[Tuple[str, bool]] = None
        input_redirect: Optional[str] = None
        command_tokens = list(tokens)

        # Handle input redirection '<'
        in_indices = [index for index, token in enumerate(command_tokens) if token == "<"]
        if in_indices:
            in_idx = in_indices[0]
            if in_idx + 1 >= len(command_tokens) or command_tokens[in_idx + 1] in ("|", ">", ">>", "<"):
                return [], None, None, CommandResult(stderr="syntax error near unexpected token `<`\n", exit_code=2)
            input_redirect = command_tokens[in_idx + 1]
            command_tokens = command_tokens[:in_idx] + command_tokens[in_idx + 2:]

        # Handle output redirection '>' and '>>'
        redirection_indices = [index for index, token in enumerate(command_tokens) if token in (">", ">>")]
        if len(redirection_indices) > 1:
            return [], None, None, CommandResult(stderr="syntax error near unexpected token `>`\n", exit_code=2)
        if redirection_indices:
            index = redirection_indices[0]
            if index == 0 or index + 2 != len(command_tokens):
                return [], None, None, CommandResult(stderr="syntax error near unexpected token `>`\n", exit_code=2)
            target = command_tokens[index + 1]
            if target in ("|", ">", ">>", "<"):
                return [], None, None, CommandResult(stderr="syntax error near unexpected token `>`\n", exit_code=2)
            redirect = (target, command_tokens[index] == ">>")
            command_tokens = command_tokens[:index]

        stages: List[List[str]] = [[]]
        for token in command_tokens:
            if token == "|":
                if not stages[-1]:
                    return [], None, None, CommandResult(stderr="syntax error near unexpected token `|'\n", exit_code=2)
                stages.append([])
            else:
                stages[-1].append(token)
        if not stages[-1]:
            return [], None, None, CommandResult(stderr="syntax error near unexpected token `|'\n", exit_code=2)
        return stages, redirect, input_redirect, None

    @staticmethod
    def _with_backlash(result: CommandResult) -> CommandResult:
        """Add the fixed electrical backlash only once for malformed/unknown input."""
        result.backlash_damage = DEFAULT_BACKLASH_DAMAGE
        return result

    def get_cwd(self) -> str:
        """Return the current VFS working directory, satisfying ``EngineProtocol``."""
        return self.vfs.get_cwd_path()

    def reset_sector(self, sector_dict: Optional[Dict[str, Any]] = None) -> None:
        """Reset the virtual filesystem to a sector layout or the standard layout."""
        if sector_dict is None:
            self.vfs = VirtualFileSystem(default_user=self.vfs.user)
        else:
            self.vfs.reset_from_dict(sector_dict)
        self.commands = ShellCommands(self.vfs)


# A concise alias is convenient for UI and integration code.
Interpreter = ShellInterpreter
