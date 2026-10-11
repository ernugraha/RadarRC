# frontend/airlines.py
"""
Mapping callsign ATC24 -> nama airline (IRL) + ICAO code.
Sumber data: komunitas PTFS ATC24.

Untuk file gambar di assets/aircraft/, Anda bisa pakai:
  - ICAO code:  a380_baw.png
  - Nama IRL:   a380_britishairways.png
  - Prefix ATC: a380_speedbird.png
  Ketiganya didukung, dipilih berurutan.
"""

# ================================================================
# MAPPING: callsign_prefix_lower -> (DisplayName, ICAO)
# ================================================================
AIRLINE_MAP = {
    # callsign_key       display name              ICAO
    "aeroflot":         ("Aeroflot",              "AFL"),
    "shamrock":         ("Aer Lingus",            "EIN"),
    "aircanada":        ("Air Canada",            "ACA"),
    "airbaltic":        ("Air Baltic",            "BTI"),
    "airfrance":        ("Air France",            "AFR"),
    "newzealand":       ("Air New Zealand",       "ANZ"),
    "american":         ("American Airlines",     "AAL"),
    "cebupacific":      ("Cebu Pacific",          "CEB"),
    "delta":            ("Delta",                 "DAL"),
    "yeti":             ("Yeti Airlines",         "NYT"),
    "yetiairlines":     ("Yeti Airlines",         "NYT"),
    "wizzair":          ("Wizz Air",              "WZZ"),
    "swiss":            ("Swiss Airlines",        "SWR"),
    "speedbird":        ("British Airways",       "BAW"),
    "ryanair":          ("Ryanair",               "RYR"),
    "cathay":           ("Cathay Pacific",        "CPA"),
    "condor":           ("Condor",                "CFG"),
    "emirates":         ("Emirates",              "UAE"),
    "easy":             ("EasyJet",               "EZY"),
    "jersey":           ("Flybe",                 "BEE"),
    "iberia":           ("Iberia",                "IBE"),
    "ideria":           ("Iberia",                "IBE"),
    "jetblue":          ("JetBlue",               "JBU"),
    "channex":          ("Jet2",                  "EXS"),
    "klm":              ("KLM",                   "KLM"),
    "koreanair":        ("Korean Air",            "KAL"),
    "lot":              ("LOT Polish Airways",    "LOT"),
    "lufthansa":        ("Lufthansa",             "DLH"),
    "tomjet":           ("TUI",                   "TOM"),
    "southwest":        ("Southwest",             "SWA"),
    "clipper":          ("Pan Am",                "PAA"),
    "qantas":           ("Qantas",                "QFA"),
    "qatari":           ("Qatar",                 "QTR"),
    "united":           ("United Airlines",       "UAL"),
    "scandinavian":     ("Scandinavian Airlines", "SAS"),
    "singapore":        ("Singapore Airlines",    "SIA"),
    "spiritwings":      ("Spirit",                "NKS"),
    "ups":              ("UPS",                   "UPS"),
    "fedex":            ("FedEx",                 "FDX"),
    "thai":             ("Thai Airways",          "THA"),
    "turkish":          ("Turkish Airlines",      "THY"),
    "dhl":              ("DHL",                   "DHK"),
}

# ================================================================
# ALIASES: varian prefix ATC24 -> key di AIRLINE_MAP
# Termasuk nama parodi PTFS dan typo
# ================================================================
ALIASES = {
    # PTFS parodies
    "aeroflat":         "aeroflot",
    "aerdingus":        "shamrock",
    "aircanadian":      "aircanada",
    "airbalistic":      "airbaltic",
    "airfrench":        "airfrance",
    "airoldzealand":    "newzealand",
    "americano":        "american",
    "americanairlines": "american",
    "cedupacific":      "cebupacific",
    "belta":            "delta",
    "betiairlines":     "yeti",
    "beti":             "yeti",
    "bizzair":          "wizzair",
    "blissairlines":    "swiss",
    "bliss":            "swiss",
    "britainairways":   "speedbird",
    "byanair":          "ryanair",
    "cafepacific":      "cathay",
    "doncor":           "condor",
    "emarates":         "emirates",
    "hardjet":          "easy",
    "flybee":           "jersey",
    "jetbloo":          "jetblue",
    "jet3":             "channex",
    "kln":              "klm",
    "koreenair":        "koreanair",
    "koreenaircargo":   "koreanair",
    "kot":              "lot",
    "lifthansa":        "lufthansa",
    "lui":              "tomjet",
    "northeast":        "southwest",
    "danam":            "clipper",
    "oantas":           "qantas",
    "oatar":            "qatari",
    "reunitedairlines": "united",
    "reunited":         "united",
    "scandialianairlines": "scandinavian",
    "scandialian":      "scandinavian",
    "singadoorairlines":"singapore",
    "singadoor":        "singapore",
    "sprit":            "spiritwings",
    "sus":              "ups",
    "tedex":            "fedex",
    "thayairways":      "thai",
    "thay":             "thai",
    "tukreyairlines":   "turkish",
    "tukrey":           "turkish",
    "turkey":           "turkish",
    "vhl":              "dhl",
    # Typo umum
    "spirit":           "spiritwings",
    "aerlingus":        "shamrock",
    "britishairways":   "speedbird",
    "british":          "speedbird",
    "panam":            "clipper",
    "tui":              "tomjet",
    "easyjet":          "easy",
    "flybe":            "jersey",
    "jet2":             "channex",
    "wizz":             "wizzair",
    "swissairlines":    "swiss",
    "qatar":            "qatari",
    "airnewzealand":    "newzealand",
    "lothansa":         "lufthansa",
}


# ================================================================
# PUBLIC API
# ================================================================
def _normalize(callsign):
    """Ambil prefix, lowercase, hapus spasi/underscore/dash."""
    if not callsign:
        return ""
    prefix = callsign.split("-")[0]
    return (prefix.lower()
            .replace(" ", "")
            .replace("_", "")
            .replace(".", ""))


def _resolve_key(callsign):
    """Cari key AIRLINE_MAP dari callsign."""
    key = _normalize(callsign)
    if not key:
        return None
    if key in AIRLINE_MAP:
        return key
    if key in ALIASES:
        return ALIASES[key]
    return None


def get_airline_name(callsign):
    """
    'Speedbird-123'  -> 'British Airways'
    'Emarates-7326'  -> 'Emirates'
    'Turkey-8048'    -> 'Turkish Airlines'
    'XXXX-999'       -> 'XXXX' (fallback: prefix apa adanya)
    """
    if not callsign:
        return "?"
    key = _resolve_key(callsign)
    if key:
        return AIRLINE_MAP[key][0]
    return callsign.split("-")[0]


def get_airline_icao(callsign):
    """
    'Speedbird-123'  -> 'BAW'
    'Emarates-7326'  -> 'UAE'
    'XXXX-999'       -> '???'
    """
    key = _resolve_key(callsign)
    if key:
        return AIRLINE_MAP[key][1]
    return "???"


def get_airline_keys(callsign):
    """
    Kembalikan daftar kandidat key untuk lookup file gambar.
    Urutan prioritas:
      1. ICAO code (misal 'baw' untuk British Airways)
      2. Nama IRL tanpa spasi (misal 'britishairways')
      3. Prefix asli (misal 'speedbird')
    """
    if not callsign:
        return []
    key = _resolve_key(callsign)
    candidates = []
    if key:
        display, icao = AIRLINE_MAP[key]
        candidates.append(icao.lower())
        candidates.append(display.lower().replace(" ", "").replace(".", ""))
        candidates.append(_normalize(callsign))
    else:
        candidates.append(_normalize(callsign))
    # Buang duplikat, jaga urutan
    seen = set()
    result = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


# Alias lama untuk backward-compat
def get_airline_key(callsign):
    """Deprecated — pakai get_airline_keys()."""
    keys = get_airline_keys(callsign)
    return keys[0] if keys else ""
