"""Dashboard entrypoint wrapper.

Use this module for normalized project layout while preserving src runtime paths.
"""

from pathlib import Path
import runpy

SRC_APP = Path(__file__).resolve().parents[1] / "src" / "dashboard.py"

if __name__ == "__main__":
    runpy.run_path(str(SRC_APP), run_name="__main__")
