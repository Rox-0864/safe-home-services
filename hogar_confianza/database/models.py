from datetime import datetime

from sqlmodel import JSON, Field, SQLModel


class ProviderDB(SQLModel, table=True):
    __tablename__ = "providers"

    id: str = Field(primary_key=True)
    name: str
    service: str
    rating: float
    verified: bool
    zip_codes: list[str] = Field(default_factory=list, sa_type=JSON)
    phone: str
    years_experience: int
    has_insurance: bool
    completed_jobs: int
    trust_score: float
    lat: float | None = None
    lng: float | None = None
    service_area_km: float = 10.0
    address_formatted: str | None = None


class BookingDB(SQLModel, table=True):
    __tablename__ = "bookings"

    id: str = Field(primary_key=True)
    user_id: str
    provider_id: str
    service: str
    description: str
    status: str
    scheduled_date: str
    scheduled_time: str
    amount: float
    escrow_held: bool
    address_id: str | None = Field(default=None, foreign_key="user_addresses.id")


class SafetyCheckInDB(SQLModel, table=True):
    __tablename__ = "safety_checkins"

    booking_id: str = Field(primary_key=True)
    provider_id: str
    check_in_time: str
    check_out_time: str | None = Field(default=None)
    selfie_confirmed: bool
    location_verified: bool
    trusted_contact_notified: bool


class UserAddressDB(SQLModel, table=True):
    __tablename__ = "user_addresses"

    id: str = Field(primary_key=True)
    user_id: str
    calle: str
    numero_exterior: str | None = None
    numero_interior: str | None = None
    colonia: str
    ciudad: str
    estado: str
    zip_code: str
    pais: str = "México"
    lat: float | None = None
    lng: float | None = None
    formatted_address: str | None = None
    place_id: str | None = None
    is_verified: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
