"""Trip-planner MCP tools.

Each tool module exposes a ``register(mcp)`` function. ``register_all`` wires
them all onto a FastMCP instance — this keeps server.py free of circular
imports (tool modules never import the server).
"""

from mcp.server.fastmcp import FastMCP

from . import (
    search_flights,
    search_hotels,
    get_weather,
    get_attractions,
    create_itinerary,
)

_MODULES = (
    search_flights,
    search_hotels,
    get_weather,
    get_attractions,
    create_itinerary,
)


def register_all(mcp: FastMCP) -> None:
    for module in _MODULES:
        module.register(mcp)
