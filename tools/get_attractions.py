"""get_attractions — points of interest via the Foursquare Places API.

Uses the current (2025+) Places platform:
  host    : https://places-api.foursquare.com
  auth    : Authorization: Bearer <SERVICE_KEY>
  version : X-Places-Api-Version: 2025-06-17  (required)

Category filtering uses the `fsq_category_ids` parameter with the canonical
24-char hex top-level category IDs (verified live against the API — the old
5-digit v3 IDs like 16000/10000 are rejected). Multiple IDs may be passed
comma-separated.
"""

import os
import httpx
from typing import Annotated

from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .utils import log_call, log_result
from .mock_data import mock_attractions

FSQ_URL = "https://places-api.foursquare.com/places/search"
FSQ_VERSION = "2025-06-17"

# Category -> Foursquare top-level category ID(s). None means no filter (all).
_CATEGORY_IDS = {
    "outdoor": "4d4b7105d754a06377d81259",  # Outdoors & Recreation
    "indoor": "4d4b7104d754a06370d81259",   # Arts & Entertainment
    "all": None,
}


def _attractions_fallback(city: str, category: str, limit: int, reason: str) -> dict:
    """Return mock attractions (same schema) when the live API can't deliver."""
    data = mock_attractions(city, category, limit)
    log_result(
        "get_attractions",
        f"{data['results_count']} {data['category']} attractions in {city} (MOCK: {reason})",
    )
    return data


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        )
    )
    async def get_attractions(
        city: Annotated[str, Field(description="City name, e.g. 'Istanbul'")],
        category: Annotated[
            str, Field(description="One of 'outdoor', 'indoor', or 'all'")
        ],
        limit: Annotated[int, Field(description="Maximum number of attractions", ge=1, le=50)] = 10,
    ) -> dict:
        """Find tourist attractions in a city, optionally biased toward
        outdoor or indoor venues."""
        log_call("get_attractions", city=city, category=category, limit=limit)
        cat = (category or "all").lower()
        if cat not in _CATEGORY_IDS:
            return {"error": "category must be one of: 'outdoor', 'indoor', 'all'."}

        api_key = os.getenv("FOURSQUARE_API_KEY")
        if not api_key:
            return _attractions_fallback(city, cat, limit, "no API key")

        params: dict = {"near": city, "limit": limit}
        category_ids = _CATEGORY_IDS[cat]
        if category_ids:
            params["fsq_category_ids"] = category_ids
        headers = {
            "Authorization": f"Bearer {api_key}",
            "X-Places-Api-Version": FSQ_VERSION,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(FSQ_URL, params=params, headers=headers)
                resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            return _attractions_fallback(city, cat, limit, f"API error {e.response.status_code}")
        except httpx.HTTPError:
            return _attractions_fallback(city, cat, limit, "API unreachable")

        results = resp.json().get("results", [])
        attractions = []
        for place in results:
            cats = place.get("categories") or []
            loc = place.get("location") or {}
            attractions.append(
                {
                    "attraction_id": place.get("fsq_place_id") or place.get("fsq_id"),
                    "name": place.get("name"),
                    "category": cats[0].get("name") if cats else "Attraction",
                    "address": loc.get("formatted_address") or loc.get("address"),
                    "distance_meters": place.get("distance"),
                }
            )

        if not attractions:
            return _attractions_fallback(city, cat, limit, "no results returned")
        log_result("get_attractions", f"{len(attractions)} {cat} attractions in {city}")
        return {
            "city": city,
            "category": cat,
            "results_count": len(attractions),
            "attractions": attractions,
        }
