"""Textual presentation layer for the existing CyberShell game loop.

The game engine remains synchronous and owns all game state.  This module adapts
its existing input/output boundary to a full-screen, responsive Textual UI.

Interaction model (live-first):

* The docs pane filters as you type - no Enter required.
* ``Ctrl+Space`` / ``Ctrl+P`` / ``:cmd`` opens a centered command palette that
  fuzzy-matches live and runs the highlighted entry with Enter.
* The shell prompt shows command/file matches live and Tab-completes them.
* The home menu is navigable with the arrow keys.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import posixpath
import queue
import re
import threading
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.theme import Theme as TextualTheme
from textual.widgets import Button, Footer, Header, Input, OptionList, ProgressBar, RichLog, Static
from textual.widgets.option_list import Option

from cybershell.ui.search import fuzzy_score, fuzzy_search_commands
from cybershell.ui.theme import THEMES, Theme, get_active_theme

# Commands / aliases that should open the palette rather than hit the shell.
_COMMAND_TRIGGERS = {
    ":cmd", ":menu", ":space", ":center", ":p", "cmd", "palette",
    "ctrl+space", "ctrl-space", "ctrl space", "<c-space>", "^space",
}


class _OutputBridge(io.TextIOBase):
    """Capture legacy feature screens and show their output in the app frame."""

    def __init__(self, app: "CyberShellTUI") -> None:
        self.app = app
        self._pending = ""

    def write(self, value: str) -> int:
        if not value:
            return 0
        if "\x1b[H\x1b[J" in value or "\x1b[2J" in value:
            self.app.post_legacy_clear()
        self._pending += value
        while "\n" in self._pending:
            line, self._pending = self._pending.split("\n", 1)
            clean = _legacy_ansi(line.rstrip("\r"))
            if _clean_terminal_controls(clean).strip() or self.app._input_mode == "legacy":
                self.app.post_legacy_output(clean)
        return len(value)

    def flush(self) -> None:
        if self._pending:
            clean = _legacy_ansi(self._pending)
            self._pending = ""
            if _clean_terminal_controls(clean).strip():
                self.app.post_legacy_output(clean)

    @property
    def encoding(self) -> str:
        return "utf-8"


_ANSI_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def _clean_terminal_controls(value: str) -> str:
    value = _ANSI_RE.sub("", value)
    return "".join(char for char in value if char == "\t" or ord(char) >= 32)


def _legacy_ansi(value: str) -> str:
    """Keep SGR colors while discarding cursor movement and screen controls."""
    sgr = _ANSI_RE.sub(
        lambda match: match.group(0) if match.group(0).startswith("\x1b[") and match.group(0).endswith("m") else "",
        value,
    )
    return "".join(char for char in sgr if char in ("\x1b", "\t") or ord(char) >= 32)


def _pixel_penguin(theme: Theme) -> Text:
    """Draw Tux in colored half-block cells, using the active game palette."""
    rows = [
        ".....OOOOOO.....",
        "....OBBBBBBO....",
        "...OBBBBBBBBO...",
        "..OBBWWBBWWBBO..",
        "..OBBWKBBKWBBO..",
        "..OBBBBBYYBBBO..",
        "..OBBBBYYYYBBO..",
        "..OBBBBBBBBBBO..",
        ".OBBBBWWWWBBBBO.",
        "OBBBBWWWWWWBBBBO",
        "OBBBBWWWWWWBBBBO",
        "OBBBBWWWWWWBBBBO",
        ".OBBBBWWWWBBBBO.",
        "..OBBBBBBBBBBO..",
        "...OBBBBBBBBO...",
        "..YYYY....YYYY..",
        ".YYYYYY..YYYYYY.",
    ]
    colors = {
        ".": theme.bg_dark,
        "O": theme.border_focus,
        "B": theme.surface_light,
        "W": theme.white,
        "K": theme.bg_dark,
        "Y": theme.yellow,
    }
    width = max(map(len, rows))
    rows = [row.center(width, ".") for row in rows]
    rows.append("." * width)
    art = Text()
    for row in range(0, len(rows), 2):
        for top, bottom in zip(rows[row], rows[row + 1]):
            if top == bottom == ".":
                art.append(" ")
            elif top == bottom:
                art.append("█", style=colors[top])
            else:
                art.append("▀", style=f"{colors[top]} on {colors[bottom]}")
        if row < len(rows) - 2:
            art.append("\n")
    return art


def _big_linux(theme: Theme) -> Text:
    """Five-row block lettering for the welcome screen."""
    letters = {
        "L": ("█    ", "█    ", "█    ", "█    ", "█████"),
        "I": ("█████", "  █  ", "  █  ", "  █  ", "█████"),
        "N": ("█   █", "██  █", "█ █ █", "█  ██", "█   █"),
        "U": ("█   █", "█   █", "█   █", "█   █", "█████"),
        "X": ("█   █", " █ █ ", "  █  ", " █ █ ", "█   █"),
    }
    art = Text()
    for row in range(5):
        art.append("  ".join(letters[letter][row] for letter in "LINUX"), style=f"bold {theme.cyan}")
        if row < 4:
            art.append("\n")
    return art


class TerminalInput(Static):
    """A single scrollable terminal surface: output plus the live prompt line.

    Unlike a separate ``Input`` widget (which is always pinned to its own row),
    this keeps the editable prompt in the same text stream as the output, so it
    scrolls away naturally like a real terminal.
    """

    can_focus = True

    def __init__(self, prompt: str = "❯", **kwargs: Any) -> None:
        super().__init__("", **kwargs)
        self._lines: list[Text] = []
        self._buffer = ""
        self._cursor = 0
        self._prompt = prompt
        self._prompt_style = "green"
        self._history: list[str] = []
        self._history_index: Optional[int] = None
        # Wired by the host app once the widget is mounted.
        self.on_submit: Optional[Any] = None
        self.on_complete: Optional[Any] = None

    # -- output ------------------------------------------------------------

    def add_line(self, line: Any) -> None:
        """Append an output line (Text or str) above the live prompt."""
        self._lines.append(line if isinstance(line, Text) else Text.from_ansi(str(line)))
        self._redraw()

    def clear_output(self) -> None:
        self._lines.clear()
        self._redraw()

    def set_prompt(self, prompt: str) -> None:
        self._prompt = prompt
        self._redraw()

    # -- editable prompt ---------------------------------------------------

    @property
    def value(self) -> str:
        return self._buffer

    def reset_value(self) -> None:
        self._buffer = ""
        self._cursor = 0
        self._history_index = None
        self._redraw()

    def _redraw(self) -> None:
        text = Text()
        for line in self._lines:
            text.append_text(line)
            text.append("\n")
        text.append_text(self._render_input())
        text.append("\n")
        self.update(text)

    def _render_input(self) -> Text:
        rendered = Text()
        rendered.append(f"{self._prompt} ", style=f"bold {self._prompt_style}")
        value = self._buffer
        cursor = min(self._cursor, len(value))
        rendered.append(value[:cursor], style=self._prompt_style)
        rendered.append(value[cursor: cursor + 1] or " ", style="reverse")
        rendered.append(value[cursor + 1:], style=self._prompt_style)
        return rendered

    # -- key handling ------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        key = event.key
        if key == "enter":
            command = self._buffer
            if command.strip():
                self._history.append(command)
            self._history_index = None
            self._submit(command)
        elif key == "backspace":
            if self._cursor > 0:
                self._buffer = self._buffer[: self._cursor - 1] + self._buffer[self._cursor:]
                self._cursor -= 1
        elif key == "delete":
            self._buffer = self._buffer[: self._cursor] + self._buffer[self._cursor + 1:]
        elif key == "left":
            self._cursor = max(0, self._cursor - 1)
        elif key == "right":
            self._cursor = min(len(self._buffer), self._cursor + 1)
        elif key == "home" or key == "ctrl+a":
            self._cursor = 0
        elif key == "end" or key == "ctrl+e":
            self._cursor = len(self._buffer)
        elif key == "up":
            self._history_move(-1)
        elif key == "down":
            self._history_move(1)
        elif key == "tab":
            self._complete()
        elif key == "space":
            self._insert(" ")
        elif len(key) == 1 and key.isprintable():
            self._insert(key)
        else:
            return
        self._redraw()
        event.stop()
        event.prevent_default()

    def _insert(self, char: str) -> None:
        self._buffer = self._buffer[: self._cursor] + char + self._buffer[self._cursor:]
        self._cursor += 1

    def _history_move(self, delta: int) -> None:
        if not self._history:
            return
        if self._history_index is None:
            if delta < 0:
                self._history_index = len(self._history) - 1
            else:
                return
        else:
            self._history_index += delta
            self._history_index = max(0, min(self._history_index, len(self._history) - 1))
        self._buffer = self._history[self._history_index]
        self._cursor = len(self._buffer)

    # -- overridable hooks -------------------------------------------------

    def _submit(self, command: str) -> None:
        if self.on_submit is not None:
            self.on_submit(command)
        self.reset_value()

    def _complete(self) -> None:
        if self.on_complete is not None:
            self.on_complete()


@dataclass
class _PaletteItem:
    """One selectable row inside :class:`SearchPalette`."""

    id: str
    label: str
    detail: str = ""
    keywords: str = ""

    def searchable(self) -> str:
        return f"{self.label} {self.detail} {self.keywords}".strip()


class SearchPalette(ModalScreen[Optional[str]]):
    """Centered overlay that fuzzy-filters rows live as the user types."""

    BINDINGS = [("escape", "dismiss_palette", "Close")]

    CSS = """
    SearchPalette { align: center middle; background: $background 60%; }
    #palette-box {
        width: 78;
        max-width: 96%;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    #palette-title { color: $primary; text-style: bold; height: 1; }
    #palette-input {
        height: 1;
        border: none;
        border-left: thick $primary;
        background: $panel;
        padding: 0 1;
        margin: 1 0;
    }
    #palette-input:focus { border: none; border-left: thick $primary; }
    #palette-list { height: auto; max-height: 16; background: transparent; }
    #palette-hint { color: $text-muted; height: 1; margin-top: 1; }
    """

    def __init__(
        self,
        title: str,
        items: Iterable[_PaletteItem],
        placeholder: str = "Search…",
        hint: str = "Type to filter  ·  ↑/↓ choose  ·  Enter run  ·  Esc close",
    ) -> None:
        super().__init__()
        self._title = title
        self._items: list[_PaletteItem] = list(items)
        self._placeholder = placeholder
        self._hint = hint

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-box"):
            yield Static(self._title, id="palette-title")
            yield Input(placeholder=self._placeholder, id="palette-input")
            yield OptionList(id="palette-list")
            yield Static(self._hint, id="palette-hint")

    def on_mount(self) -> None:
        self._refresh("")
        self.query_one("#palette-input", Input).focus()

    def _matches(self, query: str) -> list[_PaletteItem]:
        query = (query or "").strip()
        if not query:
            return self._items
        scored: list[tuple[int, str, _PaletteItem]] = []
        for item in self._items:
            matched, score = fuzzy_score(query, item.searchable())
            if matched:
                scored.append((score, item.label, item))
        scored.sort(key=lambda entry: (-entry[0], entry[1]))
        return [item for _, _, item in scored]

    def _refresh(self, query: str) -> None:
        listing = self.query_one("#palette-list", OptionList)
        listing.clear_options()
        matches = self._matches(query)
        if not matches:
            listing.add_option(Option("  No matching command", id="__none__", disabled=True))
            return
        for item in matches:
            label = f"{item.label}   {item.detail}" if item.detail else item.label
            listing.add_option(Option(label, id=item.id))
        listing.highlighted = 0

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "palette-input":
            self._refresh(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "palette-input":
            self._choose_highlighted()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        self.dismiss(event.option.id)

    def on_key(self, event: events.Key) -> None:
        listing = self.query_one("#palette-list", OptionList)
        if event.key == "up":
            listing.action_cursor_up()
        elif event.key == "down":
            listing.action_cursor_down()
        elif event.key == "pageup":
            for _ in range(5):
                listing.action_cursor_up()
        elif event.key == "pagedown":
            for _ in range(5):
                listing.action_cursor_down()
        else:
            return
        event.stop()
        event.prevent_default()

    def _choose_highlighted(self) -> None:
        option = self.query_one("#palette-list", OptionList).highlighted_option
        if option is None or option.id in (None, "__none__"):
            return
        self.dismiss(str(option.id))

    def action_dismiss_palette(self) -> None:
        self.dismiss(None)


class KeyboardGame(ModalScreen[Optional[int]]):
    """Play a turn/frame based minigame with real keyboard input.

    The game runs on its own timer and only the board widget is refreshed, so
    there is no full-screen rerender per tick. Returns the final score.
    """

    BINDINGS = [("q", "game_quit", "Quit"), ("escape", "game_quit", "Quit")]

    CSS = """
    KeyboardGame { align: center middle; background: $background 70%; }
    #game-box {
        width: auto;
        max-width: 96%;
        height: auto;
        max-height: 95%;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    #game-title { color: $primary; text-style: bold; height: 1; }
    #game-board { height: auto; width: auto; margin: 1 0; }
    #game-status { color: $text-muted; height: 1; }
    """

    TICK = 0.16

    def __init__(self) -> None:
        super().__init__()
        self._timer = None

    def compose(self) -> ComposeResult:
        from cybershell.tools.minigames.snake import TerminalSnake

        self.game = TerminalSnake(width=24, height=12, target_goals=8)
        with Vertical(id="game-box"):
            yield Static("TERMINAL SNAKE", id="game-title")
            yield Static(self._board_text(), id="game-board")
            yield Static("Steer h/j/k/l or w/a/s/d or arrows  ·  q quit", id="game-status")

    def on_mount(self) -> None:
        self._timer = self.set_interval(self.TICK, self._tick)

    def _board_text(self) -> Text:
        # Reuse the game's own ASCII board but strip ANSI; colour via Rich.
        raw = self.game.render(styled=False)
        return Text(raw, style=self._theme_text())

    def _theme_text(self) -> str:
        try:
            return self.app._theme.text  # type: ignore[attr-defined]
        except Exception:
            return "white"

    def _refresh_board(self) -> None:
        self.query_one("#game-board", Static).update(self._board_text())

    def _tick(self) -> None:
        if self.game.game_over:
            return
        alive = self.game.step("")
        self._refresh_board()
        if not alive:
            self._finish()

    def on_key(self, event: events.Key) -> None:
        if self.game.game_over:
            return
        if event.key in ("up", "k", "w"):
            self.game.turn("k")
        elif event.key in ("down", "j", "s"):
            self.game.turn("j")
        elif event.key in ("left", "h", "a"):
            self.game.turn("h")
        elif event.key in ("right", "l", "d"):
            self.game.turn("l")
        else:
            return
        event.stop()
        event.prevent_default()

    def _finish(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._refresh_board()
        self.query_one("#game-status", Static).update(
            f"{self.game.game_over_reason or 'Game over'}  ·  score {self.game.score}  ·  press q"
        )

    def action_game_quit(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self.dismiss(self.game.score)


class CyberShellTUI(App[None]):
    """Full-screen Textual front end backed by the existing game loop."""

    TITLE = "CyberShell · Linux Adventure"
    SUB_TITLE = "A hands-on Linux learning adventure"
    ENABLE_COMMAND_PALETTE = False
    CSS = """
    Screen { background: $background; color: $foreground; }
    Header { background: $panel; color: $primary; }
    Footer { background: $panel; color: $text-muted; }
    #frame { height: 1fr; padding: 1 2; }
    #home, #lesson, #legacy { height: 1fr; }
    .eyebrow { color: $primary; text-style: bold; height: 1; }
    .card { border: round $border; background: $surface; padding: 1 2; }
    #hero { height: 1fr; min-height: 16; }
    #hero-art { width: 30; height: 100%; content-align: center middle; border: round $border; background: $background; }
    #hero-copy { width: 1fr; height: 100%; padding: 1 3; border: round $border; background: $surface; content-align: left middle; }
    #brand { color: $primary; text-style: bold; text-align: left; height: 1; }
    #wordmark-large { height: 5; margin-top: 1; }
    #wordmark { display: none; color: $foreground; text-style: bold; height: 1; }
    #tagline { color: $foreground; height: auto; margin: 1 0; }
    #intro { color: $text-muted; height: auto; }
    #home-lower { height: auto; margin-top: 1; }
    #home-menu { width: 1fr; height: auto; border: round $border; background: $surface; padding: 1 2; }
    #menu-options { height: auto; layout: grid; grid-size: 2; grid-columns: 1fr 1fr; grid-gutter: 0 1; }
    #menu-options Button { width: 1fr; min-width: 18; margin: 0; border: none; background: $panel; color: $foreground; overflow: hidden; }
    #menu-options Button:hover { background: $primary-muted; color: $foreground; }
    #menu-options Button.-primary { background: $primary; color: $background; text-style: bold; }
    #menu-options Button.-selected { background: $success; color: $background; text-style: bold; }
    #home-side { width: 32; height: auto; margin-left: 1; border: round $border; background: $surface; padding: 1 2; overflow: hidden; }
    #home-side Static { height: auto; color: $text-muted; }
    #home-side Button { width: 1fr; height: 1; min-height: 1; border: none; margin-top: 1; background: $panel; color: $foreground; }
    #home-input-row { height: 3; margin-top: 1; }
    #home-input { width: 1fr; border: round $border; background: $panel; }
    #home-prompt { width: 12; content-align: left middle; color: $primary; }
    #quest-card { height: 12; border: round $border; background: $surface; padding: 1 2; margin-bottom: 1; }
    #quest-title { color: $warning; text-style: bold; height: 1; }
    #quest-question { color: $foreground; height: auto; max-height: 8; overflow-y: auto; margin-top: 1; }
    #quest-meta { color: $text-muted; height: 1; }
    #work-area { height: 1fr; min-height: 10; }
    #terminal-card, #docs-card { height: 1fr; border: round $border; background: $panel; padding: 0 1; }
    #terminal-card { width: 2fr; }
    #docs-card { width: 1fr; margin-left: 1; }
    .section-head { height: 2; color: $primary; text-style: bold; content-align: left middle; }
    #terminal-input { width: 1fr; height: 1fr; color: $foreground; padding: 0; }
    #terminal-input:focus { background: $panel; }
    #docs-search { height: 3; border: round $border; background: $surface; }
    #docs-scroll { height: 1fr; overflow-y: auto; }
    #docs-content { width: 100%; color: $foreground; }
    #pet-card { height: 12; border-top: solid $border; padding-top: 1; margin-top: 1; }
    #pet-card.hidden-pet { display: none; }
    #pet-art { width: 18; content-align: center middle; }
    #pet-copy { width: 1fr; color: $text-muted; }
    #legacy-title { height: 2; color: $primary; text-style: bold; content-align: left middle; }
    #legacy-log { height: 1fr; border: round $border; background: $panel; padding: 1 2; }
    #legacy-input-row { height: 3; }
    #legacy-prompt { width: 1fr; color: $primary; content-align: left middle; }
    #legacy-input { width: 2fr; border: round $border; background: $surface; }
    #progress-bar { width: 1fr; height: 1; }
    #progress-bar Bar { width: 1fr; }
    #progress-bar Bar > .bar--bar { background: $background; color: $primary; }
    .muted { color: $text-muted; }
    Screen.narrow #frame { padding: 0 1; }
    Screen.narrow #hero-art { width: 22; }
    Screen.narrow #home-side { width: 26; }
    Screen.narrow #docs-card { width: 34; }
    Screen.compact #hero { height: auto; min-height: 0; }
    Screen.compact #hero-art { display: none; }
    Screen.compact #home-lower { height: 1fr; }
    Screen.compact #home-side { display: none; }
    Screen.compact #docs-card { display: none; }
    Screen.compact #terminal-card { width: 1fr; }
    Screen.compact #quest-card { height: 9; }
    Screen.onboarding #wordmark-large { display: none; }
    Screen.onboarding #wordmark { display: block; }
    Screen.short #wordmark-large { display: none; }
    Screen.short #wordmark { display: block; }
    Screen.short #hero { height: 4; min-height: 0; }
    Screen.short #hero-art { display: none; }
    Screen.short #hero-copy { height: 4; padding: 0 2; }
    Screen.short #brand, Screen.short #intro, Screen.short #home-description { display: none; }
    Screen.short #home-side { display: none; }
    Screen.short #home-lower { height: 1fr; }
    Screen.short #quest-card { height: 9; padding: 0 1; }
    Screen.short #quest-question { max-height: 3; }
    Screen.short #work-area { min-height: 8; }
    Screen.short #pet-card { display: none; }
    """
    BINDINGS = [
        ("escape", "send_escape", "Back / Exit"),
        ("ctrl+q", "quit", "Quit UI"),
        ("ctrl+l", "focus_docs", "Search docs"),
        ("ctrl+p", "open_commands", "Commands"),
        ("ctrl+space", "open_commands", "Commands"),
    ]

    def __init__(self, character_name: str = "Byte", start_sector: int = 0) -> None:
        super().__init__()
        self.character_name = character_name
        self.start_sector = start_sector
        self.input_queue: queue.Queue[str] = queue.Queue()
        self._game_thread: Optional[threading.Thread] = None
        self._input_mode = "home"
        self._theme: Theme = get_active_theme()
        for palette in THEMES.values():
            self.register_theme(
                TextualTheme(
                    name=f"cybershell-{palette.id}",
                    primary=palette.cyan,
                    secondary=palette.blue,
                    accent=palette.purple,
                    warning=palette.yellow,
                    error=palette.red,
                    success=palette.green,
                    foreground=palette.text,
                    background=palette.bg_dark,
                    surface=palette.surface,
                    panel=palette.surface_light,
                    dark=not palette.is_light,
                    variables={
                        "border": palette.border,
                        "text-muted": palette.text_muted,
                        "footer-key-foreground": palette.cyan,
                        "input-selection-background": f"{palette.blue} 35%",
                    },
                )
            )
        self._vfs: Any = None
        self._capture = _OutputBridge(self)
        self._stopping = False
        self._worker_error: Optional[Exception] = None

        # Live docs search state.
        self._codex: Any = None
        self._executable_cmds: Optional[set[str]] = None
        self._docs_query = ""
        self._default_docs = Text("")

        # Home menu keyboard navigation state.
        self._home_menu_values: list[str] = []
        self._home_menu_index = 0

        # Shell prompt text mirrored from the engine.
        self._shell_prompt = "❯"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="frame"):
            with Vertical(id="home"):
                with Horizontal(id="hero"):
                    yield Static(_pixel_penguin(self._theme), id="hero-art")
                    with Vertical(id="hero-copy"):
                        yield Static("BYTE'S LINUX ADVENTURE  ·  CYBERSHELL", id="brand")
                        yield Static(_big_linux(self._theme), id="wordmark-large")
                        yield Static("CYBERSHELL", id="wordmark")
                        yield Static("Learn Linux by typing real commands.", id="tagline")
                        yield Static("A safe place to try, make mistakes, and try again.", id="intro")
                        yield Static("Start with pwd and ls. Then make files, set permissions, and use pipes across 15 levels.", id="home-description")
                with Horizontal(id="home-lower"):
                    with Vertical(id="home-menu"):
                        yield Static("YOUR NEXT MOVE", classes="eyebrow")
                        yield Vertical(id="menu-options")
                        with Horizontal(id="home-input-row"):
                            yield Static("›  CHOOSE", id="home-prompt")
                            yield Input(placeholder="Pick an action below, or type its number", id="home-input")
                    with Vertical(id="home-side"):
                        yield Static("THE FIELD KIT", classes="eyebrow")
                        yield Static("▸  A Linux sandbox\n   Explore without risk", id="feature-sandbox")
                        yield Static("▸  Learn in context\n   Real commands, clear goals", id="feature-learning")
                        yield Static("▸  Your place is saved\n   Return whenever you like", id="feature-save")
                        yield Button("T   Change theme", id="menu-t")
                        yield Button("Switch profile", id="menu-user")
                        yield Static("\nEsc back  ·  Ctrl+Q quit", id="home-help")
            with Vertical(id="lesson"):
                with Vertical(id="quest-card"):
                    yield Static("", id="quest-title")
                    yield Static("", id="quest-question")
                    yield Static("", id="quest-meta")
                    yield ProgressBar(total=100, show_eta=False, id="progress-bar")
                with Horizontal(id="work-area"):
                    with Vertical(id="terminal-card"):
                        yield Static("⌁  SHELL  /  LIVE WORKSPACE", id="terminal-head", classes="section-head")
                        yield TerminalInput(id="terminal-input")
                    with Vertical(id="docs-card"):
                        yield Static("⌕  COMMAND GUIDE", classes="section-head")
                        yield Input(placeholder="Search a command or task… (live)", id="docs-search")
                        with VerticalScroll(id="docs-scroll"):
                            yield Static("", id="docs-content")
                        with Horizontal(id="pet-card"):
                            yield Static(_pixel_penguin(self._theme), id="pet-art")
                            yield Static("Need a nudge?\nType `man command` for a guide, or `hint` for a clue.", id="pet-copy")
            with Vertical(id="legacy", classes="card"):
                yield Static("CYBERSHELL  /  EXPLORE", id="legacy-title")
                yield RichLog(id="legacy-log", wrap=True, markup=False, highlight=False, auto_scroll=True)
                with Horizontal(id="legacy-input-row"):
                    yield Static("", id="legacy-prompt")
                    yield Input(placeholder="Enter to continue…", id="legacy-input")
        yield Footer()

    def on_mount(self) -> None:
        self._show_view("home")
        self._apply_theme(self._theme)
        terminal = self.query_one("#terminal-input", TerminalInput)
        terminal.on_submit = self._on_terminal_submit
        terminal.on_complete = self._on_terminal_complete
        self.query_one("#home-input", Input).focus()
        self._update_breakpoints(self.size.width, self.size.height)
        self._game_thread = threading.Thread(target=self._run_existing_game, daemon=True)
        self._game_thread.start()

    def on_resize(self, event: events.Resize) -> None:
        self._update_breakpoints(event.size.width, event.size.height)

    def _update_breakpoints(self, width: int, height: int) -> None:
        self.screen.set_class(width < 90, "narrow")
        self.screen.set_class(width < 65, "compact")
        self.screen.set_class(height < 30, "short")

    def _run_existing_game(self) -> None:
        import builtins

        from cybershell.run import main_menu_loop

        original_input = builtins.input

        def bridged_input(prompt: str = "") -> str:
            if self._stopping:
                raise EOFError
            self.call_from_thread(self._set_prompt, prompt)
            answer = self.input_queue.get()
            if self._stopping:
                raise EOFError
            return answer

        try:
            builtins.input = bridged_input
            with contextlib.redirect_stdout(self._capture):
                main_menu_loop(self.character_name, self.start_sector, ui=self)
        except (KeyboardInterrupt, EOFError):
            pass
        except Exception as exc:
            self._worker_error = exc
            self.post_legacy_output(f"The adventure stopped: {exc}")
        finally:
            builtins.input = original_input
            if not self._stopping and self._worker_error is None:
                try:
                    self.call_from_thread(self.exit)
                except RuntimeError:
                    pass

    def show_onboarding(self, current_name: str) -> None:
        self.call_from_thread(self._show_onboarding, current_name)

    async def _show_onboarding(self, current_name: str) -> None:
        self._show_view("home")
        self.screen.set_class(True, "onboarding")
        self.query_one("#brand", Static).update("WELCOME, EXPLORER")
        self.query_one("#wordmark", Static).update("First, what should we call you?")
        self.query_one("#tagline", Static).update("Your Linux adventure starts here.")
        self.query_one("#intro", Static).update(f"Press Enter to continue as {current_name}, or type a name.")
        self.query_one("#home-description", Static).update("Your name is saved with your learning progress.")
        await self.query_one("#menu-options", Vertical).remove_children()
        self._home_menu_values = []
        self.query_one("#home-input", Input).placeholder = f"Name (Enter keeps {current_name})"
        self.query_one("#home-prompt", Static).update("›  YOUR NAME")
        self.query_one("#home-input", Input).focus()
        self._input_mode = "home"

    def show_home(self, player: Any, has_save: bool) -> None:
        self.call_from_thread(self._show_home, player, has_save)

    async def _show_home(self, player: Any, has_save: bool) -> None:
        self._show_view("home")
        self.screen.set_class(False, "onboarding")
        self._apply_theme(get_active_theme())
        level = min(15, int(getattr(player, "current_sector", 0)) + 1)
        self.query_one("#brand", Static).update("BYTE'S LINUX ADVENTURE  ·  CYBERSHELL")
        self.query_one("#wordmark", Static).update("CYBERSHELL")
        self.query_one("#tagline", Static).update("Learn Linux by typing real commands.")
        self.query_one("#intro", Static).update("A safe place to try, make mistakes, and try again.")
        self.query_one("#home-description", Static).update(
            f"Welcome back, {player.character_name}. Continue at level {level} of 15."
            if has_save else "Start with pwd and ls. Then make files, set permissions, and use pipes across 15 levels."
        )
        self.query_one("#home-prompt", Static).update("›  CHOOSE")
        self.query_one("#home-input", Input).placeholder = f"Choose 1–{8 if has_save else 7}  ·  T themes  ·  user profile"
        labels = (
            [("1", "Continue adventure", "primary"), ("2", "Start a new adventure", ""),
             ("3", "World map", ""), ("4", "Command guide", ""), ("5", "Inventory", ""),
             ("6", "Permissions puzzle", ""), ("7", "Arcade", ""), ("8", "Field manual", "")]
            if has_save else
            [("1", "Start learning", "primary"), ("2", "World map", ""),
             ("3", "Command guide", ""), ("4", "Inventory", ""),
             ("5", "Permissions puzzle", ""), ("6", "Arcade", ""), ("7", "Field manual", "")]
        )
        menu = self.query_one("#menu-options", Vertical)
        await menu.remove_children()
        for value, label, variant in labels:
            classes = "-primary" if variant == "primary" else ""
            button = Button(f"{value}   {label}", id=f"menu-{value}", classes=classes)
            await menu.mount(button)
        self._home_menu_values = [value for value, _, _ in labels]
        self._home_menu_index = 0
        self._refresh_home_selection()
        self.query_one("#home-input", Input).focus()
        self._input_mode = "home"

    # -- Home menu keyboard navigation -------------------------------------

    def _refresh_home_selection(self) -> None:
        for index, value in enumerate(self._home_menu_values):
            try:
                button = self.query_one(f"#menu-{value}", Button)
            except Exception:
                continue
            button.set_class(index == self._home_menu_index, "-selected")

    def _move_home_selection(self, delta: int) -> None:
        total = len(self._home_menu_values)
        if total == 0:
            return
        self._home_menu_index = (self._home_menu_index + delta) % total
        self._refresh_home_selection()

    def _selected_home_value(self) -> str:
        if not self._home_menu_values:
            return ""
        index = min(self._home_menu_index, len(self._home_menu_values) - 1)
        return self._home_menu_values[index]

    def show_lesson(self, **state: Any) -> None:
        self.call_from_thread(self._show_lesson, state)

    def _show_lesson(self, state: dict[str, Any]) -> None:
        self._show_view("lesson")
        self._apply_theme(get_active_theme())
        player = state["player"]
        quest = state["quest"]
        active_obj = state.get("active_obj")
        completed = state.get("completed_count", 0)
        total = state.get("total_challenges", 15)
        pct = state.get("pct_prog", 0)
        title = f"LEVEL {player.current_sector + 1:02d}   /   {quest.sector_name}"
        self.query_one("#quest-title", Static).update(title)
        question = (
            getattr(active_obj, "question", "") or active_obj.description
            if active_obj else "All goals complete. Type ‘next’ to continue."
        )
        question_text = Text(question)
        for index, option in enumerate(getattr(active_obj, "options", []) or []):
            question_text.append("\n")
            question_text.append(f"{chr(65 + index)}  ", style=f"bold {self._theme.cyan}")
            question_text.append(str(option), style=self._theme.text)
        self.query_one("#quest-question", Static).update(question_text)
        self.query_one("#quest-meta", Static).update(
            f"{completed} of {total} levels complete   ·   {pct}%   ·   {getattr(player, 'xp', 0)} XP"
        )
        self.query_one("#terminal-head", Static).update(f"⌁  SHELL   /   {state.get('cwd', '~')}")
        self._vfs = state.get("vfs")
        progress = self.query_one("#progress-bar", ProgressBar)
        progress.update(total=max(1, total), progress=completed)
        terminal = self.query_one("#terminal-input", TerminalInput)
        terminal.clear_output()
        for line in state.get("terminal_logs", []):
            terminal.add_line(Text.from_ansi(str(line)))
        self._shell_prompt = f"❯ {state.get('cwd', '~')}"
        terminal.set_prompt(self._shell_prompt)
        self._default_docs = Text.from_ansi("\n".join(state.get("docs_content", [])))
        if self._docs_query:
            self._render_docs(self._docs_query)
        else:
            self.query_one("#docs-content", Static).update(self._default_docs)
        pet = state.get("pet")
        self.query_one("#pet-card").set_class(
            pet is None or not getattr(pet, "enabled", True), "hidden-pet"
        )
        if pet is not None and getattr(pet, "enabled", True):
            self.query_one("#pet-art", Static).update(_pixel_penguin(self._theme))
            copy = Text()
            copy.append(f"BYTE  /  {getattr(pet, 'state', 'idle').upper()}\n", style=f"bold {self._theme.cyan}")
            copy.append(f"{getattr(pet, 'current_quote', 'Ready when you are.')}\n\n")
            copy.append("hint  clue\nman   manual", style=self._theme.text_muted)
            self.query_one("#pet-copy", Static).update(copy)
        terminal.focus()
        self._input_mode = "lesson"

    def show_legacy(self) -> None:
        self.call_from_thread(self._show_legacy)

    def _show_legacy(self) -> None:
        self._show_view("legacy")
        self.query_one("#legacy-title", Static).update("CYBERSHELL  /  EXPLORE")
        self._input_mode = "legacy"
        self.query_one("#legacy-input", Input).focus()

    def post_legacy_clear(self) -> None:
        try:
            self.call_from_thread(self._clear_legacy)
        except RuntimeError:
            pass

    def _clear_legacy(self) -> None:
        if self._input_mode != "legacy":
            self._show_legacy()
        self.query_one("#legacy-log", RichLog).clear()

    def post_legacy_output(self, line: str) -> None:
        try:
            self.call_from_thread(self._append_legacy, line)
        except RuntimeError:
            pass

    def _append_legacy(self, line: str) -> None:
        if self._input_mode != "legacy":
            self._show_legacy()
        log = self.query_one("#legacy-log", RichLog)
        log.write(Text.from_ansi(line))

    def _set_prompt(self, prompt: str) -> None:
        mode = self._input_mode
        cleaned = _clean_terminal_controls(prompt).strip()
        if mode == "legacy":
            self.query_one("#legacy-prompt", Static).update(cleaned or "›")
        elif mode == "lesson":
            self.query_one("#terminal-input", TerminalInput).set_prompt(self._shell_prompt)
        else:
            self.query_one("#home-prompt", Static).update(cleaned or "›  CHOOSE")

    def _show_view(self, name: str) -> None:
        for view in ("home", "lesson", "legacy"):
            self.query_one(f"#{view}").display = view == name

    def _apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        theme_name = f"cybershell-{theme.id}"
        if self.theme != theme_name:
            self.theme = theme_name
        self.query_one("#hero-art", Static).update(_pixel_penguin(theme))
        self.query_one("#wordmark-large", Static).update(_big_linux(theme))

    # -- Live docs search --------------------------------------------------

    def _docs_catalog(self) -> list[dict[str, Any]]:
        if self._codex is None:
            from cybershell.engine.interpreter import Interpreter
            from cybershell.tools.codex import Codex

            self._codex = Codex()
            self._executable_cmds = set(Interpreter().commands.command_names) | {"tree", "clear"}
        catalog = self._codex.list_commands()
        if self._executable_cmds:
            return [cmd for cmd in catalog if cmd.get("name", "") in self._executable_cmds]
        return catalog

    def _docs_width(self) -> int:
        try:
            return max(20, self.query_one("#docs-card").size.width - 4)
        except Exception:
            return 40

    def _render_docs(self, query: str) -> None:
        query = query.strip()
        self._docs_query = query
        content = Text()
        width = self._docs_width()
        if not query:
            self.query_one("#docs-content", Static).update(self._default_docs)
            return
        matches = fuzzy_search_commands(query, self._docs_catalog(), limit=40)
        content.append(f"live: '{query}'  ({len(matches)})\n", style=f"bold {self._theme.yellow}")
        if not matches:
            content.append("No matching commands. Try another word.", style=self._theme.red)
        for cmd in matches[:24]:
            name = str(cmd.get("name", ""))
            desc = str(cmd.get("purpose") or cmd.get("description", ""))
            avail = max(8, width - 9)
            if len(desc) > avail:
                desc = desc[: max(0, avail - 1)] + "…"
            content.append(f"{name:<7}", style=f"bold {self._theme.cyan}")
            content.append(f" {desc}\n", style=self._theme.text_muted)
        self.query_one("#docs-content", Static).update(content)

    def _on_docs_changed(self, value: str) -> None:
        self._render_docs(value)

    # -- Command palette ---------------------------------------------------

    def _command_items(self) -> list[_PaletteItem]:
        from cybershell.ui.command_center import PALETTE_ACTIONS

        return [
            _PaletteItem(
                id=action["id"],
                label=action["title"],
                detail=action.get("detail", ""),
                keywords=f"{action.get('id', '')} {action.get('key', '')}",
            )
            for action in PALETTE_ACTIONS
        ]

    def _open_command_palette(self) -> None:
        if isinstance(self.screen, SearchPalette):
            return
        self.push_screen(
            SearchPalette("COMMAND PALETTE", self._command_items(), placeholder="Search commands…"),
            self._handle_palette_action,
        )

    def _handle_palette_action(self, action: Optional[str]) -> None:
        if not action:
            return
        if action == "search_docs":
            if self._input_mode == "lesson" and self.size.width >= 65:
                self.query_one("#docs-search", Input).focus()
            else:
                self.query_one("#terminal-input", TerminalInput).focus()
            return
        if action == "open_manual":
            terminal = self.query_one("#terminal-input", TerminalInput)
            terminal._buffer = "man "
            terminal._cursor = 4
            terminal.focus()
            terminal._redraw()
            return
        mapping = {
            "choose_challenge": "map",
            "view_progress": ":progress",
            "open_minigames": ":games",
            "reset_challenge": ":reset",
            "toggle_pet": ":pet",
            "chmod_decoder": ":chmod",
            "theme_selector": ":theme",
            "settings": ":settings",
        }
        command = mapping.get(action)
        if command:
            self._send_to_shell(command)

    def _send_to_shell(self, command: str) -> None:
        self._show_view("lesson")
        terminal = self.query_one("#terminal-input", TerminalInput)
        terminal.focus()
        self.input_queue.put(command)
        terminal.add_line(Text(f"{self._shell_prompt} {command}", style=self._theme.text_muted))

    def _log_shell(self, message: str, title: bool = False) -> None:
        style = f"bold {self._theme.cyan}" if title else self._theme.text
        if self._input_mode == "lesson":
            self.query_one("#terminal-input", TerminalInput).add_line(
                Text(message, style=style)
            )

    def play_snake(self) -> int:
        """Run Terminal Snake on a Textual screen and return the final score.

        Called (blocking) from the game thread; the app thread owns the screen.
        """
        done = threading.Event()
        result: dict[str, int] = {}

        def _show() -> None:
            def _closed(score: Optional[int]) -> None:
                result["score"] = int(score or 0)
                done.set()

            self.push_screen(KeyboardGame(), _closed)

        try:
            self.call_from_thread(_show)
        except RuntimeError:
            return 0
        done.wait()
        return result.get("score", 0)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "docs-search":
            self._on_docs_changed(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "docs-search":
            # The filter is already live; just move focus back to the shell.
            self.query_one("#terminal-input", TerminalInput).focus()
            return
        value = event.value
        event.input.value = ""
        if event.input.id == "home-input" and not value.strip():
            value = self._selected_home_value()
        self.input_queue.put(value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("menu-"):
            self.input_queue.put(event.button.id.removeprefix("menu-"))

    def on_key(self, event: events.Key) -> None:
        if self._input_mode == "home" and self._home_menu_values:
            if event.key in ("down", "right"):
                self._move_home_selection(1)
                event.stop()
                event.prevent_default()
                return
            if event.key in ("up", "left"):
                self._move_home_selection(-1)
                event.stop()
                event.prevent_default()
                return
        if not isinstance(self.focused, Input) or self.focused.id != "docs-search":
            return
        if event.key == "escape":
            self.query_one("#terminal-input", TerminalInput).focus()

    def _on_terminal_submit(self, command: str) -> None:
        """Handle a command typed into the inline terminal prompt."""
        terminal = self.query_one("#terminal-input", TerminalInput)
        terminal.add_line(Text(f"{self._shell_prompt} {command}", style=self._theme.text_muted))
        if command.strip().lower() in _COMMAND_TRIGGERS:
            self._open_command_palette()
            return
        self.input_queue.put(command)

    def _on_terminal_complete(self) -> None:
        from cybershell.run import KNOWN_COMMANDS

        terminal = self.query_one("#terminal-input", TerminalInput)
        value = terminal.value
        if not value or terminal._cursor != len(value):
            return
        token_start = max(value.rfind(" "), value.rfind("|"), value.rfind(">")) + 1
        prefix = value[token_start:]
        if not prefix:
            return
        if token_start == 0:
            matches = sorted({name for name in KNOWN_COMMANDS if name.startswith(prefix)})
        else:
            vfs = self._vfs
            if vfs is None:
                return
            dirname, basename = posixpath.split(prefix)
            folder = vfs.resolve_path(dirname) if dirname else vfs.cwd
            if folder is None or not folder.is_directory:
                return
            matches = sorted(
                posixpath.join(dirname, name) + ("/" if node.is_directory else "")
                for name, node in folder.children.items()
                if name.startswith(basename)
            )
        if not matches:
            return
        completion = matches[0] if len(matches) == 1 else posixpath.commonprefix(matches)
        if completion != prefix:
            suffix = " " if len(matches) == 1 and token_start == 0 else ""
            terminal._buffer = value[:token_start] + completion + suffix
            terminal._cursor = len(terminal._buffer)
            terminal._redraw()
        elif len(matches) > 1:
            terminal.add_line(Text("  ".join(matches[:8]), style=self._theme.text_muted))

    def action_focus_docs(self) -> None:
        if self._input_mode == "lesson" and self.size.width >= 65:
            self.query_one("#docs-search", Input).focus()

    def action_open_commands(self) -> None:
        if isinstance(self.screen, SearchPalette):
            return
        if self._input_mode == "lesson":
            self._open_command_palette()

    async def action_quit(self) -> None:
        self._stopping = True
        self.input_queue.put("")
        if self._game_thread is not None:
            await asyncio.to_thread(self._game_thread.join, 1.0)
        self.exit()

    def action_send_escape(self) -> None:
        if isinstance(self.screen, SearchPalette):
            return
        if self._input_mode == "lesson" and getattr(self.focused, "id", None) == "docs-search":
            search = self.query_one("#docs-search", Input)
            if search.value:
                search.value = ""
                self._render_docs("")
            else:
                self.query_one("#terminal-input", TerminalInput).focus()
            return
        self.input_queue.put("esc")


def run_textual(character_name: str = "Byte", start_sector: int = 0) -> None:
    """Start the full-screen UI around the existing synchronous game loop."""
    CyberShellTUI(character_name=character_name, start_sector=start_sector).run()
