"""
Calcul des scores d'équipe : attaque, défense, forme, qualité globale.
Tous les scores sont normalisés sur 100.
"""

from data.teams import get_team
from data.players import get_team_players, get_goalkeeper, get_lineup_starters


def calculate_form_score(form_list: list) -> float:
    """
    Score de forme pondéré : les matchs récents comptent plus.
    Retourne 0-100.
    """
    if not form_list:
        return 50.0
    # Pondération exponentielle : le match le plus récent (dernier index) pèse plus
    weights = [1.0 + (i * 0.15) for i in range(len(form_list))]
    weighted_sum = sum(r * w for r, w in zip(form_list, weights))
    weight_total = sum(weights)
    avg = weighted_sum / weight_total  # entre -1 et 1

    # Mapping vers 0-100 (avec une légère courbe pour amplifier les extrêmes)
    score = 50 + (avg * 45)
    return round(max(0, min(100, score)), 1)


def calculate_attack_score(team: dict) -> float:
    """
    Score offensif basé sur :
    - Buts marqués / xG
    - Tirs cadrés
    - % over 2.5
    """
    goals = team["goals_for_avg"]
    xg = team["xg_avg"]
    sot = team["shots_on_target_avg"]
    over_25 = team["over_25_pct"]

    # Normalisation (référence PL : 1.4 buts/match en moyenne)
    goals_norm = min(100, (goals / 2.8) * 100)
    xg_norm = min(100, (xg / 2.5) * 100)
    sot_norm = min(100, (sot / 7.0) * 100)
    over_norm = over_25  # déjà en %

    # Pondération
    score = (goals_norm * 0.30) + (xg_norm * 0.30) + (sot_norm * 0.20) + (over_norm * 0.20)
    return round(score, 1)


def calculate_defense_score(team: dict) -> float:
    """
    Score défensif basé sur :
    - Buts encaissés (inverse)
    - xGA (inverse)
    - Clean sheets %
    """
    goals_against = team["goals_against_avg"]
    xga = team["xga_avg"]
    cs_pct = team["clean_sheets_pct"]

    # Inversion : moins on encaisse, plus le score est haut
    ga_norm = max(0, 100 - (goals_against / 2.0) * 100)
    xga_norm = max(0, 100 - (xga / 2.0) * 100)
    cs_norm = cs_pct * 2  # 50% CS = 100 score

    score = (ga_norm * 0.35) + (xga_norm * 0.35) + (min(100, cs_norm) * 0.30)
    return round(score, 1)


def calculate_squad_quality(team_id: str) -> float:
    """
    Qualité globale du onze type (XI le plus utilisé).
    Basée sur la forme moyenne et l'implication offensive des titulaires.
    """
    starters = get_lineup_starters(team_id, top_n=11)
    if not starters:
        return 50.0

    # Forme moyenne des titulaires (sur leurs 5 derniers matchs)
    form_avgs = []
    for p in starters:
        active_forms = [f for f in p["form_5"] if f > 0]
        if active_forms:
            form_avgs.append(sum(active_forms) / len(active_forms))

    if not form_avgs:
        return 50.0

    avg_form = sum(form_avgs) / len(form_avgs)  # sur 10
    return round(avg_form * 10, 1)  # vers 100


def calculate_lineup_stability(team_id: str) -> float:
    """
    Stabilité de la composition : % de matchs où le XI type est présent.
    Approximation basée sur le ratio starts/30 du XI le plus utilisé.
    """
    starters = get_lineup_starters(team_id, top_n=11)
    if not starters:
        return 50.0

    avg_starts = sum(p["starts"] for p in starters) / len(starters)
    stability = (avg_starts / 30) * 100
    return round(min(100, stability), 1)


def calculate_home_away_factor(team: dict, is_home: bool) -> float:
    """Facteur multiplicatif domicile/extérieur pour l'attaque."""
    if is_home:
        # Ratio buts marqués à domicile vs moyenne
        return team["home"]["goals_for"] / max(0.1, team["goals_for_avg"])
    return team["away"]["goals_for"] / max(0.1, team["goals_for_avg"])


def calculate_team_overall(team_id: str, is_home: bool = True) -> dict:
    """
    Synthèse complète des scores d'une équipe.
    """
    team = get_team(team_id)
    if not team:
        return {}

    form = calculate_form_score(team["form_10"])
    attack = calculate_attack_score(team)
    defense = calculate_defense_score(team)
    squad = calculate_squad_quality(team_id)
    stability = calculate_lineup_stability(team_id)
    venue_factor = calculate_home_away_factor(team, is_home)

    # Score global pondéré
    overall = (form * 0.25) + (attack * 0.25) + (defense * 0.25) + (squad * 0.15) + (stability * 0.10)

    return {
        "team_id": team_id,
        "team_name": team["name"],
        "form_score": form,
        "attack_score": attack,
        "defense_score": defense,
        "squad_quality": squad,
        "lineup_stability": stability,
        "venue_factor": round(venue_factor, 2),
        "overall_score": round(overall, 1),
        # Données brutes utiles pour les marchés
        "goals_for_avg": team["goals_for_avg"],
        "goals_against_avg": team["goals_against_avg"],
        "xg_avg": team["xg_avg"],
        "xga_avg": team["xga_avg"],
        "corners_for_avg": team["corners_for_avg"],
        "corners_against_avg": team["corners_against_avg"],
        "yellow_avg": team["yellow_avg"],
        "btts_pct": team["btts_pct"],
        "over_25_pct": team["over_25_pct"],
        "clean_sheets_pct": team["clean_sheets_pct"],
        "play_style": team["play_style"],
        "press_intensity": team["press_intensity"],
    }
