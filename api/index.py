"""Vercel serverless function entry point for the FastAPI backend."""

import sys
from pathlib import Path

# Add the backend directory to the Python path so imports work
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app  # noqa: E402
