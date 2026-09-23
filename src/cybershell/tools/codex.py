"""Hacker Codex - Tactical Command Encyclopedia for CyberShell RPG v2.0.

Author: Akash (Hacker Codex & Chmod Minigame)
Role: An in-game "TLDR spellbook" describing Linux/security commands, their
      flags, examples, and tactical pipeline combos. Designed so additional
      commands can be added simply by registering another entry.

Entries are stored as plain dictionaries (schema below) so they are easy to
extend, while ``CodexEntry`` DTO contract objects can be produced on demand
for integration with the rest of the game:

    {
        "name": "ls",
        "description": "...",
        "syntax": "...",
        "flags": {"-l": "...", "-a": "..."},
        "examples": ["..."],
        "combos": ["..."]
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from cybershell.contracts import CodexEntry

# Schema of a registered codex entry.
REQUIRED_KEYS: Tuple[str, ...] = ("name", "description", "syntax", "flags", "examples", "combos")

# ---------------------------------------------------------------------------
# Command database
# ---------------------------------------------------------------------------

COMMANDS: Dict[str, Dict[str, Any]] = {
    "ls": {
        "name": "ls",
        "description": "List directory contents - see what files and folders are around.",
        "syntax": "ls [options] [path]",
        "flags": {
            "-l": "Long format: show details like permissions and size.",
            "-a": "Include hidden files that start with a dot.",
            "-la": "Show all files with full details.",
        },
        "examples": [
            "ls",
            "ls -la",
            "ls garden",
        ],
        "combos": [
            "ls → cd → cat   # look around, step inside, and read notes",
        ],
    },
    "cd": {
        "name": "cd",
        "description": "Change directory - walk to a different folder.",
        "syntax": "cd [path]",
        "flags": {
            "~": "Jump back to your home folder.",
            "..": "Move one level up to the parent folder.",
            "-": "Return to the previous folder.",
        },
        "examples": [
            "cd garden",
            "cd ..",
            "cd ~",
        ],
        "combos": [
            "cd garden → ls   # step into a folder and look around",
        ],
    },
    "cat": {
        "name": "cat",
        "description": "Read and print file contents to your screen.",
        "syntax": "cat [file...]",
        "flags": {
            "-n": "Number all output lines.",
        },
        "examples": [
            "cat welcome.txt",
            "cat notes.txt",
        ],
        "combos": [
            "cat animals.txt | grep 'cat'   # read and filter text",
        ],
    },
    "less": {
        "name": "less",
        "description": "View file contents comfortably.",
        "syntax": "less [file...]",
        "flags": {},
        "examples": [
            "less welcome.txt",
            "less notes.txt",
        ],
        "combos": [
            "less story.txt   # read long notes",
        ],
    },
    "grep": {
        "name": "grep",
        "description": "Search text for words or patterns.",
        "syntax": "grep [options] PATTERN [file...]",
        "flags": {
            "-i": "Case-insensitive: ignore uppercase vs lowercase.",
            "-r": "Search through all folders recursively.",
            "-n": "Show line numbers of matches.",
            "-v": "Invert match: show lines that do NOT match.",
        },
        "examples": [
            "grep 'banana' items.txt",
            "grep -i 'hello' notes.txt",
            "grep 'password' notes.txt",
        ],
        "combos": [
            "find . -name '*.txt' | grep 'clue'   # find and filter",
        ],
    },
    "chmod": {
        "name": "chmod",
        "description": "Change permissions on a file or script.",
        "syntax": "chmod [mode] [file]",
        "flags": {
            "755": "Owner can read, write, run; everyone else can read and run.",
            "644": "Owner can read and write; everyone else can read only.",
            "+x": "Make a script executable so you can run it.",
        },
        "examples": [
            "chmod 755 play.sh",
            "chmod +x script.sh",
            "chmod 644 notes.txt",
        ],
        "combos": [
            "chmod 755 play.sh → ./play.sh   # make executable and run",
        ],
    },
    "rm": {
        "name": "rm",
        "description": "Remove unwanted files or folders.",
        "syntax": "rm [options] [target...]",
        "flags": {
            "-r": "Remove a folder and all its contents recursively.",
            "-f": "Force remove without asking.",
        },
        "examples": [
            "rm junk.tmp",
            "rm -r old_folder",
        ],
        "combos": [
            "rm junk.tmp   # clean up temporary files",
        ],
    },
    "touch": {
        "name": "touch",
        "description": "Create a new empty file or update its timestamp.",
        "syntax": "touch [file]",
        "flags": {},
        "examples": [
            "touch todo.txt",
            "touch notes.txt",
        ],
        "combos": [
            "touch todo.txt → echo 'Learn Linux' > todo.txt   # create and write",
        ],
    },
    "sort": {
        "name": "sort",
        "description": "Sort lines in text files alphabetically or numerically.",
        "syntax": "sort [options] [file...]",
        "flags": {
            "-r": "Reverse the sort order (Z to A).",
            "-n": "Sort by number value.",
            "-u": "Remove duplicate lines.",
        },
        "examples": [
            "sort names.txt",
            "sort -r scores.txt",
        ],
        "combos": [
            "cat names.txt | sort   # sort list of names",
        ],
    },
    "mkdir": {
        "name": "mkdir",
        "description": "Create a new directory folder.",
        "syntax": "mkdir [options] [dir]",
        "flags": {
            "-p": "Create parent folders if needed without errors.",
        },
        "examples": [
            "mkdir garden",
            "mkdir -p projects/notes",
        ],
        "combos": [
            "mkdir garden → cd garden   # make a folder and enter it",
        ],
    },
    "pwd": {
        "name": "pwd",
        "description": "Print working directory - shows where you are in the computer.",
        "syntax": "pwd",
        "flags": {},
        "examples": [
            "pwd",
        ],
        "combos": [
            "pwd → ls   # check where you are and what is nearby",
        ],
    },
    "find": {
        "name": "find",
        "description": "Search for files and directories in a directory hierarchy.",
        "syntax": "find [path] [expression]",
        "flags": {
            "-name": "Match files by name pattern (e.g. -name '*.txt')",
            "-type": "Filter by type: 'f' for file, 'd' for directory",
        },
        "examples": [
            "find . -name '*.txt'",
            "find /home -type f",
        ],
        "combos": [
            "find . -name '*.log' → cat   # locate files, then inspect them",
        ],
    },
    "cp": {
        "name": "cp",
        "description": "Copy files or directories to a new destination.",
        "syntax": "cp [options] <source> <dest>",
        "flags": {
            "-r": "Copy directories recursively",
        },
        "examples": [
            "cp intel.txt intel.bak",
            "cp -r /source /dest",
        ],
        "combos": [
            "cp file.txt backup/   # create a safe duplicate before modifying",
        ],
    },
    "mv": {
        "name": "mv",
        "description": "Move or rename files and directories.",
        "syntax": "mv <source> <dest>",
        "flags": {},
        "examples": [
            "mv old.txt new.txt",
            "mv file.txt /tmp/",
        ],
        "combos": [
            "mv data.log archive/   # relocate files",
        ],
    },
    "head": {
        "name": "head",
        "description": "Output the first part of files or streams.",
        "syntax": "head [-n count] [file...]",
        "flags": {
            "-n": "Number of lines to show (default: 10)",
        },
        "examples": [
            "head data.log",
            "head -n 5 traffic.txt",
        ],
        "combos": [
            "cat log.txt | head -n 10",
        ],
    },
    "tail": {
        "name": "tail",
        "description": "Output the last part of files or streams.",
        "syntax": "tail [-n count] [file...]",
        "flags": {
            "-n": "Number of lines to show (default: 10)",
        },
        "examples": [
            "tail system.log",
            "tail -n 20 events.log",
        ],
        "combos": [
            "cat stream.log | tail -n 5",
        ],
    },
    "wc": {
        "name": "wc",
        "description": "Print newline, word, and byte counts for files or streams.",
        "syntax": "wc [-l] [file...]",
        "flags": {
            "-l": "Count lines only",
            "-w": "Count words only",
            "-c": "Count bytes only",
        },
        "examples": [
            "wc -l file.txt",
            "cat access.log | wc -l",
        ],
        "combos": [
            "cat log | grep 'ERROR' | wc -l   # count occurrences",
        ],
    },
    "echo": {
        "name": "echo",
        "description": "Print a line of text or write into a file with > or >>.",
        "syntax": "echo [text] [> file]",
        "flags": {
            "-n": "Do not output trailing newline",
            ">": "Redirect output to create or overwrite a file",
            ">>": "Redirect output to append to a file without overwriting",
        },
        "examples": [
            "echo 'Hello Linux!'",
            "echo 'Hello Linux' > greeting.txt",
            "echo 'Have fun!' >> greeting.txt",
        ],
        "combos": [
            "echo 'Note' > notes.txt   # write a quick note to a file",
        ],
    },
    "man": {
        "name": "man",
        "description": "Display concise, beginner-friendly manual page for a command.",
        "syntax": "man <command>",
        "flags": {},
        "examples": [
            "man ls",
            "man grep",
            "man find",
        ],
        "combos": [
            "man grep   # learn pattern search flags and examples",
        ],
    },
    "lookup": {
        "name": "lookup",
        "description": "Quick lookup of command syntax, flags, and examples (alias for man).",
        "syntax": "lookup <command>",
        "flags": {},
        "examples": [
            "lookup chmod",
            "lookup grep",
        ],
        "combos": [
            "lookup find   # quick help on finding files",
        ],
    },
    "help": {
        "name": "help",
        "description": "Display overview of available commands and gameplay controls.",
        "syntax": "help [command]",
        "flags": {},
        "examples": [
            "help",
            "help cd",
        ],
        "combos": [
            "help   # check available tools",
        ],
    },
    "hint": {
        "name": "hint",
        "description": "Request progressive assistance for the current objective (Concept -> Category -> Direction).",
        "syntax": "hint",
        "flags": {},
        "examples": [
            "hint",
        ],
        "combos": [
            "hint   # view progressive clue without HP penalty",
        ],
    },
}


# ---------------------------------------------------------------------------
# Codex registry / lookup API
# ---------------------------------------------------------------------------

class Codex:
    """Encyclopedia of commands with lookup, search, and display helpers."""

    def __init__(self, entries: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """Build a codex. Defaults to the built-in command database."""
        self._commands: Dict[str, Dict[str, Any]] = dict(
            entries if entries is not None else COMMANDS
        )
        self._validate_entries()

    # -- internal helpers ---------------------------------------------------

    def _validate_entries(self) -> None:
        """Ensure every registered command follows the expected schema."""
        for name, data in self._commands.items():
            if not isinstance(name, str) or not name:
                raise ValueError(f"Codex command name must be a non-empty string: {name!r}")
            for key in REQUIRED_KEYS:
                if key not in data:
                    raise ValueError(f"Codex entry for {name!r} is missing key {key!r}")
            if data.get("name") != name:
                message = (
                    f"Codex entry key {name!r} does not match entry name {data.get('name')!r}"
                )
                raise ValueError(message)
            if not isinstance(data["flags"], dict):
                raise ValueError(f"Codex entry for {name!r}: 'flags' must be a dict")
            if not isinstance(data.get("examples"), list):
                raise ValueError(f"Codex entry for {name!r}: 'examples' must be a list")
            if not isinstance(data.get("combos"), list):
                raise ValueError(f"Codex entry for {name!r}: 'combos' must be a list")

    # -- retrieval ----------------------------------------------------------

    def command_names(self) -> List[str]:
        """Return sorted command names registered in the codex."""
        return sorted(self._commands)

    def has_command(self, name: str) -> bool:
        """Return True when a command exists in the codex."""
        return str(name).strip().lower() in self._commands

    def get_command(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a command record, or None when it is unknown."""
        return self._commands.get(str(name).strip().lower())

    def get_command_data(self, name: str) -> Optional[Dict[str, Any]]:
        """Alias of :meth:`get_command` returning the full dictionary record."""
        return self.get_command(name)

    def list_commands(self) -> List[Dict[str, Any]]:
        """Return all command records sorted alphabetically by name."""
        return [self._commands[name] for name in self.command_names()]

    def get_flags(self, name: str) -> Dict[str, str]:
        """Retrieve the flags for a command, or an empty dict when unknown."""
        entry = self.get_command(name)
        return dict(entry["flags"]) if entry else {}

    def get_combos(self, name: str) -> List[str]:
        """Retrieve tactical command combos for a command."""
        entry = self.get_command(name)
        return list(entry["combos"]) if entry else []

    def get_examples(self, name: str) -> List[str]:
        """Retrieve usage examples for a command."""
        entry = self.get_command(name)
        return list(entry["examples"]) if entry else []

    # -- search -------------------------------------------------------------

    def search_commands(self, query: str) -> List[Dict[str, Any]]:
        """Case-insensitive search across names, descriptions, flags, and combos."""
        needle = str(query).strip().lower()
        if not needle:
            return []
        matches: List[Dict[str, Any]] = []
        for entry in self.list_commands():
            haystack = [str(entry["name"]), str(entry["description"]), str(entry["syntax"])]
            haystack.extend(str(k) for k in entry["flags"])
            haystack.extend(str(v) for v in entry["flags"].values())
            haystack.extend(str(e) for e in entry["examples"])
            haystack.extend(str(c) for c in entry["combos"])
            if any(needle in token.lower() for token in haystack):
                matches.append(entry)
        return matches

    # -- display ------------------------------------------------------------

    def to_codex_entry(self, name: str) -> Optional[CodexEntry]:
        """Convert a command record into the shared ``CodexEntry`` DTO."""
        data = self.get_command(name)
        if not data:
            return None
        return CodexEntry(
            command=data["name"],
            syntax=data["syntax"],
            description=data["description"],
            flags=dict(data["flags"]),
            combos=list(data["combos"]),
        )

    def display_command(self, name: str, width: int = 60) -> str:
        """Render a full command detail card, or an error notice when unknown."""
        entry = self.get_command(name)
        if not entry:
            return f"[ CODEX // UNKNOWN ENTRY ] No intel on command {name!r}."

        marker = "=" * max(10, width)
        lines = [
            marker,
            f"[ COMMAND GUIDE // {entry['name']} ]",
            marker,
            f"Syntax: {entry['syntax']}",
            f"Summary: {entry['description']}",
            "",
        ]
        if entry["flags"]:
            lines.append("Flags:")
            for flag, meaning in entry["flags"].items():
                lines.append(f"  {flag:<8} {meaning}")
            lines.append("")
        if entry["examples"]:
            lines.append("Examples:")
            lines.extend(f"  > {example}" for example in entry["examples"])
            lines.append("")
        if entry["combos"]:
            lines.append("Helpful combos:")
            lines.extend(f"  » {combo}" for combo in entry["combos"])
        return "\n".join(lines)

    def display_list(self) -> str:
        """Render a compact overview of every registered command."""
        lines = ["[ COMMAND GUIDE // HANDBOOK OVERVIEW ]"]
        for entry in self.list_commands():
            lines.append(f"  {entry['name']:<10} {entry['description']}")
        lines.append("")
    def format_man_page(self, name: str) -> str:
        """Format a clean, concise, beginner-friendly manual page."""
        clean_name = str(name).strip().lower()
        entry = self.get_command(clean_name)
        if not entry:
            matches = self.search_commands(clean_name)
            if matches:
                suggestions = ", ".join(f"'{m['name']}'" for m in matches[:3])
                return f"No manual entry for '{name}'. Did you mean: {suggestions}?\nType 'help' to see all available commands.\n"
            return f"No manual entry for '{name}'. Type 'help' for available commands.\n"

        lines = [
            "NAME",
            f"    {entry['name']} - {entry['description']}",
            "",
            "SYNOPSIS",
            f"    {entry['syntax']}",
            "",
            "DESCRIPTION",
            f"    {entry['description']}",
        ]
        if entry.get("flags"):
            lines.append("")
            lines.append("OPTIONS & FLAGS")
            for flag, desc in entry["flags"].items():
                lines.append(f"    {flag:<12} {desc}")
        if entry.get("examples"):
            lines.append("")
            lines.append("EXAMPLES")
            for ex in entry["examples"]:
                lines.append(f"    $ {ex}")
        if entry.get("combos"):
            lines.append("")
            lines.append("TACTICAL COMBOS")
            for combo in entry["combos"]:
                lines.append(f"    » {combo}")
        lines.append("")
        return "\n".join(lines)


# Convariance: default module-level codex + convenience functions so both
# object-oriented and functional call styles are supported.

CODEX: Codex = Codex()


def get_command(name: str) -> Optional[Dict[str, Any]]:
    """Retrieve a command record from the default codex."""
    return CODEX.get_command(name)


def list_commands() -> List[Dict[str, Any]]:
    """List all commands registered in the default codex."""
    return CODEX.list_commands()


def command_names() -> List[str]:
    """Return the names of all commands in the default codex."""
    return CODEX.command_names()


def search_commands(query: str) -> List[Dict[str, Any]]:
    """Search the default codex for a query string."""
    return CODEX.search_commands(query)


def get_flags(name: str) -> Dict[str, str]:
    """Retrieve a command's flags from the default codex."""
    return CODEX.get_flags(name)


def get_combos(name: str) -> List[str]:
    """Retrieve a command's tactical combos from the default codex."""
    return CODEX.get_combos(name)


def get_examples(name: str) -> List[str]:
    """Retrieve a command's examples from the default codex."""
    return CODEX.get_examples(name)


def display_command(name: str) -> str:
    """Render a full command detail card from the default codex."""
    return CODEX.display_command(name)


def display_list() -> str:
    """Render the compact overview of all commands in the default codex."""
    return CODEX.display_list()


def format_man_page(name: str) -> str:
    """Render a concise beginner-friendly manual page from the default codex."""
    return CODEX.format_man_page(name)


__all__ = [
    "COMMANDS",
    "REQUIRED_KEYS",
    "Codex",
    "CODEX",
    "get_command",
    "list_commands",
    "command_names",
    "search_commands",
    "get_flags",
    "get_combos",
    "get_examples",
    "display_command",
    "display_list",
    "format_man_page",
]
