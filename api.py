"""FastAPI wrapper around the Trip Planner agent.

Exposes the Pydantic AI agent over HTTP so you can plan trips with a request
instead of editing agent.py. The agent still drives the MCP server's tools, so
the MCP server must be running too.

Architecture:  client -> FastAPI /plan -> Pydantic AI agent -> (MCP/HTTP) -> tools

Run (two terminals + a client):

    # terminal 1 — MCP server (tools)
    python server.py

    # terminal 2 — this API  (start AFTER the MCP server is up)
    uvicorn api:app --reload --port 8080

    # terminal 3 — call it
    curl -X POST http://localhost:8080/plan \
         -H "Content-Type: application/json" \
         -d '{"request": "Weekend in Istanbul from Karachi, 2026-06-03 to 2026-06-06, museums"}'
"""

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
)

from agent import EXAMPLE_REQUESTS, MCP_URL, agent


class PlanRequest(BaseModel):
    request: str | None = Field(
        default=None,
        description="Plain-English trip description. Defaults to the first example.",
        examples=[EXAMPLE_REQUESTS[0]],
    )


class PlanResponse(BaseModel):
    request: str
    output: str
    tools_used: list[str]


class ChatRequest(BaseModel):
    message: str | None = Field(
        default=None,
        description="Plain-English trip request. Defaults to the first example.",
        examples=[EXAMPLE_REQUESTS[0]],
    )


def _tools_used(result) -> list[str]:
    """Best-effort extraction of the MCP tools the agent actually called."""
    seen: list[str] = []
    try:
        for message in result.all_messages():
            for part in getattr(message, "parts", []):
                if part.__class__.__name__ == "ToolCallPart":
                    name = getattr(part, "tool_name", None)
                    if name and name not in seen:
                        seen.append(name)
    except Exception:
        pass
    return seen


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Open the MCP connection once for the app's lifetime; agent.run() can then
    # be called per request. (Start the MCP server BEFORE this API.)
    async with agent:
        yield


app = FastAPI(
    title="Trip Planner API",
    description="Plan a trip via a Pydantic AI agent backed by MCP tools.",
    version="1.0.0",
    lifespan=lifespan,
)

# Dev CORS: the React frontend (different origin) calls this API directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sse(payload: dict) -> str:
    """Format a dict as one Server-Sent Event."""
    return f"data: {json.dumps(payload)}\n\n"


def _coerce_tool_output(content):
    """Normalise an MCP tool's return content into a JSON-serialisable value."""
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            return json.loads(content)
        except (ValueError, TypeError):
            return content
    if isinstance(content, list):
        # MCP content blocks, e.g. [{"type": "text", "text": "{...}"}]
        texts = [
            item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
            for item in content
        ]
        texts = [t for t in texts if t]
        if texts:
            joined = "".join(texts)
            try:
                return json.loads(joined)
            except (ValueError, TypeError):
                return joined
    try:
        return json.loads(json.dumps(content, default=str))
    except (ValueError, TypeError):
        return str(content)


async def _agent_event_stream(prompt: str):
    """Run the Pydantic AI agent and stream its tool calls + answer as SSE.

    Event types emitted (one JSON object per SSE message):
      tool-input  {toolCallId, toolName, input}   -> tool started (live)
      tool-output {toolCallId, toolName, output}   -> tool finished
      text-delta  {delta}                          -> streamed answer text
      error       {errorText}
      done        {}
    """
    try:
        async with agent.iter(prompt) as run:
            async for node in run:
                if Agent.is_model_request_node(node):
                    async with node.stream(run.ctx) as stream:
                        async for event in stream:
                            if isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
                                if event.part.content:
                                    yield _sse({"type": "text-delta", "delta": event.part.content})
                            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                if event.delta.content_delta:
                                    yield _sse({"type": "text-delta", "delta": event.delta.content_delta})
                elif Agent.is_call_tools_node(node):
                    async with node.stream(run.ctx) as stream:
                        async for event in stream:
                            if isinstance(event, FunctionToolCallEvent):
                                part = event.part
                                try:
                                    args = part.args_as_dict()
                                except Exception:
                                    args = part.args
                                yield _sse(
                                    {
                                        "type": "tool-input",
                                        "toolCallId": part.tool_call_id,
                                        "toolName": part.tool_name,
                                        "input": args,
                                    }
                                )
                            elif isinstance(event, FunctionToolResultEvent):
                                part = event.part
                                yield _sse(
                                    {
                                        "type": "tool-output",
                                        "toolCallId": part.tool_call_id,
                                        "toolName": part.tool_name,
                                        "output": _coerce_tool_output(part.content),
                                    }
                                )
        yield _sse({"type": "done"})
    except Exception as e:  # surface failures to the UI instead of hanging
        yield _sse({"type": "error", "errorText": str(e)})
        yield _sse({"type": "done"})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "mcp_url": MCP_URL}


@app.get("/examples")
async def examples() -> dict:
    return {"examples": EXAMPLE_REQUESTS}


@app.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    """Stream the agent's tool calls and answer to the frontend as SSE."""
    prompt = body.message or EXAMPLE_REQUESTS[0]
    return StreamingResponse(
        _agent_event_stream(prompt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/plan", response_model=PlanResponse)
async def plan(body: PlanRequest) -> PlanResponse:
    prompt = body.request or EXAMPLE_REQUESTS[0]
    result = await agent.run(prompt)
    return PlanResponse(
        request=prompt,
        output=result.output,
        tools_used=_tools_used(result),
    )
