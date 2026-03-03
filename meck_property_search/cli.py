"""CLI entry point for Mecklenburg County property search."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from meck_property_search.models import PropertyReport
from meck_property_search.search import search_property
from meck_property_search.sources import portal_links


def render_report(report: PropertyReport, console: Console) -> None:
    """Render a PropertyReport to the terminal with Rich formatting."""
    console.print()

    if report.errors and not report.address_match:
        for err in report.errors:
            console.print(f"[red]Error:[/red] {err}")
        return

    # Header
    addr = report.address_match
    console.print(Panel(
        f"[bold]{addr.full_address}[/bold]\n"
        f"Parcel ID: {addr.parcel_id}  |  "
        f"Jurisdiction: {addr.jurisdiction or 'N/A'}  |  "
        f"Zip: {addr.zip_code or 'N/A'}",
        title="Property Search Result",
        border_style="blue",
    ))

    # Parcel Info
    if report.parcel:
        p = report.parcel
        table = Table(title="Parcel Info", show_header=False, border_style="dim")
        table.add_column("Field", style="bold")
        table.add_column("Value")
        table.add_row("NC PIN", p.nc_pin or "N/A")
        table.add_row("Map Book/Page", f"{p.map_book or '?'}-{p.map_page or '?'}")
        table.add_row("Block/Lot", f"{p.map_block or '?'}/{p.lot_num or '?'}")
        if p.area_sq_ft:
            acres = p.area_sq_ft / 43560
            table.add_row("Area", f"{p.area_sq_ft:,.0f} sq ft ({acres:.2f} acres)")
        console.print(table)

    # Ownership (from tax bill)
    if report.ownership:
        o = report.ownership
        table = Table(title="Ownership & Tax", show_header=False, border_style="dim")
        table.add_column("Field", style="bold")
        table.add_column("Value")
        table.add_row("Owner", o.owner_name or "N/A")
        if o.mailing_address:
            table.add_row("Address", o.mailing_address)
        if o.total_value:
            table.add_row("Total Value", f"${o.total_value:,}")
        if o.land_value:
            table.add_row("Land Value", f"${o.land_value:,}")
        if o.building_value:
            table.add_row("Building Value", f"${o.building_value:,}")
        console.print(table)

    # Zoning
    if report.zoning:
        z = report.zoning
        table = Table(title="Zoning", show_header=False, border_style="dim")
        table.add_column("Field", style="bold")
        table.add_column("Value")
        table.add_row("Zoning Code", z.zoning or "N/A")
        table.add_row("Rezone Date", z.rezone_date or "N/A")
        table.add_row("Commissioner District", z.commissioner_district or "N/A")
        console.print(table)

    # Regulations
    if report.regulations:
        reg = report.regulations
        table = Table(title="Regulations", show_header=False, border_style="dim")
        table.add_column("Field", style="bold")
        table.add_column("Value")
        table.add_row("In City Limits", "Yes" if reg.in_city_limits else "No")
        table.add_row("Business Corridor", "Yes" if reg.in_business_corridor else "No")
        table.add_row("Water District", reg.water_district or "N/A")
        table.add_row("Watershed", reg.watershed or "N/A")
        console.print(table)

    # Liens
    if report.liens:
        table = Table(title=f"City Liens ({len(report.liens)})")
        table.add_column("Lien #")
        table.add_column("Status")
        table.add_column("Name")
        table.add_column("Invoice Date")
        for lien in report.liens:
            table.add_row(
                lien.lien_no, lien.status or "", lien.customer_name or "",
                lien.invoice_date or "",
            )
        console.print(table)
    else:
        console.print("[green]No city liens found.[/green]")

    # Portal Links
    pid = addr.parcel_id
    owner = report.ownership.owner_name if report.ownership else None
    console.print()
    console.print(Panel(
        "\n".join([
            f"[link={portal_links.polaris_link(pid)}]POLARIS 3G (full property detail)[/link]",
            f"[link={portal_links.spatialest_link(pid)}]SpatialEst (property card)[/link]",
            f"[link={portal_links.tax_bill_link(pid)}]Tax Bill Lookup[/link]",
            f"[link={portal_links.geoportal_link(pid)}]GeoPortal (map)[/link]",
            f"[link={portal_links.accela_permits_link()}]Accela (permits & inspections)[/link]",
            f"[link={portal_links.register_of_deeds_link(owner or '')}]Register of Deeds (deeds & mortgages)[/link]",
        ]),
        title="Explore Further",
        border_style="cyan",
    ))

    # Errors
    if report.errors:
        console.print()
        for err in report.errors:
            console.print(f"[yellow]Warning:[/yellow] {err}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search Mecklenburg County, NC public records by property address",
    )
    parser.add_argument("address", help="Property address (e.g. '600 E 4th St, Charlotte NC')")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted table")
    args = parser.parse_args()

    console = Console(stderr=True)
    console.print(f"[dim]Searching for:[/dim] {args.address}")

    report = search_property(args.address)

    if args.json:
        # JSON goes to stdout
        print(report.to_json())
    else:
        render_report(report, Console())


if __name__ == "__main__":
    main()
