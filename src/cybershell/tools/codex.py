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
        "purpose": 'List directory contents.',
        "explanation": 'Displays files and folders in your current directory or specified path.',
        "example": 'ls -la',
        "related": ['cd', 'tree', 'pwd'],
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
        "purpose": 'Change the current working directory.',
        "explanation": 'Navigate to a different folder in the filesystem hierarchy.',
        "example": 'cd ~/project',
        "related": ['pwd', 'ls'],
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
        "purpose": 'Print file contents to the screen.',
        "explanation": 'Reads and outputs the entire content of one or more files.',
        "example": 'cat notes.txt',
        "related": ['less', 'head', 'tail'],
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
        "purpose": 'View file contents with scrolling and pagination.',
        "explanation": 'Interactive text pager allowing you to navigate forward and backward.',
        "example": 'less /var/log/syslog',
        "related": ['cat', 'head', 'tail'],
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
        "purpose": 'Search text for words or regular expression patterns.',
        "explanation": 'Filters lines matching a pattern from files or piped input.',
        "example": "grep -i 'banana' items.txt",
        "related": ['find', 'wc', 'sort'],
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
        "purpose": 'Change file access permissions.',
        "explanation": 'Sets read, write, and execute permissions using octal or symbolic modes.',
        "example": 'chmod 755 play.sh',
        "related": ['ls', 'chown'],
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
        "purpose": 'Remove files or directories.',
        "explanation": 'Deletes specified files. Use with caution as this is permanent.',
        "example": 'rm -r old_folder',
        "related": ['rmdir', 'cp', 'mv'],
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
        "purpose": 'Create empty files or update file timestamps.',
        "explanation": "Creates a new blank file if it doesn't exist, or updates its timestamp.",
        "example": 'touch todo.txt',
        "related": ['mkdir', 'rm'],
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
        "purpose": 'Sort lines of text files.',
        "explanation": 'Orders lines alphabetically or numerically from files or standard input.',
        "example": 'sort names.txt',
        "related": ['uniq', 'wc', 'grep'],
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
        "purpose": 'Create new directories (folders).',
        "explanation": 'Creates one or more new folders on the filesystem.',
        "example": 'mkdir -p ~/project',
        "related": ['rmdir', 'cd', 'ls'],
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
        "purpose": 'Print the current working directory.',
        "explanation": 'Displays the absolute pathname of your current location in the filesystem.',
        "example": 'pwd',
        "related": ['cd', 'ls'],
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
        "purpose": 'Search for files and directories in a directory hierarchy.',
        "explanation": 'Locates files based on name, size, type, or modification time.',
        "example": "find . -name '*.txt'",
        "related": ['grep', 'ls'],
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
        "purpose": 'Copy files and directories.',
        "explanation": 'Duplicates files or entire folders to a destination path.',
        "example": 'cp file.txt backup/',
        "related": ['mv', 'rm'],
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
        "purpose": 'Move or rename files and directories.',
        "explanation": 'Relocates files to a new path or renames them in place.',
        "example": 'mv old.txt new.txt',
        "related": ['cp', 'rm'],
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
        "purpose": 'Output the first part of files.',
        "explanation": 'Displays the beginning lines (default 10) of specified files.',
        "example": 'head -n 5 traffic.txt',
        "related": ['tail', 'cat', 'less'],
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
        "purpose": 'Output the last part of files.',
        "explanation": 'Displays the ending lines of files, useful for monitoring logs.',
        "example": 'tail -n 20 events.log',
        "related": ['head', 'cat', 'less'],
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
        "purpose": 'Print line, word, and byte counts for files.',
        "explanation": 'Counts lines, words, and characters in files or piped input.',
        "example": 'wc -l file.txt',
        "related": ['grep', 'sort'],
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
        "purpose": 'Display a line of text or write into a file.',
        "explanation": 'Prints arguments to standard output or redirects to a file.',
        "example": "echo 'Hello Linux' > greeting.txt",
        "related": ['cat', 'printf'],
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
        "purpose": 'Format and display the on-line manual pages.',
        "explanation": 'Shows reference documentation and flags for command-line tools.',
        "example": 'man ls',
        "related": ['help', 'hint', 'lookup'],
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
        "purpose": 'Quick in-game command reference lookup.',
        "explanation": 'Searches the built-in codex for documentation, flags, and examples.',
        "example": 'lookup grep',
        "related": ['man', 'help'],
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
        "purpose": 'Display available commands and assistance.',
        "explanation": 'Lists accessible tools, navigation options, and keyboard shortcuts.',
        "example": 'help',
        "related": ['man', 'hint'],
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
        "purpose": 'Request progressive clues for the current challenge.',
        "explanation": 'Provides hints (Concept -> Category -> Direction) to help solve tasks.',
        "example": 'hint',
        "related": ['help', 'man'],
        "syntax": "hint",
        "flags": {},
        "examples": [
            "hint",
        ],
        "combos": [
            "hint   # view progressive clue without HP penalty",
        ],
    },
    "tree": {
        "name": "tree",
        "description": "Display directory structure as a visual tree.",
        "purpose": "Shows folders and files in a visual hierarchy.",
        "syntax": "tree [options] [path]",
        "explanation": "Recursively displays files and subdirectories as an indented tree diagram.",
        "example": "tree ~",
        "flags": {
            "-L <level>": "Max display depth of the directory tree.",
            "-d": "List directories only.",
        },
        "examples": [
            "tree",
            "tree -L 2",
        ],
        "combos": [
            "tree ~   # visualize entire home folder structure",
        ],
        "related": ["ls", "find", "pwd"],
    },
    "whoami": {
        "name": "whoami",
        "description": "Print effective user name.",
        "purpose": "Displays current logged-in username.",
        "syntax": "whoami",
        "explanation": "Prints the username of the owner of the current terminal session.",
        "example": "whoami",
        "flags": {},
        "examples": [
            "whoami",
        ],
        "combos": [
            "whoami → pwd   # check identity and location",
        ],
        "related": ["pwd", "id"],
    },
    "rmdir": {
        "name": "rmdir",
        "description": "Remove empty directories.",
        "purpose": "Deletes an empty folder.",
        "syntax": "rmdir [options] <directory>",
        "explanation": "Removes the directory entry specified by directory, provided it is empty.",
        "example": "rmdir empty_dir",
        "flags": {
            "-p": "Remove directory and its ancestors if empty.",
        },
        "examples": [
            "rmdir old_folder",
        ],
        "combos": [
            "rmdir old_dir   # safely delete empty folder",
        ],
        "related": ["mkdir", "rm"],
    },
    "clear": {
        "name": "clear",
        "description": "Clear the terminal screen.",
        "purpose": "Cleans the current terminal window view.",
        "syntax": "clear",
        "explanation": "Clears your screen and scrollback view for a fresh clean slate.",
        "example": "clear",
        "flags": {},
        "examples": [
            "clear",
        ],
        "combos": [
            "clear → ls   # clear clutter and see what is nearby",
        ],
        "related": ["reset"],
    },
    "ps": {
        "name": "ps",
        "description": "Report a snapshot of the current processes.",
        "purpose": "Lists currently running system processes.",
        "syntax": "ps [options]",
        "explanation": "Displays information about active processes, their PIDs, and commands.",
        "example": "ps aux",
        "flags": {
            "aux": "Show all running processes in the system.",
            "-ef": "Standard full-format listing of processes.",
        },
        "examples": [
            "ps",
            "ps aux",
        ],
        "combos": [
            "ps aux | grep 'python'   # find a running program",
        ],
        "related": ["kill", "top"],
    },
    "kill": {
        "name": "kill",
        "description": "Send a signal to terminate a process.",
        "purpose": "Stops or terminates a running program by PID.",
        "syntax": "kill [options] <pid>",
        "explanation": "Sends a termination signal (default SIGTERM) to stop a process.",
        "example": "kill 1234",
        "flags": {
            "-9": "Force kill immediately (SIGKILL).",
            "-15": "Graceful termination request (SIGTERM).",
        },
        "examples": [
            "kill 1234",
            "kill -9 5678",
        ],
        "combos": [
            "ps aux | grep 'bug' → kill <pid>   # locate and terminate",
        ],
        "related": ["ps", "killall"],
    },
    "git": {
        "name": "git",
        "description": "Fast, scalable, distributed revision control system.",
        "purpose": "Tracks changes and versions of files in a project repository.",
        "syntax": "git <subcommand> [options]",
        "explanation": "Manages code repositories, history commits, branches, and collaboration.",
        "example": "git status",
        "flags": {
            "status": "Show modified files and branch state.",
            "diff": "Show changes between commits or working tree.",
            "log": "Show recent commit history.",
        },
        "examples": [
            "git status",
            "git log -n 5 --oneline",
            "git branch",
        ],
        "combos": [
            "git status → git add . → git commit   # stage and save changes",
        ],
        "related": ["diff", "patch"],
    },
    "vim": {
        "name": "vim",
        "description": "Vi IMproved, a programmer's text editor.",
        "purpose": "Modal terminal text editor for writing code and notes.",
        "syntax": "vim [file]",
        "explanation": "Keyboard-driven editor with Normal, Insert, and Command modes.",
        "example": "vim notes.txt",
        "flags": {},
        "examples": [
            "vim notes.txt",
            "vim script.sh",
        ],
        "combos": [
            "vim notes.txt   # edit text with modal motions",
        ],
        "related": ["nano", "cat"],
    },
    "nano": {
        "name": "nano",
        "description": "Simple, beginner-friendly terminal text editor.",
        "purpose": "Easy text editor with visible shortcut keys.",
        "syntax": "nano [file]",
        "explanation": "Straightforward editor with on-screen Ctrl shortcuts for beginners.",
        "example": "nano notes.txt",
        "flags": {},
        "examples": [
            "nano notes.txt",
        ],
        "combos": [
            "nano notes.txt   # quick edit with Ctrl+O and Ctrl+X",
        ],
        "related": ["vim", "cat"],
    },
    "diff": {
        "name": "diff",
        "description": "Compare files line by line.",
        "purpose": "Find differences between two files.",
        "syntax": "diff [options] <file1> <file2>",
        "explanation": "Compares two files line by line and highlights added, modified, or removed lines.",
        "example": "diff old.txt new.txt",
        "flags": {
            "-u": "Output unified context diff format.",
            "-y": "Output side-by-side comparison.",
        },
        "examples": [
            "diff file1.txt file2.txt",
            "diff -u original.py modified.py",
        ],
        "combos": [
            "diff -u file1 file2   # see unified code diff",
        ],
        "related": ["patch", "git"],
    },
    "tar": {
        "name": "tar",
        "description": "Tape archiver - package and extract archive files.",
        "purpose": "Creates and extracts compressed archive files (.tar.gz).",
        "syntax": "tar [options] [archive] [target...]",
        "explanation": "Bundles multiple files and folders into a single archive, optionally compressed.",
        "example": "tar -czvf backup.tar.gz project/",
        "flags": {
            "-czvf": "Create gzipped archive with verbose output.",
            "-xzvf": "Extract gzipped archive files.",
            "-tf": "List table of contents of an archive.",
        },
        "examples": [
            "tar -czvf archive.tar.gz docs/",
            "tar -xzvf archive.tar.gz",
        ],
        "combos": [
            "tar -czvf project.tar.gz .   # archive directory",
        ],
        "related": ["gzip", "zip"],
    },
    "curl": {
        "name": "curl",
        "description": "Transfer data from or to a server using web protocols.",
        "purpose": "Fetches web URLs and API endpoints from the command line.",
        "syntax": "curl [options] [url]",
        "explanation": "Sends HTTP/HTTPS network requests and downloads raw web responses.",
        "example": "curl https://icanhazip.com",
        "flags": {
            "-I": "Fetch HTTP response headers only.",
            "-O": "Save remote file with its original filename.",
            "-s": "Silent mode, hide progress meter.",
        },
        "examples": [
            "curl https://example.com",
            "curl -I https://example.com",
            "curl -O https://example.com/data.json",
        ],
        "combos": [
            "curl -s https://api.site/data | grep 'status'   # fetch and filter",
        ],
        "related": ["wget", "ssh"],
    },
    "wget": {
        "name": "wget",
        "description": "Non-interactive network downloader.",
        "purpose": "Downloads files directly from the web.",
        "syntax": "wget [options] [url]",
        "explanation": "Retrieves files via HTTP, HTTPS, and FTP in the background.",
        "example": "wget https://example.com/file.zip",
        "flags": {
            "-c": "Resume partially-downloaded file.",
            "-q": "Quiet mode with no screen output.",
        },
        "examples": [
            "wget https://example.com/installer.sh",
        ],
        "combos": [
            "wget url → tar -xzvf archive.tar.gz   # download and unpack",
        ],
        "related": ["curl"],
    },
    "df": {
        "name": "df",
        "description": "Report file system disk space usage.",
        "purpose": "Displays available and used disk space on mounted drives.",
        "syntax": "df [options]",
        "explanation": "Shows disk space usage breakdown for all mounted storage devices.",
        "example": "df -h",
        "flags": {
            "-h": "Human-readable sizes (GB, MB).",
            "-T": "Print filesystem type.",
        },
        "examples": [
            "df -h",
        ],
        "combos": [
            "df -h   # check free disk space",
        ],
        "related": ["du", "ls"],
    },
    "du": {
        "name": "du",
        "description": "Estimate file space usage.",
        "purpose": "Measures directory and file disk consumption.",
        "syntax": "du [options] [path]",
        "explanation": "Summarizes disk usage of directory trees and individual files.",
        "example": "du -sh ~/project",
        "flags": {
            "-s": "Display only a total summary for each argument.",
            "-h": "Print sizes in human-readable format.",
        },
        "examples": [
            "du -sh *",
            "du -h --max-depth=1",
        ],
        "combos": [
            "du -sh * | sort -h   # find largest folders",
        ],
        "related": ["df", "ls"],
    },
    "top": {
        "name": "top",
        "description": "Display Linux processes in an interactive real-time screen.",
        "purpose": "Monitors CPU, memory, and running system tasks.",
        "syntax": "top",
        "explanation": "Provides a live dynamic view of running system tasks and resource utilization.",
        "example": "top",
        "flags": {},
        "examples": [
            "top",
        ],
        "combos": [
            "top   # monitor active CPU and memory consumers",
        ],
        "related": ["ps", "kill"],
    },
    "uname": {
        "name": "uname",
        "description": "Print system information.",
        "purpose": "Displays Linux kernel version and hardware architecture.",
        "syntax": "uname [options]",
        "explanation": "Prints OS name, kernel release, and hardware architecture details.",
        "example": "uname -a",
        "flags": {
            "-a": "Print all system information in sequence.",
            "-r": "Print operating system kernel release.",
        },
        "examples": [
            "uname -a",
            "uname -r",
        ],
        "combos": [
            "uname -a   # check kernel and system architecture",
        ],
        "related": ["whoami", "hostname"],
    },
    "which": {
        "name": "which",
        "description": "Locate a command executable in the user's PATH.",
        "purpose": "Shows the exact path of a program binary.",
        "syntax": "which <command>",
        "explanation": "Searches directories listed in PATH and outputs the absolute path of the command executable.",
        "example": "which python3",
        "flags": {},
        "examples": [
            "which python3",
            "which git",
        ],
        "combos": [
            "which bash → ls -l /bin/bash   # find and inspect executable",
        ],
        "related": ["find", "type"],
    },
    "history": {
        "name": "history",
        "description": "GNU History Library command log.",
        "purpose": "Displays previous commands executed in the current session.",
        "syntax": "history",
        "explanation": "Shows the list of previously entered commands with their line numbers.",
        "example": "history",
        "flags": {},
        "examples": [
            "history",
            "history | grep 'git'",
        ],
        "combos": [
            "history | grep 'ssh'   # recall previous commands",
        ],
        "related": ["clear"],
    },
    "sed": {
        "name": "sed",
        "description": "Stream editor for filtering and transforming text.",
        "purpose": "Find and replace text patterns across files.",
        "syntax": "sed [options] 's/find/replace/g' <file>",
        "explanation": "Performs basic text transformations on an input stream or file.",
        "example": "sed 's/foo/bar/g' file.txt",
        "flags": {
            "-i": "Edit file in-place instead of printing to stdout.",
        },
        "examples": [
            "sed 's/old/new/g' notes.txt",
        ],
        "combos": [
            "cat file.txt | sed 's/foo/bar/g'   # pipeline replacement",
        ],
        "related": ["awk", "grep"],
    },
    "awk": {
        "name": "awk",
        "description": "Pattern scanning and text processing language.",
        "purpose": "Extracts columns and fields from formatted tabular text.",
        "syntax": "awk '{print $1, $2}' <file>",
        "explanation": "Processes text line by line and extracts specific whitespace-delimited columns.",
        "example": "awk '{print $1}' table.txt",
        "flags": {
            "-F": "Specify custom input field separator delimiter.",
        },
        "examples": [
            "awk '{print $1}' data.txt",
            "awk -F: '{print $1}' /etc/passwd",
        ],
        "combos": [
            "ps aux | awk '{print $2, $11}'   # print PID and process name",
        ],
        "related": ["sed", "grep", "cut"],
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


    def format_field_manual_entry(self, name: str) -> str:
        """Format a clean, context-aware Field Manual reference entry."""
        clean_name = str(name).strip().lower()
        entry = self.get_command(clean_name)
        if not entry:
            matches = self.search_commands(clean_name)
            if matches:
                suggestions = ", ".join(f"'{m['name']}'" for m in matches[:3])
                return f"No Field Manual entry for '{name}'. Did you mean: {suggestions}?\nType 'help' to see available commands.\n"
            return f"No Field Manual entry for '{name}'. Type 'help' to see available commands.\n"

        cmd_name = entry["name"]
        purpose = entry.get("purpose") or entry.get("description", "")
        syntax = entry.get("syntax", cmd_name)
        explanation = entry.get("explanation") or entry.get("description", "")
        example = entry.get("example") or (entry.get("examples", [""])[0] if entry.get("examples") else cmd_name)
        related_cmds = entry.get("related", [])
        if isinstance(related_cmds, list) and related_cmds:
            related_str = ", ".join(related_cmds)
        else:
            related_str = "None"

        lines = [
            f"{cmd_name} — {purpose}",
            "",
            "Purpose:",
            f"{purpose}",
            "",
            "Syntax:",
            f"{syntax}",
            "",
            "Explanation:",
            f"{explanation}",
            "",
            "Example:",
            f"{example}",
            "",
            "Related:",
            f"{related_str}",
        ]
        return "\n".join(lines)

    def get_contextual_commands(
        self,
        relevant_cmds: Optional[List[str]] = None,
        query: str = "",
        limit: int = 15,
    ) -> List[Dict[str, Any]]:
        """Return commands prioritizing current challenge relevance and matching query."""
        all_entries = self.list_commands()
        if query.strip():
            matched = self.search_commands(query.strip())
        else:
            matched = all_entries

        if not relevant_cmds:
            return matched[:limit]

        relevant_set = {r.strip().lower() for r in relevant_cmds if r}
        prio_list: List[Dict[str, Any]] = []
        other_list: List[Dict[str, Any]] = []

        for entry in matched:
            if entry["name"].lower() in relevant_set:
                prio_list.append(entry)
            else:
                other_list.append(entry)

        return (prio_list + other_list)[:limit]


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


def format_field_manual_entry(name: str) -> str:
    """Render a context-aware Field Manual reference entry from default codex."""
    return CODEX.format_field_manual_entry(name)


def get_contextual_commands(
    relevant_cmds: Optional[List[str]] = None,
    query: str = "",
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Return commands prioritizing current challenge relevance from default codex."""
    return CODEX.get_contextual_commands(relevant_cmds=relevant_cmds, query=query, limit=limit)


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
    "format_field_manual_entry",
    "get_contextual_commands",
]
