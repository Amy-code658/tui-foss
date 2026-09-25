# Changelog — `dijith` branch

## Summary

Work on this branch introduces a **full-screen Textual TUI front end** for the
existing CyberShell game engine, then makes that UI behave like a real terminal:
live search everywhere, an inline shell prompt, working arrow/ESC navigation,
and a real-time Snake game.

All changes are additive to the engine. The original blocking/ANSI engine loop
is preserved and still used when there is no interactive TTY, so the game keeps
working in pipes, smoke tests, and unknown environments.

---

## Commits compared with `feature/neovim-modern-tui`

Base (`merge-base`): `9b21d79`
Branch commits not on `feature/neovim-modern-tui` (newest first):

| Commit | Type | Summary |
| --- | --- | --- |
| `b7c9c4b` | fix | ESC works from every screen; onboarding default; test env |
| `bd2fd84` | fix | True inline terminal prompt (replaces Textual `Input`) |
| `74fedfe` | feat | Live search, inline shell prompt, arrow nav, real-time Snake |
| `c76181d` | chore/feat | Snapshot: Textual UI front end + engine `ui=` hooks |

### Files changed vs. `feature/neovim-modern-tui`

```text
 README.md                               |   6 +-
 pyproject.toml                          |  11 +-
 requirements.txt                        |   7 +-
 src/cybershell/run.py                   |  97 ++-
 src/cybershell/tools/minigames/hub.py   |   6 +-
 src/cybershell/tools/minigames/snake.py | 107 ++-
 src/cybershell/ui/renderer.py           |   1 +
 src/cybershell/ui/textual_app.py        | 1219 +++++++++++++++++++++
 tests/test_modern_features.py           |  35 +-
 uv.lock                                 | 489 +++----
 10 files changed, 1539 insertions(+), 439 deletions(-)
```

---

## Features

### 1. Full-screen Textual TUI front end (`src/cybershell/ui/textual_app.py`)

New module that adapts the engine's existing `input()`/`stdout` boundary to a
responsive full-screen UI, so the game engine stays synchronous and owns state.

- **Engine bridge** — replaces `builtins.input` with a queue-backed bridge and
  captures engine `stdout` into the UI, so the original game loop runs unmodified
  on a worker thread.
- **Views**: onboarding/home, lesson (shell), and legacy (feature screens).
- **Theme integration** — all game themes registered as Textual themes; the
  active theme drives the whole app.
- **Responsive breakpoints** — `narrow` (<90 cols), `compact` (<65), and
  `short` (<30 rows) layout classes.
- **Tux pixel art + wordmark** rendered from the active palette.
- **Auto-launch**: `run_textual()` starts automatically when stdin/stdout are
  TTYs; otherwise the original ANSI loop runs.

### 2. Live search — no Enter required (`74fedfe`)

- **Docs pane filters as you type.** Typing in the search box re-renders the
  command guide live using the engine's existing fuzzy matcher; pressing Enter
  is no longer needed to see results.
- **Native command palette.** `Ctrl+Space`, `Ctrl+P`, or `:cmd` opens a centered
  overlay (`SearchPalette`) that fuzzy-filters actions as you type and runs the
  highlighted entry with Enter. Replaces the old two-step palette that required
  a full keyword and an extra confirmation.
- Palette supports ↑/↓, PageUp/PageDown, Esc-to-close, and a no-match state.

### 3. Real terminal-style inline prompt (`bd2fd84`)

Replaced Textual's `Input` widget (which is always pinned to its own row) with
`TerminalInput`, a single scrollable surface that holds **output and the live
editable prompt line together** — the real terminal model.

- Prompt sits directly under the last output and scrolls with it.
- Inline editing with a block cursor: insert, backspace, Delete, Left/Right,
  Home/End (`Ctrl+A`/`Ctrl+E`).
- Up/Down command history.
- Enter echoes the command and submits it to the engine.
- Tab completion for commands and virtual-filesystem paths (unique prefix
  expands; multiple matches are listed).
- Only the prompt line repaints as you type.

### 4. Keyboard navigation (`74fedfe`)

- **Home menu**: ↑/↓ (and ←/→) move the selection; the highlighted item is
  visibly marked; Enter activates it. Previously the highlighted item could not
  be moved and Enter did nothing useful.
- **ESC works everywhere** (`b7c9c4b`): the engine's `wait_for_enter_or_esc`
  used to take a raw `termios` branch and block, because under the UI `stdin` is
  still a TTY. The bridge is now marked (`_cybershell_bridged`) so the helper
  reads through the UI queue instead. Verified returning `"esc"` on Esc and
  `"enter"` on Enter.

### 5. Real-time Snake (`74fedfe`, `bd2fd84`)

The game previously advanced only on Enter, and under the TUI its keystrokes
went to the shell input instead of the game, so the snake immediately hit a
wall.

- Snake now runs on its **own real-time clock** and is steered with
  `h/j/k/l`, `w/a/s/d`, or the arrow keys; `q` quits. Enter is no longer needed.
- Game logic split into `turn()` (steer) and `_advance()` (tick); classic
  tail-follow no longer counts as a self-collision.
- Added a `KeyboardGame` Textual screen so the app delivers keys to the game and
  only the board repaints — no full-screen rerender per tick.
- Thread-safe handoff: the engine thread blocks while the app runs the game
  screen and receives the final score (`CyberShellTUI.play_snake`).
- Non-TTY runs auto-advance and terminate, so smoke tests still pass.

### 6. Engine integration hooks (`c76181d`)

- `interactive_game_loop(..., ui=None)` and `prompt_player_onboarding(..., ui=None)`
  gain an optional UI handle.
- All terminal writes in the lesson loop are skipped when a UI is present; state
  is pushed to the UI instead (logs, quest, docs, pet, progress, cwd, VFS).
- `view_minigames_hub(..., ui=None)` routes Snake through the UI when available.
- New `:settings` command handler for the palette's settings action.

### 7. Fixes and housekeeping

- **Onboarding default** (`b7c9c4b`): a supplied name is honoured on a
  non-interactive stream instead of being silently replaced by `"Explorer"`.
- **Test environment**: `pexpect` declared in `pyproject.toml` /
  `requirements.txt`; the readline NUL-macro pty test now skips when the backend
  (libedit) cannot expand it — the TUI binds `Ctrl+Space` directly.

---

## Verification

```bash
.venv/bin/python -m pytest -q tests/          # 215 passed, 1 skipped
.venv/bin/python src/cybershell/run.py --smoke-test   # 216 tests, OK
```

UI behaviour was validated with Textual's test pilot:

- live docs filtering while typing (no Enter);
- command palette narrowing (`10 → 3` matches for `prog`);
- home arrow navigation moving and marking the selection;
- inline prompt editing, Tab completion (`pw` → `pwd `), Enter submission;
- Snake steering (`k` changed direction), auto-advance, and quit-to-score;
- `wait_for_enter_or_esc` returning `"esc"`/`"enter"` under a TTY with the bridge.

---

## Known limitations

- The readline `Ctrl+Space` pty test is skipped on libedit backends; this is a
  platform limitation of that legacy path, not the TUI (which handles the key
  itself).
- `ruff` reports 3 pre-existing duplicate-import warnings in `run.py`, present
  before this work.
- The Snake fix is verified by automated testing; live visual confirmation in the
  TUI is recommended.
