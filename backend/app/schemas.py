"""Schémas Pydantic v2 (validation entrée / sérialisation sortie)."""
from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
Quantity = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]

ListingStatus = Literal["draft", "published", "reserved", "in_transit", "completed", "cancelled"]
TransactionStatus = Literal[
    "pending_escrow", "escrow_locked", "collected_pending_verification", "paid", "disputed", "cancelled"
]
WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
_HOURS_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$")
_PHONE_RE = re.compile(r"^\+?[0-9 ().-]{6,30}$")


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class ErrorResponse(BaseModel):
    detail: str
    code: str


# --- Auth --------------------------------------------------------------------------
class RegisterIn(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["producer", "collector"] = "producer"
    organization_name: str | None = Field(default=None, max_length=255)
    phone: str = Field(min_length=6, max_length=30)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        if not _PHONE_RE.match(v):
            raise ValueError("Numéro de téléphone invalide")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("Le mot de passe doit contenir au moins une lettre et un chiffre")
        return v


class LoginIn(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(APIModel):
    id: UUID
    email: EmailStr
    role: Literal["producer", "collector", "admin"]
    organization_name: str | None
    phone: str
    is_active: bool
    created_at: datetime


class TokenOut(APIModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut


# --- Locations ---------------------------------------------------------------------
class LocationIn(APIModel):
    label: str | None = Field(default=None, max_length=100)
    address_text: str = Field(min_length=3)
    lat: Latitude
    lng: Longitude


class LocationOut(APIModel):
    id: UUID
    label: str | None
    address_text: str
    lat: float
    lng: float
    created_at: datetime


# --- Categories --------------------------------------------------------------------
class CategoryIn(APIModel):
    slug: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=2, max_length=100)
    unit: Literal["kg", "tonne", "litre"] = "kg"
    co2_factor_per_unit: Decimal = Field(ge=0, max_digits=8, decimal_places=4)
    suggested_price_per_unit: Money = Decimal("0")


class CategoryUpdate(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    unit: Literal["kg", "tonne", "litre"] | None = None
    co2_factor_per_unit: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=4)
    suggested_price_per_unit: Money | None = None


class CategoryOut(APIModel):
    id: UUID
    slug: str
    name: str
    unit: str
    co2_factor_per_unit: Decimal
    suggested_price_per_unit: Decimal


# --- Listings ----------------------------------------------------------------------
class PickupAvailability(APIModel):
    days: list[str] = Field(default_factory=list)
    hours: str | None = None

    @field_validator("days")
    @classmethod
    def _days(cls, v: list[str]) -> list[str]:
        v = [d.lower() for d in v]
        bad = set(v) - WEEKDAYS
        if bad:
            raise ValueError(f"Jours invalides : {', '.join(sorted(bad))}")
        return v

    @field_validator("hours")
    @classmethod
    def _hours(cls, v: str | None) -> str | None:
        if v and not _HOURS_RE.match(v):
            raise ValueError("Format attendu HH:MM-HH:MM")
        return v


class ListingCreate(APIModel):
    category_id: UUID
    location_id: UUID | None = None
    location: LocationIn | None = None
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    estimated_quantity: Quantity
    price_per_unit: Money = Decimal("0")
    is_free_donation: bool = False
    pickup_availability: PickupAvailability | None = None
    images_urls: list[str] = Field(default_factory=list, max_length=8)
    status: Literal["draft", "published"] = "published"

    @model_validator(mode="after")
    def _check(self) -> "ListingCreate":
        if not self.location_id and not self.location:
            raise ValueError("location_id ou location est requis")
        if self.is_free_donation:
            self.price_per_unit = Decimal("0")
        return self


class ListingUpdate(APIModel):
    category_id: UUID | None = None
    location_id: UUID | None = None
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    estimated_quantity: Quantity | None = None
    price_per_unit: Money | None = None
    is_free_donation: bool | None = None
    pickup_availability: PickupAvailability | None = None
    images_urls: list[str] | None = Field(default=None, max_length=8)
    status: Literal["draft", "published", "cancelled"] | None = None


class ListingOut(APIModel):
    id: UUID
    producer_id: UUID
    category_id: UUID
    category_slug: str
    category_name: str
    unit: str
    location_id: UUID
    location_label: str | None
    address_text: str
    lat: float
    lng: float
    title: str
    description: str | None
    estimated_quantity: Decimal
    price_per_unit: Decimal
    is_free_donation: bool
    pickup_availability: dict[str, Any] | None
    images_urls: list[str]
    status: ListingStatus
    producer_organization: str | None = None
    created_at: datetime
    updated_at: datetime


class NearbyListingOut(APIModel):
    id: UUID
    title: str
    estimated_quantity: Decimal
    price_per_unit: Decimal
    is_free_donation: bool
    category_name: str
    category_slug: str
    unit: str
    distance_km: float
    lat: float
    lng: float
    address_text: str
    thumbnail_url: str | None


# --- Transactions ------------------------------------------------------------------
class ReserveIn(APIModel):
    listing_id: UUID
    agreed_quantity: Quantity | None = None


class VerifyQrIn(APIModel):
    token: str = Field(min_length=16, max_length=64)


class CollectIn(APIModel):
    token: str = Field(min_length=16, max_length=64)
    final_weight: Quantity
    weighing_proof_url: str | None = Field(default=None, max_length=1000)


class DisputeIn(APIModel):
    reason: str = Field(min_length=5, max_length=2000)


class ResolveIn(APIModel):
    resolution: Literal["paid", "cancelled"]
    note: str | None = Field(default=None, max_length=2000)


class TransactionOut(APIModel):
    id: UUID
    listing_id: UUID
    listing_title: str
    listing_status: ListingStatus
    category_name: str
    unit: str
    producer_id: UUID
    producer_organization: str | None
    producer_phone: str | None
    collector_id: UUID
    collector_organization: str | None
    collector_phone: str | None
    address_text: str
    lat: float
    lng: float
    agreed_quantity: Decimal | None
    final_weight: Decimal | None
    unit_price: Decimal | None
    total_amount: Decimal | None
    payment_status: TransactionStatus
    escrow_reference: str | None
    collected_at: datetime | None
    qr_scanned_at: datetime | None
    co2_saved_total: Decimal | None
    weighing_proof_url: str | None
    collector_confirmed_at: datetime | None
    producer_confirmed_at: datetime | None
    bsdd_number: str | None
    dispute_reason: str | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime | None
    viewer_role: Literal["producer", "collector", "admin"] | None = None


class QrOut(APIModel):
    transaction_id: UUID
    token: str
    payload: str


class VerifyQrOut(APIModel):
    valid: bool
    transaction: TransactionOut


# --- Media -------------------------------------------------------------------------
class MediaOut(APIModel):
    url: str
    thumbnail_url: str
    path: str
    size: int
    content_type: str


# --- Analytics ---------------------------------------------------------------------
class MaterialImpact(APIModel):
    category_slug: str
    category_name: str
    unit: str
    total_quantity: Decimal
    co2_saved: Decimal
    financial_volume: Decimal
    transactions_count: int


class ImpactOut(APIModel):
    total_quantity_kg: Decimal
    total_co2_saved_kg: Decimal
    total_financial_volume: Decimal
    completed_transactions: int
    trees_equivalent: Decimal
    by_material: list[MaterialImpact]
    monthly: list[dict[str, Any]]


class GlobalStatsOut(ImpactOut):
    users_by_role: dict[str, int]
    listings_by_status: dict[str, int]
    open_disputes: int


class GeocodeResult(APIModel):
    display_name: str
    lat: float
    lng: float
