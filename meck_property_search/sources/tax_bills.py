"""Scraper for Mecklenburg County tax bill lookup."""

from __future__ import annotations

import urllib.request
import urllib.parse

from bs4 import BeautifulSoup

from meck_property_search.models import OwnershipInfo

SEARCH_URL = "https://taxbill.co.mecklenburg.nc.us/publicwebaccess/BillSearchResults.aspx"
TIMEOUT = 30


def get_tax_info(parcel_id: str) -> OwnershipInfo | None:
    """Look up tax bill info by parcel number. Returns owner name and address."""
    params = urllib.parse.urlencode({"searchType": "parcel", "ParcelNum": parcel_id})
    url = f"{SEARCH_URL}?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": "MeckPropertySearch/0.1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    soup = BeautifulSoup(html, "html.parser")

    # Find the results table — look for a row containing the parcel ID
    cells = soup.find_all("td")
    owner_name = None
    location = None

    for i, cell in enumerate(cells):
        text = cell.get_text(strip=True)
        if text == parcel_id and i + 2 < len(cells):
            # Table order: Bill# | OldBill# | Parcel# | Name | Location | Flags | CurrentDue
            owner_name = cells[i + 1].get_text(strip=True)
            location = cells[i + 2].get_text(strip=True)
            break

    if not owner_name:
        return None

    return OwnershipInfo(
        owner_name=owner_name,
        mailing_address=location,
    )
