"""
Mapper tennis : convertit les reponses Matchstat vers le format Varion.

Vraies structures decouvertes :

# RANKING
{ "data": [{ "position": 1, "point": 13350,
             "player": { "id": 47275, "name": "Sinner", "countryAcr": "ITA",
                         "country": { "name": "Italy", "acronym": "ITA" } } }] }

# FIXTURES / PAST MATCHES / H2H : meme structure
{ "data": [{ "id": "1242312", "date": "2026-03-11T...",
             "player1Id": 63017, "player2Id": 5992,
             "tournamentId": 21317, "match_winner": 63017,
             "result": "4-6 6-4 7-6(5)", "best_of": null,
             "odd1": "1.46", "odd2": "2.7",  # cotes parfois !
             "player1": { "id": 63017, "name": "Jack Draper", "countryAcr": "GBR" },
             "player2": { "id": 5992, "name": "Novak Djokovic", "countryAcr": "SRB" } }] }

# SURFACE SUMMARY
{ "data": [{ "year": 2025,
             "surfaces": [{ "courtId": 1, "court": "Hard",
                            "courtWins": 21, "courtLosses": 7 }] }] }
"""

from typing import Optional
from collections import defaultdict

from engine.tennis.elo import (
    calculate_player_elos_from_history,
    INITIAL_ELO,
    normalize_surface,
)


# courtId -> notre surface normalisee
COURT_ID_TO_SURFACE = {
    1: "hard",     # Hard
    2: "clay",     # Clay
    3: "hard",     # I.hard (indoor hard) -> regroupe avec hard
    4: "hard",     # Carpet -> rare, regroupe avec hard
    5: "grass",    # Grass
}


def _safe_int(val, default=0):
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def _safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


# ============ TOURNOIS ============

def detect_tournament_type(tournament_name: str) -> str:
    """Detecte le type pour ajuster K-factor ELO et format BO3/BO5."""
    if not tournament_name:
        return "Other"
    n = tournament_name.lower()
    if any(gs in n for gs in ["australian open", "roland garros", "french open", "wimbledon", "us open"]):
        return "Grand Slam"
    if "masters" in n or "1000" in n:
        return "Masters 1000"
    if "500" in n:
        return "ATP 500"
    if "250" in n:
        return "ATP 250"
    if "challenger" in n:
        return "Challenger"
    if "itf" in n:
        return "ITF"
    if "davis" in n or "billie" in n:
        return "Davis Cup"
    return "Other"


def is_best_of_5(tournament_type: str, tour: str) -> bool:
    """BO5 uniquement pour Grand Slams hommes."""
    return tournament_type == "Grand Slam" and tour.lower() == "atp"


# ============ ELO DEPUIS SURFACE-SUMMARY ============

def calculate_elo_from_surface_summary(surface_data: list) -> dict:
    """
    Calcule un ELO approximatif a partir du bilan W/L par surface (toutes annees).

    Logique : on part d'INITIAL_ELO et on ajuste selon le ratio W/L
    pondere par le volume de matchs. Plus un joueur a gagne, plus son ELO monte.

    surface_data : reponse de getPlayerSurfaceSummary
    [{ year, surfaces: [{ courtId, court, courtWins, courtLosses }] }]
    """
    # Aggreger par surface (toutes annees confondues, ponderation recente)
    aggregated = defaultdict(lambda: {"wins": 0, "losses": 0})

    current_year = 2026  # ajuster si besoin
    for entry in surface_data:
        year = entry.get("year", 0)
        # Ponderation : annees recentes comptent plus (decay exponentiel)
        recency_weight = max(0.1, 1.0 - (current_year - year) * 0.10)

        for s in entry.get("surfaces", []):
            court_id = s.get("courtId")
            surface = COURT_ID_TO_SURFACE.get(court_id, "hard")
            wins = s.get("courtWins", 0) * recency_weight
            losses = s.get("courtLosses", 0) * recency_weight
            aggregated[surface]["wins"] += wins
            aggregated[surface]["losses"] += losses

    # Convertir en ELO : ratio_W * volume_factor
    # ELO = INITIAL + 600 * (winrate - 0.5) * volume_log
    import math
    elos = {"global": INITIAL_ELO, "hard": INITIAL_ELO, "clay": INITIAL_ELO, "grass": INITIAL_ELO}

    total_wins = 0
    total_losses = 0

    for surface, stats in aggregated.items():
        w = stats["wins"]
        l = stats["losses"]
        total = w + l
        if total < 5:
            continue
        winrate = w / total
        # log scale pour eviter que les vieux joueurs explosent
        volume_factor = math.log(total + 1) / math.log(100)
        volume_factor = min(1.5, volume_factor)

        # Map winrate [0.3, 0.85] -> ELO offset [-400, +700]
        elo_offset = (winrate - 0.5) * 1300 * volume_factor
        elos[surface] = INITIAL_ELO + elo_offset

        total_wins += w
        total_losses += l

    # ELO global : moyenne ponderee de tous les matchs
    if total_wins + total_losses >= 10:
        global_winrate = total_wins / (total_wins + total_losses)
        global_volume = math.log(total_wins + total_losses + 1) / math.log(150)
        global_volume = min(1.5, global_volume)
        elos["global"] = INITIAL_ELO + (global_winrate - 0.5) * 1300 * global_volume

    return {k: round(v, 0) for k, v in elos.items()}


# ============ MAPPING JOUEURS ============

def map_player_from_ranking(rank_entry: dict, tour: str) -> dict:
    """
    Convertit une entree de ranking en player Varion (ELO neutre,
    a remplir plus tard via surface summary).
    """
    nested = rank_entry.get("player") or {}
    player_id = nested.get("id")
    if not player_id:
        return None

    name = nested.get("name", "Unknown")
    country = nested.get("countryAcr") or (nested.get("country") or {}).get("acronym") or ""
    rank = _safe_int(rank_entry.get("position"))
    points = _safe_int(rank_entry.get("point"))

    return {
        "id": str(player_id),
        "api_id": player_id,
        "name": name,
        "country": country,
        "tour": tour.upper(),
        "rank": rank,
        "points": points,
        "elo": {
            "global": INITIAL_ELO,
            "hard": INITIAL_ELO,
            "clay": INITIAL_ELO,
            "grass": INITIAL_ELO,
        },
        "recent_results": [],
    }


def create_minimal_player(player_id: str, fixture_player: dict, tour: str) -> dict:
    """Cree un player minimal pour les joueurs hors Top N (rang inconnu).

    Utilise pour les matchs ou un joueur est dans le Top mais l'autre non.
    """
    name = fixture_player.get("name") or fixture_player.get("playerName") or f"Player {player_id}"
    country = fixture_player.get("countryAcr") or (fixture_player.get("country") or {}).get("acronym") or ""

    return {
        "id": str(player_id),
        "api_id": _safe_int(player_id) if str(player_id).isdigit() else None,
        "name": name,
        "country": country,
        "tour": tour.upper(),
        "rank": 0,  # 0 = hors classement Top N
        "points": 0,
        "elo": {
            "global": INITIAL_ELO - 50,  # leger malus pour outsider
            "hard": INITIAL_ELO - 50,
            "clay": INITIAL_ELO - 50,
            "grass": INITIAL_ELO - 50,
        },
        "recent_results": [],
        "is_outsider": True,  # marqueur pour le frontend
    }


def enrich_player_with_surface_data(player: dict, surface_summary: list) -> dict:
    """Met a jour les ELO du joueur depuis surface-summary."""
    if surface_summary:
        player["elo"] = calculate_elo_from_surface_summary(surface_summary)
    return player


def enrich_player_with_recent_results(player: dict, past_matches: list) -> dict:
    """Met a jour la forme recente (5 derniers matchs).
    Format : liste d'objets [{result: 'W'/'L', date, opponent, score}, ...]
    """
    pid = player["api_id"]

    sorted_matches = sorted(past_matches, key=lambda m: m.get("date") or "", reverse=True)

    results = []
    for m in sorted_matches[:5]:
        winner = m.get("match_winner")
        if winner is None:
            continue

        won = (winner == pid)

        # Date au format court "YYYY-MM-DD"
        date_str = m.get("date") or ""
        date_short = date_str[:10] if date_str else ""

        # Adversaire (autre joueur)
        p1_id = m.get("player1Id")
        p2_id = m.get("player2Id")
        p1_name = (m.get("player1") or {}).get("name", "")
        p2_name = (m.get("player2") or {}).get("name", "")

        if p1_id == pid:
            opponent = p2_name
        else:
            opponent = p1_name

        # Score
        score = m.get("result") or m.get("score") or ""

        results.append({
            "result": "W" if won else "L",
            "won": won,  # garde le booleen pour compat
            "date": date_short,
            "opponent": opponent,
            "score": score,
        })

    player["recent_results"] = results
    return player


# ============ MAPPING H2H ============

def map_h2h(h2h_matches: list, player_a_id) -> dict:
    """
    Compte les wins de chaque joueur dans le H2H.
    Player_a_id : l'ID du joueur "A" pour notre point de vue.
    """
    if not h2h_matches:
        return {"wins_a": 0, "wins_b": 0, "last_5_matches": []}

    wins_a = 0
    wins_b = 0
    last_5 = []

    sorted_matches = sorted(h2h_matches, key=lambda m: m.get("date") or "", reverse=True)

    for m in sorted_matches:
        winner = m.get("match_winner")
        if winner is None:
            continue
        # match_winner contient l'ID du gagnant
        if winner == player_a_id:
            wins_a += 1
            who_won = "A"
        else:
            wins_b += 1
            who_won = "B"

        if len(last_5) < 5:
            last_5.append({
                "date": (m.get("date") or "")[:10],
                "result": m.get("result", ""),
                "winner": who_won,
            })

    return {
        "wins_a": wins_a,
        "wins_b": wins_b,
        "last_5_matches": last_5,
    }


# ============ MAPPING MATCHS ============

def map_match(fixture: dict, players_index: dict, tour: str) -> Optional[dict]:
    """
    Convertit un fixture API en match Varion.

    fixture : entree de /fixtures/{date} ou /past-matches/{id}
    players_index : { str(player_id): player_dict_mappe }
    """
    match_id = fixture.get("id")
    if not match_id:
        return None

    p1_id = fixture.get("player1Id")
    p2_id = fixture.get("player2Id")
    if not p1_id or not p2_id:
        return None

    player_a = players_index.get(str(p1_id))
    player_b = players_index.get(str(p2_id))
    if not player_a or not player_b:
        return None  # joueur hors top, on skip

    # Date / heure
    # date_str est au format "2026-05-06T14:30:00.000Z" (UTC)
    date_str = fixture.get("date") or ""
    date_only = date_str[:10] if date_str else ""
    time_only = date_str[11:16] if len(date_str) > 11 else ""

    # Timestamp Unix UTC pour le countdown frontend (independant de la timezone)
    start_timestamp_ms = 0
    if date_str:
        try:
            from datetime import datetime, timezone
            if date_str.endswith("Z"):
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            start_timestamp_ms = int(dt.timestamp() * 1000)
        except Exception:
            pass

    # Tournoi (on n'a que tournamentId, pas le nom ni la surface)
    # Approximation : Grand Slam = best_of=5 si fourni
    tournament_id = fixture.get("tournamentId")
    best_of = fixture.get("best_of")
    bo5 = (best_of == 5) or (tour.lower() == "atp" and best_of == 5)

    # On n'a pas la surface dans le fixture, on l'inferera plus tard ou on met hard par defaut
    surface = "hard"

    # Cotes reelles si dispo (champ odd1/odd2 dans fixture)
    odd1 = _safe_float(fixture.get("odd1"))
    odd2 = _safe_float(fixture.get("odd2"))
    if odd1 > 1.0 and odd2 > 1.0:
        odds = {"1": odd1, "2": odd2, "_source": "api"}
    else:
        # Pas de cotes API : on indique pour calcul ulterieur depuis predictions
        odds = {"1": None, "2": None, "_source": "none"}

    # Determiner BO3/BO5
    tournament_type = "Other"  # par defaut
    if bo5:
        tournament_type = "Grand Slam"

    return {
        "id": f"T_{match_id}",
        "api_id": match_id,
        "tour": tour.upper(),
        "date": date_only,
        "time": time_only,
        "start_timestamp_ms": start_timestamp_ms,  # UTC, pour countdown frontend
        "tournament_id": tournament_id,
        "tournament": "",  # a remplir si on fetch tournament info
        "tournament_type": tournament_type,
        "round": "",
        "surface": surface,
        "format": "BO5" if bo5 else "BO3",
        "max_sets": 5 if bo5 else 3,
        "status": "scheduled",
        "player_a": player_a,
        "player_b": player_b,
        "odds": odds,
    }


# ============ NOUVEAUX MAPPERS - DONNEES ENRICHIES ============

# Mapping court id -> surface name
COURT_ID_TO_SURFACE = {
    1: "hard",
    2: "clay",
    3: "indoor hard",
    4: "carpet",
    5: "grass",
}


def map_player_profile(profile_data: dict) -> dict:
    """Extrait les infos bio depuis getPlayerInfo.
    Retourne un dict propre prêt pour le frontend.
    """
    if not profile_data:
        return {}

    info = profile_data.get("information") or {}

    return {
        "status": profile_data.get("playerStatus", "Active"),  # Active / Retired
        "turned_pro": _safe_int(info.get("turnedPro")),
        "weight_kg": _safe_int(info.get("weight")),
        "height_cm": _safe_int(info.get("height")),
        "birthplace": info.get("birthplace") or "",
        "residence": info.get("residence") or "",
        "plays": info.get("plays") or "",  # ex "Right-Handed, Two-Handed Backhand"
        "coach": info.get("coach") or "",
    }


def map_tournament_info(tour_data: dict) -> dict:
    """Extrait les infos du tournoi depuis getTourInfo.
    Donne notamment la VRAIE surface (pas hardcodee) + tier.
    """
    if not tour_data:
        return {}

    court = tour_data.get("court") or {}
    country = tour_data.get("coutry") or tour_data.get("country") or {}  # bug API "coutry"

    court_name = (court.get("name") or "").lower()
    # Normalise : "Hard" -> "hard", "Clay" -> "clay", etc.
    surface = court_name if court_name else "hard"

    return {
        "id": tour_data.get("id"),
        "name": tour_data.get("name") or "",
        "tier": tour_data.get("tier") or "Other",  # "Grand Slam", "Masters 1000", etc.
        "surface": surface,
        "court_id": court.get("id"),
        "country": country.get("acronym") or "",
        "country_name": country.get("name") or "",
    }


def _safe_pct(numerator, denominator):
    """Calcule un pourcentage en evitant division par zero."""
    n = _safe_float(numerator)
    d = _safe_float(denominator)
    if d <= 0:
        return 0.0
    return round(100.0 * n / d, 1)


def map_career_stats(vs_all_data: dict) -> dict:
    """Extrait les stats career depuis getH2HVsAllOppStats.
    Retourne stats du joueur + miroir adversaires.
    """
    if not vs_all_data:
        return {}

    p_stats = vs_all_data.get("playerStats") or {}
    o_stats = vs_all_data.get("opponentStats") or {}

    matches_played = _safe_int(p_stats.get("statMatchesPlayed"))
    matches_won = _safe_int(p_stats.get("matchesWon"))

    return {
        "matches_played": matches_played,
        "matches_won": matches_won,
        "matches_lost": matches_played - matches_won,
        "win_rate_pct": _safe_pct(matches_won, matches_played),

        # SERVICE
        "first_serve_pct": _safe_int(p_stats.get("firstServePercentage")),
        "won_first_serve_pct": _safe_int(p_stats.get("winningOnFirstServePercentage")),
        "won_second_serve_pct": _safe_int(p_stats.get("winningOnSecondServePercentage")),
        "aces_total": _safe_int(p_stats.get("aces")),
        "aces_per_match": round(_safe_int(p_stats.get("aces")) / matches_played, 1) if matches_played > 0 else 0,
        "double_faults_total": _safe_int(p_stats.get("doubleFaults")),
        "df_per_match": round(_safe_int(p_stats.get("doubleFaults")) / matches_played, 1) if matches_played > 0 else 0,
        "first_serve_speed_avg": round(_safe_float(p_stats.get("averageFirstServeSpeed")), 0),
        "second_serve_speed_avg": round(_safe_float(p_stats.get("averageSecondServeSpeed")), 0),
        "fastest_serve": _safe_int(p_stats.get("fastestServe")),

        # RETOUR
        "return_pts_won_pct": _safe_int(p_stats.get("returnPtsWinPercentage")),
        "break_pts_converted_pct": _safe_int(p_stats.get("breakpointsWonPercentage")),

        # MENTAL / CLUTCH
        "first_set_won_match_won_pct": _safe_int(p_stats.get("firstSetWinMatchWinPercentage")),
        "first_set_lost_match_won_pct": _safe_int(p_stats.get("firstSetLoseMatchWinPercentage")),
        "deciding_set_win_pct": _safe_int(p_stats.get("decidingSetWinPercentage")),
        "tiebreak_win_pct": _safe_int(p_stats.get("totalTBWinPercentage")),

        # FORMAT
        "bo3_win_pct": _safe_int(p_stats.get("bestOfThreeWonPercentage")),
        "bo5_win_pct": _safe_int(p_stats.get("bestOfFiveWonPercentage")),

        # PALMARES
        "titles": _safe_int(p_stats.get("title")),
        "wins_grand_slam": _safe_int(p_stats.get("grandSlam")),
        "wins_masters": _safe_int(p_stats.get("masters")),
        "wins_main_tour": _safe_int(p_stats.get("mainTour")),
        "wins_challengers": _safe_int(p_stats.get("challengers")),

        # PAR SURFACE (victoires totales)
        "wins_hard": _safe_int(p_stats.get("hard")),
        "wins_clay": _safe_int(p_stats.get("clay")),
        "wins_grass": _safe_int(p_stats.get("grass")),
        "wins_indoor_hard": _safe_int(p_stats.get("iHard")),

        # MIROIR : stats des adversaires moyens (pour comparer)
        "opponent_first_serve_pct": _safe_int(o_stats.get("firstServePercentage")),
        "opponent_aces_per_match": round(_safe_int(o_stats.get("aces")) / matches_played, 1) if matches_played > 0 else 0,
        "opponent_break_pts_converted_pct": _safe_int(o_stats.get("breakpointsWonPercentage")),

        # Duree moyenne match
        "avg_match_time": p_stats.get("avgTime") or "",
    }


def map_h2h_specific_stats(h2h_data: dict, player1_id) -> dict:
    """Extrait les stats H2H specifiques entre 2 joueurs.
    Calcule winrate par surface depuis les wins par court (hard/clay/grass/iHard).
    """
    if not h2h_data:
        return {}

    p1 = h2h_data.get("player1Stats") or {}
    p2 = h2h_data.get("player2Stats") or {}

    matches_count = _safe_int(h2h_data.get("matchesCount"))
    p1_wins = _safe_int(p1.get("matchesWon"))
    p2_wins = _safe_int(p2.get("matchesWon"))

    # Determine quel cote est player_a (notre joueur de reference) vs player_b
    if str(p1.get("id")) == str(player1_id):
        a, b = p1, p2
    else:
        a, b = p2, p1

    return {
        "matches_count": matches_count,
        "wins_a": _safe_int(a.get("matchesWon")),
        "wins_b": _safe_int(b.get("matchesWon")),

        # Wins par surface dans leur H2H
        "wins_a_hard": _safe_int(a.get("hard")),
        "wins_b_hard": _safe_int(b.get("hard")),
        "wins_a_clay": _safe_int(a.get("clay")),
        "wins_b_clay": _safe_int(b.get("clay")),
        "wins_a_grass": _safe_int(a.get("grass")),
        "wins_b_grass": _safe_int(b.get("grass")),

        # Stats serve dans leur H2H
        "first_serve_pct_a": _safe_int(a.get("firstServePercentage")),
        "first_serve_pct_b": _safe_int(b.get("firstServePercentage")),
        "deciding_set_pct_a": _safe_int(a.get("decidingSetWinPercentage")),
        "deciding_set_pct_b": _safe_int(b.get("decidingSetWinPercentage")),
        "tiebreak_pct_a": _safe_int(a.get("totalTBWinPercentage")),
        "tiebreak_pct_b": _safe_int(b.get("totalTBWinPercentage")),

        # Duree moyenne de leurs matchs
        "avg_match_time": a.get("avgTime") or "",
    }


def aggregate_perf_breakdown(perf_data: dict, last_n_years: int = 3) -> dict:
    """Agrege les stats des N dernieres annees depuis getPlayerPerformanceBreakdown.
    Plus pertinent que la donnee career complete pour predire un match a venir.
    """
    if not perf_data:
        return {}

    # Tri annees decroissantes (les + recentes d'abord)
    years_sorted = sorted(perf_data.keys(), reverse=True)
    recent_years = years_sorted[:last_n_years]

    # Agregats
    courts = {1: {"aw": 0, "al": 0}, 2: {"aw": 0, "al": 0},
              3: {"aw": 0, "al": 0}, 4: {"aw": 0, "al": 0},
              5: {"aw": 0, "al": 0}}
    ranks = {"top1": {"aw": 0, "al": 0}, "top5": {"aw": 0, "al": 0},
             "top10": {"aw": 0, "al": 0}, "top20": {"aw": 0, "al": 0},
             "top50": {"aw": 0, "al": 0}, "top100": {"aw": 0, "al": 0}}
    levels = {"masters": {"aw": 0, "al": 0}, "tourFinals": {"aw": 0, "al": 0},
              "mainTour": {"aw": 0, "al": 0}, "grandSlam": {"aw": 0, "al": 0},
              "cups": {"aw": 0, "al": 0}, "challengers": {"aw": 0, "al": 0}}

    for year in recent_years:
        ydata = perf_data.get(year) or {}

        # Cumul courts
        for cid in [1, 2, 3, 4, 5]:
            cdata = (ydata.get("court") or {}).get(str(cid)) or (ydata.get("court") or {}).get(cid) or {}
            if isinstance(cdata, dict):
                courts[cid]["aw"] += _safe_int(cdata.get("aw"))
                courts[cid]["al"] += _safe_int(cdata.get("al"))

        # Cumul rank vs Top X
        for rk in ranks:
            rdata = (ydata.get("rank") or {}).get(rk) or {}
            if isinstance(rdata, dict):
                ranks[rk]["aw"] += _safe_int(rdata.get("aw"))
                ranks[rk]["al"] += _safe_int(rdata.get("al"))

        # Cumul level
        for lv in levels:
            ldata = (ydata.get("level") or {}).get(lv) or {}
            if isinstance(ldata, dict):
                levels[lv]["aw"] += _safe_int(ldata.get("aw"))
                levels[lv]["al"] += _safe_int(ldata.get("al"))

    # Format frontend friendly avec winrate calcule
    def fmt(d):
        w, l = d["aw"], d["al"]
        total = w + l
        return {"wins": w, "losses": l, "total": total,
                "win_rate": round(100.0 * w / total, 1) if total > 0 else 0.0}

    return {
        "years_analyzed": recent_years,
        # Par surface (courts)
        "hard": fmt(courts[1]),
        "clay": fmt(courts[2]),
        "indoor_hard": fmt(courts[3]),
        "grass": fmt(courts[5]),
        # Par niveau adversaire
        "vs_top10": fmt(ranks["top10"]),
        "vs_top20": fmt(ranks["top20"]),
        "vs_top50": fmt(ranks["top50"]),
        "vs_top100": fmt(ranks["top100"]),
        # Par niveau tournoi
        "lv_grand_slam": fmt(levels["grandSlam"]),
        "lv_masters": fmt(levels["masters"]),
        "lv_main_tour": fmt(levels["mainTour"]),
        "lv_challengers": fmt(levels["challengers"]),
    }


# ============ COMPUTE FAIR ODDS DEPUIS PREDICTIONS ============

def compute_fair_odds_from_predictions(predictions: dict, bookmaker_margin: float = 0.06) -> dict:
    """A defaut de cotes reelles, calcule des cotes 'realistes' depuis nos predictions ELO.
    
    Principe :
      - Cote brute = 1 / probabilite (cote vraie sans marge)
      - Bookmaker ajoute une marge typique 4-8% reduisant les cotes
    
    bookmaker_margin = 0.06 (6%) est typique sur les bookmakers serieux (Pinnacle 4%, Bet365 7%).
    """
    winner = predictions.get("winner") or {}
    prob_a = winner.get("prob_a", 50) / 100.0
    prob_b = winner.get("prob_b", 50) / 100.0
    
    if prob_a <= 0 or prob_b <= 0:
        return {"1": None, "2": None, "_source": "none"}
    
    # Cote vraie = 1 / proba
    fair_odd_a = 1.0 / prob_a
    fair_odd_b = 1.0 / prob_b
    
    # Application marge bookmaker (overround)
    # En pratique bookies multiplient par 1+m/2 pour chaque cote, simplifie ici
    margin_factor = 1.0 - bookmaker_margin / 2.0
    odd_a = round(fair_odd_a * margin_factor, 2)
    odd_b = round(fair_odd_b * margin_factor, 2)
    
    # Garde-fou : cote minimum 1.01
    odd_a = max(1.01, odd_a)
    odd_b = max(1.01, odd_b)
    
    return {"1": odd_a, "2": odd_b, "_source": "estimated"}
