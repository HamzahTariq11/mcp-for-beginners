"""create_itinerary — assemble a trip into a JSON file on disk.

No external API. Writes to data/itineraries/{itinerary_id}.json (path resolved
from paths.py). This is the only tool that writes (readOnlyHint=False).
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Annotated

from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from paths import ITINERARIES_DIR
from .utils import log_call, log_result


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    def create_itinerary(
        trip_name: Annotated[str, Field(description="Human-readable trip name, e.g. 'Istanbul Weekend'")],
        flight_id: Annotated[str, Field(description="flight_id from a search_flights result")],
        hotel_id: Annotated[int, Field(description="hotel_id from a search_hotels result")],
        hotel_name: Annotated[str, Field(description="Hotel name, for readability")],
        checkin: Annotated[str, Field(description="Check-in date, ISO format YYYY-MM-DD")],
        checkout: Annotated[str, Field(description="Check-out date, ISO format YYYY-MM-DD")],
        total_flight_cost: Annotated[float, Field(description="Total flight cost")],
        total_hotel_cost: Annotated[float, Field(description="Total hotel cost")],
        daily_schedule: Annotated[
            dict[str, list[str]],
            Field(description="Map of ISO date -> list of attraction names for that day"),
        ],
        notes: Annotated[str, Field(description="Optional free-text notes")] = "",
    ) -> dict:
        """Persist a finalised trip plan as a JSON file and return its id,
        total cost, and file path."""
        log_call(
            "create_itinerary",
            trip_name=trip_name,
            hotel_name=hotel_name,
            checkin=checkin,
            checkout=checkout,
        )
        itinerary_id = "IT-" + uuid.uuid4().hex[:8]
        total_cost = round(total_flight_cost + total_hotel_cost, 2)

        itinerary = {
            "itinerary_id": itinerary_id,
            "trip_name": trip_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "flight_id": flight_id,
            "hotel_id": hotel_id,
            "hotel_name": hotel_name,
            "checkin": checkin,
            "checkout": checkout,
            "total_flight_cost": round(total_flight_cost, 2),
            "total_hotel_cost": round(total_hotel_cost, 2),
            "total_cost": total_cost,
            "daily_schedule": daily_schedule,
            "notes": notes,
        }

        try:
            ITINERARIES_DIR.mkdir(parents=True, exist_ok=True)
            file_path = ITINERARIES_DIR / f"{itinerary_id}.json"
            file_path.write_text(json.dumps(itinerary, indent=2), encoding="utf-8")
        except OSError as e:
            log_result("create_itinerary", f"FAILED to write file: {e}")
            return {"error": f"Failed to write itinerary file: {e}"}

        log_result("create_itinerary", f"saved {itinerary_id} (total ${total_cost})")
        return {
            "itinerary_id": itinerary_id,
            "trip_name": trip_name,
            "total_cost": total_cost,
            "file_path": str(file_path),
            "message": f"Itinerary '{trip_name}' saved as {itinerary_id}.",
        }
