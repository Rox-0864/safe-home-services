from pydantic import BaseModel
from typing import Optional
from enum import Enum


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


class ServiceRequest(BaseModel):
    service_type: ServiceType
    description: str
    zip_code: str
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    urgency: str = "normal"


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


class SafetyCheckIn(BaseModel):
    booking_id: str
    provider_id: str
    check_in_time: str
    check_out_time: Optional[str] = None
    selfie_confirmed: bool
    location_verified: bool
    trusted_contact_notified: bool
