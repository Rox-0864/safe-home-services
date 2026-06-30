from sqlmodel import Session, text

from hogar_confianza.database.models import ProviderDB

PROVIDERS_SEED_DATA = [
    dict(id="PROV-001", name="Juan Pérez", service="plomeria", rating=4.5, verified=True,
         zip_codes=["06600", "06700", "06500"], phone="+525512345678", years_experience=8,
         has_insurance=True, completed_jobs=342, trust_score=4.7,
         lat=19.419, lng=-99.163, service_area_km=10.0, address_formatted="Col. Roma Norte, CDMX"),
    dict(id="PROV-002", name="María García", service="electricidad", rating=4.8, verified=True,
         zip_codes=["06600", "06601", "06800"], phone="+525512345679", years_experience=12,
         has_insurance=True, completed_jobs=567, trust_score=4.9,
         lat=19.386, lng=-99.169, service_area_km=8.0, address_formatted="Col. Del Valle Centro, CDMX"),
    dict(id="PROV-003", name="Carlos López", service="pintura", rating=4.2, verified=True,
         zip_codes=["06700", "06701", "06600"], phone="+525512345680", years_experience=5,
         has_insurance=False, completed_jobs=189, trust_score=3.8,
         lat=19.413, lng=-99.176, service_area_km=6.0, address_formatted="Col. Condesa, CDMX"),
    dict(id="PROV-004", name="Ana Martínez", service="limpieza", rating=4.6, verified=True,
         zip_codes=["06600", "06800", "06900"], phone="+525512345681", years_experience=6,
         has_insurance=True, completed_jobs=423, trust_score=4.5,
         lat=19.433, lng=-99.191, service_area_km=12.0, address_formatted="Col. Polanco, CDMX"),
    dict(id="PROV-005", name="Roberto Sánchez", service="impermeabilizacion", rating=4.3, verified=True,
         zip_codes=["06500", "06600", "06700"], phone="+525512345682", years_experience=10,
         has_insurance=True, completed_jobs=278, trust_score=4.2,
         lat=19.396, lng=-99.143, service_area_km=8.0, address_formatted="Col. Narvarte, CDMX"),
    dict(id="PROV-006", name="Laura Torres", service="carpinteria", rating=4.7, verified=True,
         zip_codes=["06600", "06700", "06800"], phone="+525512345683", years_experience=7,
         has_insurance=True, completed_jobs=312, trust_score=4.6,
         lat=19.407, lng=-99.188, service_area_km=7.0, address_formatted="Col. Escandón, CDMX"),
    dict(id="PROV-007", name="Pedro Hernández", service="jardineria", rating=4.1, verified=False,
         zip_codes=["06900", "07000"], phone="+525512345684", years_experience=3,
         has_insurance=False, completed_jobs=95, trust_score=3.2,
         lat=19.350, lng=-99.162, service_area_km=5.0, address_formatted="Col. Coyoacán Centro, CDMX"),
    dict(id="PROV-008", name="Diana Flores", service="albañileria", rating=4.4, verified=True,
         zip_codes=["06600", "06500"], phone="+525512345685", years_experience=15,
         has_insurance=True, completed_jobs=689, trust_score=4.8,
         lat=19.295, lng=-99.056, service_area_km=15.0, address_formatted="San Pedro Tláhuac, CDMX"),
]


def seed_providers(engine):
    with Session(engine) as session:
        result = session.exec(text("SELECT COUNT(*) FROM providers")).first()
        if result and result[0] > 0:
            return
        for data in PROVIDERS_SEED_DATA:
            session.add(ProviderDB(**data))
        session.commit()
