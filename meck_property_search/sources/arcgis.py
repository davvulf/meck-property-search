"""Client for Charlotte/Mecklenburg County ArcGIS REST services."""

from __future__ import annotations

import httpx

from meck_property_search.models import (
    AddressMatch, ParcelInfo, ZoningInfo, LienRecord, RegulationInfo,
)

BASE_URL = "https://gis.charlottenc.gov/arcgis/rest/services"
TIMEOUT = 30


def _query(service_path: str, where: str, out_fields: str = "*",
           return_geometry: bool = False, max_records: int = 100) -> list[dict]:
    """Generic ArcGIS MapServer query. Returns the list of feature attributes."""
    url = f"{BASE_URL}/{service_path}/query"
    params = {
        "where": where,
        "outFields": out_fields,
        "returnGeometry": str(return_geometry).lower(),
        "resultRecordCount": max_records,
        "f": "json",
    }

    all_features = []
    offset = 0

    while True:
        params["resultOffset"] = offset
        resp = httpx.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(f"ArcGIS error: {data['error']}")

        features = data.get("features", [])
        all_features.extend(f["attributes"] for f in features)

        if data.get("exceededTransferLimit"):
            offset += len(features)
        else:
            break

    return all_features


def resolve_address(normalized_address: str) -> list[AddressMatch]:
    """Resolve a normalized address string to matching address records."""
    where = f"FullAddress LIKE '{normalized_address}%'"
    rows = _query("CountyData/MasterAddress/MapServer/0", where)

    results = []
    for r in rows:
        results.append(AddressMatch(
            full_address=r.get("FullAddress", ""),
            house_number=r.get("HouseNumber"),
            direction=r.get("Direction"),
            street_name=r.get("StreetName"),
            street_type=r.get("StreetType"),
            unit=r.get("Unit"),
            jurisdiction=r.get("Jurisdiction"),
            postal_city=r.get("PostalCity"),
            zip_code=r.get("ZipCode"),
            parcel_id=r.get("ParcelID"),
            x_coordinate=r.get("XCoordinate"),
            y_coordinate=r.get("YCoordinate"),
        ))
    return results


def get_parcel(pid: str) -> ParcelInfo | None:
    """Get parcel details by Parcel ID."""
    rows = _query("CountyData/Parcels/MapServer/0", f"PID='{pid}'")
    if not rows:
        return None
    r = rows[0]
    return ParcelInfo(
        pid=r.get("PID", pid),
        nc_pin=r.get("NC_PIN"),
        map_book=r.get("MAP_BOOK"),
        map_page=r.get("MAP_PAGE"),
        map_block=r.get("MAP_BLOCK"),
        lot_num=r.get("LOT_NUM"),
        parcel_type=r.get("PARCEL_TYPE"),
        condo_flag=r.get("CONDO_TOWN_FLAG"),
        area_sq_ft=r.get("Shape.STArea()"),
    )


def get_zoning(pid: str) -> ZoningInfo | None:
    """Get zoning info by Parcel ID."""
    rows = _query("ODP/Parcel_Zoning_Lookup/MapServer/0", f"PID='{pid}'")
    if not rows:
        return None
    r = rows[0]

    rezone_date = r.get("RezoneDate")
    if isinstance(rezone_date, (int, float)) and rezone_date:
        from datetime import datetime, timezone
        rezone_date = datetime.fromtimestamp(rezone_date / 1000, tz=timezone.utc).strftime("%Y-%m-%d")

    return ZoningInfo(
        pid=r.get("PID", pid),
        zoning=r.get("Zoning"),
        rezone_date=rezone_date,
        commissioner_district=r.get("Commissioner_District"),
    )


def get_liens(pid: str) -> list[LienRecord]:
    """Get city liens by Parcel ID."""
    rows = _query("ODP/FMSLienData/MapServer/0", f"ParcelID='{pid}'")
    return [
        LienRecord(
            lien_no=r.get("LienNo", ""),
            status=r.get("Lien_Status"),
            customer_name=r.get("Customer_Name"),
            property_address=r.get("Property_Address"),
            invoice_no=r.get("InvoiceNo"),
            invoice_date=r.get("Invoice_Date"),
        )
        for r in rows
    ]


def get_regulations(pid: str) -> RegulationInfo | None:
    """Get parcel regulations (watershed, water district, etc.) by Parcel ID."""
    rows = _query(
        "ODP/PCSR_Parcel_Regulations/MapServer/0", f"PID='{pid}'",
        out_fields="PID,InBusCorridor,Current_Zoning,PCS_Water_District,Watershed_Name,CityLimits",
    )
    if not rows:
        return None
    r = rows[0]
    return RegulationInfo(
        pid=r.get("PID", pid),
        in_business_corridor=r.get("InBusCorridor", "N").strip() == "Y",
        current_zoning=r.get("Current_Zoning"),
        water_district=(r.get("PCS_Water_District") or "").strip() or None,
        watershed=r.get("Watershed_Name"),
        in_city_limits=r.get("CityLimits", "No").strip() == "Yes",
    )
