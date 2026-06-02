"""Trip Planner MCP server.

Runs over streamable-HTTP by default so a separate client (the CrewAI agent)
can connect to it:

    python server.py                      # serves http://127.0.0.1:8000/mcp

Override via env vars: MCP_TRANSPORT (streamable-http | stdio | sse),
MCP_HOST, MCP_PORT.

Exposes 5 tools: search_flights, search_hotels, get_weather,
get_attractions, create_itinerary.
"""

import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

HOST = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "8000"))

mcp = FastMCP("trip_planner_mcp", host=HOST, port=PORT)

# Import after load_dotenv so tools see the env if they read it at import time.
from tools import register_all  # noqa: E402

register_all(mcp)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    # NEVER write to stdout under stdio transport — it corrupts the protocol.
    if transport != "stdio":
        print(
            f"Trip Planner MCP serving on http://{HOST}:{PORT}/mcp "
            f"(transport={transport})",
            file=sys.stderr,
        )
    mcp.run(transport=transport)
