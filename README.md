# Trip Planner MCP

An MCP server that gives an agent five tools to plan a trip, plus a
[Pydantic AI](https://ai.pydantic.dev/) agent that drives them. Built for a
training session.

## Tools

| Tool | Source | Needs key | Notes |
|------|--------|-----------|-------|
| `search_flights` | Duffel API (test mode) | `DUFFEL_API_KEY` | One-way offers with live prices |
| `search_hotels` | local SQLite (`db/hotels_training.db`) | — | Fully offline |
| `get_weather` | OpenWeather 5-day forecast | `OPENWEATHER_API_KEY` | ~5 days ahead only |
| `get_attractions` | Foursquare Places API | `FOURSQUARE_API_KEY` | Outdoor / indoor / all |
| `create_itinerary` | local filesystem | — | Writes `data/itineraries/*.json` |

## Setup

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # then fill in your keys (incl. ANTHROPIC_API_KEY for the agent)
```

## Run it (two terminals)

The server runs over **streamable-HTTP** and the Pydantic AI agent connects to it.

```bash
# terminal 1 — start the MCP server
python server.py                 # serves http://localhost:8000/mcp

# terminal 2 — run the agent
python agent.py
```

Server transport/host/port can be overridden with `MCP_TRANSPORT`
(`streamable-http` | `stdio` | `sse`), `MCP_HOST`, `MCP_PORT`. The agent's
target URL can be overridden with `MCP_URL`.

> The agent uses Pydantic AI with Claude Sonnet 4.6 and connects via
> `MCPServerStreamableHTTP`. Edit the `REQUEST` variable in `agent.py` to change
> the trip prompt.

## Project layout

```
server.py              # FastMCP init + registers all tools (HTTP transport)
agent.py               # Pydantic AI agent that connects over HTTP and plans a trip
paths.py               # __file__-based paths (DB, itineraries)
tools/                 # one module per tool, each exposing register(mcp)
db/hotels_training.db  # hotel dataset
data/itineraries/      # create_itinerary output
examples/              # older LangGraph/CrewAI MCP samples (reference only)
```
