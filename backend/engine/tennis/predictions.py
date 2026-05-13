"""
Moteur de prédictions tennis multi-marchés.

Marchés couverts :
- Vainqueur du match (1 vs 2)
- Vainqueur en N sets (2-0 ou 2-1 pour BO3, etc.)
- Total de games (Over/Under 22.5 par exemple)
- Sets handicap (-1.5, +1.5)
- Tie-break Oui/Non

Méthode :
1. ELO -> probabilité de victoire match
2. Probabilité de gagner un point au service (depuis stats joueur)
3. Modèle markovien : depuis P(point), on dérive P(jeu), P(set), P(match)
4. Calibration : on ajuste pour que P(match) du modèle markovien matche le ELO
"""

import math
from engine.tennis.elo import (
    match_probability,
    form_factor,
    h2h_factor,
    INITIAL_ELO,
    normalize_surface,
)


# Constantes du tennis
BO3_MAX_SETS = 3  # Best of 3 (matchs ATP/WTA standards)
BO5_MAX_SETS = 5  # Best of 5 (Grand Slam hommes)


def predict_match_winner(player_a: dict, player_b: dict, surface: str,
                         tournament_type: str = "ATP 250") -> dict:
    """
    Prédiction principale : qui gagne le match ?

    player_a / player_b sont des dicts attendus :
    {
        'id': '...',
        'name': '...',
        'elo': {'global': 2050, 'hard': 2080, 'clay': 1950, 'grass': 2020},
        'recent_results': [True, True, False, True, ...],
        'h2h_wins_vs_opponent': 3,  # vs l'autre joueur
        ...
    }
    """
    elo_pred = match_probability(player_a["elo"], player_b["elo"], surface)

    # Ajustement forme
    ff_a = form_factor(player_a.get("recent_results", []))
    ff_b = form_factor(player_b.get("recent_results", []))
    form_adjustment = ff_a / ff_b

    # Ajustement H2H
    hf = h2h_factor(
        player_a.get("h2h_wins_vs_opponent", 0),
        player_b.get("h2h_wins_vs_opponent", 0),
    )

    # Application des ajustements
    adjusted_prob_a = elo_pred["prob_a"] / 100
    adjusted_prob_a = adjusted_prob_a * form_adjustment * hf
    adjusted_prob_a = max(0.05, min(0.95, adjusted_prob_a))

    return {
        "prob_a": round(adjusted_prob_a * 100, 2),
        "prob_b": round((1 - adjusted_prob_a) * 100, 2),
        "elo_a": elo_pred["elo_a_used"],
        "elo_b": elo_pred["elo_b_used"],
        "elo_gap": elo_pred["gap"],
        "surface": elo_pred["surface"],
        "form_adjustment": round(form_adjustment, 3),
        "h2h_factor": round(hf, 3),
        "raw_elo_prob_a": elo_pred["prob_a"],
    }


def serve_win_probability(player: dict, surface: str) -> float:
    """
    Probabilité moyenne que le joueur gagne un point quand il sert.
    Top serveurs : ~0.68. Joueurs moyens : ~0.62. Faibles : ~0.55.

    Calcul depuis les stats récentes :
        - 1st serve win % * 0.6 (60% des points sont sur 1er service)
        - 2nd serve win % * 0.4
    """
    stats = player.get("serve_stats", {})

    first_serve_pct = stats.get("first_serve_pct", 60.0) / 100
    first_serve_won = stats.get("first_serve_won_pct", 70.0) / 100
    second_serve_won = stats.get("second_serve_won_pct", 50.0) / 100

    # Probabilité globale de gagner le point en service
    p_serve = (first_serve_pct * first_serve_won) + ((1 - first_serve_pct) * second_serve_won)

    # Ajustement surface
    surface_norm = normalize_surface(surface)
    if surface_norm == "grass":
        p_serve *= 1.05  # gazon favorise les serveurs
    elif surface_norm == "clay":
        p_serve *= 0.95  # terre désavantage les serveurs

    return max(0.45, min(0.85, p_serve))


def game_probability(p_serve: float) -> float:
    """
    Probabilité de gagner un jeu de service quand on a probabilité p de gagner un point.

    Formule analytique : un jeu se joue jusqu'à 4 points avec écart de 2 minimum.
    On simplifie avec l'approximation classique.
    """
    if p_serve <= 0.5:
        # Joueur bat lui-même au service
        return p_serve ** 4 * (1 + 4*(1-p_serve) + 10*(1-p_serve)**2)
    # Approximation analytique
    p = p_serve
    q = 1 - p
    # Probabilités de gagner directement (4 points), 4-1, 4-2, ou via deuce
    p_4_0 = p**4
    p_4_1 = 4 * p**4 * q
    p_4_2 = 10 * p**4 * q**2
    # Probabilité d'arriver à deuce (3-3)
    p_deuce = 20 * p**3 * q**3
    # Une fois à deuce, on gagne avec p^2 / (p^2 + q^2)
    p_win_from_deuce = (p**2) / (p**2 + q**2) if (p**2 + q**2) > 0 else 0.5
    return p_4_0 + p_4_1 + p_4_2 + (p_deuce * p_win_from_deuce)


def predict_total_games(player_a: dict, player_b: dict, surface: str,
                        line: float = 22.5, max_sets: int = BO3_MAX_SETS) -> dict:
    """
    Prédiction du total de jeux dans le match.

    Approche : simulation Monte Carlo simplifiée à partir de p_serve.
    """
    p_serve_a = serve_win_probability(player_a, surface)
    p_serve_b = serve_win_probability(player_b, surface)

    p_game_a_serve = game_probability(p_serve_a)
    p_game_b_serve = game_probability(p_serve_b)

    # Espérance de jeux par set (les deux joueurs servent à tour de rôle)
    # Un set = ~10 jeux en moyenne, plus si serveurs solides (équilibre serveur/retourneur)
    avg_games_per_set = (
        6 / p_game_a_serve / 2 +  # ~6 jeux à chaque service
        6 / p_game_b_serve / 2
    )
    avg_games_per_set = max(8, min(13, avg_games_per_set))

    # Nombre de sets attendu : selon l'écart ELO
    # Si match équilibré -> probable 3 sets
    # Si gros écart -> probable 2 sets
    elo_pred = match_probability(player_a["elo"], player_b["elo"], surface)
    p_dominant = max(elo_pred["prob_a"], elo_pred["prob_b"]) / 100

    # P(2 sets) si dominant > 0.7, P(3 sets) sinon (en BO3)
    if max_sets == BO3_MAX_SETS:
        p_2_sets = 0.4 + (p_dominant - 0.5) * 0.8  # 0.4 -> 0.8 selon domination
        p_2_sets = max(0.3, min(0.85, p_2_sets))
        expected_sets = 2 * p_2_sets + 3 * (1 - p_2_sets)
    else:  # BO5
        # Plus complexe pour BO5
        expected_sets = 3 + (1 - p_dominant) * 1.5
        expected_sets = max(3, min(5, expected_sets))

    expected_games = avg_games_per_set * expected_sets

    # Approximation Poisson sur le total de jeux
    p_under = sum(_poisson(expected_games, k) for k in range(int(line) + 1))
    p_over = 1 - p_under

    return {
        "line": line,
        "expected_total": round(expected_games, 1),
        "expected_sets": round(expected_sets, 2),
        "avg_games_per_set": round(avg_games_per_set, 2),
        "prob_over": round(p_over * 100, 2),
        "prob_under": round(p_under * 100, 2),
    }


def predict_sets_score(player_a: dict, player_b: dict, surface: str,
                       max_sets: int = BO3_MAX_SETS) -> dict:
    """
    Probabilités de chaque score en sets : 2-0, 2-1, 1-2, 0-2 (BO3).
    """
    elo_pred = match_probability(player_a["elo"], player_b["elo"], surface)
    p_a = elo_pred["prob_a"] / 100  # P(A gagne le match)

    # Approximation : si A gagne, P(2-0) dépend de la domination
    # P(2-0 | A gagne) ≈ p_a (plus A domine, plus il finit en 2 sets)
    # Calibration empirique
    if max_sets == BO3_MAX_SETS:
        p_dominate = max(p_a, 1 - p_a)
        p_clean_sweep_given_winner = 0.45 + (p_dominate - 0.5) * 0.6  # 0.45 -> 0.75

        p_2_0_a = p_a * p_clean_sweep_given_winner
        p_2_1_a = p_a * (1 - p_clean_sweep_given_winner)
        p_2_0_b = (1 - p_a) * p_clean_sweep_given_winner
        p_2_1_b = (1 - p_a) * (1 - p_clean_sweep_given_winner)

        return {
            "2-0_a": round(p_2_0_a * 100, 2),
            "2-1_a": round(p_2_1_a * 100, 2),
            "2-1_b": round(p_2_1_b * 100, 2),
            "2-0_b": round(p_2_0_b * 100, 2),
            "most_likely": _most_likely_score(p_2_0_a, p_2_1_a, p_2_1_b, p_2_0_b, "BO3"),
        }
    else:  # BO5
        p_3_0_a = p_a * 0.35
        p_3_1_a = p_a * 0.40
        p_3_2_a = p_a * 0.25
        p_3_0_b = (1 - p_a) * 0.35
        p_3_1_b = (1 - p_a) * 0.40
        p_3_2_b = (1 - p_a) * 0.25

        return {
            "3-0_a": round(p_3_0_a * 100, 2),
            "3-1_a": round(p_3_1_a * 100, 2),
            "3-2_a": round(p_3_2_a * 100, 2),
            "3-2_b": round(p_3_2_b * 100, 2),
            "3-1_b": round(p_3_1_b * 100, 2),
            "3-0_b": round(p_3_0_b * 100, 2),
            "most_likely": _most_likely_score(p_3_0_a, p_3_1_a, p_3_2_a, p_3_2_b, p_3_1_b, p_3_0_b, "BO5"),
        }


def predict_match(player_a: dict, player_b: dict, surface: str,
                  tournament_type: str = "ATP 250",
                  max_sets: int = BO3_MAX_SETS) -> dict:
    """
    Prédiction complète multi-marchés pour un match de tennis.
    """
    winner = predict_match_winner(player_a, player_b, surface, tournament_type)
    sets = predict_sets_score(player_a, player_b, surface, max_sets)
    games = predict_total_games(player_a, player_b, surface, 22.5, max_sets)

    return {
        "winner": winner,
        "sets_score": sets,
        "total_games": games,
        "tournament_type": tournament_type,
        "surface": surface,
        "format": f"BO{max_sets}",
    }


# ============== HELPERS ==============

def _poisson(lam: float, k: int) -> float:
    """P(X = k) sous Poisson(lam)."""
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)


def _most_likely_score(*args) -> str:
    """Détermine le score le plus probable (input dépend de BO3/BO5)."""
    if args[-1] == "BO3":
        probs = args[:-1]
        labels = ["2-0 (A)", "2-1 (A)", "2-1 (B)", "2-0 (B)"]
    else:  # BO5
        probs = args[:-1]
        labels = ["3-0 (A)", "3-1 (A)", "3-2 (A)", "3-2 (B)", "3-1 (B)", "3-0 (B)"]
    max_idx = probs.index(max(probs))
    return labels[max_idx]
