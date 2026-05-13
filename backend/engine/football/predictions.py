"""
Moteur de prédiction multi-marchés.

Utilise principalement le modèle de Poisson bivarié pour les buts,
puis dérive les probabilités des marchés (1X2, BTTS, Over/Under, CS).
Les corners et cartons sont modélisés séparément.
"""

import math
from data.teams import get_team
from data.matches import get_h2h
from engine.team_analysis import calculate_team_overall


# ============== MOYENNES DE LA LIGUE (référence) ==============
LEAGUE_AVG_GOALS_HOME = 1.55
LEAGUE_AVG_GOALS_AWAY = 1.20
LEAGUE_AVG_CORNERS = 10.5
LEAGUE_AVG_CARDS = 4.2


# ============== POISSON ==============

def poisson_prob(lam: float, k: int) -> float:
    """P(X = k) sous Poisson(lam)"""
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)


def expected_goals(home_id: str, away_id: str) -> tuple:
    """
    Calcule les buts attendus (lambda Poisson) pour chaque équipe.
    Méthode : modèle de Dixon-Coles simplifié + xG.
    """
    home = get_team(home_id)
    away = get_team(away_id)

    # Force d'attaque/défense relative à la ligue
    home_attack = home["xg_avg"] / LEAGUE_AVG_GOALS_HOME
    away_defense = away["xga_avg"] / LEAGUE_AVG_GOALS_HOME

    away_attack = away["xg_avg"] / LEAGUE_AVG_GOALS_AWAY
    home_defense = home["xga_avg"] / LEAGUE_AVG_GOALS_AWAY

    # Lambda = base ligue × force attaque × faiblesse défense
    lambda_home = LEAGUE_AVG_GOALS_HOME * home_attack * away_defense
    lambda_away = LEAGUE_AVG_GOALS_AWAY * away_attack * home_defense

    # Bonus domicile via le ratio buts maison/déplacement
    home_factor = home["home"]["goals_for"] / max(0.1, home["goals_for_avg"])
    away_factor = away["away"]["goals_for"] / max(0.1, away["goals_for_avg"])
    lambda_home *= home_factor
    lambda_away *= away_factor

    # Ajustement par la forme récente (5 derniers matchs)
    recent_home_form = sum(home["form_10"][-5:]) / 5  # entre -1 et 1
    recent_away_form = sum(away["form_10"][-5:]) / 5
    lambda_home *= (1 + recent_home_form * 0.10)
    lambda_away *= (1 + recent_away_form * 0.10)

    # Ajustement H2H (si historique récent dominant)
    h2h = get_h2h(home_id, away_id)
    if h2h:
        home_wins = sum(1 for m in h2h if m.get("winner") == home_id)
        away_wins = sum(1 for m in h2h if m.get("winner") == away_id)
        if home_wins >= 3:
            lambda_home *= 1.07
            lambda_away *= 0.95
        elif away_wins >= 3:
            lambda_away *= 1.07
            lambda_home *= 0.95

    return round(max(0.1, lambda_home), 3), round(max(0.1, lambda_away), 3)


# ============== 1X2 ==============

def predict_1x2(home_id: str, away_id: str) -> dict:
    """
    Probabilités Victoire / Nul / Défaite via matrice de score Poisson.
    """
    lam_h, lam_a = expected_goals(home_id, away_id)
    max_goals = 7

    p_home = p_draw = p_away = 0.0
    matrix = []

    for h in range(max_goals):
        row = []
        for a in range(max_goals):
            p = poisson_prob(lam_h, h) * poisson_prob(lam_a, a)
            row.append(p)
            if h > a:
                p_home += p
            elif h == a:
                p_draw += p
            else:
                p_away += p
        matrix.append(row)

    # Normalisation (les queues > max_goals)
    total = p_home + p_draw + p_away
    p_home /= total
    p_draw /= total
    p_away /= total

    # Score le plus probable
    best_h, best_a, best_p = 0, 0, 0
    for h in range(max_goals):
        for a in range(max_goals):
            if matrix[h][a] > best_p:
                best_p = matrix[h][a]
                best_h, best_a = h, a

    return {
        "lambda_home": lam_h,
        "lambda_away": lam_a,
        "prob_home_win": round(p_home * 100, 2),
        "prob_draw": round(p_draw * 100, 2),
        "prob_away_win": round(p_away * 100, 2),
        "most_likely_score": f"{best_h}-{best_a}",
        "most_likely_score_prob": round(best_p * 100, 2),
    }


# ============== BTTS ==============

def predict_btts(home_id: str, away_id: str) -> dict:
    """Both Teams To Score : P(les deux marquent au moins 1)."""
    lam_h, lam_a = expected_goals(home_id, away_id)
    p_home_no_goal = poisson_prob(lam_h, 0)
    p_away_no_goal = poisson_prob(lam_a, 0)

    # P(BTTS) = 1 - P(home=0) - P(away=0) + P(both=0)
    p_btts = 1 - p_home_no_goal - p_away_no_goal + (p_home_no_goal * p_away_no_goal)

    # Calibration via les % BTTS historiques des deux équipes
    home = get_team(home_id)
    away = get_team(away_id)
    historical = (home["btts_pct"] + away["btts_pct"]) / 200  # moyenne en proba
    # Mix 70% modèle / 30% historique
    final = p_btts * 0.7 + historical * 0.3

    return {
        "prob_yes": round(final * 100, 2),
        "prob_no": round((1 - final) * 100, 2),
    }


# ============== OVER/UNDER ==============

def predict_over_under(home_id: str, away_id: str, line: float = 2.5) -> dict:
    """P(buts > line) via Poisson."""
    lam_h, lam_a = expected_goals(home_id, away_id)
    total_lambda = lam_h + lam_a

    p_under = 0.0
    threshold = int(line)  # 2.5 -> 2 (under = 0,1,2 buts)
    for k in range(threshold + 1):
        p_under += poisson_prob(total_lambda, k)

    p_over = 1 - p_under

    return {
        "line": line,
        "expected_total": round(total_lambda, 2),
        "prob_over": round(p_over * 100, 2),
        "prob_under": round(p_under * 100, 2),
    }


# ============== CLEAN SHEET ==============

def predict_clean_sheet(home_id: str, away_id: str) -> dict:
    """Probabilité de clean sheet pour chaque équipe."""
    lam_h, lam_a = expected_goals(home_id, away_id)

    # CS pour le domicile = away ne marque pas
    cs_home = poisson_prob(lam_a, 0)
    cs_away = poisson_prob(lam_h, 0)

    # Calibration via le % CS historique du gardien (déjà dans team)
    home = get_team(home_id)
    away = get_team(away_id)
    cs_home_calib = (cs_home * 0.65) + ((home["clean_sheets_pct"] / 100) * 0.35)
    cs_away_calib = (cs_away * 0.65) + ((away["clean_sheets_pct"] / 100) * 0.35)

    return {
        "prob_cs_home": round(cs_home_calib * 100, 2),
        "prob_cs_away": round(cs_away_calib * 100, 2),
    }


# ============== CORNERS ==============

def predict_corners(home_id: str, away_id: str, line: float = 9.5) -> dict:
    """
    Modèle simple : moyennes pour/contre + style de jeu.
    """
    home = get_team(home_id)
    away = get_team(away_id)

    # Moyennes attendues : attaque maison * défense corner adverse
    expected_home = (home["corners_for_avg"] + away["corners_against_avg"]) / 2
    expected_away = (away["corners_for_avg"] + home["corners_against_avg"]) / 2

    # Bonus style de jeu (équipes possession + ailes => + corners)
    style_bonus = {
        "possession_attack": 1.10,
        "high_press_attack": 1.08,
        "balanced_attack": 1.03,
        "balanced": 1.00,
        "counter_attack": 0.95,
        "possession_build": 1.05,
    }
    expected_home *= style_bonus.get(home["play_style"], 1.0)
    expected_away *= style_bonus.get(away["play_style"], 1.0)

    # Bonus domicile
    expected_home *= 1.08

    expected_total = expected_home + expected_away

    # Approximation Poisson sur le total
    p_under = sum(poisson_prob(expected_total, k) for k in range(int(line) + 1))
    p_over = 1 - p_under

    return {
        "line": line,
        "expected_home": round(expected_home, 2),
        "expected_away": round(expected_away, 2),
        "expected_total": round(expected_total, 2),
        "prob_over": round(p_over * 100, 2),
        "prob_under": round(p_under * 100, 2),
    }


# ============== CARTONS ==============

def predict_cards(home_id: str, away_id: str, match_context: dict, line: float = 4.5) -> dict:
    """
    Cartons jaunes attendus + probabilité over/under.
    Prend en compte arbitre + contexte (derby, enjeu).
    """
    home = get_team(home_id)
    away = get_team(away_id)

    base_home = home["yellow_avg"]
    base_away = away["yellow_avg"]
    base_total = base_home + base_away

    # Influence arbitre
    ref_yellow = match_context.get("ref_yellow_avg", LEAGUE_AVG_CARDS)
    league_avg = LEAGUE_AVG_CARDS
    ref_factor = ref_yellow / league_avg
    expected_total = base_total * ref_factor

    # Bonus derby
    if match_context.get("is_derby"):
        expected_total *= 1.18

    # Bonus enjeu fort
    if match_context.get("stakes") == "high":
        expected_total *= 1.10

    # Bonus pressing intensité (deux équipes qui pressent fort = + cartons)
    avg_press = (home["press_intensity"] + away["press_intensity"]) / 2
    if avg_press > 0.85:
        expected_total *= 1.08

    p_under = sum(poisson_prob(expected_total, k) for k in range(int(line) + 1))
    p_over = 1 - p_under

    return {
        "line": line,
        "expected_total": round(expected_total, 2),
        "ref_yellow_avg": ref_yellow,
        "is_derby": match_context.get("is_derby", False),
        "prob_over": round(p_over * 100, 2),
        "prob_under": round(p_under * 100, 2),
    }


# ============== INTENSITÉ DU MATCH ==============

def calculate_match_intensity(home_id: str, away_id: str, match_context: dict) -> dict:
    """Score d'intensité 0-100 (cartons attendus + enjeu)."""
    home = get_team(home_id)
    away = get_team(away_id)

    base = (home["yellow_avg"] + away["yellow_avg"]) / 8 * 100  # ~50 pour 4 cartons
    if match_context.get("is_derby"):
        base += 15
    if match_context.get("stakes") == "high":
        base += 10
    avg_press = (home["press_intensity"] + away["press_intensity"]) / 2
    base += (avg_press - 0.7) * 50

    return round(max(0, min(100, base)), 1)


# ============== AGRÉGATION ==============

def predict_match(home_id: str, away_id: str, match_context: dict = None) -> dict:
    """
    Prédiction complète multi-marchés pour un match.
    """
    match_context = match_context or {}

    result_1x2 = predict_1x2(home_id, away_id)
    btts = predict_btts(home_id, away_id)
    ou_25 = predict_over_under(home_id, away_id, 2.5)
    ou_35 = predict_over_under(home_id, away_id, 3.5)
    cs = predict_clean_sheet(home_id, away_id)
    corners = predict_corners(home_id, away_id, 9.5)
    cards = predict_cards(home_id, away_id, match_context, 4.5)
    intensity = calculate_match_intensity(home_id, away_id, match_context)

    return {
        "result": result_1x2,
        "btts": btts,
        "over_under_25": ou_25,
        "over_under_35": ou_35,
        "clean_sheet": cs,
        "corners": corners,
        "cards": cards,
        "intensity_score": intensity,
    }
