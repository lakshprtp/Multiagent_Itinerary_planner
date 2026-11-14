import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

# Mapping of popular cities/countries to major destination airport IATA codes
AIRPORT_CODES = {
    # Asia
    "tokyo": "HND", "japan": "HND", "osaka": "KIX", "kyoto": "KIX",
    "bangkok": "BKK", "thailand": "BKK", "phuket": "HKT",
    "bali": "DPS", "indonesia": "DPS", "jakarta": "CGK",
    "singapore": "SIN",
    "dubai": "DXB", "uae": "DXB", "abu dhabi": "AUH",
    "delhi": "DEL", "mumbai": "BOM", "india": "DEL", "goa": "GOI", "bengaluru": "BLR", "bangalore": "BLR",
    "maldives": "MLE", "male": "MLE",
    "seoul": "ICN", "korea": "ICN",
    "vietnam": "HAN", "hanoi": "HAN", "ho chi minh": "SGN", "da nang": "DAD",
    "kuala lumpur": "KUL", "malaysia": "KUL",
    "hong kong": "HKG",

    # Europe
    "paris": "CDG", "france": "CDG", "nice": "NCE",
    "rome": "FCO", "italy": "FCO", "milan": "MXP", "venice": "VCE",
    "london": "LHR", "uk": "LHR", "england": "LHR", "manchester": "MAN",
    "amsterdam": "AMS", "netherlands": "AMS",
    "barcelona": "BCN", "madrid": "MAD", "spain": "BCN",
    "switzerland": "ZRH", "zurich": "ZRH", "geneva": "GVA",
    "berlin": "BER", "germany": "FRA", "frankfurt": "FRA", "munich": "MUC",
    "istanbul": "IST", "turkey": "IST",
    "athens": "ATH", "greece": "ATH", "santorini": "JTR",
    "vienna": "VIE", "austria": "VIE",
    "prague": "PRG", "czech": "PRG",

    # Americas
    "new york": "JFK", "nyc": "JFK", "usa": "JFK",
    "los angeles": "LAX", "san francisco": "SFO",
    "chicago": "ORD", "miami": "MIA", "las vegas": "LAS",
    "toronto": "YYZ", "canada": "YYZ", "vancouver": "YVR",

    # Middle East & Africa & Oceania
    "cairo": "CAI", "egypt": "CAI",
    "sydney": "SYD", "australia": "SYD", "melbourne": "MEL",
}


def extract_destination_iata(query: str) -> str | None:
    """Extract an arrival IATA code from the user query."""
    q_lower = query.lower()

    # 1. Match known cities and countries
    for name, iata in AIRPORT_CODES.items():
        if re.search(r'\b' + re.escape(name) + r'\b', q_lower):
            return iata

    # 2. Check for explicit 3-letter uppercase IATA codes in original query
    words = re.findall(r'\b[A-Z]{3}\b', query)
    for w in words:
        if w in AIRPORT_CODES.values():
            return w

    return None


def search_flights(query: str) -> str:
    url = "http://api.aviationstack.com/v1/flights"
    arr_iata = extract_destination_iata(query)

    flights = []
    # Only query AviationStack if we identified a specific destination airport
    if arr_iata:
        params = {
            "access_key": API_KEY,
            "limit": 5,
            "arr_iata": arr_iata
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                for flight in data["data"][:5]:
                    airline = flight.get("airline", {}).get("name", "Unknown Airline")
                    flight_no = flight.get("flight", {}).get("iata", "N/A")
                    dep_info = flight.get("departure", {})
                    arr_info = flight.get("arrival", {})

                    departure = dep_info.get("airport") or dep_info.get("iata") or "Unknown"
                    arrival = arr_info.get("airport") or arr_info.get("iata") or "Unknown"
                    status = flight.get("flight_status", "Scheduled")

                    flights.append(
                        f"✈️ **{airline}** ({flight_no})\n"
                        f"   • Route: {departure} → {arrival}\n"
                        f"   • Status: {status.capitalize()}"
                    )
        except Exception as e:
            print(f"AviationStack API error: {e}")

    # Fallback to Tavily web search if no IATA code was matched or AviationStack returned no results
    if not flights:
        try:
            from tools.tavily_tool import tavily_search
            fallback_query = f"Flights and airlines for {query}"
            return tavily_search(fallback_query)
        except Exception:
            return "No specific flight details found for this destination."

    return "\n\n".join(flights)
