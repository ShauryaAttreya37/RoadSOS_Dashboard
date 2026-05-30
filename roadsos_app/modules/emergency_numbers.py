from __future__ import annotations

from typing import TypedDict


GLOBAL_GSM_FALLBACK = "112"


class GlobalSOSProfile(TypedDict):
    country_code: str
    ambulance: str
    police: str
    fire: str
    unified: str
    coverage: str
    is_mobile_fallback: bool
    note: str


EMERGENCY_NUMBERS = {
    # Africa
    "DZ": {"ambulance": "14",    "police": "17",    "fire": "14",    "unified": "14"},
    "EG": {"ambulance": "123",   "police": "122",   "fire": "180",   "unified": "123"},
    "ET": {"ambulance": "907",   "police": "991",   "fire": "939",   "unified": "907"},
    "GH": {"ambulance": "193",   "police": "191",   "fire": "192",   "unified": "193"},
    "KE": {"ambulance": "999",   "police": "999",   "fire": "999",   "unified": "999"},
    "MA": {"ambulance": "150",   "police": "190",   "fire": "150",   "unified": "150"},
    "NG": {"ambulance": "112",   "police": "112",   "fire": "112",   "unified": "112"},
    "TN": {"ambulance": "190",   "police": "197",   "fire": "198",   "unified": "197"},
    "TZ": {"ambulance": "114",   "police": "112",   "fire": "115",   "unified": "114"},
    "ZA": {"ambulance": "10177", "police": "10111", "fire": "10177", "unified": "112"},
    # Americas
    "AR": {"ambulance": "107",   "police": "101",   "fire": "100",   "unified": "911"},
    "BO": {"ambulance": "118",   "police": "110",   "fire": "119",   "unified": "118"},
    "BR": {"ambulance": "192",   "police": "190",   "fire": "193",   "unified": "192"},
    "CA": {"ambulance": "911",   "police": "911",   "fire": "911",   "unified": "911"},
    "CL": {"ambulance": "131",   "police": "133",   "fire": "132",   "unified": "133"},
    "CO": {"ambulance": "123",   "police": "123",   "fire": "119",   "unified": "123"},
    "CR": {"ambulance": "911",   "police": "911",   "fire": "911",   "unified": "911"},
    "DO": {"ambulance": "911",   "police": "911",   "fire": "911",   "unified": "911"},
    "EC": {"ambulance": "911",   "police": "911",   "fire": "911",   "unified": "911"},
    "MX": {"ambulance": "911",   "police": "911",   "fire": "911",   "unified": "911"},
    "PE": {"ambulance": "117",   "police": "105",   "fire": "116",   "unified": "105"},
    "PY": {"ambulance": "141",   "police": "911",   "fire": "131",   "unified": "911"},
    "US": {"ambulance": "911",   "police": "911",   "fire": "911",   "unified": "911"},
    "UY": {"ambulance": "105",   "police": "911",   "fire": "104",   "unified": "911"},
    "VE": {"ambulance": "171",   "police": "171",   "fire": "171",   "unified": "171"},
    # Asia-Pacific
    "AU": {"ambulance": "000",   "police": "000",   "fire": "000",   "unified": "112"},
    "BD": {"ambulance": "999",   "police": "999",   "fire": "999",   "unified": "999"},
    "CN": {"ambulance": "120",   "police": "110",   "fire": "119",   "unified": "120"},
    "ID": {"ambulance": "118",   "police": "110",   "fire": "113",   "unified": "112"},
    "IN": {"ambulance": "108",   "police": "100",   "fire": "101",   "unified": "112"},
    "JP": {"ambulance": "119",   "police": "110",   "fire": "119",   "unified": "112"},
    "KH": {"ambulance": "119",   "police": "117",   "fire": "118",   "unified": "117"},
    "KR": {"ambulance": "119",   "police": "112",   "fire": "119",   "unified": "112"},
    "LK": {"ambulance": "110",   "police": "119",   "fire": "110",   "unified": "110"},
    "MM": {"ambulance": "192",   "police": "199",   "fire": "191",   "unified": "191"},
    "MY": {"ambulance": "999",   "police": "999",   "fire": "994",   "unified": "999"},
    "NP": {"ambulance": "102",   "police": "100",   "fire": "101",   "unified": "100"},
    "NZ": {"ambulance": "111",   "police": "111",   "fire": "111",   "unified": "111"},
    "PH": {"ambulance": "911",   "police": "911",   "fire": "911",   "unified": "911"},
    "PK": {"ambulance": "1122",  "police": "15",    "fire": "16",    "unified": "1122"},
    "SG": {"ambulance": "995",   "police": "999",   "fire": "995",   "unified": "999"},
    "TH": {"ambulance": "1669",  "police": "191",   "fire": "199",   "unified": "191"},
    "VN": {"ambulance": "115",   "police": "113",   "fire": "114",   "unified": "113"},
    # Central Asia
    "AF": {"ambulance": "112",   "police": "119",   "fire": "119",   "unified": "119"},
    "KZ": {"ambulance": "103",   "police": "102",   "fire": "101",   "unified": "112"},
    "UZ": {"ambulance": "103",   "police": "102",   "fire": "101",   "unified": "112"},
    # Europe (non-EU)
    "CH": {"ambulance": "144",   "police": "117",   "fire": "118",   "unified": "112"},
    "DE": {"ambulance": "112",   "police": "110",   "fire": "112",   "unified": "112"},
    "ES": {"ambulance": "112",   "police": "112",   "fire": "112",   "unified": "112"},
    "FR": {"ambulance": "15",    "police": "17",    "fire": "18",    "unified": "112"},
    "GB": {"ambulance": "999",   "police": "999",   "fire": "999",   "unified": "112"},
    "IT": {"ambulance": "118",   "police": "113",   "fire": "115",   "unified": "112"},
    "NL": {"ambulance": "112",   "police": "112",   "fire": "112",   "unified": "112"},
    "RU": {"ambulance": "103",   "police": "102",   "fire": "101",   "unified": "112"},
    "TR": {"ambulance": "112",   "police": "155",   "fire": "110",   "unified": "112"},
    "UA": {"ambulance": "103",   "police": "102",   "fire": "101",   "unified": "112"},
    # Middle East
    "AE": {"ambulance": "998",   "police": "999",   "fire": "997",   "unified": "999"},
    "IQ": {"ambulance": "122",   "police": "104",   "fire": "115",   "unified": "122"},
    "IR": {"ambulance": "115",   "police": "110",   "fire": "125",   "unified": "115"},
    "IL": {"ambulance": "101",   "police": "100",   "fire": "102",   "unified": "101"},
    "JO": {"ambulance": "911",   "police": "911",   "fire": "911",   "unified": "911"},
    "KW": {"ambulance": "112",   "police": "112",   "fire": "112",   "unified": "112"},
    "LB": {"ambulance": "140",   "police": "112",   "fire": "175",   "unified": "112"},
    "QA": {"ambulance": "999",   "police": "999",   "fire": "999",   "unified": "999"},
    "SA": {"ambulance": "997",   "police": "999",   "fire": "998",   "unified": "911"},
}

# The European Commission documents 112 as the free emergency number across
# the EU. Keep the unified route available for EU members not listed above.
EU_MEMBER_CODES = {
    "AT", "BE", "BG", "CY", "CZ", "DK", "EE", "FI", "GR", "HR", "HU", "IE",
    "LT", "LU", "LV", "MT", "PL", "PT", "RO", "SE", "SI", "SK",
}
for _country_code in EU_MEMBER_CODES:
    EMERGENCY_NUMBERS.setdefault(
        _country_code,
        {
            "ambulance": GLOBAL_GSM_FALLBACK,
            "police": GLOBAL_GSM_FALLBACK,
            "fire": GLOBAL_GSM_FALLBACK,
            "unified": GLOBAL_GSM_FALLBACK,
        },
    )


def get_global_sos_profile(country_code: str) -> GlobalSOSProfile:
    resolved_code = str(country_code or "XX").strip().upper()
    numbers = EMERGENCY_NUMBERS.get(resolved_code)
    if numbers is None:
        return {
            "country_code": resolved_code or "XX",
            "ambulance": GLOBAL_GSM_FALLBACK,
            "police": GLOBAL_GSM_FALLBACK,
            "fire": GLOBAL_GSM_FALLBACK,
            "unified": GLOBAL_GSM_FALLBACK,
            "coverage": "Global GSM mobile fallback",
            "is_mobile_fallback": True,
            "note": "Country-specific routing is unavailable. Call 112 from a GSM mobile phone and confirm the local emergency route.",
        }

    return {
        "country_code": resolved_code,
        **numbers,
        "coverage": "Country-specific emergency routing",
        "is_mobile_fallback": False,
        "note": "Numbers resolved from the detected country. Use the unified SOS number for immediate dispatch.",
    }


def get_emergency_numbers(country_code: str) -> dict[str, str]:
    profile = get_global_sos_profile(country_code)
    return {key: profile[key] for key in ("ambulance", "police", "fire", "unified")}


def all_countries() -> list[str]:
    return sorted(EMERGENCY_NUMBERS.keys())
