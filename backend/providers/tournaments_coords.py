"""
Coordonnees geographiques + altitude des principaux tournois de tennis.

Utilise pour la recuperation des donnees meteo via Open-Meteo Archive API.
Les noms sont normalises pour matcher avec ce que renvoie l'API tennis.
"""

# Coordonnees : (latitude, longitude, altitude_metres)
TOURNAMENTS_COORDS = {
    # Grand Slams
    "australian open": (-37.81, 144.96, 25),
    "roland garros": (48.85, 2.35, 35),
    "french open": (48.85, 2.35, 35),
    "wimbledon": (51.43, -0.21, 25),
    "us open": (40.72, -73.84, 10),

    # Masters 1000
    "indian wells": (33.72, -116.37, 72),
    "miami open": (25.76, -80.19, 1),
    "monte carlo": (43.73, 7.42, 0),
    "monte-carlo": (43.73, 7.42, 0),
    "madrid open": (40.41, -3.70, 667),  # Altitude !
    "mutua madrid": (40.41, -3.70, 667),
    "madrid": (40.41, -3.70, 667),
    "italian open": (41.90, 12.49, 21),
    "rome": (41.90, 12.49, 21),

    # ATP 500
    "barcelona open": (41.38, 2.17, 10),
    "barcelona": (41.38, 2.17, 10),
    "halle": (51.93, 8.93, 97),
    "queens": (51.49, -0.21, 25),
    "queen's club": (51.49, -0.21, 25),

    # ATP 250 / others
    "marrakech": (31.62, -7.98, 466),
    "geneva": (46.20, 6.14, 375),
    "geneve": (46.20, 6.14, 375),

    # Bonus (lieux courants Challengers)
    "wuxi": (31.49, 120.31, 5),
    "nottingham": (52.95, -1.15, 50),
    "surbiton": (51.39, -0.31, 15),
    "mauthausen": (48.24, 14.51, 250),
}


def get_coords(tournament_name: str):
    """Retourne (lat, lon, altitude_m) pour un tournoi, ou None si inconnu.

    Match fuzzy : cherche si une cle est SUBSTRING du nom de tournoi (case-insensitive).
    """
    if not tournament_name:
        return None
    tname = tournament_name.lower().strip()
    # Match exact d'abord
    if tname in TOURNAMENTS_COORDS:
        return TOURNAMENTS_COORDS[tname]
    # Match fuzzy : chaque cle dans le nom
    for key, coords in TOURNAMENTS_COORDS.items():
        if key in tname or tname in key:
            return coords
    return None


if __name__ == "__main__":
    # Tests
    assert get_coords("Roland Garros 2024") == (48.85, 2.35, 35)
    assert get_coords("Madrid Mutua Open ATP") == (40.41, -3.70, 667)
    assert get_coords("Italian Open Rome") is not None
    assert get_coords("Unknown Tournament") is None
    print("OK : tests tournaments_coords passes")
