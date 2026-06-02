"""get_weather — daily forecast via OpenWeather's free 5-day/3-hour endpoint.

The API returns forecasts in 3-hour steps; we group them by day, summarise
each day, and add an outdoor/indoor recommendation. Note: the free tier only
covers ~5 days ahead, so far-future trips return an empty forecast.
"""

import os
import httpx
from collections import Counter
from typing import Annotated

from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .utils import log_call, log_result, parse_iso_date

FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        )
    )
    async def get_weather(
        city: Annotated[str, Field(description="City name, e.g. 'Istanbul'")],
        start_date: Annotated[str, Field(description="Start date, ISO format YYYY-MM-DD")],
        end_date: Annotated[str, Field(description="End date (inclusive), ISO format YYYY-MM-DD")],
    ) -> dict:
        """Daily weather forecast for a city over a date range, plus an
        overall 'outdoor' / 'mixed' / 'indoor' recommendation."""
        log_call("get_weather", city=city, start_date=start_date, end_date=end_date)
        try:
            d_start = parse_iso_date(start_date, "start_date")
            d_end = parse_iso_date(end_date, "end_date")
        except ValueError as e:
            return {"error": str(e)}
        if d_end < d_start:
            return {"error": "end_date must be on or after start_date."}

        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return {"error": "OPENWEATHER_API_KEY is not set in the environment."}

        params = {"q": city, "appid": api_key, "units": "metric", "cnt": 40}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(FORECAST_URL, params=params)
                if resp.status_code == 404:
                    return {"error": f"City not found: {city!r}"}
                resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            return {"error": f"OpenWeather API error {e.response.status_code}: {e.response.text[:200]}"}
        except httpx.HTTPError as e:
            return {"error": f"Failed to reach OpenWeather API: {e}"}

        by_date: dict[str, list] = {}
        for item in resp.json().get("list", []):
            day = (item.get("dt_txt") or "").split(" ")[0]
            if not day:
                continue
            try:
                d = parse_iso_date(day, "day")
            except ValueError:
                continue
            if d_start <= d <= d_end:
                by_date.setdefault(day, []).append(item)

        forecast = []
        for day in sorted(by_date):
            entries = by_date[day]
            descs = [e["weather"][0]["description"] for e in entries if e.get("weather")]
            icons = [e["weather"][0]["icon"] for e in entries if e.get("weather")]
            highs = [e["main"]["temp_max"] for e in entries if e.get("main")]
            lows = [e["main"]["temp_min"] for e in entries if e.get("main")]
            pops = [e.get("pop", 0) or 0 for e in entries]
            forecast.append(
                {
                    "date": day,
                    "condition": Counter(descs).most_common(1)[0][0] if descs else "unknown",
                    "temp_high": round(max(highs), 1) if highs else None,
                    "temp_low": round(min(lows), 1) if lows else None,
                    "rain_chance": round(max(pops) * 100) if pops else 0,
                    "icon": Counter(icons).most_common(1)[0][0] if icons else None,
                }
            )

        if not forecast:
            log_result("get_weather", "no forecast in range (free tier covers ~5 days)")
            return {
                "city": city,
                "unit": "celsius",
                "forecast": [],
                "message": (
                    "No forecast available for that date range. The free "
                    "OpenWeather forecast only covers about 5 days ahead."
                ),
            }

        avg_rain = sum(f["rain_chance"] for f in forecast) / len(forecast)
        recommendation = "outdoor" if avg_rain < 40 else "mixed" if avg_rain < 70 else "indoor"
        log_result("get_weather", f"{len(forecast)} days, recommendation={recommendation}")
        return {
            "city": city,
            "unit": "celsius",
            "recommendation": recommendation,
            "forecast": forecast,
        }
