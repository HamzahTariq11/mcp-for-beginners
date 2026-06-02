"""Small shared helpers for the trip-planner tools."""

import logging
import sys
from datetime import date, datetime

# Dedicated logger that always writes to stderr, so tool activity is visible in
# the server terminal (and never pollutes stdout, which matters under the stdio
# transport). These lines showcase the agent's flow: one per tool call + result.
logger = logging.getLogger("trip_planner.tools")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("%(asctime)s  [tool] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def log_call(tool: str, **params) -> None:
    """Log that a tool was called, with its (non-empty) arguments."""
    args = ", ".join(f"{k}={v!r}" for k, v in params.items() if v is not None)
    logger.info(f">> CALL {tool}({args})")


def log_result(tool: str, summary: str) -> None:
    """Log a one-line summary of what a tool returned."""
    logger.info(f"<< DONE {tool}: {summary}")


def parse_iso_date(value: str, field: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD) or raise ValueError with a clear
    message naming the offending field."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(
            f"{field} must be an ISO date in YYYY-MM-DD format (got {value!r})"
        )
