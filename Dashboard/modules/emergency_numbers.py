EMERGENCY_NUMBERS = {
    "AE": {"ambulance": "998", "police": "999", "fire": "997", "unified": "999"},
    "AR": {"ambulance": "107", "police": "101", "fire": "100", "unified": "911"},
    "AU": {"ambulance": "000", "police": "000", "fire": "000", "unified": "112"},
    "BD": {"ambulance": "999", "police": "999", "fire": "999", "unified": "999"},
    "BR": {"ambulance": "192", "police": "190", "fire": "193", "unified": "192"},
    "CA": {"ambulance": "911", "police": "911", "fire": "911", "unified": "911"},
    "CN": {"ambulance": "120", "police": "110", "fire": "119", "unified": "120"},
    "DE": {"ambulance": "112", "police": "110", "fire": "112", "unified": "112"},
    "ES": {"ambulance": "112", "police": "112", "fire": "112", "unified": "112"},
    "FR": {"ambulance": "15", "police": "17", "fire": "18", "unified": "112"},
    "GB": {"ambulance": "999", "police": "999", "fire": "999", "unified": "112"},
    "ID": {"ambulance": "118", "police": "110", "fire": "113", "unified": "112"},
    "IN": {"ambulance": "108", "police": "100", "fire": "101", "unified": "112"},
    "IT": {"ambulance": "118", "police": "113", "fire": "115", "unified": "112"},
    "JP": {"ambulance": "119", "police": "110", "fire": "119", "unified": "112"},
    "KR": {"ambulance": "119", "police": "112", "fire": "119", "unified": "112"},
    "MX": {"ambulance": "911", "police": "911", "fire": "911", "unified": "911"},
    "MY": {"ambulance": "999", "police": "999", "fire": "994", "unified": "999"},
    "NG": {"ambulance": "112", "police": "112", "fire": "112", "unified": "112"},
    "NL": {"ambulance": "112", "police": "112", "fire": "112", "unified": "112"},
    "NZ": {"ambulance": "111", "police": "111", "fire": "111", "unified": "111"},
    "PH": {"ambulance": "911", "police": "911", "fire": "911", "unified": "911"},
    "RU": {"ambulance": "103", "police": "102", "fire": "101", "unified": "112"},
    "SA": {"ambulance": "997", "police": "999", "fire": "998", "unified": "911"},
    "SG": {"ambulance": "995", "police": "999", "fire": "995", "unified": "999"},
    "TH": {"ambulance": "1669", "police": "191", "fire": "199", "unified": "191"},
    "TR": {"ambulance": "112", "police": "112", "fire": "112", "unified": "112"},
    "US": {"ambulance": "911", "police": "911", "fire": "911", "unified": "911"},
    "ZA": {"ambulance": "10177", "police": "10111", "fire": "10177", "unified": "112"},
}


def get_emergency_numbers(country_code: str) -> dict[str, str]:
    return EMERGENCY_NUMBERS.get(
        country_code.upper(),
        {"ambulance": "112", "police": "112", "fire": "112", "unified": "112"},
    )


def all_countries() -> list[str]:
    return sorted(EMERGENCY_NUMBERS.keys())

