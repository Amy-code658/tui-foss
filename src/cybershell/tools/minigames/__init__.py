"""CyberShell Mini-Games Suite.

Modules:
- snake: Terminal Snake with Linux-themed items
- vim_dojo: Vim target muscle-memory practice
- typing_dojo: Safe Linux command speed drills
- hub: Central arcade launcher
"""

from cybershell.tools.minigames.snake import TerminalSnake, play_snake_interactive
from cybershell.tools.minigames.vim_dojo import VimDojo, play_vim_dojo_interactive
from cybershell.tools.minigames.typing_dojo import TypingDojo, play_typing_dojo_interactive
from cybershell.tools.minigames.hub import render_minigames_menu, view_minigames_hub

__all__ = [
    "TerminalSnake",
    "play_snake_interactive",
    "VimDojo",
    "play_vim_dojo_interactive",
    "TypingDojo",
    "play_typing_dojo_interactive",
    "render_minigames_menu",
    "view_minigames_hub",
]
