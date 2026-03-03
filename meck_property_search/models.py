from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date, datetime


@dataclass
class AddressMatch:
    full_address: str
    house_number: int | None = None
    direction: str | None = None
    street_name: str | None = None
    street_type: str | None = None
    unit: str | None = None
    jurisdiction: str | None = None
    postal_city: str | None = None
    zip_code: str | None = None
    parcel_id: str | None = None
    x_coordinate: float | None = None
    y_coordinate: float | None = None


@dataclass
class ParcelInfo:
    pid: str
    nc_pin: str | None = None
    map_book: str | None = None
    map_page: str | None = None
    map_block: str | None = None
    lot_num: str | None = None
    parcel_type: int | None = None
    condo_flag: int | None = None
    area_sq_ft: float | None = None


@dataclass
class ZoningInfo:
    pid: str
    zoning: str | None = None
    rezone_date: str | None = None
    commissioner_district: str | None = None


@dataclass
class LienRecord:
    lien_no: str
    status: str | None = None
    customer_name: str | None = None
    property_address: str | None = None
    invoice_no: str | None = None
    invoice_date: str | None = None


@dataclass
class RegulationInfo:
    pid: str
    in_business_corridor: bool = False
    current_zoning: str | None = None
    water_district: str | None = None
    watershed: str | None = None
    in_city_limits: bool = False


@dataclass
class OwnershipInfo:
    owner_name: str | None = None
    mailing_address: str | None = None
    land_value: int | None = None
    building_value: int | None = None
    total_value: int | None = None
    tax_year: str | None = None
    land_use: str | None = None
    acreage: float | None = None
    year_built: int | None = None
    heated_area: int | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None


@dataclass
class SaleRecord:
    sale_date: str | None = None
    sale_price: int | None = None
    deed_book: str | None = None
    deed_page: str | None = None
    buyer: str | None = None
    seller: str | None = None
    instrument_type: str | None = None


@dataclass
class DeedRecord:
    document_type: str | None = None
    book: str | None = None
    page: str | None = None
    recording_date: str | None = None
    grantor: str | None = None
    grantee: str | None = None


@dataclass
class PermitRecord:
    permit_number: str | None = None
    permit_type: str | None = None
    status: str | None = None
    issue_date: str | None = None
    description: str | None = None
    address: str | None = None


@dataclass
class PropertyReport:
    query_address: str
    address_match: AddressMatch | None = None
    parcel: ParcelInfo | None = None
    zoning: ZoningInfo | None = None
    liens: list[LienRecord] = field(default_factory=list)
    regulations: RegulationInfo | None = None
    ownership: OwnershipInfo | None = None
    sales: list[SaleRecord] = field(default_factory=list)
    deeds: list[DeedRecord] = field(default_factory=list)
    permits: list[PermitRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        def serialize(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        return json.dumps(asdict(self), default=serialize, indent=indent)
