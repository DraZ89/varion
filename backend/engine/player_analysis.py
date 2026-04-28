"""
Analyse individuelle des joueurs :
- Impact offensif
- Forme individuelle
- Probabilité de marquer / d'être décisif
- Surperformance / sous-performance vs xG
"""

from data.players import get_team_players, get_player, get_goalkeeper
from data.teams import get_team


def player_form_score(player: dict) -> float:
    """
    Score de forme sur les 5 derniers matchs (sur 10).
    Ignore les matchs où le joueur n'a pas joué (note 0).
    """
    active = [f for f in player["form_5"] if f > 0]
    if not active:
        return 5.0
    # Pondération : le match le plus récent compte plus
    weights = [1.0 + (i * 0.2) for i in range(len(active))]
    weighted = sum(f * w for f, w in zip(active, weights))
    return round(weighted / sum(weights), 2)


def offensive_impact(player: dict, team_total_goals: float) -> dict:
    """
    Implication offensive du joueur dans les buts de son équipe.
    """
    if player["pos"] == "GK":
        return {"goal_pct": 0.0, "assist_pct": 0.0, "ga_pct": 0.0}

    goals = player["goals"]
    assists = player["assists"]
    ga = goals + assists

    # team_total_goals = goals_for_avg * matches_played (approximation)
    if team_total_goals <= 0:
        return {"goal_pct": 0.0, "assist_pct": 0.0, "ga_pct": 0.0}

    return {
        "goal_pct": round((goals / team_total_goals) * 100, 1),
        "assist_pct": round((assists / team_total_goals) * 100, 1),
        "ga_pct": round((ga / team_total_goals) * 100, 1),
    }


def xg_overperformance(player: dict) -> dict:
    """
    Le joueur surperforme-t-il ou sous-performe-t-il vs son xG ?
    """
    goals = player["goals"]
    xg = player["xg"]
    diff = goals - xg

    status = "neutral"
    if diff >= 2.5:
        status = "overperforming"  # peut régresser - prudence
    elif diff <= -2.5:
        status = "underperforming"  # peut rebondir - opportunité

    return {
        "goals": goals,
        "xg": round(xg, 2),
        "diff": round(diff, 2),
        "status": status,
    }


def goal_probability(player: dict, opponent_def_score: float, is_home: bool) -> float:
    """
    Probabilité estimée que le joueur marque dans le prochain match.

    Modèle :
    - Base = goals/match historique
    - Ajusté par la forme récente
    - Ajusté par la défense adverse
    - Bonus domicile
    """
    if player["pos"] == "GK":
        return 0.0
    if player["minutes"] < 200:
        return 0.0

    # Buts par 90 minutes
    goals_per_90 = (player["goals"] / max(1, player["minutes"])) * 90

    # Probabilité Poisson approchée d'au moins un but
    # On pondère xG/90 pour fiabiliser
    xg_per_90 = (player["xg"] / max(1, player["minutes"])) * 90
    expected = (goals_per_90 * 0.4) + (xg_per_90 * 0.6)

    # Ajustement défense adverse (50 = moyenne ; > = bonne défense, baisse proba)
    def_factor = 1.0 + ((50 - opponent_def_score) / 100)
    expected *= def_factor

    # Ajustement forme
    form = player_form_score(player)
    form_factor = 0.7 + (form / 10) * 0.6  # entre 0.7 et 1.3
    expected *= form_factor

    # Bonus domicile
    if is_home:
        expected *= 1.10

    # Conversion en proba via 1 - e^(-λ) (Poisson : P(X≥1))
    import math
    proba = 1 - math.exp(-expected)
    return round(min(0.85, max(0.0, proba)) * 100, 1)


def assist_probability(player: dict, opponent_def_score: float, is_home: bool) -> float:
    """Probabilité d'être passeur décisif (modèle similaire avec xA)."""
    if player["pos"] == "GK":
        return 0.0
    if player["minutes"] < 200:
        return 0.0

    assists_per_90 = (player["assists"] / max(1, player["minutes"])) * 90
    xa_per_90 = (player["xa"] / max(1, player["minutes"])) * 90
    expected = (assists_per_90 * 0.4) + (xa_per_90 * 0.6)

    def_factor = 1.0 + ((50 - opponent_def_score) / 100)
    expected *= def_factor

    form = player_form_score(player)
    form_factor = 0.7 + (form / 10) * 0.6
    expected *= form_factor

    if is_home:
        expected *= 1.08

    import math
    proba = 1 - math.exp(-expected)
    return round(min(0.75, max(0.0, proba)) * 100, 1)


def analyze_team_players(team_id: str, opponent_def_score: float = 50.0, is_home: bool = True) -> list:
    """
    Analyse tous les joueurs d'une équipe et retourne les insights.
    """
    team = get_team(team_id)
    if not team:
        return []
    team_total_goals = team["goals_for_avg"] * team["played"]

    players = get_team_players(team_id)
    results = []

    for p in players:
        if p["pos"] == "GK":
            continue
        if p["minutes"] < 200:
            continue

        form = player_form_score(p)
        impact = offensive_impact(p, team_total_goals)
        xg_status = xg_overperformance(p)
        goal_prob = goal_probability(p, opponent_def_score, is_home)
        assist_prob = assist_probability(p, opponent_def_score, is_home)

        # Score global du joueur (impact * forme)
        impact_score = (form * 10) * 0.5 + impact["ga_pct"] * 0.5

        results.append({
            "id": p["id"],
            "name": p["name"],
            "pos": p["pos"],
            "starts": p["starts"],
            "minutes": p["minutes"],
            "goals": p["goals"],
            "assists": p["assists"],
            "xg": round(p["xg"], 2),
            "xa": round(p["xa"], 2),
            "shots": p["shots"],
            "shots_on_target": p["sot"],
            "yellow": p["yellow"],
            "red": p["red"],
            "is_key": p.get("is_key", False),
            "form_score": form,
            "ga_involvement_pct": impact["ga_pct"],
            "goal_involvement_pct": impact["goal_pct"],
            "assist_involvement_pct": impact["assist_pct"],
            "xg_status": xg_status,
            "goal_probability": goal_prob,
            "assist_probability": assist_prob,
            "player_score": round(impact_score, 1),
        })

    # Tri : meilleur impact d'abord
    results.sort(key=lambda x: -x["player_score"])
    return results


def analyze_goalkeeper(team_id: str) -> dict:
    """
    Analyse spécifique du gardien titulaire :
    probabilité de clean sheet basée sur ses arrêts et xGOT.
    """
    gk = get_goalkeeper(team_id)
    team = get_team(team_id)
    if not gk or not team:
        return {}

    form = player_form_score(gk)

    # Différentiel xGOT vs buts encaissés (par match) : indicateur clé
    matches_played = max(1, gk["starts"])
    cs_rate = gk["clean_sheets"] / matches_played
    xgot_per_match = gk.get("xgot_faced", 1.4)

    # Goals encaissés moyens par match du gardien
    goals_conceded_per_match = team["goals_against_avg"]
    # Performance : si xGOT > buts encaissés alors le gardien sauve mieux que prévu
    save_overperformance = round(xgot_per_match - goals_conceded_per_match, 2)

    return {
        "id": gk["id"],
        "name": gk["name"],
        "starts": gk["starts"],
        "minutes": gk["minutes"],
        "saves_per_game": gk.get("saves_per_game", 0),
        "xgot_faced": round(xgot_per_match, 2),
        "clean_sheets": gk["clean_sheets"],
        "clean_sheet_rate": round(cs_rate * 100, 1),
        "save_overperformance": save_overperformance,
        "form_score": form,
    }


def detect_key_players_to_watch(team_id: str, opponent_def_score: float, is_home: bool, top_n: int = 4) -> list:
    """
    Sélectionne les N joueurs les plus susceptibles d'influencer le match.
    Pondère : forme + impact offensif + proba de marquer.
    """
    players = analyze_team_players(team_id, opponent_def_score, is_home)

    def watch_score(p):
        return (
            p["form_score"] * 5 +
            p["ga_involvement_pct"] * 1.5 +
            p["goal_probability"] * 0.5 +
            p["assist_probability"] * 0.3 +
            (15 if p["is_key"] else 0)
        )

    sorted_players = sorted(players, key=lambda x: -watch_score(x))
    return sorted_players[:top_n]
