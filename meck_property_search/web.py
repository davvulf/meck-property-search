"""Extremely basic web frontend for Mecklenburg County property search."""

from __future__ import annotations

from flask import Flask, request, render_template_string

from meck_property_search.search import search_property
from meck_property_search.sources import portal_links

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mecklenburg County Property Search</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #1a1a1a; }
  h1 { margin-bottom: 4px; font-size: 1.5rem; }
  .subtitle { color: #666; margin-bottom: 20px; font-size: 0.9rem; }
  form { display: flex; gap: 8px; margin-bottom: 24px; }
  input[type=text] { flex: 1; padding: 10px 14px; font-size: 1rem; border: 2px solid #ccc; border-radius: 6px; }
  input[type=text]:focus { outline: none; border-color: #2563eb; }
  button { padding: 10px 20px; font-size: 1rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }
  button:hover { background: #1d4ed8; }
  button:disabled { background: #93c5fd; cursor: wait; }
  #status { color: #666; margin-bottom: 16px; }
  .error { color: #dc2626; margin-bottom: 12px; }
  .section { border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 16px; overflow: hidden; }
  .section h2 { background: #f9fafb; padding: 10px 16px; font-size: 0.95rem; border-bottom: 1px solid #e5e7eb; }
  .section table { width: 100%; border-collapse: collapse; }
  .section td { padding: 8px 16px; border-bottom: 1px solid #f3f4f6; }
  .section td:first-child { font-weight: 600; width: 40%; color: #374151; }
  .links a { display: block; padding: 8px 16px; color: #2563eb; text-decoration: none; border-bottom: 1px solid #f3f4f6; }
  .links a:hover { background: #f0f7ff; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
  .badge-green { background: #dcfce7; color: #166534; }
  .badge-red { background: #fee2e2; color: #991b1b; }
</style>
</head>
<body>
<h1>Mecklenburg County Property Search</h1>
<p class="subtitle">Search public records by property address</p>

<form id="searchForm">
  <input type="text" id="address" placeholder="e.g. 600 E 4th St, Charlotte NC" autofocus>
  <button type="submit" id="btn">Search</button>
</form>

<div id="status"></div>
<div id="results"></div>

<script>
const form = document.getElementById('searchForm');
const input = document.getElementById('address');
const btn = document.getElementById('btn');
const status = document.getElementById('status');
const results = document.getElementById('results');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const addr = input.value.trim();
  if (!addr) return;

  btn.disabled = true;
  status.textContent = 'Searching...';
  results.innerHTML = '';

  try {
    const resp = await fetch('/api/search?address=' + encodeURIComponent(addr));
    const data = await resp.json();
    status.textContent = '';
    renderReport(data);
  } catch (err) {
    status.innerHTML = '<span class="error">Search failed: ' + err.message + '</span>';
  } finally {
    btn.disabled = false;
  }
});

function renderReport(r) {
  let html = '';

  if (r.errors && r.errors.length && !r.address_match) {
    html += r.errors.map(e => '<p class="error">' + esc(e) + '</p>').join('');
    results.innerHTML = html;
    return;
  }

  const a = r.address_match;
  html += '<div class="section"><h2>' + esc(a.full_address) + '</h2>';
  html += '<table>';
  html += row('Parcel ID', a.parcel_id);
  html += row('Jurisdiction', a.jurisdiction);
  html += row('Zip Code', a.zip_code);
  html += '</table></div>';

  if (r.ownership) {
    html += section('Ownership & Tax', [
      ['Owner', r.ownership.owner_name],
      ['Address', r.ownership.mailing_address],
      r.ownership.total_value ? ['Total Value', '$' + Number(r.ownership.total_value).toLocaleString()] : null,
      r.ownership.land_value ? ['Land Value', '$' + Number(r.ownership.land_value).toLocaleString()] : null,
      r.ownership.building_value ? ['Building Value', '$' + Number(r.ownership.building_value).toLocaleString()] : null,
    ]);
  }

  if (r.parcel) {
    const p = r.parcel;
    const area = p.area_sq_ft ? Number(p.area_sq_ft).toLocaleString() + ' sq ft (' + (p.area_sq_ft / 43560).toFixed(2) + ' acres)' : null;
    html += section('Parcel Info', [
      ['NC PIN', p.nc_pin],
      ['Map Book/Page', (p.map_book || '?') + '-' + (p.map_page || '?')],
      ['Block/Lot', (p.map_block || '?') + '/' + (p.lot_num || '?')],
      area ? ['Area', area] : null,
    ]);
  }

  if (r.zoning) {
    html += section('Zoning', [
      ['Zoning Code', r.zoning.zoning],
      ['Rezone Date', r.zoning.rezone_date],
      ['Commissioner District', r.zoning.commissioner_district],
    ]);
  }

  if (r.regulations) {
    const reg = r.regulations;
    html += section('Regulations', [
      ['In City Limits', badge(reg.in_city_limits)],
      ['Business Corridor', badge(reg.in_business_corridor)],
      ['Water District', reg.water_district],
      ['Watershed', reg.watershed],
    ]);
  }

  if (r.liens && r.liens.length > 0) {
    html += '<div class="section"><h2>City Liens (' + r.liens.length + ')</h2><table>';
    r.liens.forEach(l => {
      html += row(l.lien_no, (l.status || '') + ' — ' + (l.invoice_date || ''));
    });
    html += '</table></div>';
  } else {
    html += '<div class="section"><h2>City Liens</h2><table>' + row('Status', '<span class="badge badge-green">None found</span>') + '</table></div>';
  }

  // Portal links
  const pid = a.parcel_id;
  if (pid) {
    html += '<div class="section"><h2>Explore Further</h2><div class="links">';
    html += link('POLARIS 3G — Full Property Detail', r._links.polaris);
    html += link('SpatialEst — Property Card', r._links.spatialest);
    html += link('Tax Bill Lookup', r._links.tax_bill);
    html += link('GeoPortal — Map', r._links.geoportal);
    html += link('Accela — Permits & Inspections', r._links.accela);
    html += link('Register of Deeds', r._links.register_of_deeds);
    html += '</div></div>';
  }

  if (r.errors && r.errors.length) {
    html += r.errors.map(e => '<p class="error">Warning: ' + esc(e) + '</p>').join('');
  }

  results.innerHTML = html;
}

function section(title, rows) {
  let html = '<div class="section"><h2>' + esc(title) + '</h2><table>';
  rows.forEach(r => { if (r) html += row(r[0], r[1]); });
  return html + '</table></div>';
}

function row(label, value) {
  return '<tr><td>' + esc(label || '') + '</td><td>' + (value || 'N/A') + '</td></tr>';
}

function badge(val) {
  return val
    ? '<span class="badge badge-green">Yes</span>'
    : '<span class="badge badge-red">No</span>';
}

function link(text, url) {
  return '<a href="' + esc(url) + '" target="_blank">' + esc(text) + ' &#8599;</a>';
}

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = String(s);
  return d.innerHTML;
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/search")
def api_search():
    address = request.args.get("address", "").strip()
    if not address:
        return {"error": "address parameter required"}, 400

    report = search_property(address)
    import json
    from dataclasses import asdict
    data = json.loads(report.to_json())

    # Inject portal links for the frontend
    pid = None
    owner = None
    if report.address_match and report.address_match.parcel_id:
        pid = report.address_match.parcel_id
    if report.ownership and report.ownership.owner_name:
        owner = report.ownership.owner_name

    data["_links"] = {}
    if pid:
        data["_links"]["polaris"] = portal_links.polaris_link(pid)
        data["_links"]["spatialest"] = portal_links.spatialest_link(pid)
        data["_links"]["tax_bill"] = portal_links.tax_bill_link(pid)
        data["_links"]["geoportal"] = portal_links.geoportal_link(pid)
        data["_links"]["accela"] = portal_links.accela_permits_link()
        data["_links"]["register_of_deeds"] = portal_links.register_of_deeds_link(owner or "")

    return data


def main():
    import os
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
