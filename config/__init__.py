"""Compatibility exports for project configuration.

This package name collides with imports like `from config import ...`.
Re-export symbols from `src.config` so existing imports resolve reliably.
"""

from src.config import *  # noqa: F401,F403
