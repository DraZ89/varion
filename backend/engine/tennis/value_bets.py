"""
Value Bet Engine pour le tennis.

Marches couverts :
- Vainqueur du match (1/2)
- Plus tard : sets handicap, total games, etc.
"""

MIN_EDGE = 0.03
MIN_PROBA = 0.20

# Seuil de confiance minimum pour generer un "model pick" (pari sans cote API)
# Permet de tracker la fiabilite du modele meme sans cotes bookmaker reelles
MIN_MODEL_CONFIDENCE = 0.70  # 70% : objectif 90% win rate


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
    Compare les predictions du modele tennis aux cotes bookmaker.
    Si les cotes ont _source == "estimated" (calculees par nous), on ne genere
    PAS de value bet (puisqu'il n'y a pas d'edge a exploiter contre nous-memes).
    """
    bets = []

    # Si les cotes ne sont pas reelles (estimees ou absentes), pas de value bet
    # Sources acceptees : "api" (RapidAPI Tennis) et "the_odds_api" (bookmakers reels)
    source = odds.get("_source")
    if source not in ("api", "the_odds_api"):
        return bets

    winner = predictions.get("winner", {})

    # Vainqueur joueur A
    if odds.get("1") and odds["1"] > 1.0:
        prob = winner.get("prob_a", 0) / 100
        book_prob = implied_probability(odds["1"])
        edge = calculate_edge(prob, odds["1"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": f"Victoire {player_a_name}",
                "market_key": "1",
                "selection": player_a_name,
                "odds": odds["1"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Vainqueur A", prob, book_prob, edge),
            })

    # Vainqueur joueur B
    if odds.get("2") and odds["2"] > 1.0:
        prob = winner.get("prob_b", 0) / 100
        book_prob = implied_probability(odds["2"])
        edge = calculate_edge(prob, odds["2"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": f"Victoire {player_b_name}",
                "market_key": "2",
                "selection": player_b_name,
                "odds": odds["2"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Vainqueur B", prob, book_prob, edge),
            })

    bets.sort(key=lambda b: -b["edge_pct"])
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
