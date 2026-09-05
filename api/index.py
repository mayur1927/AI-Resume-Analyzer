"""Vercel Serverless Function entrypoint."""

import sys
from pathlib import Path

# Ensure root directory is on sys.path so backend module imports cleanly
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from backend.main import app
