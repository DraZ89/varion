"""
Job de resolution des paris pending.

Pour chaque pari en status='pending' dont le match est passe (date < now - 1h),
on essaie de recuperer le resultat via les past_matches du joueur, et on resoud
automatiquement le pari.

Usage :
    python -m jobs.resolve_bets

A executer apres chaque cron tennis (ou en standalone).
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Permet l'execution directe
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.bets_db import BetsDB
from providers.api_rapidapi_tennis import TennisAPI, TennisAPIRateLimit


def parse_score_to_sets(score_str: str) -> tuple:
    """Parse un score type '6-4 6-3' en (sets_a, sets_b).

    Le 1er nombre de chaque set = points gagnes par player1, le 2eme par player2.
    On compte qui gagne le set (>= 6 jeux et 2 d'ecart).
    """
    if not score_str:
        return None, None
    sets_a, sets_b = 0, 0
    for set_str in score_str.split():
        if '-' not in set_str:
            continue
        parts = set_str.split('-')
        if len(parts) != 2:
            continue
        try:
            ga = int(parts[0])
            gb = int(parts[1].split('(')[0])  # ignore (TB)
            if ga > gb:
                sets_a += 1
            else:
                sets_b += 1
        except ValueError:
            continue
    return sets_a, sets_b


def find_match_in_past_matches(past_matches: list, opponent_id: int, match_date: str) -> dict:
    """Cherche un match specifique dans la liste past_matches d'un joueur.

    past_matches : liste retournee par api.get_player_past_matches
    opponent_id : id du player adversaire
    match_date : date approximative du match (string ISO)

    Retourne le match dict si trouve.
    """
    if not past_matches or not opponent_id:
        return None

    target_date = match_date[:10] if match_date else ""

    for m in past_matches:
        # Le format past_matches contient generalement player1Id, player2Id, date, score
        opp = None
        if str(m.get("player1Id")) == str(opponent_id):
            opp = "p1"
        elif str(m.get("player2Id")) == str(opponent_id):
            opp = "p2"

        if not opp:
            continue

        # Match avec cet adversaire trouve. Verif date proche
        m_date = (m.get("date") or "")[:10]
        if target_date and m_date and m_date == target_date:
            return m
        # Si pas de date target precise, on prend le 1er match avec cet adversaire
        if not target_date:
            return m
    return None


def resolve_match_winner(api: TennisAPI, db: BetsDB, bet: dict) -> str:
    """Pour un pari pending, essaie de retrouver le resultat du match.

    Retourne :
      - "resolved" si le pari a ete resolu (won/lost)
      - "no_data" si pas de resultat trouve (match peut-etre pas encore termine)
      - "error" si erreur API
    """
    match_id = bet.get("match_id")
    api_match_id = bet.get("api_match_id")
    tour = (bet.get("tour") or "ATP").lower()

    p_a_id = bet.get("player_a_id")
    p_b_id = bet.get("player_b_id")
    match_date = bet.get("match_date") or ""

    if not p_a_id or not p_b_id:
        return "no_data"

    # On regarde dans past_matches du joueur A pour trouver ce match
    try:
        past_a = api.get_player_past_matches(tour, p_a_id)
    except TennisAPIRateLimit:
        return "rate_limit"
    except Exception as e:
        print(f"  [WARN] past_matches {p_a_id} : {e}")
        return "error"

    found = find_match_in_past_matches(past_a, p_b_id, match_date)
    fetched_from = "A" if found else None  # Track depuis quel joueur on a trouve

    if not found:
        # Essaie aussi cote B
        try:
            past_b = api.get_player_past_matches(tour, p_b_id)
            found = find_match_in_past_matches(past_b, p_a_id, match_date)
            if found:
                fetched_from = "B"
        except Exception:
            pass

    if not found:
        return "no_data"

    # Determine le winner depuis le resultat
    # 1. CHAMP API REEL : "match_winner" = 1 ou 2 (pointe vers player1Id ou player2Id)
    winner_id = None
    match_winner = found.get("match_winner")
    if match_winner in (1, "1"):
        winner_id = found.get("player1Id")
    elif match_winner in (2, "2"):
        winner_id = found.get("player2Id")

    # 2. Fallback : winnerId direct (autres formats API)
    if not winner_id:
        winner_id = found.get("winnerId") or found.get("winner_id")

    # 3. Fallback : champ "winner" string ou number
    if not winner_id:
        w = found.get("winner")
        if w in (1, "1"):
            winner_id = found.get("player1Id")
        elif w in (2, "2"):
            winner_id = found.get("player2Id")
        elif isinstance(w, (int, str)) and str(w).isdigit() and int(w) > 100:
            # ID direct
            winner_id = int(w)

    # 4. Sinon, deduire de result/score depuis la perspective du joueur fetch
    if not winner_id:
        result = (found.get("result") or found.get("status") or "").lower()
        if result in ("win", "w", "won", "winner", "1"):
            winner_id = p_a_id if fetched_from == "A" else p_b_id
        elif result in ("loss", "l", "lost", "loser", "0"):
            winner_id = p_b_id if fetched_from == "A" else p_a_id

    if not winner_id:
        # Debug : print pour comprendre la structure
        print(f"  [DEBUG] Match trouve mais winner indeterminable. Cles : {list(found.keys())[:15]}")
        return "no_data"

    # Stocke le resultat du match (score + cotes reelles si dispo)
    # Le champ "result" contient le score type "6-4 6-3" ou "6-4, 6-3"
    score = (found.get("score") or found.get("result_score") or
             found.get("result") or "")
    # Si "result" est juste "win"/"loss", on l'ignore comme score
    if score and score.lower() in ("win", "loss", "won", "lost", "w", "l", ""):
        score = ""
    sets_a, sets_b = parse_score_to_sets(score)
    winner_name = bet.get("player_a_name") if str(winner_id) == str(p_a_id) else bet.get("player_b_name")
    db.store_match_result(
        match_id=match_id, api_match_id=api_match_id,
        winner_player_id=int(winner_id), winner_name=winner_name,
        final_score=score, sets_a=sets_a, sets_b=sets_b,
    )

    # BONUS : si le pari etait en cotes "estimated", on le met a jour avec la vraie cote
    # Recupere les vraies cotes depuis le past_match (champs odd1/odd2)
    real_odd1 = found.get("odd1")
    real_odd2 = found.get("odd2")
    try:
        if real_odd1 and real_odd2:
            real_odd1 = float(real_odd1)
            real_odd2 = float(real_odd2)
            if real_odd1 > 1.0 and real_odd2 > 1.0:
                # Update tous les paris pending de ce match avec les vraies cotes
                update_bet_with_real_odds(db, match_id, real_odd1, real_odd2)
    except (TypeError, ValueError):
        pass

    # Resoud tous les paris du match
    result = db.resolve_match(match_id, winner_player_id=int(winner_id))
    print(f"  [OK] {match_id} : winner={winner_name} score={score} ({result['won']} won, {result['lost']} lost)")
    return "resolved"


def update_bet_with_real_odds(db: BetsDB, match_id: str, odd1: float, odd2: float):
    """Met a jour les cotes des paris pending avec les vraies cotes du match passe."""
    from data.bets_db import get_conn
    with get_conn() as conn:
        # Pour chaque pari pending de ce match, mettre a jour la cote selon market_key
        rows = conn.execute("""
            SELECT id, market_key, odds FROM bets
            WHERE match_id = ? AND status = 'pending'
        """, (match_id,)).fetchall()
        for row in rows:
            new_odd = odd1 if row["market_key"] == "1" else (odd2 if row["market_key"] == "2" else None)
            if new_odd and abs(float(row["odds"]) - new_odd) > 0.01:
                conn.execute("UPDATE bets SET odds = ? WHERE id = ?", (new_odd, row["id"]))
                print(f"    -> Cote mise a jour : {row['odds']:.2f} -> {new_odd:.2f}")


def main():
    """Job principal : resout les paris pending dont le match est passe."""
    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("[ERROR] RAPIDAPI_KEY manquante")
        return

    db = BetsDB()
    api = TennisAPI(api_key)

    # IMPORTANT : vider le cache past_matches pour forcer le re-fetch
    # Sinon on lit l'ancienne version qui ne contient pas le match d'aujourd'hui
    from providers import cache as _cache
    deleted = _cache.clear_pattern("tennis_past_")
    if deleted > 0:
        print(f"Cache past_matches vide : {deleted} fichiers supprimes (force re-fetch)")

    # On ne traite que les paris dont le match est passe depuis au moins 1h
    # (laisse le temps a l'API de mettre a jour les resultats)
    now_utc = datetime.now(timezone.utc)
    cutoff_ms = int((now_utc - timedelta(hours=1)).timestamp() * 1000)

    pending = db.get_pending_bets()
    if not pending:
        print("Aucun pari pending. Rien a resoudre.")
        return

    # Filtre : que les paris dont le match est suffisamment passe
    to_resolve = [b for b in pending if b.get("match_timestamp_ms")
                  and b["match_timestamp_ms"] < cutoff_ms]

    print(f"Paris pending total : {len(pending)}")
    print(f"Paris a resoudre (match passe > 1h) : {len(to_resolve)}")

    if not to_resolve:
        return

    # Groupes par match_id pour eviter de traiter 2 fois le meme match
    seen_matches = set()
    stats = {"resolved": 0, "no_data": 0, "error": 0, "rate_limit": 0}

    for bet in to_resolve:
        match_id = bet.get("match_id")
        if match_id in seen_matches:
            continue
        seen_matches.add(match_id)

        result = resolve_match_winner(api, db, bet)
        stats[result] = stats.get(result, 0) + 1

        if result == "rate_limit":
            print("[STOP] Rate limit atteint")
            break

    print(f"\n=== RESOLUTION ===")
    print(f"Resolus : {stats.get('resolved', 0)}")
    print(f"Pas de data : {stats.get('no_data', 0)} (match pas encore dans past_matches)")
    print(f"Erreurs : {stats.get('error', 0)}")
    print(f"API calls : {api.calls_made}")

    # Print stats globales
    g = db.get_global_stats()
    print(f"\n=== STATS GLOBALES ===")
    print(f"Total paris : {g['total']} (settled : {g['settled']}, pending : {g['pending']})")
    print(f"Win rate : {g['win_rate_pct']}% ({g['won']}W / {g['lost']}L)")
    print(f"ROI : {g['roi_pct']}% (profit : {g['profit_units']:+.2f}u)")


if __name__ == "__main__":
    main()
