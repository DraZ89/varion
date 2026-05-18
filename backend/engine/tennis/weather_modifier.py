"""
Module d'ajustement meteo des predictions tennis.

Ne remplace pas le moteur de prediction existant : ajoute une COUCHE de ponderation
basee sur conditions reelles + profil joueur.

3 niveaux :
1. Calcul physique : vitesse balle effective (altitude, temperature, humidite)
2. Detection archetype joueur (grand serveur / defenseur / serveur-volleyeur)
3. Regles metier : bonus/malus selon archetype × conditions × surface
"""

from typing import Optional


# ============== 1. PHYSIQUE ==============

def compute_ball_speed_modifier(altitude_m: float, temp_c: float, humidity_pct: float) -> dict:
    """Calcule le modificateur de vitesse de balle effective.

    Formules :
        - Altitude : +8.5% par 1000m
        - Temperature : +0.3% par °C au-dessus de 20°C (negatif si en dessous)
        - Humidite : -0.2% par % au-dessus de 50%

    Returns: dict {alt_effect, temp_effect, hum_effect, total_modifier}
    """
    alt = altitude_m or 0
    t = temp_c if temp_c is not None else 20.0
    h = humidity_pct if humidity_pct is not None else 50.0

    alt_effect = 1.0 + 0.085 * (alt / 1000.0)
    temp_effect = 1.0 + 0.003 * (t - 20.0)
    hum_effect = 1.0 - 0.002 * (h - 50.0)

    total = alt_effect * temp_effect * hum_effect

    return {
        "alt_effect": round(alt_effect, 4),
        "temp_effect": round(temp_effect, 4),
        "hum_effect": round(hum_effect, 4),
        "total_modifier": round(total, 4),
        "speed_change_pct": round((total - 1.0) * 100, 2),
    }


# ============== 2. ARCHETYPE JOUEUR ==============

def detect_archetype(player_data: dict) -> str:
    """Detecte l'archetype d'un joueur a partir de ses stats.

    Cherche notamment :
    - aces_per_match (>10 = grand serveur)
    - 1st_serve_pct (>70% = serveur)
    - return_pct (>40% = bon retourneur)
    - net_points_won_pct (>65% = serveur-volleyeur)
    - rally_length (>5 = defenseur fond de court)

    Retourne un str : 'big_server' | 'defender' | 'serve_volleyer' | 'baseliner' | 'unknown'
    """
    if not player_data:
        return "unknown"

    profile = player_data.get("profile") or {}
    stats = profile.get("stats") or profile.get("career") or {}

    # Heuristiques sur stats disponibles (peuvent etre None)
    aces = profile.get("aces_per_match") or stats.get("aces_per_match") or 0
    first_serve_pct = profile.get("first_serve_pct") or stats.get("first_serve_pct") or 0
    net_points_pct = profile.get("net_points_won_pct") or stats.get("net_points_won_pct") or 0
    return_pct = profile.get("return_points_won_pct") or stats.get("return_points_won_pct") or 0
    height_cm = profile.get("height") or 0

    # Detection priorisee
    if net_points_pct > 65 and first_serve_pct > 60:
        return "serve_volleyer"
    if aces > 10 or (first_serve_pct > 70 and height_cm > 190):
        return "big_server"
    if return_pct > 42:
        return "defender"
    # Fallback : si on a une taille on classifie un peu
    if height_cm and height_cm < 180:
        return "defender"
    return "baseliner"


# ============== 3. REGLES METIER ==============

def apply_player_weather_bonus(archetype: str, surface: str, weather: dict) -> dict:
    """Calcule un bonus/malus (en pourcentage) pour un joueur selon son archetype
    et les conditions de jeu.

    Args:
        archetype : 'big_server' | 'defender' | 'serve_volleyer' | 'baseliner'
        surface : 'Clay' | 'Hard' | 'Grass' | etc.
        weather : dict avec temp_mean_c, humidity_pct, altitude_m, precipitation_mm, etc.

    Returns: dict {bonus_pct, reasons}
        - bonus_pct : float, le boost a appliquer a la proba (ex: +5 = +5pp)
        - reasons : liste de strings expliquant le calcul
    """
    bonus = 0.0
    reasons = []

    if not weather:
        return {"bonus_pct": 0.0, "reasons": []}

    surface = (surface or "").lower()
    temp = weather.get("temp_mean_c") or 20
    hum = weather.get("humidity_pct") or 50
    alt = weather.get("altitude_m") or 0
    rain = weather.get("precipitation_mm") or 0

    # === GRAND SERVEUR ===
    if archetype == "big_server":
        # Bonus : altitude haute, chaleur seche, gazon
        if alt > 400:
            bonus += 3.0
            reasons.append(f"+3.0pp altitude {alt}m favorise gros service")
        if temp > 25 and hum < 50:
            bonus += 2.0
            reasons.append(f"+2.0pp chaleur seche ({temp:.0f}°C, {hum:.0f}%hum)")
        if surface == "grass":
            bonus += 2.5
            reasons.append("+2.5pp gazon favorise grand serveur")
        # Malus : humidite haute, froid, terre battue
        if hum > 75:
            bonus -= 2.5
            reasons.append(f"-2.5pp humidite haute ({hum:.0f}%) ralentit balle")
        if temp < 15:
            bonus -= 2.0
            reasons.append(f"-2.0pp froid ({temp:.0f}°C) reduit service")
        if surface == "clay":
            bonus -= 3.0
            reasons.append("-3.0pp terre battue defavorise grand serveur")

    # === DEFENSEUR FOND DE COURT ===
    elif archetype == "defender":
        # Bonus : terre battue + humidite moderee
        if surface == "clay":
            bonus += 3.0
            reasons.append("+3.0pp terre battue ideale pour defenseur")
            if 50 <= hum <= 75:
                bonus += 1.5
                reasons.append(f"+1.5pp humidite moderee ({hum:.0f}%) avantage rallye")
        # Malus : gazon + chaleur seche
        if surface == "grass":
            bonus -= 2.5
            reasons.append("-2.5pp gazon defavorise defenseur (rebond bas)")
        if surface == "grass" and temp > 25 and hum < 50:
            bonus -= 2.0
            reasons.append("-2.0pp gazon+chaleur seche tres defavorable")

    # === SERVEUR-VOLLEYEUR ===
    elif archetype == "serve_volleyer":
        # Bonus : gazon + pluie recente (rebond bas, irregularite)
        if surface == "grass":
            bonus += 3.5
            reasons.append("+3.5pp gazon est surface naturelle du SV")
            if rain > 5:
                bonus += 1.5
                reasons.append(f"+1.5pp pluie recente ({rain:.0f}mm) → rebond bas")
        # Malus : terre battue + chaleur
        if surface == "clay":
            bonus -= 3.5
            reasons.append("-3.5pp terre battue tres defavorable au SV")
            if temp > 25:
                bonus -= 1.5
                reasons.append(f"-1.5pp terre + chaleur ({temp:.0f}°C) ralentit jeu rapide")

    return {"bonus_pct": round(bonus, 2), "reasons": reasons}


# ============== 4. CONDITIONS EXTREMES (reduction confiance) ==============

def detect_extreme_conditions(weather: dict, surface: str = None) -> dict:
    """Detecte des conditions extremes qui rendent les predictions moins fiables.

    Returns: dict {is_extreme: bool, confidence_penalty_pct: float, reasons: [str]}
    """
    if not weather:
        return {"is_extreme": False, "confidence_penalty_pct": 0, "reasons": []}

    penalty = 0.0
    reasons = []

    temp_max = weather.get("temp_max_c") or weather.get("temp_mean_c") or 20
    wind = weather.get("wind_max_kmh") or 0
    rain = weather.get("precipitation_mm") or 0
    surface_l = (surface or "").lower()

    # Chaleur extreme
    if temp_max > 35:
        penalty += 8.0
        reasons.append(f"Chaleur extreme {temp_max:.0f}°C → fatigue physique imprevisible")

    # Vent fort
    if wind > 30:
        penalty += 5.0
        reasons.append(f"Vent fort {wind:.0f}km/h → service degrade")

    # Pluie sur gazon (rare, mais perturbe)
    if surface_l == "grass" and rain > 10:
        penalty += 6.0
        reasons.append(f"Pluie sur gazon ({rain:.0f}mm) → rebond chaotique")

    return {
        "is_extreme": penalty > 5.0,
        "confidence_penalty_pct": round(penalty, 2),
        "reasons": reasons,
    }


# ============== 5. APPLICATION FINALE ==============

def apply_weather_to_prediction(
    raw_probabilities: dict,
    player_a_data: dict,
    player_b_data: dict,
    surface: str,
    weather: dict,
) -> dict:
    """Applique l'ajustement meteo aux probabilites brutes de victoire.

    Args:
        raw_probabilities: {"player_a_prob": 0.6, "player_b_prob": 0.4, "confidence": 0.7}
        player_a_data, player_b_data : dicts des joueurs avec profile
        surface : nom de la surface
        weather : dict meteo (ou None)

    Returns: dict {
        "player_a_prob": float ajuste,
        "player_b_prob": float ajuste,
        "confidence": float ajuste,
        "weather_applied": bool,
        "weather_details": { ... infos pour transparence ... }
    }
    """
    pa_prob = float(raw_probabilities.get("player_a_prob", 0.5))
    pb_prob = float(raw_probabilities.get("player_b_prob", 1.0 - pa_prob))
    confidence = float(raw_probabilities.get("confidence", 0.7))

    if not weather:
        return {
            "player_a_prob": pa_prob,
            "player_b_prob": pb_prob,
            "confidence": confidence,
            "weather_applied": False,
            "weather_details": None,
        }

    # Detect archetypes
    arch_a = detect_archetype(player_a_data)
    arch_b = detect_archetype(player_b_data)

    # Bonus/malus pour chaque joueur
    bonus_a = apply_player_weather_bonus(arch_a, surface, weather)
    bonus_b = apply_player_weather_bonus(arch_b, surface, weather)

    # Conditions extremes
    extreme = detect_extreme_conditions(weather, surface)

    # Vitesse balle effective
    speed = compute_ball_speed_modifier(
        weather.get("altitude_m", 0),
        weather.get("temp_mean_c"),
        weather.get("humidity_pct"),
    )

    # Application : bonus en POURCENTAGE POINTS sur la proba
    # bonus_a = +3 → pa_prob passe de 0.60 a 0.63
    new_pa = pa_prob + (bonus_a["bonus_pct"] / 100.0)
    new_pb = pb_prob + (bonus_b["bonus_pct"] / 100.0)

    # Renormaliser pour que somme = 1
    total = new_pa + new_pb
    if total > 0:
        new_pa = new_pa / total
        new_pb = new_pb / total

    # Clamp [0.05, 0.95] pour rester realiste
    new_pa = max(0.05, min(0.95, new_pa))
    new_pb = max(0.05, min(0.95, new_pb))

    # Renormaliser apres clamp
    total = new_pa + new_pb
    new_pa = new_pa / total
    new_pb = new_pb / total

    # Ajuster confiance : reduire si conditions extremes
    new_conf = confidence * (1.0 - extreme["confidence_penalty_pct"] / 100.0)
    new_conf = max(0.1, min(1.0, new_conf))

    return {
        "player_a_prob": round(new_pa, 4),
        "player_b_prob": round(new_pb, 4),
        "confidence": round(new_conf, 4),
        "weather_applied": True,
        "weather_details": {
            "archetype_a": arch_a,
            "archetype_b": arch_b,
            "bonus_a_pct": bonus_a["bonus_pct"],
            "bonus_b_pct": bonus_b["bonus_pct"],
            "reasons_a": bonus_a["reasons"],
            "reasons_b": bonus_b["reasons"],
            "extreme_conditions": extreme["is_extreme"],
            "confidence_penalty_pct": extreme["confidence_penalty_pct"],
            "extreme_reasons": extreme["reasons"],
            "ball_speed_change_pct": speed["speed_change_pct"],
            "temp_c": weather.get("temp_mean_c"),
            "humidity_pct": weather.get("humidity_pct"),
            "altitude_m": weather.get("altitude_m"),
            "wind_max_kmh": weather.get("wind_max_kmh"),
            "precipitation_mm": weather.get("precipitation_mm"),
        },
    }


# ============== TESTS ==============

if __name__ == "__main__":
    # Test physique
    s = compute_ball_speed_modifier(667, 25, 40)
    assert s["alt_effect"] > 1.05, "Altitude Madrid devrait booster vitesse"
    assert s["temp_effect"] > 1.01, "25°C > 20°C devrait booster"
    assert s["hum_effect"] > 1.0, "Humidite 40% < 50% devrait booster (air sec)"
    print(f"Madrid 25°C/40%hum/667m : vitesse balle {s['speed_change_pct']:+.1f}%")

    s = compute_ball_speed_modifier(25, 15, 80)
    print(f"Wimbledon 15°C/80%hum/25m : vitesse balle {s['speed_change_pct']:+.1f}%")

    # Test archetype
    p_serveur = {"profile": {"aces_per_match": 15, "height": 198, "first_serve_pct": 72}}
    assert detect_archetype(p_serveur) == "big_server"
    p_def = {"profile": {"return_points_won_pct": 45, "height": 178}}
    assert detect_archetype(p_def) == "defender"

    # Test bonus
    weather = {"temp_mean_c": 28, "humidity_pct": 35, "altitude_m": 667, "precipitation_mm": 0}
    bonus = apply_player_weather_bonus("big_server", "hard", weather)
    print(f"Grand serveur a Madrid hard chaud sec : {bonus['bonus_pct']:+.1f}pp")
    for r in bonus["reasons"]:
        print(f"  - {r}")

    # Test application complete
    raw = {"player_a_prob": 0.60, "player_b_prob": 0.40, "confidence": 0.75}
    result = apply_weather_to_prediction(
        raw,
        p_serveur, p_def,
        "Clay", weather,
    )
    print(f"\nApplication complete (servvol vs def, clay, Madrid) :")
    print(f"  Proba A : {raw['player_a_prob']:.1%} -> {result['player_a_prob']:.1%}")
    print(f"  Proba B : {raw['player_b_prob']:.1%} -> {result['player_b_prob']:.1%}")
    print(f"  Confiance : {raw['confidence']:.1%} -> {result['confidence']:.1%}")

    print("\nOK : tests weather_modifier passes")
