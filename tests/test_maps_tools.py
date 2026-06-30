import json

from hogar_confianza.tools import maps_tools


def test_geocode_address_returns_json_string():
    result = maps_tools.geocode_address("Av. Reforma 222, CDMX")
    parsed = json.loads(result)
    assert parsed["success"] is True
    assert parsed["mock"] is True
    assert "result" in parsed


def test_validate_address_valid():
    result = maps_tools.validate_address("Av. Reforma 222, CDMX")
    parsed = json.loads(result)
    assert parsed["success"] is True
    assert parsed["valid"] is True
    assert parsed["formatted_address"] is not None
    assert parsed["lat"] is not None


def test_calculate_distance():
    result = maps_tools.calculate_distance(
        {"lat": 19.419, "lng": -99.163},
        {"lat": 19.413, "lng": -99.176},
    )
    parsed = json.loads(result)
    assert parsed["success"] is True
    assert isinstance(parsed["distance_km"], float)
    assert parsed["distance_km"] > 0


def test_search_places():
    result = maps_tools.search_places("Reforma 222, CDMX")
    parsed = json.loads(result)
    assert parsed["success"] is True
    assert isinstance(parsed["results"], list)
    assert len(parsed["results"]) > 0


def test_geocode_address_roundtrip():
    result = maps_tools.geocode_address("Calle 123, Colonia Centro, CDMX")
    parsed = json.loads(result)
    assert "success" in parsed
    assert "mock" in parsed
