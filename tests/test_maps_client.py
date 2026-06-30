from unittest.mock import patch

from hogar_confianza.tools.maps_client import GoogleMapsClient, _haversine


def test_haversine_roma_to_condesa():
    dist = _haversine(19.419, -99.163, 19.413, -99.176)
    assert 1.0 <= dist <= 2.0


def test_haversine_same_point():
    dist = _haversine(19.4326, -99.1332, 19.4326, -99.1332)
    assert dist == 0.0


def test_haversine_coyoacan_to_tlahuac():
    dist = _haversine(19.350, -99.162, 19.295, -99.056)
    assert 10.0 <= dist <= 15.0


def test_mock_mode_geocode(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    client = GoogleMapsClient()
    assert client._mock_mode is True

    result = client.geocode("Av. Reforma 222, CDMX")
    assert result["success"] is True
    assert result["mock"] is True
    assert result["result"]["lat"] == 19.4326
    assert result["result"]["lng"] == -99.1332
    assert "place_id" in result["result"]


def test_mock_mode_reverse_geocode(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    client = GoogleMapsClient()

    result = client.reverse_geocode(19.4326, -99.1332)
    assert result["success"] is True
    assert result["mock"] is True


def test_mock_mode_distance_matrix(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    client = GoogleMapsClient()

    result = client.distance_matrix(
        {"lat": 19.419, "lng": -99.163},
        {"lat": 19.413, "lng": -99.176},
    )
    assert result["success"] is True
    assert result["mock"] is True
    assert isinstance(result["distance_km"], float)
    assert result["distance_km"] > 0


def test_mock_mode_places_autocomplete(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    client = GoogleMapsClient()

    results = client.places_autocomplete("Reforma")
    assert len(results) > 0
    assert results[0]["place_id"].startswith("mock-")


def test_cache_hit(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    client = GoogleMapsClient()

    result1 = client.geocode("Av. Reforma 222, CDMX")
    result2 = client.geocode("Av. Reforma 222, CDMX")
    assert result1 == result2


def test_geoocode_with_real_api_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    client = GoogleMapsClient()
    assert client._mock_mode is False

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": "OK",
            "results": [{
                "geometry": {"location": {"lat": 19.426, "lng": -99.158}},
                "formatted_address": "Av. Paseo de la Reforma 222, CDMX",
                "address_components": [
                    {"long_name": "Av. Paseo de la Reforma", "types": ["route"]},
                    {"long_name": "222", "types": ["street_number"]},
                    {"long_name": "06600", "types": ["postal_code"]},
                    {"long_name": "Ciudad de México", "types": ["locality"]},
                    {"long_name": "México", "types": ["country"]},
                ],
                "place_id": "ChIJ-test",
            }],
        }

        result = client.geocode("Av. Reforma 222, CDMX")
        assert result["success"] is True
        assert result["mock"] is False
        assert result["result"]["lat"] == 19.426
        assert result["result"]["components"]["street"] == "Av. Paseo de la Reforma"
        assert result["result"]["components"]["zip"] == "06600"


def test_geocode_zero_results(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    client = GoogleMapsClient()

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ZERO_RESULTS", "results": []}

        result = client.geocode("Calle Falsa 99999, Colonia Inexistente")
        assert result["success"] is True
        assert result["result"] is None
        assert "No se encontró" in result["error"]


def test_reverse_geocode_with_real_api_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    client = GoogleMapsClient()

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": "OK",
            "results": [{
                "formatted_address": "Av. Reforma, CDMX",
                "place_id": "ChIJ-test-reverse",
            }],
        }

        result = client.reverse_geocode(19.426, -99.158)
        assert result["success"] is True
        assert result["mock"] is False


def test_distance_matrix_timeout(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    client = GoogleMapsClient()

    with patch("requests.get") as mock_get:
        mock_get.side_effect = __import__("requests").Timeout()

        result = client.distance_matrix(
            {"lat": 19.419, "lng": -99.163},
            {"lat": 19.413, "lng": -99.176},
        )
        assert result["success"] is False
        assert "tiempo de espera" in result["error"]
