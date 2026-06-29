from sqlmodel import JSON, Column, Field, SQLModel


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


class SafetyCheckInDB(SQLModel, table=True):
    __tablename__ = "safety_checkins"

    booking_id: str = Field(primary_key=True)
    provider_id: str
    check_in_time: str
    check_out_time: str | None = Field(default=None)
    selfie_confirmed: bool
    location_verified: bool
    trusted_contact_notified: bool
