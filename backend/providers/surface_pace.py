"""
Court Pace Index (CPI) par tournoi de tennis.

Le CPI mesure la vitesse effective d'une surface :
  - 0-29  : Slow (favorise les rallyeurs, defenseurs)
  - 30-34 : Medium (neutre)
  - 35-44 : Medium-Fast
  - 45+   : Fast (favorise les serveurs)

Sources : ITF officiel + observations communaute tennis (RossPro, Match Stat).
Toutes les surfaces "Hard" NE sont PAS egales. Cincinnati est 2x plus rapide
qu'Indian Wells malgre les deux etant "Hard".
"""

# CPI par tournoi (cle = nom normalise lowercase)
# Format : (CPI, categorie_descriptive)
COURT_PACE_INDEX = {
    # =========== TERRE BATTUE (toutes lentes) ===========
    "roland garros": (18, "very_slow"),
    "french open": (18, "very_slow"),
    "monte carlo": (20, "very_slow"),
    "monte-carlo": (20, "very_slow"),
    "madrid open": (24, "medium_slow"),    # Altitude rend Madrid plus rapide qu'une terre normale
    "mutua madrid": (24, "medium_slow"),
    "madrid": (24, "medium_slow"),
    "italian open": (20, "very_slow"),
    "rome": (20, "very_slow"),
    "barcelona open": (19, "very_slow"),
    "barcelona": (19, "very_slow"),
    "marrakech": (22, "slow"),
    "geneva": (21, "slow"),
    "geneve": (21, "slow"),

    # =========== GAZON (toutes rapides) ===========
    "wimbledon": (47, "fast"),
    "halle": (44, "medium_fast"),
    "queens": (45, "fast"),
    "queen's club": (45, "fast"),
    "nottingham": (43, "medium_fast"),
    "surbiton": (44, "medium_fast"),

    # =========== HARD COURTS — vitesses tres differentes ===========
    "australian open": (34, "medium"),       # Plexicushion, medium
    "us open": (37, "medium_fast"),          # Decoturf, plus rapide
    "indian wells": (26, "slow"),            # Connue pour etre tres lente !
    "miami open": (32, "medium"),            # Laykold, medium
    "cincinnati": (39, "medium_fast"),       # Connue pour etre rapide !

    # =========== CHALLENGERS (peu de data, neutre par defaut) ===========
    "wuxi": (33, "medium"),
    "mauthausen": (33, "medium"),
}


def get_cpi(tournament_name: str):
    """Retourne (cpi, category) pour un tournoi, ou None si inconnu.

    Match : cle complete dans le nom (avec frontieres de mots pour eviter
    qu'un nom comme 'challenger' matche 'halle').
    """
    if not tournament_name:
        return None
    import re
    tname = tournament_name.lower().strip()
    # Match exact d'abord
    if tname in COURT_PACE_INDEX:
        return COURT_PACE_INDEX[tname]
    # Match avec frontieres de mots : 'halle' ne matchera pas 'challenger'
    for key, val in COURT_PACE_INDEX.items():
        # Echapper les caracteres speciaux et chercher avec word boundaries
        pattern = r"\b" + re.escape(key) + r"\b"
        if re.search(pattern, tname):
            return val
    return None


def get_cpi_for_surface(surface: str):
    """Fallback : CPI par defaut selon la surface (si tournoi inconnu)."""
    if not surface:
        return None
    s = surface.lower().strip()
    if s in ("clay", "terre battue", "terre", "red clay"):
        return (20, "slow")
    if s in ("grass", "gazon"):
        return (45, "fast")
    if s in ("hard", "dur", "hardcourt", "indoor hard", "dur (indoor)"):
        return (33, "medium")
    if s in ("carpet", "moquette"):
        return (40, "medium_fast")
    return None


def get_cpi_label(category: str) -> str:
    """Label descriptif en FR."""
    return {
        "very_slow": "Très lente",
        "slow": "Lente",
        "medium_slow": "Moyennement lente",
        "medium": "Moyenne",
        "medium_fast": "Moyennement rapide",
        "fast": "Rapide",
    }.get(category, "—")


if __name__ == "__main__":
    # Tests
    assert get_cpi("Indian Wells")[0] == 26
    assert get_cpi("Cincinnati Masters 1000")[0] == 39
    assert get_cpi("Wimbledon 2025")[0] == 47
    assert get_cpi("Unknown Challenger") is None
    # Fallback surface
    assert get_cpi_for_surface("Clay") == (20, "slow")
    assert get_cpi_for_surface("Hard") == (33, "medium")
    print("OK : tests surface_pace passes")
