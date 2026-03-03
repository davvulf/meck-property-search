"""Main orchestrator: address -> full property report."""

from __future__ import annotations

import logging

from meck_property_search.address_parser import normalize_address
from meck_property_search.models import PropertyReport
from meck_property_search.sources import arcgis, tax_bills

log = logging.getLogger(__name__)


def search_property(address: str) -> PropertyReport:
    """Search all available sources for a property and return a unified report."""
    report = PropertyReport(query_address=address)
    normalized = normalize_address(address)

    # Step 1: Resolve address to parcel ID via ArcGIS
    try:
        matches = arcgis.resolve_address(normalized)
    except Exception as e:
        report.errors.append(f"Address resolution failed: {e}")
        return report

    if not matches:
        report.errors.append(
            f"No address matches found for '{normalized}'. "
            "Try a simpler format like '123 Main St'."
        )
        return report

    # Pick the primary address (no unit) or first match
    primary = next((m for m in matches if not m.unit), matches[0])
    report.address_match = primary
    pid = primary.parcel_id

    if not pid:
        report.errors.append("Address matched but no Parcel ID found.")
        return report

    # Step 2: Fan out to all sources
    # ArcGIS: Parcel info
    try:
        report.parcel = arcgis.get_parcel(pid)
    except Exception as e:
        report.errors.append(f"Parcel lookup failed: {e}")

    # ArcGIS: Zoning
    try:
        report.zoning = arcgis.get_zoning(pid)
    except Exception as e:
        report.errors.append(f"Zoning lookup failed: {e}")

    # ArcGIS: Liens
    try:
        report.liens = arcgis.get_liens(pid)
    except Exception as e:
        report.errors.append(f"Lien lookup failed: {e}")

    # ArcGIS: Regulations
    try:
        report.regulations = arcgis.get_regulations(pid)
    except Exception as e:
        report.errors.append(f"Regulations lookup failed: {e}")

    # Tax bill: Owner name
    try:
        report.ownership = tax_bills.get_tax_info(pid)
    except Exception as e:
        report.errors.append(f"Tax bill lookup failed: {e}")

    return report
