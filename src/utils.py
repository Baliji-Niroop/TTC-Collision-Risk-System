"""Compatibility wrapper for Pass-A migration.

Canonical implementation moved to `python/utils.py`.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from python.utils import *  # noqa: F401,F403
