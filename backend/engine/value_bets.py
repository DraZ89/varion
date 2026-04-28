"""
Value Bet Engine

Principe :
- Probabilité bookmaker = 1 / cote (sans marge)
- Probabilité modèle = sortie du moteur de prédiction
- Edge = (proba_modèle * cote) - 1
- Si edge > seuil (ex: 5%) ET probabilité modèle > 30% (filtre fiabilité) -> Value Bet

Niveaux de confiance :
- Edge > 15% : 🔥 Strong Value
- Edge 8-15% : ✅ Value
- Edge 3-8% : 💡 Slight Value
- Edge < 3% : pas de value affiché
"""

MIN_EDGE = 0.03  # 3% minimum
MIN_PROBA = 0.20  # filtre les petites probas peu fiables


def implied_probability(odds: float) -> float:
    """Probabilité implicite du bookmaker à partir de la cote."""
    if odds <= 1.0:
        return 0.0
    return 1.0 / odds


def calculate_edge(model_prob: float, odds: float) -> float:
    """Edge = avantage du parieur. Positif = value."""
    if odds <= 1.0:
        return 0.0
    return (model_prob * odds) - 1.0


def confidence_level(edge: float, model_prob: float) -> str:
    """Étiquette de confiance qualitative."""
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
    """Génère une explication lisible du value bet."""
    diff_pct = (model_prob - book_prob) * 100
    edge_pct = edge * 100
    return (
        f"Le modèle estime la probabilité à {model_prob*100:.1f}% "
        f"alors que le bookmaker l'évalue à {book_prob*100:.1f}% "
        f"(écart de {diff_pct:+.1f} pts). "
        f"Edge de {edge_pct:+.1f}%."
    )


def detect_value_bets(predictions: dict, odds: dict, scorer_predictions: list = None) -> list:
    """
    Compare toutes les prédictions du modèle aux cotes du bookmaker.
    Retourne la liste des value bets détectés (triés par edge décroissant).
    """
    bets = []

    # ---- 1X2 ----
    if "1" in odds:
        prob = predictions["result"]["prob_home_win"] / 100
        book_prob = implied_probability(odds["1"])
        edge = calculate_edge(prob, odds["1"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Victoire domicile",
                "market_key": "1",
                "selection": "1",
                "odds": odds["1"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Victoire domicile", prob, book_prob, edge),
            })

    if "X" in odds:
        prob = predictions["result"]["prob_draw"] / 100
        book_prob = implied_probability(odds["X"])
        edge = calculate_edge(prob, odds["X"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Match nul",
                "market_key": "X",
                "selection": "X",
                "odds": odds["X"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Match nul", prob, book_prob, edge),
            })

    if "2" in odds:
        prob = predictions["result"]["prob_away_win"] / 100
        book_prob = implied_probability(odds["2"])
        edge = calculate_edge(prob, odds["2"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Victoire extérieur",
                "market_key": "2",
                "selection": "2",
                "odds": odds["2"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Victoire extérieur", prob, book_prob, edge),
            })

    # ---- BTTS ----
    if "btts_yes" in odds:
        prob = predictions["btts"]["prob_yes"] / 100
        book_prob = implied_probability(odds["btts_yes"])
        edge = calculate_edge(prob, odds["btts_yes"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Les deux équipes marquent (BTTS)",
                "market_key": "btts_yes",
                "selection": "Oui",
                "odds": odds["btts_yes"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("BTTS Oui", prob, book_prob, edge),
            })

    if "btts_no" in odds:
        prob = predictions["btts"]["prob_no"] / 100
        book_prob = implied_probability(odds["btts_no"])
        edge = calculate_edge(prob, odds["btts_no"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "BTTS Non",
                "market_key": "btts_no",
                "selection": "Non",
                "odds": odds["btts_no"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("BTTS Non", prob, book_prob, edge),
            })

    # ---- OVER/UNDER 2.5 ----
    if "over_25" in odds:
        prob = predictions["over_under_25"]["prob_over"] / 100
        book_prob = implied_probability(odds["over_25"])
        edge = calculate_edge(prob, odds["over_25"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Plus de 2.5 buts",
                "market_key": "over_25",
                "selection": "Over",
                "odds": odds["over_25"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Over 2.5", prob, book_prob, edge),
            })

    if "under_25" in odds:
        prob = predictions["over_under_25"]["prob_under"] / 100
        book_prob = implied_probability(odds["under_25"])
        edge = calculate_edge(prob, odds["under_25"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Moins de 2.5 buts",
                "market_key": "under_25",
                "selection": "Under",
                "odds": odds["under_25"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Under 2.5", prob, book_prob, edge),
            })

    # ---- OVER/UNDER 3.5 ----
    if "over_35" in odds:
        prob = predictions["over_under_35"]["prob_over"] / 100
        book_prob = implied_probability(odds["over_35"])
        edge = calculate_edge(prob, odds["over_35"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Plus de 3.5 buts",
                "market_key": "over_35",
                "selection": "Over",
                "odds": odds["over_35"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Over 3.5", prob, book_prob, edge),
            })

    if "under_35" in odds:
        prob = predictions["over_under_35"]["prob_under"] / 100
        book_prob = implied_probability(odds["under_35"])
        edge = calculate_edge(prob, odds["under_35"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Moins de 3.5 buts",
                "market_key": "under_35",
                "selection": "Under",
                "odds": odds["under_35"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Under 3.5", prob, book_prob, edge),
            })

    # ---- CLEAN SHEETS ----
    if "cs_home" in odds:
        prob = predictions["clean_sheet"]["prob_cs_home"] / 100
        book_prob = implied_probability(odds["cs_home"])
        edge = calculate_edge(prob, odds["cs_home"])
        if edge > MIN_EDGE and prob > 0.15:  # seuil plus bas pour CS
            bets.append({
                "market": "Clean sheet domicile",
                "market_key": "cs_home",
                "selection": "Oui",
                "odds": odds["cs_home"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("CS domicile", prob, book_prob, edge),
            })

    if "cs_away" in odds:
        prob = predictions["clean_sheet"]["prob_cs_away"] / 100
        book_prob = implied_probability(odds["cs_away"])
        edge = calculate_edge(prob, odds["cs_away"])
        if edge > MIN_EDGE and prob > 0.15:
            bets.append({
                "market": "Clean sheet extérieur",
                "market_key": "cs_away",
                "selection": "Oui",
                "odds": odds["cs_away"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("CS extérieur", prob, book_prob, edge),
            })

    # ---- CORNERS ----
    if "corners_over_95" in odds:
        prob = predictions["corners"]["prob_over"] / 100
        book_prob = implied_probability(odds["corners_over_95"])
        edge = calculate_edge(prob, odds["corners_over_95"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Plus de 9.5 corners",
                "market_key": "corners_over_95",
                "selection": "Over",
                "odds": odds["corners_over_95"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Corners Over 9.5", prob, book_prob, edge),
            })

    if "corners_under_95" in odds:
        prob = predictions["corners"]["prob_under"] / 100
        book_prob = implied_probability(odds["corners_under_95"])
        edge = calculate_edge(prob, odds["corners_under_95"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Moins de 9.5 corners",
                "market_key": "corners_under_95",
                "selection": "Under",
                "odds": odds["corners_under_95"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Corners Under 9.5", prob, book_prob, edge),
            })

    # ---- CARTONS ----
    if "cards_over_45" in odds:
        prob = predictions["cards"]["prob_over"] / 100
        book_prob = implied_probability(odds["cards_over_45"])
        edge = calculate_edge(prob, odds["cards_over_45"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Plus de 4.5 cartons jaunes",
                "market_key": "cards_over_45",
                "selection": "Over",
                "odds": odds["cards_over_45"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Cartons Over 4.5", prob, book_prob, edge),
            })

    if "cards_under_45" in odds:
        prob = predictions["cards"]["prob_under"] / 100
        book_prob = implied_probability(odds["cards_under_45"])
        edge = calculate_edge(prob, odds["cards_under_45"])
        if edge > MIN_EDGE and prob > MIN_PROBA:
            bets.append({
                "market": "Moins de 4.5 cartons jaunes",
                "market_key": "cards_under_45",
                "selection": "Under",
                "odds": odds["cards_under_45"],
                "model_prob": round(prob * 100, 2),
                "implied_prob": round(book_prob * 100, 2),
                "edge_pct": round(edge * 100, 2),
                "confidence": confidence_level(edge, prob),
                "explanation": explain_value("Cartons Under 4.5", prob, book_prob, edge),
            })

    # ---- BUTEURS ----
    if scorer_predictions and "scorer" in odds:
        for player_id, scorer_odds in odds["scorer"].items():
            pred = next((p for p in scorer_predictions if p["id"] == player_id), None)
            if not pred:
                continue
            prob = pred["goal_probability"] / 100
            book_prob = implied_probability(scorer_odds)
            edge = calculate_edge(prob, scorer_odds)
            if edge > MIN_EDGE and prob > MIN_PROBA:
                bets.append({
                    "market": f"Buteur : {pred['name']}",
                    "market_key": f"scorer_{player_id}",
                    "selection": pred["name"],
                    "odds": scorer_odds,
                    "model_prob": round(prob * 100, 2),
                    "implied_prob": round(book_prob * 100, 2),
                    "edge_pct": round(edge * 100, 2),
                    "confidence": confidence_level(edge, prob),
                    "explanation": explain_value("Buteur", prob, book_prob, edge),
                })

    # Tri par edge décroissant
    bets.sort(key=lambda b: -b["edge_pct"])
    return bets
