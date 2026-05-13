"""
Mappers : convertissent les réponses brutes de API-Football vers le format
attendu par le moteur d'analyse de Varion (data/teams.py, data/players.py, etc.).

C'est ici que se concentre toute la logique de "compatibilité". Si on change
de fournisseur d'API plus tard, on n'a qu'à modifier ce fichier.
"""

import random
from typing import Optional


def _form_string_to_list(form_str: str) -> list:
    """
    Convertit "WWLDW" en [1, 1, -1, 0, 1] (le plus récent en dernier).
    """
    if not form_str:
        return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    mapping = {"W": 1, "D": 0, "L": -1}
    return [mapping.get(c, 0) for c in form_str[-10:]]


def _safe_div(num, den, default=0.0):
    try:
        if den is None or den == 0:
            return default
        return num / den
    except (TypeError, ZeroDivisionError):
        return default


def map_team(stats_response: dict, standing_entry: dict, league_short: str) -> dict:
    """
    Convertit la réponse /teams/statistics + une entrée de /standings
    vers le format Varion (cf data/teams.py pour la structure attendue).
    """
    team_info = stats_response.get("team", {}) or {}
    fixtures = stats_response.get("fixtures", {}) or {}
    goals = stats_response.get("goals", {}) or {}
    cards = stats_response.get("cards", {}) or {}
    cs = stats_response.get("clean_sheet", {}) or {}
    form_str = stats_response.get("form", "") or ""

    played_total = (fixtures.get("played", {}) or {}).get("total", 0) or 1
    played_home = (fixtures.get("played", {}) or {}).get("home", 0) or 1
    played_away = (fixtures.get("played", {}) or {}).get("away", 0) or 1

    # Buts
    goals_for_total = (goals.get("for", {}).get("total", {}) or {}).get("total", 0) or 0
    goals_for_home = (goals.get("for", {}).get("total", {}) or {}).get("home", 0) or 0
    goals_for_away = (goals.get("for", {}).get("total", {}) or {}).get("away", 0) or 0
    goals_against_total = (goals.get("against", {}).get("total", {}) or {}).get("total", 0) or 0
    goals_against_home = (goals.get("against", {}).get("total", {}) or {}).get("home", 0) or 0
    goals_against_away = (goals.get("against", {}).get("total", {}) or {}).get("away", 0) or 0

    # Wins per venue (depuis /standings.all et home/away splits)
    wins_home = (fixtures.get("wins", {}) or {}).get("home", 0) or 0
    wins_away = (fixtures.get("wins", {}) or {}).get("away", 0) or 0

    # Cartons (jaune et rouge totaux sur la saison)
    yellow_total = sum(
        (cards.get("yellow", {}) or {}).get(str(slot), {}).get("total", 0) or 0
        for slot in ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90", "91-105", "106-120"]
    )
    red_total = sum(
        (cards.get("red", {}) or {}).get(str(slot), {}).get("total", 0) or 0
        for slot in ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90", "91-105", "106-120"]
    )

    # Clean sheets
    cs_total = cs.get("total", 0) or 0

    # BTTS et Over 2.5 — non fournis directement, on les déduit des matchs joués
    # Approximation simple basée sur les moyennes
    avg_goals_match = _safe_div(goals_for_total + goals_against_total, played_total)
    btts_estimate = _btts_estimate(avg_goals_match)
    over_25_estimate = _over_25_estimate(avg_goals_match)
    over_35_estimate = max(15, over_25_estimate - 25)  # heuristique

    # Standings : rang, points
    rank = standing_entry.get("rank", 0)
    points = standing_entry.get("points", 0)

    # Forme : standings.form est plus récente que stats.form
    form10 = _form_string_to_list(standing_entry.get("form", form_str))

    # xG / xGA : pas dispo dans /teams/statistics du free tier
    # On approxime avec les buts (réalisme statistique acceptable)
    xg_avg = _safe_div(goals_for_total, played_total) * 0.95
    xga_avg = _safe_div(goals_against_total, played_total) * 0.95

    # Couleur : on prendra le 1er des 2 connus si disponible
    logo_color = team_info.get("logo_color", "#444")

    # Style de jeu : pas dispo, valeur par défaut
    play_style = "balanced"

    return {
        "id": team_info.get("code") or str(team_info.get("id", "")),
        "api_id": team_info.get("id"),
        "name": team_info.get("name", "Unknown"),
        "short": team_info.get("name", "Unknown")[:15],
        "league": league_short,
        "logo_color": logo_color,
        "logo_url": team_info.get("logo"),
        "rank": rank,
        "points": points,
        "played": played_total,
        "form_10": form10,
        "goals_for_avg": round(_safe_div(goals_for_total, played_total), 2),
        "goals_against_avg": round(_safe_div(goals_against_total, played_total), 2),
        "xg_avg": round(xg_avg, 2),
        "xga_avg": round(xga_avg, 2),
        # Stats non fournies par /teams/statistics : valeurs neutres
        "shots_avg": 12.0,
        "shots_on_target_avg": 4.5,
        "possession_avg": 50.0,
        "corners_for_avg": 5.5,
        "corners_against_avg": 5.0,
        "yellow_avg": round(_safe_div(yellow_total, played_total), 2),
        "red_avg": round(_safe_div(red_total, played_total), 2),
        "clean_sheets_pct": round(_safe_div(cs_total, played_total) * 100, 1),
        "btts_pct": btts_estimate,
        "over_25_pct": over_25_estimate,
        "over_35_pct": over_35_estimate,
        "home": {
            "goals_for": round(_safe_div(goals_for_home, played_home), 2),
            "goals_against": round(_safe_div(goals_against_home, played_home), 2),
            "wins_pct": round(_safe_div(wins_home, played_home) * 100, 1),
        },
        "away": {
            "goals_for": round(_safe_div(goals_for_away, played_away), 2),
            "goals_against": round(_safe_div(goals_against_away, played_away), 2),
            "wins_pct": round(_safe_div(wins_away, played_away) * 100, 1),
        },
        "play_style": play_style,
        "press_intensity": 0.75,
    }


def map_player(player_response: dict, team_api_id: int, team_internal_id: str) -> dict:
    """
    Convertit la réponse /players (1 entry) vers le format Varion.

    Note : les stats varient selon les compétitions. On agrège sur la saison
    pour la ligue principale.
    """
    player = player_response.get("player", {}) or {}
    stats_list = player_response.get("statistics", []) or []

    # On prend les stats agrégées (toutes compétitions confondues pour cette saison)
    if not stats_list:
        return None

    # Agréger
    total_goals = 0
    total_assists = 0
    total_minutes = 0
    total_appearances = 0
    total_lineups = 0
    total_shots = 0
    total_shots_on = 0
    total_yellow = 0
    total_red = 0
    position = ""

    for s in stats_list:
        games = s.get("games", {}) or {}
        goals = s.get("goals", {}) or {}
        shots = s.get("shots", {}) or {}
        cards = s.get("cards", {}) or {}

        total_goals += goals.get("total") or 0
        total_assists += goals.get("assists") or 0
        total_minutes += games.get("minutes") or 0
        total_appearances += games.get("appearences") or 0
        total_lineups += games.get("lineups") or 0
        total_shots += shots.get("total") or 0
        total_shots_on += shots.get("on") or 0
        total_yellow += cards.get("yellow") or 0
        total_red += cards.get("red") or 0
        if not position:
            position = games.get("position") or ""

    pos = _normalize_position(position)

    # xG / xA : pas dans le free tier, on approxime
    xg_estimate = total_goals * 0.85  # léger underperform attendu
    xa_estimate = total_assists * 0.9

    # Forme récente : pas calculable directement, valeurs neutres
    form_5 = [7.0, 7.0, 7.0, 7.0, 7.0]

    # Joueur clé si beaucoup de titularisations OU but/passe à fort impact
    is_key = total_lineups >= 8 or total_goals >= 3 or total_assists >= 4

    return {
        "id": f"{team_internal_id}_{player.get('id')}",
        "api_id": player.get("id"),
        "name": player.get("name", "Unknown"),
        "pos": pos,
        "team": team_internal_id,
        "starts": total_lineups,
        "minutes": total_minutes,
        "goals": total_goals,
        "assists": total_assists,
        "xg": round(xg_estimate, 2),
        "xa": round(xa_estimate, 2),
        "shots": total_shots,
        "sot": total_shots_on,
        "yellow": total_yellow,
        "red": total_red,
        "form_5": form_5,
        "is_key": is_key,
    }


def _normalize_position(pos_raw: str) -> str:
    """API-Football utilise 'Goalkeeper', 'Defender', 'Midfielder', 'Attacker'."""
    if not pos_raw:
        return "MID"
    p = pos_raw.lower()
    if "goal" in p:
        return "GK"
    if "def" in p:
        return "DEF"
    if "mid" in p:
        return "MID"
    if "att" in p or "for" in p:
        return "FWD"
    return "MID"


def _btts_estimate(avg_goals_match: float) -> float:
    """Heuristique simple : plus la moyenne de buts est élevée, plus BTTS est probable."""
    if avg_goals_match < 2.0:
        return 38.0
    if avg_goals_match < 2.5:
        return 48.0
    if avg_goals_match < 3.0:
        return 55.0
    if avg_goals_match < 3.5:
        return 62.0
    return 68.0


def _over_25_estimate(avg_goals_match: float) -> float:
    """Heuristique simple."""
    if avg_goals_match < 2.0:
        return 35.0
    if avg_goals_match < 2.5:
        return 50.0
    if avg_goals_match < 3.0:
        return 60.0
    if avg_goals_match < 3.5:
        return 70.0
    return 78.0


def map_fixture(fixture_response: dict, team_id_map: dict) -> Optional[dict]:
    """
    Convertit une fixture API-Football en match Varion.

    team_id_map : mapping {api_id: internal_id} pour faire le lien.
    """
    fixture = fixture_response.get("fixture", {}) or {}
    league = fixture_response.get("league", {}) or {}
    teams = fixture_response.get("teams", {}) or {}

    home_api_id = (teams.get("home") or {}).get("id")
    away_api_id = (teams.get("away") or {}).get("id")

    home_id = team_id_map.get(home_api_id)
    away_id = team_id_map.get(away_api_id)

    if not home_id or not away_id:
        # Une des équipes n'est pas dans notre dataset → on skip
        return None

    # Date et heure
    date_str = fixture.get("date", "")
    date_only = date_str[:10] if date_str else ""
    time_only = date_str[11:16] if date_str else ""

    # Cotes simulées (le user verra plus tard)
    odds = _generate_default_odds()

    # Détection derby (basique : équipes même ville/pays)
    is_derby = _detect_derby(teams.get("home", {}).get("name", ""), teams.get("away", {}).get("name", ""))

    return {
        "id": f"M_{fixture.get('id')}",
        "api_id": fixture.get("id"),
        "home": home_id,
        "away": away_id,
        "date": date_only,
        "kickoff": time_only,
        "venue": (fixture.get("venue") or {}).get("name", ""),
        "competition": f"{league.get('name', '')} - J{league.get('round', '').replace('Regular Season - ', '')}",
        "referee": fixture.get("referee") or "TBD",
        "ref_yellow_avg": 4.2,
        "ref_red_avg": 0.12,
        "stakes": "medium",
        "is_derby": is_derby,
        "odds": odds,
    }


def _generate_default_odds() -> dict:
    """Cotes simulées en attendant la vraie API de cotes."""
    return {
        "1": 2.20, "X": 3.40, "2": 3.20,
        "btts_yes": 1.75, "btts_no": 2.05,
        "over_25": 1.85, "under_25": 1.95,
        "over_35": 2.50, "under_35": 1.55,
        "cs_home": 4.00, "cs_away": 5.00,
        "corners_over_95": 1.90, "corners_under_95": 1.90,
        "cards_over_45": 1.90, "cards_under_45": 1.90,
        "scorer": {},
    }


def _detect_derby(home_name: str, away_name: str) -> bool:
    """Heuristique simple pour détecter les derbies par mot commun."""
    if not home_name or not away_name:
        return False
    derbies_keywords = [
        # Anglais
        ("Manchester City", "Manchester United"),
        ("Liverpool", "Manchester United"),
        ("Arsenal", "Tottenham"),
        ("Chelsea", "Tottenham"),
        ("Chelsea", "Arsenal"),
        # Espagnols
        ("Real Madrid", "Barcelona"),
        ("Real Madrid", "Atletico"),
        ("Barcelona", "Espanyol"),
        # Italiens
        ("Milan", "Inter"),
        ("Roma", "Lazio"),
        ("Juventus", "Torino"),
        # Allemands
        ("Bayern", "Dortmund"),
        # Français
        ("PSG", "Marseille"),
        ("Paris", "Marseille"),
    ]
    for a, b in derbies_keywords:
        if (a in home_name and b in away_name) or (b in home_name and a in away_name):
            return True
    return False


def map_h2h(h2h_response: list, home_api_id: int) -> list:
    """Convertit les fixtures H2H en format Varion."""
    out = []
    for fix in h2h_response[:5]:
        fixture = fix.get("fixture", {}) or {}
        teams = fix.get("teams", {}) or {}
        score = fix.get("score", {}).get("fulltime", {}) or {}

        home_t = teams.get("home", {}) or {}
        away_t = teams.get("away", {}) or {}

        h_score = score.get("home")
        a_score = score.get("away")
        if h_score is None or a_score is None:
            continue

        winner = None
        if h_score > a_score:
            winner = "home" if home_t.get("id") == home_api_id else "away"
        elif a_score > h_score:
            winner = "away" if home_t.get("id") == home_api_id else "home"

        out.append({
            "date": fixture.get("date", "")[:10],
            "score": f"{h_score}-{a_score}",
            "venue": (fixture.get("venue") or {}).get("name", ""),
            "winner": winner,
        })
    return out
