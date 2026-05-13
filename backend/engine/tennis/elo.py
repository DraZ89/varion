"""
Système ELO pour tennis avec ajustement par surface.

Inspiré de :
- Tennis Abstract (Jeff Sackmann) - https://github.com/JeffSackmann/tennis_atp
- FiveThirtyEight tennis ratings

Principe :
- Chaque joueur a un ELO global (toutes surfaces)
- Et un ELO par surface (gazon, terre, dur)
- Pour prédire un match : 70% surface + 30% global

ELO de départ : 1500 (joueur lambda)
Top 10 mondial : ~2100-2300
N°1 mondial actuel : ~2400+

Formule de probabilité :
    P(A bat B) = 1 / (1 + 10^((ELO_B - ELO_A) / 400))

Mise à jour après match :
    K-factor = 32 (par défaut, ajusté par tournoi)
    nouveau_ELO = ancien_ELO + K * (resultat_reel - resultat_attendu)
"""

from typing import Optional


# Constantes
INITIAL_ELO = 1500
DEFAULT_K = 32

# K-factor selon importance du tournoi (plus haut = plus volatile)
K_BY_TOURNAMENT = {
    "Grand Slam": 50,
    "Masters 1000": 40,
    "ATP 500": 32,
    "ATP 250": 28,
    "WTA 1000": 40,
    "WTA 500": 32,
    "WTA 250": 28,
    "ITF": 20,
    "Challenger": 24,
    "Davis Cup": 30,
    "Other": 28,
}

# Pondération surface vs global pour les prédictions
SURFACE_WEIGHT = 0.70
GLOBAL_WEIGHT = 0.30

# Surfaces supportées
SURFACES = ["hard", "clay", "grass"]


def normalize_surface(surface_raw: str) -> str:
    """Normalise les noms de surface variés vers hard/clay/grass."""
    if not surface_raw:
        return "hard"
    s = surface_raw.lower()
    if "clay" in s or "terre" in s:
        return "clay"
    if "grass" in s or "gazon" in s:
        return "grass"
    if "carpet" in s:
        return "hard"  # carpet est rare, traité comme hard
    return "hard"  # défaut


def expected_probability(elo_a: float, elo_b: float) -> float:
    """
    Probabilité que A batte B (formule ELO standard).
    Retourne entre 0 et 1.
    """
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))


def match_probability(player_a_elo: dict, player_b_elo: dict, surface: str) -> dict:
    """
    Calcule la probabilité de victoire du joueur A vs B sur une surface donnée.

    player_a_elo / player_b_elo : dicts avec clés 'global', 'hard', 'clay', 'grass'
    surface : 'hard', 'clay' ou 'grass'

    Retourne :
    {
        'prob_a': 0.65,
        'prob_b': 0.35,
        'elo_a_used': 2050,  # ELO combiné utilisé
        'elo_b_used': 1980,
        'gap': 70,
    }
    """
    surface_norm = normalize_surface(surface)

    elo_a_global = player_a_elo.get("global", INITIAL_ELO)
    elo_b_global = player_b_elo.get("global", INITIAL_ELO)
    elo_a_surface = player_a_elo.get(surface_norm, elo_a_global)
    elo_b_surface = player_b_elo.get(surface_norm, elo_b_global)

    # ELO combiné (70% surface, 30% global)
    elo_a_combined = (elo_a_surface * SURFACE_WEIGHT) + (elo_a_global * GLOBAL_WEIGHT)
    elo_b_combined = (elo_b_surface * SURFACE_WEIGHT) + (elo_b_global * GLOBAL_WEIGHT)

    prob_a = expected_probability(elo_a_combined, elo_b_combined)

    return {
        "prob_a": round(prob_a * 100, 2),
        "prob_b": round((1 - prob_a) * 100, 2),
        "elo_a_used": round(elo_a_combined, 0),
        "elo_b_used": round(elo_b_combined, 0),
        "elo_a_global": round(elo_a_global, 0),
        "elo_b_global": round(elo_b_global, 0),
        "elo_a_surface": round(elo_a_surface, 0),
        "elo_b_surface": round(elo_b_surface, 0),
        "gap": round(elo_a_combined - elo_b_combined, 0),
        "surface": surface_norm,
    }


def update_elo(player_elo: float, opponent_elo: float, won: bool, k: float = DEFAULT_K) -> float:
    """
    Met à jour l'ELO d'un joueur après un match.

    won : True si le joueur a gagné
    k : K-factor (32 par défaut, plus haut = plus volatile)
    """
    expected = expected_probability(player_elo, opponent_elo)
    actual = 1.0 if won else 0.0
    new_elo = player_elo + k * (actual - expected)
    return new_elo


def k_factor_for_tournament(tournament_type: str) -> float:
    """Récupère le K-factor en fonction du type de tournoi."""
    return K_BY_TOURNAMENT.get(tournament_type, DEFAULT_K)


def calculate_player_elos_from_history(matches: list) -> dict:
    """
    Calcule les ELO d'un joueur à partir de son historique de matchs.

    matches : liste de dicts avec :
    {
        'opponent_elo': float (ou None, défaut INITIAL_ELO),
        'opponent_elo_surface': float (idem),
        'surface': 'hard'/'clay'/'grass',
        'won': bool,
        'tournament_type': 'Grand Slam' / 'ATP 500' / etc.
        'date': str (ISO),  # pour ordonner si pas déjà fait
    }

    Retourne {'global': X, 'hard': Y, 'clay': Z, 'grass': W}.
    """
    elos = {
        "global": INITIAL_ELO,
        "hard": INITIAL_ELO,
        "clay": INITIAL_ELO,
        "grass": INITIAL_ELO,
    }

    # Trier par date croissante (plus ancien d'abord)
    matches_sorted = sorted(matches, key=lambda m: m.get("date", ""))

    for m in matches_sorted:
        surface = normalize_surface(m.get("surface", "hard"))
        opponent_global = m.get("opponent_elo", INITIAL_ELO)
        opponent_surface = m.get("opponent_elo_surface", opponent_global)
        won = m.get("won", False)
        k = k_factor_for_tournament(m.get("tournament_type", "Other"))

        # Mise a jour ELO global
        elos["global"] = update_elo(elos["global"], opponent_global, won, k=k * 0.7)

        # Mise a jour ELO surface (K-factor plus élevé sur la surface du match)
        if surface in elos:
            elos[surface] = update_elo(elos[surface], opponent_surface, won, k=k)

    return elos


def form_factor(recent_results: list) -> float:
    """
    Bonus de forme récente : entre 0.95 (mauvaise forme) et 1.05 (excellente forme).
    recent_results : liste des 5-10 derniers résultats.
    Accepte 2 formats :
      - Booléens : [True, True, False, True, ...]
      - Objets : [{"result": "W"/"L", "won": True/False, ...}, ...]
    """
    if not recent_results:
        return 1.0

    # Normaliser : extraire le booleen 'won' de chaque element
    bools = []
    for r in recent_results:
        if isinstance(r, bool):
            bools.append(r)
        elif isinstance(r, dict):
            # Format objet : on lit 'won' (booleen) ou 'result' ('W'/'L')
            if "won" in r:
                bools.append(bool(r["won"]))
            elif "result" in r:
                bools.append(r["result"] == "W")
            else:
                bools.append(False)
        else:
            bools.append(False)

    # Pondération : les plus récents comptent plus
    weights = [1 + 0.2 * i for i in range(len(bools))]
    weighted_wins = sum(w for w, r in zip(weights, bools) if r)
    weighted_total = sum(weights)
    win_rate = weighted_wins / weighted_total if weighted_total > 0 else 0.5
    # Map [0, 1] -> [0.95, 1.05]
    return 0.95 + (win_rate * 0.10)


def h2h_factor(h2h_wins_a: int, h2h_wins_b: int) -> float:
    """
    Bonus H2H : si A domine B historiquement, léger bonus pour A.
    Retourne un multiplicateur entre 0.95 et 1.05.
    """
    total = h2h_wins_a + h2h_wins_b
    if total < 3:  # Pas assez de matchs pour conclure
        return 1.0
    win_rate_a = h2h_wins_a / total
    return 0.95 + (win_rate_a * 0.10)
