import logging
import math
import os
from datetime import datetime, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)

MOCK_COORDS = {"lat": 19.4326, "lng": -99.1332}

MOCK_PLACES = [
    {
        "place_id": "mock-place-001",
        "description": "Av. Paseo de la Reforma 222, Juárez, 06600 Ciudad de México, CDMX",
        "lat": 19.426,
        "lng": -99.158,
    },
    {
        "place_id": "mock-place-002",
        "description": "Av. Paseo de la Reforma 300, Juárez, 06600 Ciudad de México, CDMX",
        "lat": 19.428,
        "lng": -99.160,
    },
]

GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    EARTH_RADIUS_KM = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _mock_geocode(address: str) -> dict:
    return {
        "success": True,
        "result": {
            "lat": MOCK_COORDS["lat"],
            "lng": MOCK_COORDS["lng"],
            "formatted_address": f"{address}, Ciudad de México, CDMX, Mexico",
            "components": {
                "street": address.split(",")[0].strip() if "," in address else address,
                "city": "Ciudad de México",
                "state": "Ciudad de México",
                "country": "México",
            },
            "place_id": "mock-place-center",
        },
        "mock": True,
    }


def _mock_reverse_geocode(lat: float, lng: float) -> dict:
    return {
        "success": True,
        "result": {
            "lat": lat,
            "lng": lng,
            "formatted_address": f"{lat:.4f}, {lng:.4f}, Ciudad de México, CDMX, Mexico",
            "components": {"city": "Ciudad de México", "state": "Ciudad de México", "country": "México"},
            "place_id": "mock-place-reverse",
        },
        "mock": True,
    }


def _mock_places_autocomplete(query: str) -> list[dict]:
    return [p for p in MOCK_PLACES if query.lower() in p["description"].lower()] or MOCK_PLACES


class GoogleMapsClient:
    def __init__(self):
        self._api_key = os.getenv("GOOGLE_API_KEY")
        self._mock_mode = not self._api_key
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = timedelta(hours=1)

        if self._mock_mode:
            logger.info("GOOGLE_API_KEY no configurada → modo mock")
        else:
            logger.info("GOOGLE_API_KEY configurada → modo real")

    def _cache_get(self, key: str) -> Any | None:
        if key in self._cache:
            ts, value = self._cache[key]
            if datetime.now().timestamp() - ts < self._cache_ttl.total_seconds():
                return value
            del self._cache[key]
        return None

    def _cache_set(self, key: str, value: Any) -> None:
        self._cache[key] = (datetime.now().timestamp(), value)

    def geocode(self, address: str) -> dict:
        if self._mock_mode:
            return _mock_geocode(address)

        cached = self._cache_get(f"geocode:{address}")
        if cached:
            return cached

        try:
            resp = requests.get(
                GEOCODING_URL,
                params={"address": address, "key": self._api_key},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            if data["status"] == "ZERO_RESULTS":
                result = {"success": True, "result": None, "error": "No se encontró la dirección"}
                self._cache_set(f"geocode:{address}", result)
                return result

            if data["status"] != "OK":
                return {"success": False, "error": f"Error de geocoding: {data['status']}"}

            location = data["results"][0]["geometry"]["location"]
            components = {}
            for c in data["results"][0].get("address_components", []):
                types = c["types"]
                if "route" in types:
                    components["street"] = c["long_name"]
                elif "street_number" in types:
                    components["number"] = c["long_name"]
                elif "neighborhood" in types or "sublocality" in types:
                    components["neighborhood"] = c["long_name"]
                elif "locality" in types:
                    components["city"] = c["long_name"]
                elif "administrative_area_level_1" in types:
                    components["state"] = c["long_name"]
                elif "postal_code" in types:
                    components["zip"] = c["long_name"]
                elif "country" in types:
                    components["country"] = c["long_name"]

            result = {
                "success": True,
                "result": {
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "formatted_address": data["results"][0]["formatted_address"],
                    "components": components,
                    "place_id": data["results"][0].get("place_id", ""),
                },
                "mock": False,
            }
            self._cache_set(f"geocode:{address}", result)
            return result

        except requests.Timeout:
            return {"success": False, "error": "La solicitud de geocoding excedió el tiempo de espera"}
        except requests.HTTPError as e:
            return {"success": False, "error": f"Error de conexión con Google Maps: {e.response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Error inesperado en geocoding: {str(e)}"}

    def reverse_geocode(self, lat: float, lng: float) -> dict:
        if self._mock_mode:
            return _mock_reverse_geocode(lat, lng)

        cached = self._cache_get(f"reverse:{lat},{lng}")
        if cached:
            return cached

        try:
            resp = requests.get(
                GEOCODING_URL,
                params={"latlng": f"{lat},{lng}", "key": self._api_key},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            if data["status"] != "OK":
                return {"success": False, "error": f"Error de reverse geocoding: {data['status']}"}

            result = {
                "success": True,
                "result": {
                    "lat": lat,
                    "lng": lng,
                    "formatted_address": data["results"][0]["formatted_address"],
                    "place_id": data["results"][0].get("place_id", ""),
                },
                "mock": False,
            }
            self._cache_set(f"reverse:{lat},{lng}", result)
            return result

        except requests.Timeout:
            return {"success": False, "error": "La solicitud de reverse geocoding excedió el tiempo de espera"}
        except requests.HTTPError as e:
            return {"success": False, "error": f"Error de conexión con Google Maps: {e.response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Error inesperado en reverse geocoding: {str(e)}"}

    def distance_matrix(self, origin: dict, destination: dict) -> dict:
        lat1, lng1 = origin.get("lat", 0), origin.get("lng", 0)
        lat2, lng2 = destination.get("lat", 0), destination.get("lng", 0)
        distance_km = round(_haversine(lat1, lng1, lat2, lng2), 1)

        if self._mock_mode:
            return {
                "success": True,
                "distance_km": distance_km,
                "duration_minutes": round(distance_km / 30 * 60),
                "mode": "driving",
                "mock": True,
            }

        try:
            origin_str = f"{lat1},{lng1}"
            dest_str = f"{lat2},{lng2}"
            resp = requests.get(
                DISTANCE_MATRIX_URL,
                params={
                    "origins": origin_str,
                    "destinations": dest_str,
                    "key": self._api_key,
                    "mode": "driving",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            if data["status"] != "OK":
                return {"success": False, "error": f"Error de Distance Matrix: {data['status']}"}

            element = data["rows"][0]["elements"][0]
            if element["status"] != "OK":
                return {"success": True, "distance_km": distance_km, "duration_minutes": None, "mode": "driving"}

            return {
                "success": True,
                "distance_km": round(element["distance"]["value"] / 1000, 1),
                "duration_minutes": round(element["duration"]["value"] / 60),
                "mode": "driving",
                "mock": False,
            }

        except requests.Timeout:
            return {"success": False, "error": "La solicitud de distancia excedió el tiempo de espera"}
        except Exception:
            return {"success": True, "distance_km": distance_km, "duration_minutes": None, "mode": "driving", "mock": True}

    def places_autocomplete(self, query: str, restrict_to_mx: bool = True) -> list[dict]:
        if self._mock_mode:
            return _mock_places_autocomplete(query)

        cached = self._cache_get(f"places:{query}")
        if cached:
            return cached

        try:
            params = {
                "input": query,
                "key": self._api_key,
                "language": "es",
            }
            if restrict_to_mx:
                params["components"] = "country:mx"

            resp = requests.get(PLACES_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data["status"] != "OK":
                return []

            results = []
            for p in data.get("predictions", [])[:5]:
                results.append({
                    "place_id": p["place_id"],
                    "description": p["description"],
                    "lat": None,
                    "lng": None,
                })
            self._cache_set(f"places:{query}", results)
            return results

        except Exception:
            return []
