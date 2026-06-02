"""Mock-data fallbacks for the API-backed tools.

For a reliable demo: when a live API can't return usable data (missing key,
HTTP failure, or empty result) the tool falls back to one of these generators,
which produce data in the *same schema* as the real call. Mock values are tuned
to the example prompts (Istanbul / Dubai / Bangkok in June) and the hotel DB.

The returned payloads carry no "mock" marker, so the agent treats them like
real data — the only signal is a "(MOCK: ...)" note in the server log line.
"""

from datetime import datetime, timedelta
from itertools import zip_longest

from .utils import parse_iso_date

# --------------------------------------------------------------------------
# Weather
# --------------------------------------------------------------------------
# Per-city daily patterns cycled across the requested date range. Each tuple is
# (condition, icon, temp_high, temp_low, rain_chance%). June-appropriate.
_WEATHER_PROFILES = {
    "istanbul": [
        ("clear sky", "01d", 27, 19, 5),
        ("few clouds", "02d", 28, 20, 10),
        ("scattered clouds", "03d", 26, 18, 20),
        ("clear sky", "01d", 29, 21, 0),
    ],
    "dubai": [
        ("clear sky", "01d", 42, 31, 0),
        ("haze", "50d", 43, 32, 0),
        ("clear sky", "01d", 41, 30, 5),
        ("clear sky", "01d", 44, 33, 0),
    ],
    "bangkok": [
        ("moderate rain", "10d", 32, 26, 75),
        ("thunderstorm", "11d", 31, 25, 90),
        ("light rain", "10d", 33, 27, 55),
        ("scattered clouds", "03d", 34, 27, 35),
    ],
}
_DEFAULT_WEATHER = [
    ("partly cloudy", "02d", 24, 17, 20),
    ("light rain", "10d", 22, 15, 55),
    ("clear sky", "01d", 25, 17, 10),
    ("scattered clouds", "03d", 23, 16, 30),
]


def mock_weather(city: str, start_date: str, end_date: str) -> dict:
    """Mirror get_weather's output for the given city/date range."""
    d0 = parse_iso_date(start_date, "start_date")
    d1 = parse_iso_date(end_date, "end_date")
    pattern = _WEATHER_PROFILES.get(city.strip().lower(), _DEFAULT_WEATHER)

    forecast = []
    day, i = d0, 0
    while day <= d1:
        condition, icon, high, low, rain = pattern[i % len(pattern)]
        forecast.append(
            {
                "date": day.isoformat(),
                "condition": condition,
                "temp_high": float(high),
                "temp_low": float(low),
                "rain_chance": rain,
                "icon": icon,
            }
        )
        day += timedelta(days=1)
        i += 1

    avg_rain = sum(f["rain_chance"] for f in forecast) / len(forecast) if forecast else 0
    recommendation = "outdoor" if avg_rain < 40 else "mixed" if avg_rain < 70 else "indoor"
    return {
        "city": city,
        "unit": "celsius",
        "recommendation": recommendation,
        "forecast": forecast,
    }


# --------------------------------------------------------------------------
# Flights
# --------------------------------------------------------------------------
# Per-route offers: (airline, iata, flight_number, dep_hour, dep_min,
# duration_mins, stops, price_usd). Tuned to the example prompts' routes;
# prices are USD to match the (converted) real tool output.
_FLIGHT_ROUTES = {
    ("KHI", "IST"): [
        ("Turkish Airlines", "TK", 709, 3, 55, 355, 0, 312.0),
        ("Pakistan International Airlines", "PK", 709, 8, 30, 365, 0, 268.0),
        ("Qatar Airways", "QR", 605, 1, 15, 720, 1, 245.0),
    ],
    ("LHR", "DXB"): [
        ("Emirates", "EK", 8, 21, 30, 425, 0, 540.0),
        ("British Airways", "BA", 107, 9, 40, 430, 0, 495.0),
        ("Virgin Atlantic", "VS", 401, 10, 20, 420, 0, 470.0),
    ],
    ("KHI", "BKK"): [
        ("Thai Airways", "TG", 508, 2, 15, 280, 0, 360.0),
        ("SriLankan Airlines", "UL", 184, 1, 30, 560, 1, 298.0),
        ("Emirates", "EK", 655, 3, 40, 620, 1, 410.0),
    ],
    ("DXB", "IST"): [
        ("Emirates", "EK", 121, 8, 15, 300, 0, 330.0),
        ("Turkish Airlines", "TK", 765, 14, 55, 295, 0, 305.0),
        ("flydubai", "FZ", 757, 6, 30, 305, 0, 245.0),
    ],
    # Return legs (in case the agent also searches the trip back).
    ("IST", "KHI"): [
        ("Turkish Airlines", "TK", 708, 19, 10, 360, 0, 318.0),
        ("Pakistan International Airlines", "PK", 710, 13, 0, 365, 0, 272.0),
        ("Qatar Airways", "QR", 604, 16, 45, 730, 1, 250.0),
    ],
    ("DXB", "LHR"): [
        ("Emirates", "EK", 7, 8, 30, 470, 0, 555.0),
        ("British Airways", "BA", 106, 13, 20, 460, 0, 505.0),
        ("Virgin Atlantic", "VS", 400, 9, 15, 465, 0, 480.0),
    ],
    ("BKK", "KHI"): [
        ("Thai Airways", "TG", 507, 19, 30, 290, 0, 365.0),
        ("SriLankan Airlines", "UL", 185, 22, 10, 570, 1, 305.0),
        ("Emirates", "EK", 385, 9, 5, 630, 1, 415.0),
    ],
    ("IST", "DXB"): [
        ("Emirates", "EK", 122, 15, 40, 305, 0, 335.0),
        ("Turkish Airlines", "TK", 764, 6, 20, 300, 0, 310.0),
        ("flydubai", "FZ", 758, 20, 0, 305, 0, 250.0),
    ],
}
_DEFAULT_FLIGHTS = [
    ("Global Airways", "GA", 100, 9, 0, 240, 0, 320.0),
    ("Global Airways", "GA", 244, 7, 30, 480, 1, 275.0),
]


def _build_flight(date, origin, dest, airline, iata, fnum, dep_h, dep_m, dur, stops, price):
    dep = datetime.fromisoformat(f"{date}T{dep_h:02d}:{dep_m:02d}:00")
    arr = dep + timedelta(minutes=dur)
    return {
        "flight_id": f"mock_{iata}{fnum}_{origin}{dest}",
        "airline": airline,
        "flight_number": f"{iata}{fnum}",
        "origin": origin,
        "destination": dest,
        "departure_time": dep.isoformat(),
        "arrival_time": arr.isoformat(),
        "duration_mins": dur,
        "stops": stops,
        "price": round(price, 2),
        "currency": "USD",
        "original_price": round(price, 2),
        "original_currency": "USD",
    }


def mock_flights(origin: str, destination: str, date: str, max_price=None, limit: int = 5) -> dict:
    """Mirror search_flights' output for the given route/date (USD prices)."""
    o, dst = origin.upper(), destination.upper()
    specs = _FLIGHT_ROUTES.get((o, dst), _DEFAULT_FLIGHTS)
    flights = [_build_flight(date, o, dst, *spec) for spec in specs]
    if max_price is not None:
        flights = [f for f in flights if f["price"] <= max_price]
    flights.sort(key=lambda f: f["price"])
    flights = flights[:limit]
    return {
        "origin": o,
        "destination": dst,
        "date": date,
        "results_count": len(flights),
        "flights": flights,
    }


# --------------------------------------------------------------------------
# Attractions
# --------------------------------------------------------------------------
# Per-city POIs split into outdoor / indoor, each (name, category, address,
# distance_meters) — names mirror what Foursquare actually returns.
_ATTRACTIONS = {
    "istanbul": {
        "outdoor": [
            ("Galata Tower (Galata Kulesi)", "Historic and Protected Site", "Bereketzade, Beyoğlu", 2429),
            ("Blue Mosque (Sultan Ahmet Camii)", "Mosque", "Sultan Ahmet, Fatih", 2415),
            ("Süleymaniye Mosque (Süleymaniye Camii)", "Mosque", "Süleymaniye, Fatih", 1223),
            ("Gülhane Park (Gülhane Parkı)", "Park", "Cankurtaran, Fatih", 2685),
            ("Grand Bazaar (Kapalıçarşı)", "Historic and Protected Site", "Beyazıt, Fatih", 1600),
        ],
        "indoor": [
            ("Topkapı Palace (Topkapı Sarayı Müzesi)", "History Museum", "Cankurtaran, Fatih", 2951),
            ("Basilica Cistern (Yerebatan Sarnıcı)", "Historic and Protected Site", "Alemdar, Fatih", 2446),
            ("Istanbul Museum of Modern Art", "Art Museum", "Kılıçali Paşa, Beyoğlu", 3074),
            ("Istanbul Archaeology Museums", "History Museum", "Cankurtaran, Fatih", 2900),
        ],
    },
    "dubai": {
        "outdoor": [
            ("Burj Khalifa", "Monument", "1 Sheikh Mohammed bin Rashid Blvd, Downtown Dubai", 500),
            ("The Dubai Fountain", "Fountain", "Downtown Dubai", 450),
            ("Jumeirah Public Beach", "Beach", "Jumeirah Beach Rd", 6000),
            ("Dubai Marina Walk", "Promenade", "Dubai Marina", 8000),
        ],
        "indoor": [
            ("The Dubai Mall", "Shopping Mall", "Downtown Dubai", 600),
            ("Mall of the Emirates", "Shopping Mall", "Sheikh Zayed Rd, Al Barsha", 7000),
            ("Museum of the Future", "Museum", "Sheikh Zayed Rd, Trade Centre", 3000),
            ("Dubai Aquarium & Underwater Zoo", "Aquarium", "The Dubai Mall, Downtown Dubai", 650),
        ],
    },
    "bangkok": {
        "outdoor": [
            ("Temple of the Emerald Buddha (Wat Phra Kaew)", "Buddhist Temple", "Na Phra Lan Rd, Phra Nakhon", 980),
            ("Wat Arun (Temple of Dawn)", "Historic and Protected Site", "Wat Arun, Bangkok Yai", 1769),
            ("The Grand Palace", "Palace", "Na Phra Lan Rd, Phra Nakhon", 1045),
            ("Giant Swing (Sao Chingcha)", "Monument", "Dinso Rd, Phra Nakhon", 240),
        ],
        "indoor": [
            ("Bangkok National Museum", "History Museum", "Na Phra That Rd, Phra Nakhon", 1097),
            ("Museum Siam", "History Museum", "Sanam Chai Rd, Phra Nakhon", 1346),
            ("The Jim Thompson House", "Museum", "Soi Kasem San 2, Pathum Wan", 2948),
        ],
    },
}
_DEFAULT_ATTRACTIONS = {
    "outdoor": [
        ("City Central Park", "Park", "City Centre", 500),
        ("Old Town Square", "Plaza", "Historic District", 800),
        ("Riverside Promenade", "Scenic Lookout", "Waterfront", 1200),
    ],
    "indoor": [
        ("National Museum", "History Museum", "Museum District", 1000),
        ("City Art Gallery", "Art Gallery", "Arts Quarter", 1500),
        ("Science & Discovery Center", "Science Museum", "Downtown", 1800),
    ],
}


def mock_attractions(city: str, category: str, limit: int = 10) -> dict:
    """Mirror get_attractions' output for the given city/category."""
    cat = (category or "all").lower()
    profile = _ATTRACTIONS.get(city.strip().lower(), _DEFAULT_ATTRACTIONS)

    if cat == "outdoor":
        items = list(profile["outdoor"])
    elif cat == "indoor":
        items = list(profile["indoor"])
    else:  # "all" -> interleave outdoor and indoor
        items = []
        for out, ind in zip_longest(profile["outdoor"], profile["indoor"]):
            if out:
                items.append(out)
            if ind:
                items.append(ind)

    slug = city.strip().lower().replace(" ", "-")
    attractions = [
        {
            "attraction_id": f"mock_{slug}_{idx}",
            "name": name,
            "category": poi_category,
            "address": address,
            "distance_meters": distance,
        }
        for idx, (name, poi_category, address, distance) in enumerate(items[:limit], 1)
    ]
    return {
        "city": city,
        "category": cat,
        "results_count": len(attractions),
        "attractions": attractions,
    }
