"""Filesystem paths resolved relative to this file (NOT the current working
directory). An MCP stdio server is launched by the client, so the CWD is
unpredictable — always resolve data/db paths from here."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "db" / "hotels_training.db"
ITINERARIES_DIR = ROOT / "data" / "itineraries"
