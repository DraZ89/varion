"""
Générateur de résumé en langage naturel.
Pas de fake IA marketing : juste une synthèse structurée des données.
"""

from data.teams import get_team


def generate_match_summary(home_id: str, away_id: str,
                           home_overall: dict, away_overall: dict,
                           predictions: dict,
                           value_bets: list,
                           key_home: list, key_away: list) -> str:
    """
    Construit un paragraphe résumant l'analyse complète du match.
    Style : analyste sportif, factuel.
    """
    home = get_team(home_id)
    away = get_team(away_id)

    parts = []

    # 1. Forme générale
    delta_overall = home_overall["overall_score"] - away_overall["overall_score"]
    if delta_overall > 8:
        parts.append(
            f"{home['name']} aborde cette rencontre avec un net avantage statistique "
            f"({home_overall['overall_score']:.0f} vs {away_overall['overall_score']:.0f}), "
            f"porté par une attaque cotée {home_overall['attack_score']:.0f}/100."
        )
    elif delta_overall < -8:
        parts.append(
            f"{away['name']} se présente comme le favori malgré le déplacement "
            f"({away_overall['overall_score']:.0f} vs {home_overall['overall_score']:.0f}), "
            f"avec une attaque solide ({away_overall['attack_score']:.0f}/100)."
        )
    else:
        parts.append(
            f"Match très équilibré sur le papier "
            f"({home_overall['overall_score']:.0f} vs {away_overall['overall_score']:.0f}). "
            f"Les deux équipes affichent un niveau global comparable."
        )

    # 2. Forme récente
    home_form = home_overall["form_score"]
    away_form = away_overall["form_score"]
    if home_form > 75 and away_form < 50:
        parts.append(
            f"La dynamique penche clairement en faveur de {home['short']} "
            f"(forme {home_form:.0f}/100), tandis que {away['short']} traverse une période plus délicate."
        )
    elif away_form > 75 and home_form < 50:
        parts.append(
            f"{away['short']} arrive en pleine confiance (forme {away_form:.0f}/100) "
            f"alors que {home['short']} reste sur une série en demi-teinte."
        )

    # 3. Prédiction marché principal
    p1 = predictions["result"]["prob_home_win"]
    pX = predictions["result"]["prob_draw"]
    p2 = predictions["result"]["prob_away_win"]
    score = predictions["result"]["most_likely_score"]
    if p1 > max(pX, p2) + 10:
        parts.append(
            f"Le modèle privilégie la victoire de {home['short']} "
            f"({p1:.0f}% vs nul {pX:.0f}% / extérieur {p2:.0f}%). "
            f"Score le plus probable : {score}."
        )
    elif p2 > max(pX, p1) + 10:
        parts.append(
            f"Le modèle voit {away['short']} l'emporter "
            f"({p2:.0f}% vs nul {pX:.0f}% / domicile {p1:.0f}%). "
            f"Score le plus probable : {score}."
        )
    else:
        parts.append(
            f"Issue très ouverte : {p1:.0f}% / {pX:.0f}% / {p2:.0f}%. "
            f"Score le plus probable : {score}."
        )

    # 4. Tendance buts
    expected_goals = predictions["over_under_25"]["expected_total"]
    if expected_goals > 3.0:
        parts.append(
            f"Forte attente offensive : {expected_goals:.1f} buts attendus, "
            f"BTTS à {predictions['btts']['prob_yes']:.0f}%."
        )
    elif expected_goals < 2.2:
        parts.append(
            f"Match potentiellement fermé ({expected_goals:.1f} buts attendus). "
            f"L'option Under 2.5 ({predictions['over_under_25']['prob_under']:.0f}%) mérite attention."
        )

    # 5. Joueur clé domicile
    if key_home:
        top_home = key_home[0]
        if top_home["goal_probability"] > 35:
            parts.append(
                f"Côté {home['short']}, {top_home['name']} reste l'élément clé "
                f"(impliqué dans {top_home['ga_involvement_pct']:.0f}% des buts récents, "
                f"forme {top_home['form_score']:.1f}/10)."
            )

    # 6. Joueur clé extérieur
    if key_away:
        top_away = key_away[0]
        if top_away["goal_probability"] > 35:
            parts.append(
                f"Côté {away['short']}, {top_away['name']} sera à surveiller "
                f"({top_away['goal_probability']:.0f}% de probabilité de marquer, "
                f"{top_away['ga_involvement_pct']:.0f}% d'implication offensive)."
            )

    # 7. Cartons / corners
    cards = predictions["cards"]
    if cards.get("is_derby"):
        parts.append(
            f"Contexte de derby : intensité élevée attendue, "
            f"{cards['expected_total']:.1f} cartons jaunes prévus en moyenne."
        )

    # 8. Value bets headline
    strong_bets = [b for b in value_bets if b["confidence"] in ("strong", "high")]
    if strong_bets:
        top = strong_bets[0]
        parts.append(
            f"💎 Value bet identifié : {top['market']} @ {top['odds']:.2f} "
            f"(edge {top['edge_pct']:+.1f}%)."
        )
    elif value_bets:
        top = value_bets[0]
        parts.append(
            f"Value modérée détectée sur {top['market']} @ {top['odds']:.2f} "
            f"(edge {top['edge_pct']:+.1f}%)."
        )
    else:
        parts.append(
            "Aucun value bet significatif détecté : les cotes du bookmaker reflètent bien la réalité statistique."
        )

    return " ".join(parts)


def confidence_score(predictions: dict, value_bets: list) -> int:
    """
    Score global de confiance du match (0-100).
    Basé sur la clarté du favori + force des value bets.
    """
    result = predictions["result"]
    max_prob = max(result["prob_home_win"], result["prob_draw"], result["prob_away_win"])

    # Plus le favori est clair, plus la confiance est haute
    favorite_clarity = (max_prob - 33.3) * 1.5  # ~0 si toutes equiprobables, ~100 si 100%

    # Bonus value bets
    value_boost = 0
    if value_bets:
        top_edge = max(b["edge_pct"] for b in value_bets)
        value_boost = min(20, top_edge)

    score = favorite_clarity + value_boost
    return int(max(0, min(100, score)))
