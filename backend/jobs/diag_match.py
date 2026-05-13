"""
Diagnostic : pour un match du data_tennis.json, dump tout ce qu'on sait
+ va re-fetcher l'API (sans cache) pour comparer.

Usage :
    python -m jobs.diag_match Milic
    python -m jobs.diag_match T_1234
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from providers.api_rapidapi_tennis import TennisAPI
from providers import cache as _cache


def diag_match(query: str):
    # 1. Lire data_tennis.json
    path = Path(__file__).resolve().parent.parent.parent / "frontend" / "data_tennis.json"
    if not path.exists():
        print(f"[ERROR] data_tennis.json absent : {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = data.get("matches") or []
    print(f"data_tennis.json : {len(matches)} matchs (genere {data.get('generated_at', '?')})")
    print()

    # 2. Trouver le match qui matche la query
    found = None
    for m in matches:
        haystack = (
            f"{m.get('id', '')} {(m.get('player_a') or {}).get('name', '')} "
            f"{(m.get('player_b') or {}).get('name', '')}"
        ).lower()
        if query.lower() in haystack:
            found = m
            break

    if not found:
        print(f"[NO MATCH] Aucun match correspondant a : {query}")
        print("\nMatchs presents :")
        for m in matches:
            pa = (m.get('player_a') or {}).get('name', '?')
            pb = (m.get('player_b') or {}).get('name', '?')
            print(f"  {m.get('id')} : {pa} vs {pb}")
        return

    # 3. Dump du match local
    print(f"=== MATCH LOCAL (data_tennis.json) ===")
    print(f"  ID : {found.get('id')}")
    print(f"  API match ID : {found.get('api_id')}")
    print(f"  Date : {found.get('date')} | Time : {found.get('time')}")
    print(f"  Tournament : {found.get('tournament')}")
    print(f"  Tournament ID : {found.get('tournament_id')}")
    print(f"  Player A : {(found.get('player_a') or {}).get('name')} (ID {(found.get('player_a') or {}).get('api_id')})")
    print(f"  Player B : {(found.get('player_b') or {}).get('name')} (ID {(found.get('player_b') or {}).get('api_id')})")
    print(f"  Round : {found.get('round')}")
    print()

    # 4. Re-fetch API sans cache (force refresh)
    api_match_id = found.get('api_id')
    if not api_match_id:
        print("[WARN] Pas d'api_id, impossible de comparer avec API")
        return

    # Vide le cache fixtures pour forcer re-fetch
    _cache.clear_pattern("tennis_fixtures_")
    print("Cache fixtures vide (force re-fetch)")

    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("[ERROR] RAPIDAPI_KEY manquante")
        return

    api = TennisAPI(api_key)
    tour = (found.get('tour') or 'atp').lower()

    # Re-fetch fixtures pour la date du match
    date_only = found.get('date', '')[:10]
    print(f"\n=== RE-FETCH API ({tour}, {date_only}) ===")
    try:
        # Cette methode doit fetcher avec date specifique
        fixtures = api.get_fixtures_by_date(tour, date_only) if hasattr(api, 'get_fixtures_by_date') else api.get_matches_recent_days(tour)
    except Exception as e:
        print(f"[ERROR] Fetch API : {e}")
        return

    # Cherche le match par api_id
    api_match = None
    for fx in (fixtures or []):
        if str(fx.get('id')) == str(api_match_id):
            api_match = fx
            break

    if api_match:
        print(f"  ID : {api_match.get('id')}")
        print(f"  Date API : {api_match.get('date')}")
        print(f"  Player1 : {(api_match.get('player1') or {}).get('name')} (ID {api_match.get('player1Id')})")
        print(f"  Player2 : {(api_match.get('player2') or {}).get('name')} (ID {api_match.get('player2Id')})")
        print(f"  Round ID : {api_match.get('roundId')}")
        print(f"  Tournament ID : {api_match.get('tournamentId')}")
        print()

        # Comparer
        local_a = (found.get('player_a') or {}).get('api_id')
        local_b = (found.get('player_b') or {}).get('api_id')
        api_a = api_match.get('player1Id')
        api_b = api_match.get('player2Id')

        if str(local_a) != str(api_a) or str(local_b) != str(api_b):
            print("[!!! DIFFERENCE !!!] Les joueurs ont change cote API depuis le dernier refresh")
            print(f"  Local : A={local_a} B={local_b}")
            print(f"  API   : A={api_a} B={api_b}")
            print("\n  -> Solution : python -m jobs.refresh_tennis (force le re-fetch)")
        else:
            print("[OK] Local et API matchent. Le bug est ailleurs.")
            print(f"  Si tu penses que les joueurs sont faux dans la realite,")
            print(f"  le probleme vient de l'API (donnees obsoletes cote provider).")
    else:
        print(f"[NOT FOUND] Match api_id={api_match_id} introuvable dans la reponse API actuelle")
        print(f"  -> Le tournoi a ete mis a jour, ce match n'existe plus.")
        print(f"  -> Solution : python -m jobs.refresh_tennis")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python -m jobs.diag_match <nom_joueur_ou_match_id>")
        sys.exit(1)
    diag_match(sys.argv[1])
