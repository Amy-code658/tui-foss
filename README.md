# 🌱 Byte's Linux Adventure

> **A Fun, Chill, and Playful Terminal Game for Learning Real Linux Commands**

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

**Byte's Linux Adventure** is an interactive, bite-sized terminal game designed to make learning Linux welcoming, fun, and relaxing! 

Join your friendly guide **Byte** `(・ω・) 🌱` as you explore cozy directories, tidy up digital gardens, inspect scrolls, organize files, and master command-line superpowers.

### 🌟 Key Philosophy
* **Zero Damage, Zero Intimidation**: Typos and syntax mistakes deal **0 damage**. Friendly coaching messages guide you back on track.
* **15 Finite Levels**: Complete a clear, structured progression from basic `pwd` to multi-stage pipelines and redirects.
* **Progressive Hints**: Stuck? Ask `?` or `hint` for 3-tier clues (Concept ➔ Syntax ➔ Solution) with no penalties.
* **Friendly Mascots**: Learn alongside Byte `(・ω・)`, Fern `(◕‿◕)`, Penny `(•ᴗ•)`, and Nova `(★ω★)`.
* **Full-screen TUI**: Built with Textual for responsive panels, keyboard and mouse navigation, and theme-aware rendering.

---

## 🗺️ The 15-Level Adventure Journey

| Level | Topic | Key Commands & Skills |
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
* Textual is installed automatically by `uv run` or from `requirements.txt`.

### Option 1: Run via `uv` (Recommended)
```bash
# Clone the repository
git clone https://github.com/Amy-code658/tui-foss.git
cd tui-foss

# Run the game directly
uv run cybershell
```

**Helpful launcher flags:**
```bash
uv run cybershell --name Fern          # Start with a custom explorer name
uv run cybershell --level 0            # Jump directly to a specific level
uv run cybershell --demo               # Run a visual screen tour
uv run cybershell --smoke-test         # Run diagnostics & test suite
```

### Option 2: Run via Standard Python
```bash
# Launch the main game directly
python3 src/cybershell/run.py
```

---

## 🎮 How to Play

### 🧭 Navigation & Commands
When exploring in the terminal:
* **Run a command**: Type your command (e.g., `pwd`, `ls`, `cat notes.txt`) and press **Enter**.
* **Get a hint**: Type `?` or `hint` to see friendly progressive clues with 0 XP deduction.
* **Understand syntax**: Type `explain` or `explain <command>` for an interactive syntax breakdown.
* **View Adventure Map**: Type `map` to view your 15-level roadmap and progress.
* **Main Menu**: Type `menu` or `0` to return to the destination hub.

### 🏠 Menu Destinations
From the Main Directory, enter a number to switch stations:
* `[1]` **Adventure Playground** — Active terminal, task card, and coaching ticker
* `[2]` **Adventure Map** — Visual 15-level progress map
* `[3]` **Command Guide** — Handbook with explanations and examples for every command
* `[4]` **Backpack & Badges** — Collected items and unlocked explorer achievements
* `[5]` **Permissions Puzzle** — Practice `chmod` math with an interactive mini-puzzle
* `[6]` **Field Manual & Rules** — Friendly instructions and mascot advice
* `[0]` **Exit Adventure** — Save progress and return to the system

---

## 🧪 Testing & Code Quality

Run the comprehensive automated test suite (140 tests):
```bash
python3 -m unittest discover -s tests
```

Run static analysis:
```bash
python3 src/cybershell/run.py --smoke-test
```

---

## 📄 License
MIT License. Created with ❤️ for beginners everywhere.
