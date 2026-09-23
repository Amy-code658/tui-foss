#!/usr/bin/env python3
"""Byte's Linux Adventure - Standalone Distribution Launcher.

A fun, chill, beginner-friendly terminal adventure for learning Linux commands.
Journey through 15 bite-sized levels with mascot Byte (・ω・) 🌱!
"""

from __future__ import annotations

import os
import sys

# Ensure src/ is on pythonpath for seamless execution
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from cybershell.run import main

if __name__ == "__main__":
    sys.exit(main())
