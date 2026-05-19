"""
Value Bet Engine pour le tennis.

DEUX modes de detection :

1. CONFIDENT FAVORITE (defaut) : favori solide avec cote raisonnable
   - Proba IA >= 75%
   - Cote entre 1.40 et 2.20 (eviter trop "safe" ou trop incertain)
   - Strategie : gagner souvent avec gain modere

2. VALUE BET (pur math) : edge mathematique positif
   - Edge >= 5%
   - Strategie : gain long terme via volume
"""

# === SEUILS MODE CONFIDENT FAVORITE (mode actif) ===
CONFIDENT_MIN_PROB = 0.75    # 75% : forte conviction de l'IA
CONFIDENT_MIN_ODDS = 1.40    # cote >= 1.40 : eviter les "1.05" qui rapportent rien
CONFIDENT_MAX_ODDS = 2.20    # cote <= 2.20 : eviter les "outsiders" tagges 'favoris'

# === SEUILS MODE VALUE BET PUR (desactive par defaut) ===
MIN_EDGE = 0.05              # edge >= 5%
MIN_PROBA = 0.20

# === MODEL PICKS SANS COTES (fallback) ===
# Seuil de confiance minimum pour generer un "model pick" (pari sans cote API)
# Permet de tracker la fiabilite du modele meme sans cotes bookmaker reelles
MIN_MODEL_CONFIDENCE = 0.75  # aligne avec CONFIDENT_MIN_PROB

# === STRATEGIE ACTIVE ===
# 'confident_favorite' : favori >= 75% avec cote interessante (recommande)
# 'value_bet'          : pari mathematique pur (perte freq mais ROI long terme)
STRATEGY = "confident_favorite"


def implied_probability(odds: float) -> float:
    if odds <= 1.0:
        return 0.0
    return 1.0 / odds


def calculate_edge(model_prob: float, odds: float) -> float:
    if odds <= 1.0:
        return 0.0
    return (model_prob * odds) - 1.0


def confidence_level(edge: float, model_prob: float) -> str:
    if model_prob < MIN_PROBA:
        return "low"
    if edge > 0.15:
        return "strong"
    elif edge > 0.08:
        return "high"
    elif edge > MIN_EDGE:
        return "moderate"
    return "none"


def explain_value(market: str, model_prob: float, book_prob: float, edge: float) -> str:
    diff_pct = (model_prob - book_prob) * 100
    edge_pct = edge * 100
    return (
        f"Modele : {model_prob*100:.1f}% vs bookmaker {book_prob*100:.1f}% "
        f"(ecart {diff_pct:+.1f} pts). Edge {edge_pct:+.1f}%."
    )


def detect_tennis_value_bets(predictions: dict, odds: dict,
                             player_a_name: str, player_b_name: str) -> list:
    """
    Detecte les paris recommandes selon la STRATEGY active.

    Mode 'confident_favorite' (defaut) :
      → IA donne >= 75% à un joueur ET la cote est dans [1.40, 2.20]
      → on recommande de parier sur lui

    Mode 'value_bet' :
      → Edge mathematique positif (proba IA > proba bookmaker implicite)
      → strategie classique value betting
    """
    bets = []

    # Si les cotes ne sont pas reelles (estimees ou absentes), pas de recommendation
    source = odds.get("_source")
    if source not in ("api", "the_odds_api"):
        return bets

    winner = predictions.get("winner", {})
    prob_a = winner.get("prob_a", 0) / 100
    prob_b = winner.get("prob_b", 0) / 100
    odd_1 = odds.get("1") or 0
    odd_2 = odds.get("2") or 0

    if STRATEGY == "confident_favorite":
        # --- Joueur A : favori confiant ---
        if (prob_a >= CONFIDENT_MIN_PROB
                and odd_1 >= CONFIDENT_MIN_ODDS
                and odd_1 <= CONFIDENT_MAX_ODDS):
            book_prob = implied_probability(odd_1)
            edge = calculate_edge(prob_a, odd_1)
            bets.append({
                "market": f"Victoire {player_a_name}",
                "market_key": "1",
                "selection": player_a_name,
                "odds": odd_1,
                "model_prob": round(prob_a * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": "confident",
                "explanation": (
                    f"Favori solide : modele donne {prob_a*100:.1f}% a {player_a_name} "
                    f"@ cote {odd_1:.2f} (gain net +{(odd_1-1)*100:.0f}% si gagne)."
                ),
            })

        # --- Joueur B : favori confiant ---
        if (prob_b >= CONFIDENT_MIN_PROB
                and odd_2 >= CONFIDENT_MIN_ODDS
                and odd_2 <= CONFIDENT_MAX_ODDS):
            book_prob = implied_probability(odd_2)
            edge = calculate_edge(prob_b, odd_2)
            bets.append({
                "market": f"Victoire {player_b_name}",
                "market_key": "2",
                "selection": player_b_name,
                "odds": odd_2,
                "model_prob": round(prob_b * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": "confident",
                "explanation": (
                    f"Favori solide : modele donne {prob_b*100:.1f}% a {player_b_name} "
                    f"@ cote {odd_2:.2f} (gain net +{(odd_2-1)*100:.0f}% si gagne)."
                ),
            })

    else:
        # Mode 'value_bet' classique (edge mathematique)
        if odd_1 > 1.0:
            book_prob = implied_probability(odd_1)
            edge = calculate_edge(prob_a, odd_1)
            if edge > MIN_EDGE and prob_a > MIN_PROBA:
                bets.append({
                    "market": f"Victoire {player_a_name}",
                    "market_key": "1",
                    "selection": player_a_name,
                    "odds": odd_1,
                    "model_prob": round(prob_a * 100, 2),
                    "implied_prob": round(book_prob * 100, 2),
                    "edge_pct": round(edge * 100, 2),
                    "confidence": confidence_level(edge, prob_a),
                    "explanation": explain_value("Vainqueur A", prob_a, book_prob, edge),
                })

        if odd_2 > 1.0:
            book_prob = implied_probability(odd_2)
            edge = calculate_edge(prob_b, odd_2)
            if edge > MIN_EDGE and prob_b > MIN_PROBA:
                bets.append({
                    "market": f"Victoire {player_b_name}",
                    "market_key": "2",
                    "selection": player_b_name,
                    "odds": odd_2,
                    "model_prob": round(prob_b * 100, 2),
                    "implied_prob": round(book_prob * 100, 2),
                    "edge_pct": round(edge * 100, 2),
                    "confidence": confidence_level(edge, prob_b),
                    "explanation": explain_value("Vainqueur B", prob_b, book_prob, edge),
                })

    bets.sort(key=lambda b: -b.get("model_prob", 0))
    return bets


def generate_model_picks(predictions: dict, odds: dict,
                         player_a_name: str, player_b_name: str,
                         player_a_id=None, player_b_id=None) -> list:
    """Genere des paris bases uniquement sur la confiance du modele.

    Le model_pick est independant des cotes : il analyse les stats des joueurs
    (ELO, forme, H2H, surface, etc.) et picke le favori si confiance >= seuil.

    Si une cote bookmaker (the_odds_api) est dispo, on la stocke pour mesurer
    l'edge plus tard. Sinon, on stocke 0 dans 'odds' (= pas evaluable ROI).
    """
    picks = []
    winner = predictions.get("winner", {})
    prob_a = winner.get("prob_a", 0) / 100
    prob_b = winner.get("prob_b", 0) / 100

    # Cote reelle uniquement si source = the_odds_api ou api (RapidAPI)
    source = odds.get("_source", "none")
    has_real_odds = source in ("the_odds_api", "api")

    def _make_pick(name, market_key, prob, pid):
        real_odd = float(odds.get(market_key, 0)) if has_real_odds else 0
        implied = round(implied_probability(real_odd) * 100, 2) if real_odd > 1.0 else 0
        edge = 0
        if real_odd > 1.0 and prob > 0:
            edge = round(((prob * real_odd) - 1) * 100, 2)
        return {
            "market": f"Victoire {name}",
            "market_key": market_key,
            "selection": name,
            "selection_player_id": pid,
            "odds": real_odd,                 # 0 si pas de cote bookmaker
            "model_prob": round(prob * 100, 2),
            "implied_prob": implied,
            "edge_pct": edge,
            "confidence": "model_only",
            "type": "model_pick",
            "no_real_odds": not has_real_odds, # flag pour tracking DB
            "explanation": f"Le modele donne {prob*100:.1f}% de chances a {name}.",
        }

    if prob_a >= MIN_MODEL_CONFIDENCE:
        picks.append(_make_pick(player_a_name, "1", prob_a, player_a_id))
    elif prob_b >= MIN_MODEL_CONFIDENCE:
        picks.append(_make_pick(player_b_name, "2", prob_b, player_b_id))

    return picks


# Templates de phrases par langue pour le summary
_SUMMARY_TEMPLATES = {
    "fr": {
        "fav_strong_a": "{a} est nettement favori sur {surf} ({pa:.0f}% vs {pb:.0f}%) avec un ELO de {ea:.0f} contre {eb:.0f} (ecart de {gap:.0f} points).",
        "fav_strong_b": "{b} part favori sur {surf} ({pb:.0f}% vs {pa:.0f}%) avec un ELO de {eb:.0f} contre {ea:.0f}.",
        "fav_open": "Match tres ouvert sur {surf} ({pa:.0f}% vs {pb:.0f}%). ELOs proches ({ea:.0f} vs {eb:.0f}).",
        "h2h_a_dom": "{a} domine le H2H {wa}-{wb}, ce qui renforce son statut de favori.",
        "h2h_b_dom": "{b} mene le H2H {wb}-{wa} - element a prendre en compte.",
        "h2h_balanced": "H2H equilibre ({wa}-{wb}).",
        "score": "Score le plus probable : {sets}.",
        "games": "Total de jeux attendu : {gms:.1f} (Over 22.5: {ovr:.0f}%).",
        "form_a": "{a} en bonne forme recente.",
        "form_b": "{b} sur une meilleure dynamique recente.",
        "value_bet": "Value bet detecte : {mkt} @ {odd:.2f} (edge {edge:+.1f}%).",
    },
    "en": {
        "fav_strong_a": "{a} is a clear favorite on {surf} ({pa:.0f}% vs {pb:.0f}%) with an ELO of {ea:.0f} against {eb:.0f} (gap of {gap:.0f} points).",
        "fav_strong_b": "{b} is the favorite on {surf} ({pb:.0f}% vs {pa:.0f}%) with an ELO of {eb:.0f} against {ea:.0f}.",
        "fav_open": "Very open match on {surf} ({pa:.0f}% vs {pb:.0f}%). Similar ELOs ({ea:.0f} vs {eb:.0f}).",
        "h2h_a_dom": "{a} dominates the H2H {wa}-{wb}, reinforcing the favorite status.",
        "h2h_b_dom": "{b} leads the H2H {wb}-{wa} - worth noting.",
        "h2h_balanced": "Balanced H2H ({wa}-{wb}).",
        "score": "Most likely score: {sets}.",
        "games": "Expected total games: {gms:.1f} (Over 22.5: {ovr:.0f}%).",
        "form_a": "{a} in good recent form.",
        "form_b": "{b} on a better recent run.",
        "value_bet": "Value bet detected: {mkt} @ {odd:.2f} (edge {edge:+.1f}%).",
    },
    "es": {
        "fav_strong_a": "{a} es claramente favorito en {surf} ({pa:.0f}% vs {pb:.0f}%) con un ELO de {ea:.0f} contra {eb:.0f} (diferencia de {gap:.0f} puntos).",
        "fav_strong_b": "{b} parte como favorito en {surf} ({pb:.0f}% vs {pa:.0f}%) con un ELO de {eb:.0f} contra {ea:.0f}.",
        "fav_open": "Partido muy abierto en {surf} ({pa:.0f}% vs {pb:.0f}%). ELOs similares ({ea:.0f} vs {eb:.0f}).",
        "h2h_a_dom": "{a} domina el H2H {wa}-{wb}, reforzando su estatus de favorito.",
        "h2h_b_dom": "{b} lidera el H2H {wb}-{wa} - elemento a tener en cuenta.",
        "h2h_balanced": "H2H equilibrado ({wa}-{wb}).",
        "score": "Marcador mas probable: {sets}.",
        "games": "Total de juegos esperados: {gms:.1f} (Over 22.5: {ovr:.0f}%).",
        "form_a": "{a} en buena forma reciente.",
        "form_b": "{b} con mejor dinamica reciente.",
        "value_bet": "Value bet detectado: {mkt} @ {odd:.2f} (edge {edge:+.1f}%).",
    },
}


def generate_tennis_summary(predictions: dict, player_a: dict, player_b: dict,
                             h2h: dict, value_bets: list, lang: str = "fr") -> str:
    """Genere un resume narratif du match dans la langue specifiee.

    lang : "fr" (defaut), "en", "es"
    """
    if lang not in _SUMMARY_TEMPLATES:
        lang = "fr"
    tpl = _SUMMARY_TEMPLATES[lang]

    winner = predictions.get("winner", {})
    sets = predictions.get("sets_score", {})
    games = predictions.get("total_games", {})
    surface = predictions.get("surface", "hard")

    parts = []

    prob_a = winner.get("prob_a", 50)
    prob_b = winner.get("prob_b", 50)
    elo_a = winner.get("elo_a", 0)
    elo_b = winner.get("elo_b", 0)
    elo_gap = abs(winner.get("elo_gap", 0))

    name_a = player_a["name"]
    name_b = player_b["name"]

    # Headline favori
    if prob_a > prob_b + 15:
        parts.append(tpl["fav_strong_a"].format(
            a=name_a, b=name_b, surf=surface,
            pa=prob_a, pb=prob_b, ea=elo_a, eb=elo_b, gap=elo_gap,
        ))
    elif prob_b > prob_a + 15:
        parts.append(tpl["fav_strong_b"].format(
            a=name_a, b=name_b, surf=surface,
            pa=prob_a, pb=prob_b, ea=elo_a, eb=elo_b,
        ))
    else:
        parts.append(tpl["fav_open"].format(
            surf=surface, pa=prob_a, pb=prob_b, ea=elo_a, eb=elo_b,
        ))

    # H2H
    if h2h and h2h.get("wins_a", 0) + h2h.get("wins_b", 0) >= 3:
        wa = h2h["wins_a"]
        wb = h2h["wins_b"]
        if wa > wb * 1.5:
            parts.append(tpl["h2h_a_dom"].format(a=name_a, wa=wa, wb=wb))
        elif wb > wa * 1.5:
            parts.append(tpl["h2h_b_dom"].format(b=name_b, wa=wa, wb=wb))
        else:
            parts.append(tpl["h2h_balanced"].format(wa=wa, wb=wb))

    # Score
    most_likely = sets.get("most_likely", "")
    if most_likely:
        parts.append(tpl["score"].format(sets=most_likely))

    # Total games
    expected_games = games.get("expected_total", 0)
    if expected_games:
        parts.append(tpl["games"].format(
            gms=expected_games, ovr=games.get("prob_over", 0),
        ))

    # Forme
    form_adj = winner.get("form_adjustment", 1.0)
    if form_adj > 1.05:
        parts.append(tpl["form_a"].format(a=name_a))
    elif form_adj < 0.95:
        parts.append(tpl["form_b"].format(b=name_b))

    # Value bets
    if value_bets:
        top = value_bets[0]
        if top["confidence"] in ("strong", "high"):
            parts.append(tpl["value_bet"].format(
                mkt=top["market"], odd=top["odds"], edge=top["edge_pct"],
            ))

    return " ".join(parts)


def confidence_score_match(predictions: dict, value_bets: list) -> int:
    """Score de confiance global du match (0-100)."""
    winner = predictions.get("winner", {})
    max_prob = max(winner.get("prob_a", 50), winner.get("prob_b", 50))
    favorite_clarity = (max_prob - 50) * 2  # 0 si 50/50, 100 si 100/0

    value_boost = 0
    if value_bets:
        top_edge = max(b["edge_pct"] for b in value_bets)
        value_boost = min(20, top_edge)

    score = favorite_clarity + value_boost
    return int(max(0, min(100, score)))
