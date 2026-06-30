from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ServiceType(str, Enum):
    LIMPIEZA = "limpieza"
    ELECTRICIDAD = "electricidad"
    PLOMERIA = "plomeria"
    PINTURA = "pintura"
    IMPERMEABILIZACION = "impermeabilizacion"
    CARPINTERIA = "carpinteria"
    JARDINERIA = "jardineria"
    ALBAÑILERIA = "albañileria"
    CERRAJERIA = "cerrajeria"
    OTRO = "otro"


class Address(BaseModel):
    calle: str
    numero_exterior: Optional[str] = None
    numero_interior: Optional[str] = None
    colonia: str
    ciudad: str
    estado: str
    zip_code: str
    pais: str = "México"
    lat: Optional[float] = None
    lng: Optional[float] = None
    formatted_address: Optional[str] = None


class ServiceRequest(BaseModel):
    service_type: ServiceType
    description: str
    zip_code: str
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    urgency: str = "normal"
    address: Optional[Address] = None


class Provider(BaseModel):
    id: str
    name: str
    service: ServiceType
    rating: float
    verified: bool
    zip_codes: list[str]
    phone: str
    years_experience: int
    has_insurance: bool
    completed_jobs: int
    trust_score: float
    lat: Optional[float] = None
    lng: Optional[float] = None
    service_area_km: float = 10.0
    address_formatted: Optional[str] = None


class Booking(BaseModel):
    id: str
    user_id: str
    provider_id: str
    service: ServiceType
    description: str
    status: str
    scheduled_date: str
    scheduled_time: str
    amount: float
    escrow_held: bool
    address: Optional[Address] = None


class SafetyCheckIn(BaseModel):
    booking_id: str
    provider_id: str
    check_in_time: str
    check_out_time: Optional[str] = None
    selfie_confirmed: bool
    location_verified: bool
    trusted_contact_notified: bool
