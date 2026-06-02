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

## HTTP API (optional)

Instead of the CLI, you can drive the agent over HTTP with FastAPI:

```bash
# terminal 1 — MCP server (tools)
python server.py

# terminal 2 — API (start AFTER the MCP server is up)
uvicorn api:app --reload --port 8090

# terminal 3 — call it
curl -X POST http://localhost:8090/plan \
     -H "Content-Type: application/json" \
     -d '{"request": "Weekend in Istanbul from Karachi, 2026-06-03 to 2026-06-06, museums"}'
```

`POST /plan` runs the agent and returns `{request, output, tools_used}` (one-shot,
non-streaming). Other endpoints: `GET /health`, `GET /examples`, interactive docs
at `/docs`, and `POST /chat` (streaming — see below). The API opens the MCP
connection once at startup, so the MCP server must be running first.

## Web UI (frontend/)

A React (TanStack Start) chat UI that shows tool calls live, renders the answer
as Markdown, and renders the itinerary in a side panel. **All intelligence lives
in the Python backend** — the frontend has no LLM/AI code; it just streams from
`POST /chat`.

```
browser (frontend/)  →  FastAPI POST /chat  →  Pydantic AI agent.iter()  →  MCP server
                     ←──────────── SSE: tool-input / tool-output / text-delta ──────────
```

Run all three:

Ports: **MCP server = 8000**, **frontend (Vite) = 8080** (fixed by the template),
**FastAPI = 8090**. They must all differ.

```bash
# terminal 1 — MCP server (tools)  -> http://localhost:8000/mcp
python server.py

# terminal 2 — FastAPI (the agent/brain), streams /chat  -> http://localhost:8090
uv run uvicorn api:app --port 8090 --reload

# terminal 3 — frontend  -> http://localhost:8080
cd frontend && npm install && npm run dev
```

The frontend reads `VITE_API_URL` (default `http://localhost:8090`) to find the
API. No API keys are needed in the frontend — `ANTHROPIC_API_KEY` only lives in
the Python `.env`.

## Project layout

```
server.py              # FastMCP init + registers all tools (HTTP transport)
agent.py               # Pydantic AI agent that connects over HTTP and plans a trip
api.py                 # FastAPI wrapper exposing the agent over HTTP (/plan)
paths.py               # __file__-based paths (DB, itineraries)
tools/                 # one module per tool, each exposing register(mcp)
db/hotels_training.db  # hotel dataset
data/itineraries/      # create_itinerary output
examples/              # older LangGraph/CrewAI MCP samples (reference only)
```
