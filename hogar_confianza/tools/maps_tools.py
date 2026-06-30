import json

from hogar_confianza.tools.maps_client import GoogleMapsClient

_client = GoogleMapsClient()


def geocode_address(address: str) -> str:
    result = _client.geocode(address)
    return json.dumps(result, ensure_ascii=False, indent=2)


def validate_address(address: str) -> str:
    result = _client.geocode(address)
    if not result.get("success"):
        return json.dumps(result, ensure_ascii=False, indent=2)

    geo = result.get("result")
    if geo is None:
        return json.dumps({
            "success": True,
            "valid": False,
            "formatted_address": None,
            "suggestions": [],
            "mock": result.get("mock", False),
        }, ensure_ascii=False, indent=2)

    return json.dumps({
        "success": True,
        "valid": True,
        "formatted_address": geo["formatted_address"],
        "lat": geo["lat"],
        "lng": geo["lng"],
        "suggestions": [],
        "mock": result.get("mock", False),
    }, ensure_ascii=False, indent=2)


def calculate_distance(origin: dict, destination: dict) -> str:
    result = _client.distance_matrix(origin, destination)
    return json.dumps(result, ensure_ascii=False, indent=2)


def search_places(query: str) -> str:
    results = _client.places_autocomplete(query)
    return json.dumps({
        "success": True,
        "results": results,
    }, ensure_ascii=False, indent=2)
