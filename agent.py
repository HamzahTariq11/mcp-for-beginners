"""Trip Planner agent (Pydantic AI).

Drives the Trip Planner MCP server's five tools with Claude Sonnet 4.6 to plan
a trip and save an itinerary. Pydantic AI talks to the MCP server directly and
exposes the tools with their plain names — no provider shim compiling tool
schemas into a strict grammar.

Run in two terminals:

    # terminal 1 — start the MCP server
    python server.py            # serves http://localhost:8000/mcp

    # terminal 2 — run the agent
    python agent.py
"""

import asyncio
import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

load_dotenv()

MCP_URL = os.getenv("MCP_URL", "http://localhost:8000/mcp")

# ---------------------------------------------------------------------------
# YOUR PROMPT. A plain sentence describing the trip; the agent infers IATA
# codes, dates, budget, and activity style from it.
#
# NOTE 1: hotels only exist for these destinations -> Istanbul, Dubai, Bangkok.
#         Any city can be an ORIGIN (flights only); Karachi and London have no hotels.
# NOTE 2: weather only forecasts ~5 days ahead, so keep trip dates within a few
#         days of TODAY for get_weather to return real data. (Prices are USD.)
EXAMPLE_REQUESTS = [
    (
        "Plan a 3-day cultural weekend in Istanbul from Karachi departing 2026-06-03, "
        "back 2026-06-06. I have about 650 USD for the flight. I love museums and "
        "historic sites, but want outdoor time too when the weather is nice. Compare a "
        "few flights and hotels, check the forecast for each day, and give me a full "
        "day-by-day plan."
    ),
    (
        "Research a luxury 3-night Dubai escape from London, 2026-06-03 to 2026-06-06. "
        "I want a 5-star hotel, ideally with a spa. Compare flights, find the best hotel "
        "within reason, check the weather, and mix indoor attractions (malls, galleries) "
        "with outdoor ones for the cooler parts of the day. Save a full day-by-day itinerary."
    ),
    (
        "Plan a budget-friendly 3-night Bangkok trip from Karachi, 2026-06-04 to "
        "2026-06-07, under 600 USD for the flight. I'm into temples, street-food markets, "
        "and a couple of museums. Compare flight options, find a well-rated central hotel, "
        "check the forecast, and build a daily schedule of outdoor and indoor spots."
    ),
    (
        "I want a relaxed weekend in Istanbul from Dubai, 2026-06-04 to 2026-06-06. Prefer "
        "a highly-rated hotel near the historic centre. Find good flights, check the "
        "forecast, pick scenic outdoor spots plus a couple of art museums, and save a "
        "day-by-day itinerary."
    ),
]

REQUEST = EXAMPLE_REQUESTS[2]
# ---------------------------------------------------------------------------

INSTRUCTIONS = (
    "You are a meticulous travel agent who never guesses: you call every tool "
    "available, compare options before committing, match activities to the "
    "forecast, and deliver a concrete saved itinerary rather than vague "
    "suggestions.\n\n"
    "Handle the user's travel request thoroughly, using ALL of your tools, with "
    "the end goal of producing a saved itinerary. First infer sensible IATA "
    "airport codes, dates, budget, and preferences from the request. Then "
    "research extensively — do not skip any tool:\n"
    "1. search_flights — pull several flight options for the route and date, then "
    "choose the best within budget, weighing price, stops, and duration.\n"
    "2. search_hotels — compare the available hotels for the stay and choose a "
    "well-rated one within budget; briefly justify the pick.\n"
    "3. get_weather — get the daily forecast across the whole trip and note its "
    "outdoor/indoor recommendation.\n"
    "4. get_attractions — look up BOTH outdoor and indoor attractions, then assign "
    "them to days based on each day's weather (indoor on wet days, outdoor when dry).\n"
    "5. create_itinerary — assemble the flight, hotel, costs, and a day-by-day "
    "attraction schedule into a final plan and SAVE it. Always finish by calling "
    "create_itinerary; the saved itinerary is the goal.\n\n"
    "Every one of the five tools must be used at least once before you produce the "
    "final answer. End with a detailed summary: chosen flight (airline, times, "
    "stops, price, plus alternatives considered); hotel (name, rating, nightly + "
    "total price, why); day-by-day weather; day-by-day attraction schedule; total "
    "cost; and the saved itinerary id and file path."
)

# Pydantic AI exposes the MCP tools with their plain names (search_flights, …) —
# no URL-derived prefix, so there's no invalid-tool-name issue.
trip_server = MCPServerStreamableHTTP(MCP_URL)

agent = Agent(
    "anthropic:claude-sonnet-4-6",
    instructions=INSTRUCTIONS,
    toolsets=[trip_server],
    defer_model_check=True,  # accept the model id without the known-model check
)


async def main() -> None:
    # Entering the agent context opens the MCP connection(s) in `toolsets`.
    async with agent:
        result = await agent.run(REQUEST)
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
