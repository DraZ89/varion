"""
Matchs à venir + historique head-to-head + cotes bookmakers réalistes.
Les cotes sont calibrées pour permettre la détection de value bets.
"""

UPCOMING_MATCHES = [
    {
        "id": "M001",
        "home": "ARS",
        "away": "MCI",
        "date": "2026-04-30",
        "kickoff": "20:00",
        "venue": "Emirates Stadium",
        "competition": "Premier League - J31",
        "referee": "Michael Oliver",
        "ref_yellow_avg": 4.8,
        "ref_red_avg": 0.18,
        "stakes": "high",  # course au titre
        "is_derby": False,
        # Cotes bookmakers (Pinnacle-style, marge ~3%)
        "odds": {
            "1": 2.30, "X": 3.45, "2": 2.95,
            "btts_yes": 1.72, "btts_no": 2.10,
            "over_25": 1.78, "under_25": 2.05,
            "over_35": 2.55, "under_35": 1.50,
            "cs_home": 4.20, "cs_away": 4.50,
            "corners_over_95": 1.85, "corners_under_95": 1.95,
            "cards_over_45": 1.88, "cards_under_45": 1.92,
            # Buteurs (Salah, Haaland, etc.)
            "scorer": {
                "MCI_F1": 1.95,  # Haaland
                "ARS_F1": 2.30,  # Saka
                "ARS_M3": 3.40,  # Havertz
                "MCI_M4": 3.20,  # Foden
            }
        },
    },
    {
        "id": "M002",
        "home": "LIV",
        "away": "MUN",
        "date": "2026-05-01",
        "kickoff": "17:30",
        "venue": "Anfield",
        "competition": "Premier League - J31",
        "referee": "Anthony Taylor",
        "ref_yellow_avg": 5.2,
        "ref_red_avg": 0.22,
        "stakes": "high",
        "is_derby": True,  # rivalité historique
        "odds": {
            "1": 1.55, "X": 4.40, "2": 5.80,
            "btts_yes": 1.65, "btts_no": 2.25,
            "over_25": 1.65, "under_25": 2.25,
            "over_35": 2.20, "under_35": 1.65,
            "cs_home": 3.30, "cs_away": 7.50,
            "corners_over_95": 1.78, "corners_under_95": 2.02,
            "cards_over_45": 1.55, "cards_under_45": 2.40,
            "scorer": {
                "LIV_F1": 1.75,  # Salah
                "LIV_F2": 3.20,  # Diaz
                "MUN_M1": 3.60,  # B.Fernandes
                "MUN_F3": 4.20,  # Hojlund
            }
        },
    },
    {
        "id": "M003",
        "home": "CHE",
        "away": "TOT",
        "date": "2026-05-02",
        "kickoff": "16:00",
        "venue": "Stamford Bridge",
        "competition": "Premier League - J31",
        "referee": "Simon Hooper",
        "ref_yellow_avg": 4.5,
        "ref_red_avg": 0.15,
        "stakes": "medium",
        "is_derby": True,  # London derby
        "odds": {
            "1": 2.05, "X": 3.60, "2": 3.40,
            "btts_yes": 1.50, "btts_no": 2.55,
            "over_25": 1.55, "under_25": 2.45,
            "over_35": 2.05, "under_35": 1.78,
            "cs_home": 4.80, "cs_away": 5.80,
            "corners_over_95": 1.82, "corners_under_95": 1.98,
            "cards_over_45": 1.65, "cards_under_45": 2.20,
            "scorer": {
                "CHE_M3": 1.85,  # Palmer
                "CHE_F1": 2.85,  # Jackson
                "TOT_F1": 2.40,  # Son
                "TOT_F3": 2.95,  # Solanke
            }
        },
    },
    {
        "id": "M004",
        "home": "AVL",
        "away": "NEW",
        "date": "2026-05-02",
        "kickoff": "20:00",
        "venue": "Villa Park",
        "competition": "Premier League - J31",
        "referee": "Stuart Attwell",
        "ref_yellow_avg": 4.2,
        "ref_red_avg": 0.10,
        "stakes": "medium",  # course Europe
        "is_derby": False,
        "odds": {
            "1": 2.15, "X": 3.50, "2": 3.20,
            "btts_yes": 1.62, "btts_no": 2.30,
            "over_25": 1.72, "under_25": 2.10,
            "over_35": 2.45, "under_35": 1.55,
            "cs_home": 4.50, "cs_away": 5.20,
            "corners_over_95": 1.95, "corners_under_95": 1.85,
            "cards_over_45": 1.95, "cards_under_45": 1.85,
            "scorer": {
                "AVL_F1": 2.10,  # Watkins
                "AVL_F3": 3.50,  # Rogers
                "NEW_F1": 2.05,  # Isak
                "NEW_F2": 3.30,  # Gordon
            }
        },
    },
    {
        "id": "M005",
        "home": "BHA",
        "away": "WHU",
        "date": "2026-05-03",
        "kickoff": "15:00",
        "venue": "Amex Stadium",
        "competition": "Premier League - J31",
        "referee": "Craig Pawson",
        "ref_yellow_avg": 3.9,
        "ref_red_avg": 0.08,
        "stakes": "low",
        "is_derby": False,
        "odds": {
            "1": 1.85, "X": 3.80, "2": 4.20,
            "btts_yes": 1.55, "btts_no": 2.40,
            "over_25": 1.62, "under_25": 2.30,
            "over_35": 2.20, "under_35": 1.65,
            "cs_home": 4.20, "cs_away": 6.50,
            "corners_over_95": 1.88, "corners_under_95": 1.92,
            "cards_over_45": 2.05, "cards_under_45": 1.75,
            "scorer": {
                "BHA_F2": 2.50,  # Welbeck
                "BHA_F1": 2.75,  # Joao Pedro
                "WHU_F1": 2.30,  # Bowen
                "WHU_F3": 3.80,  # Fullkrug
            }
        },
    },
]

# Head-to-head : 5 derniers matchs entre les deux équipes
H2H = {
    ("ARS", "MCI"): [
        {"date": "2025-09-22", "score": "2-2", "venue": "Emirates", "winner": None},
        {"date": "2025-03-31", "score": "0-0", "venue": "Etihad", "winner": None},
        {"date": "2024-10-08", "score": "2-2", "venue": "Etihad", "winner": None},
        {"date": "2024-03-31", "score": "0-0", "venue": "Emirates", "winner": None},
        {"date": "2023-10-08", "score": "1-0", "venue": "Emirates", "winner": "ARS"},
    ],
    ("LIV", "MUN"): [
        {"date": "2025-09-01", "score": "3-0", "venue": "Anfield", "winner": "LIV"},
        {"date": "2025-04-07", "score": "2-2", "venue": "Old Trafford", "winner": None},
        {"date": "2024-12-17", "score": "0-0", "venue": "Anfield", "winner": None},
        {"date": "2024-04-07", "score": "2-2", "venue": "Old Trafford", "winner": None},
        {"date": "2023-12-17", "score": "0-0", "venue": "Anfield", "winner": None},
    ],
    ("CHE", "TOT"): [
        {"date": "2025-12-08", "score": "4-3", "venue": "Stamford Bridge", "winner": "CHE"},
        {"date": "2025-05-02", "score": "2-0", "venue": "Tottenham Hotspur Stadium", "winner": "TOT"},
        {"date": "2024-11-12", "score": "4-1", "venue": "Stamford Bridge", "winner": "CHE"},
        {"date": "2024-05-02", "score": "2-0", "venue": "Tottenham Hotspur Stadium", "winner": "TOT"},
        {"date": "2023-11-06", "score": "1-1", "venue": "Tottenham Hotspur Stadium", "winner": None},
    ],
    ("AVL", "NEW"): [
        {"date": "2025-12-26", "score": "3-0", "venue": "St James' Park", "winner": "NEW"},
        {"date": "2025-08-19", "score": "5-1", "venue": "Villa Park", "winner": "AVL"},
        {"date": "2024-08-19", "score": "5-1", "venue": "Villa Park", "winner": "AVL"},
        {"date": "2024-04-30", "score": "3-1", "venue": "St James' Park", "winner": "NEW"},
        {"date": "2024-01-30", "score": "1-3", "venue": "Villa Park", "winner": "NEW"},
    ],
    ("BHA", "WHU"): [
        {"date": "2025-09-21", "score": "3-2", "venue": "Amex", "winner": "BHA"},
        {"date": "2025-02-02", "score": "0-0", "venue": "London Stadium", "winner": None},
        {"date": "2024-09-21", "score": "3-1", "venue": "Amex", "winner": "BHA"},
        {"date": "2024-02-02", "score": "0-0", "venue": "London Stadium", "winner": None},
        {"date": "2023-08-26", "score": "1-3", "venue": "Amex", "winner": "WHU"},
    ],
}


def get_match(match_id: str):
    for m in UPCOMING_MATCHES:
        if m["id"] == match_id:
            return m
    return None


def get_all_matches():
    return UPCOMING_MATCHES


def get_h2h(home: str, away: str):
    """Récupère le head-to-head dans les deux sens"""
    if (home, away) in H2H:
        return H2H[(home, away)]
    if (away, home) in H2H:
        return H2H[(away, home)]
    return []
