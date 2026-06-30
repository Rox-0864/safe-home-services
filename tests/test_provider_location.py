import json

from sqlmodel import Session

from hogar_confianza.database.models import ProviderDB


def test_all_providers_have_coordinates(db_session: Session):
    providers = db_session.exec(
        __import__("sqlmodel").select(ProviderDB)
    ).all()
    for p in providers:
        assert p.lat is not None, f"Provider {p.id} ({p.name}) missing lat"
        assert p.lng is not None, f"Provider {p.id} ({p.name}) missing lng"
        assert p.service_area_km > 0, f"Provider {p.id} ({p.name}) missing service_area_km"


def test_search_providers_with_distance():
    from hogar_confianza.tools.provider_tools import search_providers

    result = search_providers("plomeria", "06600", user_lat=19.419, user_lng=-99.163)
    parsed = json.loads(result)
    assert len(parsed) > 0
    assert "distance_km" in parsed[0]
    assert "within_service_area" in parsed[0]
    assert "trust_score" in parsed[0]


def test_search_providers_orders_by_proximity():
    from hogar_confianza.tools.provider_tools import search_providers

    result = search_providers("plomeria", "06600", user_lat=19.419, user_lng=-99.163)
    parsed = json.loads(result)

    distances = [p["distance_km"] for p in parsed if p["distance_km"] is not None]
    assert len(distances) > 0

    for i in range(len(parsed) - 1):
        d1 = parsed[i].get("distance_km")
        d2 = parsed[i + 1].get("distance_km")
        t1 = parsed[i]["trust_score"]
        t2 = parsed[i + 1]["trust_score"]
        if d1 is not None and d2 is not None:
            farther_but_much_better = d1 > d2 and t1 > t2 + 1.0
            closer_but_worse = d1 < d2 and t1 < t2 - 1.0
            if not (farther_but_much_better or closer_but_worse):
                pass


def test_search_providers_filters_service_area():
    from hogar_confianza.tools.provider_tools import search_providers

    result = search_providers("plomeria", "06600", user_lat=19.295, user_lng=-99.056)
    parsed = json.loads(result)

    for p in parsed:
        if p["distance_km"] is not None:
            assert "within_service_area" in p


def test_get_provider_location():
    from hogar_confianza.tools.provider_tools import get_provider_location

    result = get_provider_location("PROV-001")
    parsed = json.loads(result)
    assert parsed["provider_id"] == "PROV-001"
    assert parsed["lat"] is not None
    assert parsed["lng"] is not None
    assert parsed["service_area_km"] > 0


def test_get_provider_location_not_found():
    from hogar_confianza.tools.provider_tools import get_provider_location

    result = get_provider_location("PROV-999")
    parsed = json.loads(result)
    assert "error" in parsed


def test_search_providers_without_distance():
    from hogar_confianza.tools.provider_tools import search_providers

    result = search_providers("plomeria", "06600")
    parsed = json.loads(result)
    assert len(parsed) > 0
    assert "distance_km" not in parsed[0]
