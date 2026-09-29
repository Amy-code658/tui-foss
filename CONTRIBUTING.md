# 🌱 Contributing to CyberShell (Byte's Linux Adventure)

Welcome! We are so excited you want to contribute to CyberShell! 

This project is built by **FOSS MEC** as a safe, gamified environment for beginners to learn Linux. Because our goal is to help beginners, **this repository is designed to be the perfect place for your very first open-source contribution!**

Don't worry if you've never contributed to open source before. This guide will walk you through everything step-by-step.

---

## 🛠️ Step 1: Setting Up Your Environment

You only need two things installed on your computer to work on CyberShell:
1. **Python 3.10+**
2. **[uv](https://docs.astral.sh/uv/)** (an incredibly fast Python package manager)

### Fork and Clone
1. Click the **Fork** button at the top right of this repository to create your own copy.
2. Clone your fork to your computer:
   ```bash
   git clone https://github.com/<YOUR-USERNAME>/tui-foss.git
   cd tui-foss
   ```

### Run the Game
Because we use `uv`, you don't even need to manually create a virtual environment! Just run:
```bash
uv run cybershell
```
*`uv` will automatically download the dependencies (like the Textual framework) and launch the game for you!*

---

## 💻 Step 2: Making Changes

Before making changes, create a new branch for your feature or bugfix:
```bash
git checkout -b my-new-feature
```

### Project Structure (Where to look)
* `src/cybershell/ui/textual_app.py` ➔ The graphical user interface and layouts.
* `src/cybershell/engine/commands.py` ➔ Where Linux commands (like `ls`, `cd`, `cat`) are simulated.
* `src/cybershell/game/quests.py` ➔ Where the 15 adventure levels and storylines are defined.
* `src/cybershell/tools/minigames/` ➔ The arcade games (Snake, Chmod Decoder, etc.).
* `src/cybershell/ui/theme.py` ➔ Want to add a new color theme? Look here!

### Testing your code
Before submitting your changes, make sure the game still works! We have a built-in test suite:
```bash
# Run the automated smoke tests
uv run python3 src/cybershell/run.py --smoke-test

# Run the unit tests
uv run python3 -m pytest tests/
```

---

## 🚀 Step 3: Submitting Your Contribution

1. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: added a cool new feature"
   ```
2. **Push to your fork:**
   ```bash
   git push origin my-new-feature
   ```
3. **Open a Pull Request (PR):**
   * Go to the original `Amy-code658/tui-foss` repository on GitHub.
   * You'll see a green button that says **"Compare & pull request"**. Click it!
   * Give your PR a descriptive title and explain what you changed.

---

## 🙋 Need Help?
If you get stuck, please don't hesitate to ask for help! You can open an issue with the tag `help wanted` or reach out to the FOSS MEC team. **No question is too simple.** 

Happy coding! 🚀
