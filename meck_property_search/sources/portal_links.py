"""Generate deep links to Mecklenburg County public record portals."""

from __future__ import annotations

from urllib.parse import quote


def polaris_link(parcel_id: str) -> str:
    """POLARIS 3G property detail page."""
    return f"https://polaris3g.mecklenburgcountync.gov/pid/{parcel_id}"


def tax_bill_link(parcel_id: str) -> str:
    """Tax bill lookup by parcel number."""
    return (
        f"https://taxbill.co.mecklenburg.nc.us/publicwebaccess/"
        f"BillSearchResults.aspx?searchType=parcel&ParcelNum={parcel_id}"
    )


def register_of_deeds_link(owner_name: str) -> str:
    """Register of Deeds search by name (requires login/disclaimer acceptance)."""
    return "https://meckrod.manatron.com/"


def register_of_deeds_book_page_link(book: str, page: str) -> str:
    """Direct link to a deed record by book/page."""
    return f"https://meckrod.manatron.com/RealEstate/SearchDetail.aspx?bk={book}&pg={page}&type=BkPg"


def accela_permits_link() -> str:
    """Accela permit search portal."""
    return "https://aca-prod.accela.com/Mecklenburg/"


def spatialest_link(parcel_id: str) -> str:
    """SpatialEst property record card."""
    return f"https://property.spatialest.com/nc/mecklenburg/#/property/{parcel_id}"


def geoportal_link(parcel_id: str) -> str:
    """Mecklenburg County GeoPortal."""
    return f"https://mcmap.org/geoportal/?pid={parcel_id}"


def gis_map_link(parcel_id: str) -> str:
    """Direct ArcGIS parcel map."""
    return (
        f"https://gis.charlottenc.gov/arcgis/rest/services/CountyData/Parcels/MapServer/0/"
        f"query?where=PID%3D%27{parcel_id}%27&outFields=*&f=html"
    )
