"""Parse free-form address input into the format expected by the ArcGIS MasterAddress service."""

import re

DIRECTION_MAP = {
    "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W",
    "NORTHEAST": "NE", "NORTHWEST": "NW", "SOUTHEAST": "SE", "SOUTHWEST": "SW",
    "N": "N", "S": "S", "E": "E", "W": "W",
    "NE": "NE", "NW": "NW", "SE": "SE", "SW": "SW",
}

STREET_TYPE_MAP = {
    "STREET": "ST", "ROAD": "RD", "DRIVE": "DR", "AVENUE": "AV",
    "BOULEVARD": "BV", "LANE": "LN", "COURT": "CT", "CIRCLE": "CI",
    "PLACE": "PL", "WAY": "WY", "TRAIL": "TR", "PARKWAY": "PY",
    "TERRACE": "TE", "LOOP": "LP", "HIGHWAY": "HW", "PATH": "PT",
    "ALLEY": "AL", "CROSSING": "XG", "POINT": "PT", "RUN": "RN",
    "COVE": "CV", "COMMONS": "CM", "WALK": "WK",
    # Already abbreviated forms
    "ST": "ST", "RD": "RD", "DR": "DR", "AV": "AV", "AVE": "AV",
    "BV": "BV", "BLVD": "BV", "LN": "LN", "CT": "CT", "CI": "CI",
    "CIR": "CI", "PL": "PL", "WY": "WY", "TR": "TR", "PY": "PY",
    "PKWY": "PY", "TE": "TE", "LP": "LP", "HW": "HW", "HWY": "HW",
}

# Tokens to strip from user input (city, state, zip)
STRIP_SUFFIXES = re.compile(
    r",?\s*(CHARLOTTE|CORNELIUS|DAVIDSON|HUNTERSVILLE|MATTHEWS|MINT HILL|PINEVILLE|STALLINGS)"
    r"(\s*,?\s*NC)?(\s+\d{5}(-\d{4})?)?$",
    re.IGNORECASE,
)
STATE_ZIP = re.compile(r",?\s*NC\s*\d{0,5}(-\d{4})?$", re.IGNORECASE)

UNIT_PATTERNS = re.compile(
    r"\b(APT|UNIT|STE|SUITE|#)\s*([A-Z0-9-]+)\b", re.IGNORECASE
)


def normalize_address(raw: str) -> str:
    """Convert a free-form address string to the ArcGIS FullAddress LIKE pattern.

    Returns an uppercase string suitable for: WHERE FullAddress LIKE '{result}%'
    """
    addr = raw.strip().upper()

    # Strip city/state/zip
    addr = STRIP_SUFFIXES.sub("", addr)
    addr = STATE_ZIP.sub("", addr)
    addr = addr.strip().rstrip(",").strip()

    # Remove unit info (we search for primary address, units come back as extra matches)
    addr = UNIT_PATTERNS.sub("", addr).strip()

    tokens = addr.split()
    if not tokens:
        return raw.upper()

    result = []
    i = 0

    # First token should be house number
    if tokens[0].isdigit():
        result.append(tokens[0])
        i = 1
    else:
        return " ".join(tokens)

    # Second token might be a direction
    if i < len(tokens) and tokens[i] in DIRECTION_MAP:
        result.append(DIRECTION_MAP[tokens[i]])
        i += 1

    # Remaining tokens are street name and type
    remaining = tokens[i:]
    if remaining:
        last = remaining[-1]
        if last in STREET_TYPE_MAP:
            street_name_parts = remaining[:-1]
            street_type = STREET_TYPE_MAP[last]
            if street_name_parts:
                result.extend(street_name_parts)
            result.append(street_type)
        else:
            result.extend(remaining)

    return " ".join(result)
