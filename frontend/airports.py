# frontend/airports.py
"""Mapping kode ICAO bandara PTFS -> nama kota / bandara."""

AIRPORT_NAMES = {
    "IRFD": "Greater Rockford",
    "IPPH": "Perth",
    "ILAR": "Larnaca",
    "IPAP": "Paphos",
    "ITKO": "Tokyo",
    "IZOL": "Izolirani",
    "IGRV": "Grindavik",
    "IKFL": "Keflavik",
    "IMLR": "Mellor",
    "IBTH": "Saint Barthélemy",
    "ISAU": "Sauthemptona",
    "IJAF": "Al Najaf",
    "IBAR": "Barra",
    "IHEN": "Henstridge",
    "ISCM": "RAF Scampton",
    "IDCS": "Saba",
    "ILKL": "Lukla",
    "IGAR": "Airbase Garry",
    "IBLT": "Boltic",
    "ITRC": "Training Centre",
    "FSSB": "Bird Island",
}


def get_airport_name(code):
    if not code:
        return ""
    code_clean = code.upper().strip()
    return AIRPORT_NAMES.get(code_clean, code_clean)
