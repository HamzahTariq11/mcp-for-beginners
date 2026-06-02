"""search_flights — one-way flight offers via the Duffel API (test mode).

Duffel test tokens (duffel_test_...) have an unlimited balance and return
synthetic but realistically-shaped offers, including live prices, for any
route/date. Flow: POST an offer request with return_offers=true and read the
offers straight back.

Prices are normalised to USD (Duffel returns the account's currency, often
GBP) so flight costs line up with the USD hotel prices in the itinerary. The
original amount/currency are kept on each result for transparency.
"""

import os
import re
import httpx
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .utils import log_call, log_result, parse_iso_date

DUFFEL_URL = "https://api.duffel.com/air/offer_requests"
DUFFEL_VERSION = "v2"

# ISO-8601 durations like "PT4H30M" or "P1DT2H".
_DURATION_RE = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?")

# Approximate FX rates: 1 unit of currency -> this many USD. Used to normalise
# Duffel offer prices (account currency) to USD so they match hotel prices.
_USD_PER = {
    "USD": 1.0,
    "GBP": 1.27,
    "EUR": 1.08,
    "AED": 0.27,
    "PKR": 0.0036,
    "THB": 0.028,
    "TRY": 0.031,
}


def _iso_duration_to_minutes(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    m = _DURATION_RE.fullmatch(value)
    if not m:
        return None
    days, hours, mins, secs = (int(x) if x else 0 for x in m.groups())
    return days * 1440 + hours * 60 + mins + round(secs / 60)


def _to_usd(amount: float, currency: Optional[str]) -> Optional[float]:
    """Convert an amount to USD, or None if the currency is unknown."""
    rate = _USD_PER.get((currency or "USD").upper())
    return round(amount * rate, 2) if rate is not None else None


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        )
    )
    async def search_flights(
        origin: Annotated[str, Field(description="Origin IATA airport code, e.g. 'KHI'")],
        destination: Annotated[str, Field(description="Destination IATA airport code, e.g. 'IST'")],
        date: Annotated[str, Field(description="Departure date, ISO format YYYY-MM-DD")],
        max_price: Annotated[
            Optional[float],
            Field(description="Optional budget ceiling in USD; flights priced above this are dropped"),
        ] = None,
        limit: Annotated[int, Field(description="Maximum number of flights to return", ge=1, le=20)] = 5,
    ) -> dict:
        """Search one-way flight offers for a route and date. Returns offers
        sorted by price (cheapest first), each with airline, times, duration,
        number of stops, and price."""
        log_call(
            "search_flights",
            origin=origin,
            destination=destination,
            date=date,
            max_price=max_price,
            limit=limit,
        )
        try:
            parse_iso_date(date, "date")
        except ValueError as e:
            return {"error": str(e)}

        api_key = os.getenv("DUFFEL_API_KEY")
        if not api_key:
            return {"error": "DUFFEL_API_KEY is not set in the environment."}

        payload = {
            "data": {
                "slices": [
                    {
                        "origin": origin.upper(),
                        "destination": destination.upper(),
                        "departure_date": date,
                    }
                ],
                "passengers": [{"type": "adult"}],
                "cabin_class": "economy",
            }
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Duffel-Version": DUFFEL_VERSION,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(
                    DUFFEL_URL,
                    params={"return_offers": "true"},
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            return {"error": f"Duffel API error {e.response.status_code}: {e.response.text[:300]}"}
        except httpx.HTTPError as e:
            return {"error": f"Failed to reach Duffel API: {e}"}

        offers = (resp.json().get("data") or {}).get("offers") or []
        flights = []
        for offer in offers:
            try:
                raw = float(offer.get("total_amount") or 0)
            except (TypeError, ValueError):
                raw = 0.0
            raw_ccy = offer.get("total_currency", "USD")
            usd = _to_usd(raw, raw_ccy)
            price = usd if usd is not None else round(raw, 2)
            currency = "USD" if usd is not None else raw_ccy
            if max_price is not None and price > max_price:
                continue

            slice0 = (offer.get("slices") or [{}])[0]
            segments = slice0.get("segments") or []
            first_seg = segments[0] if segments else {}
            last_seg = segments[-1] if segments else {}
            carrier = first_seg.get("marketing_carrier") or offer.get("owner") or {}
            flight_no = first_seg.get("marketing_carrier_flight_number") or ""

            flights.append(
                {
                    "flight_id": offer.get("id"),
                    "airline": (offer.get("owner") or {}).get("name"),
                    "flight_number": f"{carrier.get('iata_code', '')}{flight_no}".strip(),
                    "origin": (slice0.get("origin") or {}).get("iata_code", origin.upper()),
                    "destination": (slice0.get("destination") or {}).get("iata_code", destination.upper()),
                    "departure_time": first_seg.get("departing_at"),
                    "arrival_time": last_seg.get("arriving_at"),
                    "duration_mins": _iso_duration_to_minutes(slice0.get("duration")),
                    "stops": max(len(segments) - 1, 0),
                    "price": price,
                    "currency": currency,
                    "original_price": round(raw, 2),
                    "original_currency": raw_ccy,
                }
            )

        flights.sort(key=lambda f: f["price"])
        flights = flights[:limit]

        if not flights:
            log_result("search_flights", "0 flights found")
            return {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "date": date,
                "results_count": 0,
                "flights": [],
                "message": "No flights found for the given criteria.",
            }
        log_result(
            "search_flights",
            f"{len(flights)} flights, cheapest ${flights[0]['price']} {flights[0]['currency']}",
        )
        return {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "date": date,
            "results_count": len(flights),
            "flights": flights,
        }
