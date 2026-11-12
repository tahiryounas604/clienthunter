#!/usr/bin/env python3
"""Entry point: `python3 clienthunter.py hunt --city Lahore --category cafe`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clienthunter.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
