# 🌱 Byte's Linux Adventure

> **A Fun, Chill, and Modern Terminal Game for Learning Real Linux Commands**

```text
  ____             _           _      _                    _                    
 | __ ) _   _   __| |_  ___   | |    (_)_ __  _   ___  __ / \   __| |_   _____  
 |  _ \| | | | / _` \ \/ / _ \ | |    | | '_ \| | | \ \/ // _ \ / _` \ \ / / _ \ 
 | |_) | |_| || (_| |>  <  __/ | |___ | | | | | |_| |>  </ ___ \ (_| |\ V /  __/ 
 |____/ \__, | \__,_/_/\_\___| |_____||_|_| |_|\__,_/_/\_/_/   \_\__,_| \_/ \___|
        |___/                                                                    
```

---

## 🍃 Overview

**Byte's Linux Adventure** (CyberShell) is an interactive, bite-sized terminal game designed to make learning Linux welcoming, hands-on, and fun! 

Guided by **Byte** `(・ω・) 🌱` and Tux the penguin, you explore directories, inspect scrolls, organize files, connect shell pipelines, and master command-line superpowers inside a safe, simulated Linux environment.

### 🌟 Key Philosophy & Highlights
* **Zero Damage, Zero Intimidation**: Typos and syntax mistakes deal **0 damage**. Friendly coaching messages guide you back on track.
* **15 Progressive Levels**: Structured step-by-step curriculum from basic `pwd` and `ls` to multi-stage pipelines (`|`), redirects (`>`, `<`), and search tools (`find`, `grep`).
* **Progressive 3-Tier Hints**: Stuck? Type `?` or `hint` for tiered guidance (Concept ➔ Syntax ➔ Solution) with zero penalties.
* **Modern Full-Screen Textual TUI**: Built with [Textual](https://textual.textualize.io/) featuring a Neovim-inspired aesthetic, responsive layout breakpoints, and theme-aware rendering.
* **Authentic Terminal Feel**: Live inline editable terminal with command history, Tab-completion, and unified scrolling output.
* **Interactive Minigames & Tools**: Real-time Terminal Snake, interactive `chmod` permissions lab, and instant command palette.

---

## ✨ Modern TUI Features

The latest release introduces a modernized full-screen terminal user interface:

* **Real Terminal-Style Inline Prompt**: Output and editable command input live on a single unified scrolling surface with a block cursor, Up/Down history browsing, and Tab completion for commands and virtual filesystem paths.
* **Live Command Guide Search**: The documentation pane filters commands and guides live as you type—no Enter key required!
* **Fast Command Palette (`Ctrl+Space` / `Ctrl+P` / `:cmd`)**: Centered overlay to fuzzy-search actions and jump directly to challenges, settings, minigames, or themes.
* **Full Keyboard Navigation**: Arrow keys (`↑`, `↓`, `←`, `→`) navigate menus seamlessly on the home screen; `Esc` works reliably across all screens and dialogs.
* **Real-Time Terminal Snake**: Integrated minigame running on its own frame clock with real-time steering (`h/j/k/l`, `w/a/s/d`, or arrow keys).
* **Responsive Breakpoints**: Adapts cleanly across `compact` (<65 cols), `narrow` (<90 cols), and `short` (<30 rows) terminal dimensions.
* **Graceful Fallback**: Automatically launches the rich Textual TUI in interactive terminals, with an ANSI engine loop for headless pipes and automated tests.

---

## 🗺️ The 15-Level Adventure Journey

| Level | Topic | Key Commands & Concepts |
| :---: | :--- | :--- |
| **1** | **Look Around** | `pwd`, `ls` — See where you are and list items |
| **2** | **Step Inside** | `cd`, `cd ..` — Move between rooms and folders |
| **3** | **Peeking Inside Files** | `cat`, `less` — Read notes, scrolls, and recipes |
| **4** | **Hidden Treasures** | `ls -a`, `ls -la` — Discover hidden dotfiles (`.secret_recipe`) |
| **5** | **Lost & Found** | `find` — Search directory trees by name |
| **6** | **Word Detective** | `grep` — Find matching words and patterns in text |
| **7** | **Moving Day** | `cp`, `mv` — Copy files and move/rename items |
| **8** | **Plant & Tidy** | `mkdir`, `touch`, `rm` — Create directories and clean up |
| **9** | **Secret Handshakes** | `chmod` — Adjust read, write, and execute permissions |
| **10** | **Counting & Sorting** | `wc -l`, `sort` — Count lines and organize lists |
| **11** | **The Pipeline Garden** | `\|` — Connect commands together like building blocks |
| **12** | **Writing to Journals** | `>`, `>>` — Save and append outputs into files |
| **13** | **Reading From Scrolls** | `<` — Feed files into command inputs |
| **14** | **Detective Work** | `find ... \| xargs grep` or `grep` pipelines |
| **15** | **Grand Master Explorer** | Combine navigation, searching, and piping for your victory badge! |

---

## 🚀 Quick Start & Installation

### Requirements
* **Python 3.11+** (Linux, macOS, or Windows)
* Dependencies (`textual>=8.2.8`) are installed automatically when running via `uv` or `pip`.

### Option 1: Run via `uv` (Recommended)
[`uv`](https://github.com/astral-sh/uv) is an extremely fast Python package manager:
```bash
# Clone the repository
git clone https://github.com/Amy-code658/tui-foss.git
cd tui-foss

# Run the game directly (uv sets up the virtual environment automatically)
uv run cybershell
```

**Helpful launcher flags:**
```bash
uv run cybershell --name "Byte"       # Start with a custom explorer name
uv run cybershell --sector 0          # Jump directly to a specific level (0-14)
uv run cybershell --demo              # Run a visual screen tour
uv run cybershell --smoke-test        # Run pre-flight diagnostics & test suite
```

### Option 2: Run via Standard Python
```bash
# Set up a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch the game directly
python3 src/cybershell/run.py
```

---

## 🎮 How to Play

### ⌨️ Keybindings & Shortcuts

| Shortcut | Context | Action |
| :--- | :--- | :--- |
| `Ctrl+Space` / `Ctrl+P` | Anywhere in TUI | Open the fuzzy **Command Palette** |
| `Ctrl+L` | Lesson Screen | Focus the **Live Docs Search** input |
| `Esc` | Anywhere | Return to previous screen, exit search, or cancel |
| `Ctrl+Q` | Anywhere in TUI | Quit the application |
| `Tab` | Terminal Prompt | Autocomplete commands and file paths |
| `↑` / `↓` | Terminal Prompt | Cycle through command history |
| `↑` / `↓` / `←` / `→` | Home Screen | Select menu destinations |
| `h` / `j` / `k` / `l` or Arrows | Snake Minigame | Steer the snake in real time (`q` to quit) |

### 🧭 In-Game Commands
Type these directly into the terminal prompt during an adventure:
* **Execute commands**: `pwd`, `ls -la`, `cd <dir>`, `cat <file>`, `mkdir <dir>`, etc.
* **Get progressive hints**: Type `?` or `hint` for 3-tier clues with 0 XP penalty.
* **Interactive explanations**: Type `explain` or `explain <cmd>` for a breakdown of syntax and flags.
* **View Adventure Map**: Type `map` to inspect the 15-level progress map.
* **Open Command Palette**: Type `:cmd`, `:menu`, or `palette`.
* **Switch Themes**: Type `:theme` to cycle through available color schemes.
* **Launch Minigames**: Type `:games` to enter the arcade hub (Terminal Snake, Chmod lockpick).
* **Return to Main Hub**: Type `menu` or `0`.

### 🏠 Menu Destinations
From the Home Hub, select using the arrow keys or type the corresponding number:
* `[1]` **Adventure Playground** — Active terminal, task card, quest objective, and coaching ticker
* `[2]` **Adventure Map** — Visual 15-level progress roadmap
* `[3]` **Command Guide** — Handbook with interactive fuzzy search and usage examples
* `[4]` **Backpack & Badges** — Collected inventory items and unlocked explorer achievements
* `[5]` **Permissions Puzzle** — Interactive `chmod` octal/symbolic calculation mini-puzzle
* `[6]` **Arcade Minigames** — Real-time Terminal Snake and unlockable mini-challenges
* `[7]` **Field Manual & Rules** — Friendly instructions, concepts, and mascot advice
* `[0]` **Exit Adventure** — Save player progress and return to your system shell

---

## 👥 Contributors & Team Credits

CyberShell is collaboratively built with dedicated modular ownership across the team:

| Contributor | Batch / Dept | Core Role & Contributions |
| :--- | :---: | :--- |
| **Amy** | `CU 29` | **Project Lead & Master Integrator** — Architecture, packaging (`pyproject.toml`, `requirements.txt`), launcher loop, contract definitions, and integration test suites. |
| **Rudra** | `CSA 29` | **VFS Architect** — Virtual Filesystem (`vfs.py`), tree node data structures (`node.py`), file permissions, path resolution, and filesystem tests. |
| **Aswin** | `CU 29` | **Game State & Quest Engine** — Player statistics tracking (`state.py`), dynamic quest evaluation (`evaluator.py`), and progression logic. |
| **Akash** | `CU 29` | **Hacker Codex & Tooling** — Linux command reference (`codex.py`), interactive `chmod` calculator, lockpicking minigame, and map topology. |
| **Poornendhu** | `CSA 29` | **TUI Layout & Frame Renderer** — Double-header system, split panels, responsive layout boxes, OverTheWire quest cards, and frame rendering (`renderer.py`). |
| **Aniketh** | `CU 29` | **Shell Pipeline & Interpreter** — Custom `Interpreter`, command tokenization, piping (`\|`), redirection (`>`, `<`), and pipeline execution. |
| **Gautham** | `ME 29` | **ASCII Art & Terminal FX** — Larry Ewing Tux artwork, animated welcome banners, NPC companion portraits, and terminal visual effects (`ascii_art.py`). |
| **Neha** | `CSB 29` | **Storyline & Challenge Levels** — 15-level adventure design (`quests.py`), level dialogues, quest objective sets, and game progression tests. |
| **Dijith** | `CU 28` | **Modern Textual TUI & UX** — Full-screen Textual application (`textual_app.py`), true inline terminal prompt, live docs search, keyboard navigation, and real-time Snake. |

---

## 🧪 Testing & Code Quality

The codebase is backed by a comprehensive automated test suite (216 tests):

```bash
# Run unit and integration tests via unittest
python3 -m unittest discover -s tests

# Or run the built-in smoke test runner
python3 src/cybershell/run.py --smoke-test
```

---

## 📄 License
MIT License. Created with ❤️ for learners and terminal explorers everywhere.
