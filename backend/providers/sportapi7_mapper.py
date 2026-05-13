"""
Mapper SportAPI7 : convertit les reponses vers le format Varion existant.

Format cible (compatible engine/football/*) :
- TEAMS : {tid: {id, name, short, rank, points, form_10, xg_avg, ...}}
- MATCHES : [{id, home, away, date, kickoff, ..., odds: {1, X, 2, btts_yes, ...}}]
- H2H : {(tid_a, tid_b): [{date, score, winner}, ...]}
"""

from typing import Optional


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


def _short_id_from_team(team: dict) -> str:
    """Genere un id court interne (3 lettres) depuis un team SportAPI7."""
    name_code = team.get("nameCode") or team.get("shortName") or team.get("name", "")
    return name_code[:3].upper().replace(" ", "")


def _form_string_to_list(form_str: str) -> list:
    """Convertit 'WWLDW' en [1, 1, -1, 0, 1] (le plus recent en dernier)."""
    if not form_str:
        return [0] * 10
    mapping = {"W": 1, "D": 0, "L": -1}
    return [mapping.get(c, 0) for c in form_str[-10:]]


# ============ TEAM ============

def map_team_from_standings(row: dict, league_short: str) -> dict:
    """
    Mappe une entree de standings SportAPI7 vers une team Varion.

    Structure typique row :
    {
      "team": { "id", "name", "shortName", "nameCode", "teamColors": {...} },
      "position", "matches", "wins", "draws", "losses",
      "scoresFor", "scoresAgainst", "points", "promotion": {...}
    }
    """
    team = row.get("team", {}) or {}
    team_id_api = team.get("id")
    if not team_id_api:
        return None

    name = team.get("name", "Unknown")
    short = team.get("nameCode") or team.get("shortName") or name[:3]
    rank = _safe_int(row.get("position"))
    points = _safe_int(row.get("points"))
    played = _safe_int(row.get("matches", 1))
    wins = _safe_int(row.get("wins"))
    losses = _safe_int(row.get("losses"))
    goals_for = _safe_int(row.get("scoresFor"))
    goals_against = _safe_int(row.get("scoresAgainst"))

    # Couleur principale
    colors = team.get("teamColors", {}) or {}
    logo_color = colors.get("primary") or "#444"

    # Approximation des stats (les stats detaillees viendront de get_team_performance ou event stats)
    avg_goals_match = (goals_for + goals_against) / max(played, 1)
    btts_estimate = _btts_estimate(avg_goals_match)
    over_25_estimate = _over_25_estimate(avg_goals_match)

    return {
        "id": _short_id_from_team(team),
        "api_id": team_id_api,
        "name": name,
        "short": short,
        "league": league_short,
        "logo_color": logo_color,
        "logo_url": None,  # sportapi7 expose /team/{id}/image
        "rank": rank,
        "points": points,
        "played": played,
        "form_10": [0] * 10,  # a remplir via get_event_pregame_form
        "goals_for_avg": round(goals_for / max(played, 1), 2),
        "goals_against_avg": round(goals_against / max(played, 1), 2),
        "xg_avg": round(goals_for / max(played, 1) * 0.95, 2),  # approximation
        "xga_avg": round(goals_against / max(played, 1) * 0.95, 2),
        "shots_avg": 12.0,
        "shots_on_target_avg": 4.5,
        "possession_avg": 50.0,
        "corners_for_avg": 5.5,
        "corners_against_avg": 5.0,
        "yellow_avg": 2.0,
        "red_avg": 0.1,
        "clean_sheets_pct": 30.0,
        "btts_pct": btts_estimate,
        "over_25_pct": over_25_estimate,
        "over_35_pct": max(15, over_25_estimate - 25),
        "home": {
            "goals_for": round(goals_for / max(played, 1), 2),
            "goals_against": round(goals_against / max(played, 1), 2),
            "wins_pct": round(wins / max(played, 1) * 100, 1),
        },
        "away": {
            "goals_for": round(goals_for / max(played, 1), 2),
            "goals_against": round(goals_against / max(played, 1), 2),
            "wins_pct": round(wins / max(played, 1) * 100, 1),
        },
        "play_style": "balanced",
        "press_intensity": 0.75,
    }


def enrich_team_with_pregame_form(team: dict, pregame_form: dict, is_home: bool) -> dict:
    """Met a jour form_10 d'une equipe a partir de pregame-form du match."""
    if not pregame_form:
        return team
    side_data = pregame_form.get("homeTeam" if is_home else "awayTeam") or {}
    form_str = side_data.get("form") or ""
    if form_str:
        team["form_10"] = _form_string_to_list(form_str)
    # On peut aussi extraire avgRating, position, value
    avg_rating = side_data.get("avgRating")
    if avg_rating:
        team["avg_rating"] = _safe_float(avg_rating)
    return team


def enrich_team_with_event_stats(team: dict, event_stats: list) -> dict:
    """
    Met a jour les stats detaillees d'une equipe depuis event statistics.
    event_stats est une liste de {period, groups: [{statisticsItems: [...]}]}
    On agrege quelques metriques cles.
    """
    # Cette fonction est plus complexe car le format event_stats varie.
    # Pour le MVP, on laisse les stats par defaut et on enrichit plus tard.
    return team


# ============ MATCH ============

def map_match(event: dict, team_id_map: dict) -> Optional[dict]:
    """
    Mappe un event SportAPI7 vers un match Varion.

    team_id_map : { api_id: short_id_internal } pour faire le lien
    """
    event_id = event.get("id")
    if not event_id:
        return None

    home_team = event.get("homeTeam", {}) or {}
    away_team = event.get("awayTeam", {}) or {}
    home_api = home_team.get("id")
    away_api = away_team.get("id")

    if not home_api or not away_api:
        return None

    home_id = team_id_map.get(home_api)
    away_id = team_id_map.get(away_api)

    if not home_id or not away_id:
        return None  # equipe pas dans notre dataset

    # Date / heure depuis startTimestamp (Unix)
    ts = event.get("startTimestamp", 0)
    if ts:
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        date_only = dt.strftime("%Y-%m-%d")
        time_only = dt.strftime("%H:%M")
    else:
        date_only = ""
        time_only = ""

    # Tournoi
    tournament = event.get("tournament", {}) or {}
    round_info = event.get("roundInfo", {}) or {}
    round_num = round_info.get("round", "")
    competition = f"{tournament.get('name', '')} - J{round_num}" if round_num else tournament.get("name", "")

    # Stade
    venue = event.get("venue", {}).get("stadium", {}).get("name") if event.get("venue") else ""

    # Detection derby (basique)
    is_derby = _detect_derby(home_team.get("name", ""), away_team.get("name", ""))

    # Cotes par defaut (on les enrichira via get_event_odds)
    odds = _default_odds()

    return {
        "id": f"M_{event_id}",
        "api_id": event_id,
        "home": home_id,
        "away": away_id,
        "date": date_only,
        "kickoff": time_only,
        "venue": venue or "",
        "competition": competition,
        "referee": "TBD",  # sportapi7 a un endpoint dedie pour ca
        "ref_yellow_avg": 4.2,
        "ref_red_avg": 0.12,
        "stakes": "medium",
        "is_derby": is_derby,
        "odds": odds,
    }


def enrich_match_with_odds(match: dict, odds_data) -> dict:
    """
    Met a jour les cotes d'un match depuis l'endpoint /event/{id}/odds.

    odds_data peut etre une list de markets ou un dict {markets: [...]}.
    Structure d'un market :
      {marketName: "Full time", choices: [{name: "1"/"X"/"2", fractionalValue, odds: ...}]}
    """
    if not odds_data:
        return match

    if isinstance(odds_data, dict):
        markets = odds_data.get("markets") or []
    else:
        markets = odds_data

    for market in markets:
        market_name = (market.get("marketName") or "").lower()
        choices = market.get("choices") or []

        # 1X2
        if "full time" in market_name or "match winner" in market_name:
            for c in choices:
                cname = c.get("name", "")
                # Conversion fractional vers decimal si necessaire
                odds_val = _parse_odds(c)
                if cname == "1":
                    match["odds"]["1"] = odds_val
                elif cname == "X":
                    match["odds"]["X"] = odds_val
                elif cname == "2":
                    match["odds"]["2"] = odds_val

        # BTTS (Both teams to score)
        if "both teams to score" in market_name or "btts" in market_name:
            for c in choices:
                cname = (c.get("name") or "").lower()
                odds_val = _parse_odds(c)
                if "yes" in cname:
                    match["odds"]["btts_yes"] = odds_val
                elif "no" in cname:
                    match["odds"]["btts_no"] = odds_val

        # Over/Under 2.5
        if "total" in market_name and "2.5" in market_name:
            for c in choices:
                cname = (c.get("name") or "").lower()
                odds_val = _parse_odds(c)
                if "over" in cname:
                    match["odds"]["over_25"] = odds_val
                elif "under" in cname:
                    match["odds"]["under_25"] = odds_val

        # Over/Under 3.5
        if "total" in market_name and "3.5" in market_name:
            for c in choices:
                cname = (c.get("name") or "").lower()
                odds_val = _parse_odds(c)
                if "over" in cname:
                    match["odds"]["over_35"] = odds_val
                elif "under" in cname:
                    match["odds"]["under_35"] = odds_val

    return match


def _parse_odds(choice: dict) -> float:
    """Parse les odds (fractional ou decimal) en float decimal."""
    # Format possible : odds direct (decimal)
    if "odds" in choice:
        try:
            return float(choice["odds"])
        except (ValueError, TypeError):
            pass

    # Format fractionalValue (ex: "5/4" -> 2.25)
    fv = choice.get("fractionalValue")
    if fv and isinstance(fv, str) and "/" in fv:
        try:
            num, den = fv.split("/")
            return round(int(num) / int(den) + 1, 2)
        except (ValueError, ZeroDivisionError):
            pass

    return 2.0  # fallback


# ============ H2H ============

def expand_h2h_summary_to_fake_events(summary: dict, home_internal_id: str, away_internal_id: str) -> list:
    """
    Genere une fake liste d'events H2H a partir du summary pour rester compatible
    avec le moteur Varion qui attend une liste de matchs avec un champ 'winner'.

    Le moteur ne s'interesse qu'au COUNT de victoires, pas aux details, donc on
    peut generer des events synthetiques.

    Exemple : summary {home_wins: 4, away_wins: 6, draws: 0} pour Burnley vs Leeds
    -> 4 events fake "winner: BUR" + 6 events fake "winner: LEE" + 0 draws
    """
    if not summary or summary.get("total", 0) == 0:
        return []

    fake_events = []
    for _ in range(summary.get("home_wins", 0)):
        fake_events.append({
            "date": "",
            "score": "",
            "winner": home_internal_id,
            "synthetic": True,
        })
    for _ in range(summary.get("away_wins", 0)):
        fake_events.append({
            "date": "",
            "score": "",
            "winner": away_internal_id,
            "synthetic": True,
        })
    for _ in range(summary.get("draws", 0)):
        fake_events.append({
            "date": "",
            "score": "",
            "winner": None,
            "synthetic": True,
        })

    return fake_events


def map_h2h_events(events: list, home_team_api_id: int) -> list:
    """
    Convertit la liste detaillee /h2h/events en format Varion.

    events : liste retournee par /event/{id}/h2h/events
    Chaque event a la meme structure qu'un scheduled-event :
      { id, startTimestamp, homeTeam: {id, name}, awayTeam: {id, name},
        homeScore: {current, normaltime}, awayScore: {...},
        winnerCode (1=home, 2=away, 3=draw) }
    """
    if not events:
        return []

    # Trier par date decroissante (plus recent d'abord)
    sorted_events = sorted(events, key=lambda e: e.get("startTimestamp", 0), reverse=True)

    out = []
    for ev in sorted_events[:5]:  # 5 derniers
        ts = ev.get("startTimestamp", 0)
        if ts:
            from datetime import datetime, timezone
            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        else:
            date_str = ""

        home = ev.get("homeTeam", {}) or {}
        away = ev.get("awayTeam", {}) or {}
        h_score = (ev.get("homeScore") or {}).get("current")
        a_score = (ev.get("awayScore") or {}).get("current")
        winner_code = ev.get("winnerCode", 0)

        # winnerCode : 1=home, 2=away, 3=draw
        # On normalise par rapport a l'equipe "home_team_api_id" du match qu'on analyse
        if winner_code == 3:
            winner = "draw"
        elif winner_code == 1:
            winner = "home" if home.get("id") == home_team_api_id else "away"
        elif winner_code == 2:
            winner = "away" if home.get("id") == home_team_api_id else "home"
        else:
            winner = None

        if h_score is None or a_score is None:
            continue

        # Normaliser le score : toujours dans l'ordre (home_team_courant, away_team_courant)
        if home.get("id") == home_team_api_id:
            score_str = f"{h_score}-{a_score}"
        else:
            score_str = f"{a_score}-{h_score}"  # inversion car teams permutes

        out.append({
            "date": date_str,
            "score": score_str,
            "venue": "",
            "winner": winner,
            "tournament": (ev.get("tournament", {}) or {}).get("name", ""),
        })

    return out


def map_h2h_summary(summary: dict, home_team_api_id: int = None) -> dict:
    """
    Convertit la reponse stats agregees /h2h en stats H2H Varion.

    summary : { "teamDuel": {"homeWins": 4, "awayWins": 6, "draws": 0}, "managerDuel": ... }

    Note : "homeWins" / "awayWins" depend de quelle equipe est "home" sur l'event courant.
    Comme c'est l'event courant qui definit home/away, on peut directement utiliser ces valeurs.
    """
    if not summary:
        return {"home_wins": 0, "away_wins": 0, "draws": 0, "total": 0}

    team_duel = summary.get("teamDuel") or {}
    home_wins = team_duel.get("homeWins", 0) or 0
    away_wins = team_duel.get("awayWins", 0) or 0
    draws = team_duel.get("draws", 0) or 0

    return {
        "home_wins": home_wins,
        "away_wins": away_wins,
        "draws": draws,
        "total": home_wins + away_wins + draws,
    }


def map_h2h(h2h_data, home_team_api_id: int) -> list:
    """
    LEGACY : conserve pour compat. Detecte automatiquement le format.

    Si h2h_data est un dict avec 'teamDuel' -> stats agregees, on retourne []
    Si h2h_data est une list -> events, on retourne map_h2h_events
    """
    if isinstance(h2h_data, list):
        return map_h2h_events(h2h_data, home_team_api_id)
    if isinstance(h2h_data, dict):
        # Si c'est { events: [...] }, on extrait
        events = h2h_data.get("events")
        if events and isinstance(events, list):
            return map_h2h_events(events, home_team_api_id)
        # Sinon c'est un summary, pas d'events detailles
        return []
    return []


# ============ HELPERS ============

def _btts_estimate(avg_goals_match: float) -> float:
    if avg_goals_match < 2.0: return 38.0
    if avg_goals_match < 2.5: return 48.0
    if avg_goals_match < 3.0: return 55.0
    if avg_goals_match < 3.5: return 62.0
    return 68.0


def _over_25_estimate(avg_goals_match: float) -> float:
    if avg_goals_match < 2.0: return 35.0
    if avg_goals_match < 2.5: return 50.0
    if avg_goals_match < 3.0: return 60.0
    if avg_goals_match < 3.5: return 70.0
    return 78.0


def _default_odds() -> dict:
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
    derbies = [
        ("Manchester City", "Manchester United"),
        ("Liverpool", "Manchester United"),
        ("Arsenal", "Tottenham"),
        ("Chelsea", "Tottenham"),
        ("Real Madrid", "Barcelona"),
        ("Real Madrid", "Atletico"),
        ("AC Milan", "Inter"),
        ("Roma", "Lazio"),
        ("Bayern", "Dortmund"),
        ("PSG", "Marseille"),
        ("Paris", "Marseille"),
    ]
    if not home_name or not away_name:
        return False
    for a, b in derbies:
        if (a in home_name and b in away_name) or (b in home_name and a in away_name):
            return True
    return False
