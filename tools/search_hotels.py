"""search_hotels — hotel availability from the local SQLite training DB.

No external API. Reads db/hotels_training.db (path resolved from paths.py so
it works regardless of the process working directory).

Schema:
  cities (id, name, country, iata_code)
  hotels (id, city_id, name, stars, rating, price_per_night, address,
          amenities, cancellation_policy, available)
  rooms  (id, hotel_id, room_type, price_multiplier, max_guests)
"""

import sqlite3
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from paths import DB_PATH
from .utils import log_call, log_result, parse_iso_date

_BASE_SQL = """
SELECT h.id            AS hotel_id,
       h.name          AS name,
       c.name          AS city,
       c.country       AS country,
       h.stars         AS stars,
       h.rating        AS rating,
       h.address       AS address,
       h.amenities     AS amenities,
       h.cancellation_policy AS cancellation_policy,
       r.room_type     AS room_type,
       r.max_guests    AS max_guests,
       h.price_per_night AS price_per_night,
       r.price_multiplier AS price_multiplier
FROM hotels h
JOIN cities c ON h.city_id = c.id
JOIN rooms  r ON r.hotel_id = h.id
WHERE LOWER(c.name) = LOWER(?)
  AND h.available = 1
  AND r.room_type = ?
"""


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    def search_hotels(
        city: Annotated[str, Field(description="City name, e.g. 'Istanbul'")],
        checkin: Annotated[str, Field(description="Check-in date, ISO format YYYY-MM-DD")],
        checkout: Annotated[str, Field(description="Check-out date, ISO format YYYY-MM-DD")],
        max_price_per_night: Annotated[
            Optional[float], Field(description="Optional ceiling on price per night (USD)")
        ] = None,
        min_rating: Annotated[
            Optional[float], Field(description="Optional minimum guest rating (0-5)")
        ] = None,
        cancellation_policy: Annotated[
            Optional[str],
            Field(description="Optional filter: 'free_cancellation' or 'non_refundable'"),
        ] = None,
        room_type: Annotated[
            str, Field(description="Room type: 'Standard', 'Deluxe', 'Suite', or 'Family'")
        ] = "Standard",
        limit: Annotated[int, Field(description="Maximum number of hotels to return", ge=1, le=50)] = 10,
    ) -> dict:
        """Find available hotels in a city for a date range. Computes per-night
        and total price for the chosen room type and returns them sorted by
        rating (desc) then price (asc)."""
        log_call(
            "search_hotels",
            city=city,
            checkin=checkin,
            checkout=checkout,
            room_type=room_type,
            max_price_per_night=max_price_per_night,
            min_rating=min_rating,
            cancellation_policy=cancellation_policy,
        )
        try:
            d_in = parse_iso_date(checkin, "checkin")
            d_out = parse_iso_date(checkout, "checkout")
        except ValueError as e:
            return {"error": str(e)}

        nights = (d_out - d_in).days
        if nights <= 0:
            return {"error": "checkout must be after checkin (stay must be at least 1 night)."}

        sql_parts = [_BASE_SQL]
        params: list = [city, room_type]
        if max_price_per_night is not None:
            sql_parts.append("AND (h.price_per_night * r.price_multiplier) <= ?")
            params.append(max_price_per_night)
        if min_rating is not None:
            sql_parts.append("AND h.rating >= ?")
            params.append(min_rating)
        if cancellation_policy is not None:
            sql_parts.append("AND h.cancellation_policy = ?")
            params.append(cancellation_policy)
        sql_parts.append("ORDER BY h.rating DESC, (h.price_per_night * r.price_multiplier) ASC")
        sql_parts.append("LIMIT ?")
        params.append(limit)
        sql = "\n".join(sql_parts)

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}
        finally:
            if conn is not None:
                conn.close()

        hotels = []
        for r in rows:
            room_price = round(r["price_per_night"] * r["price_multiplier"], 2)
            hotels.append(
                {
                    "hotel_id": r["hotel_id"],
                    "name": r["name"],
                    "city": r["city"],
                    "country": r["country"],
                    "stars": r["stars"],
                    "rating": r["rating"],
                    "address": r["address"],
                    "amenities": [a.strip() for a in (r["amenities"] or "").split(",") if a.strip()],
                    "cancellation_policy": r["cancellation_policy"],
                    "room_type": r["room_type"],
                    "max_guests": r["max_guests"],
                    "price_per_night": room_price,
                    "total_price": round(room_price * nights, 2),
                    "nights": nights,
                    "checkin": checkin,
                    "checkout": checkout,
                }
            )

        log_result("search_hotels", f"{len(hotels)} hotels in {city} ({nights} nights)")
        return {
            "city": city,
            "checkin": checkin,
            "checkout": checkout,
            "nights": nights,
            "room_type": room_type,
            "results_count": len(hotels),
            "hotels": hotels,
        }
