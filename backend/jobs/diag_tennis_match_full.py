"""
Diag : examine la fixture d'aujourd'hui pour comprendre :
1. Si les cotes sont dans la response ou dans un endpoint different
2. Si player a une photo URL dans son profil
3. La structure complete d'une fixture

Aucune requete API : on lit le cache.
Usage : python -m jobs.diag_tennis_match_full
"""

import os
import sys
import json

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BACKEND_DIR, "cache")


def main():
    print("=" * 60)
    print("DIAG : structure complete fixture + ranking + past_matches")
    print("=" * 60)

    # 1. Cherche fixtures
    print("\n>>> 1. STRUCTURE FIXTURE COMPLETE")
    fixture_files = [f for f in sorted(os.listdir(CACHE_DIR)) if "fixtures" in f and f.endswith(".json")]
    if not fixture_files:
        print("  Aucun cache fixtures trouve.")
        return

    # On prend le dernier
    fname = fixture_files[-1]
    print(f"  Fichier : {fname}")
    with open(os.path.join(CACHE_DIR, fname), "r", encoding="utf-8") as f:
        cache = json.load(f)

    fixtures = (cache.get("data") or {}).get("data") or []
    print(f"  Nb fixtures : {len(fixtures)}")

    if fixtures:
        # Cherche Dzumhur ou Mannarino
        target = None
        for fix in fixtures:
            p1 = (fix.get("player1") or {}).get("name", "")
            p2 = (fix.get("player2") or {}).get("name", "")
            if "Dzumhur" in p1 or "Dzumhur" in p2 or "Mannarino" in p1 or "Mannarino" in p2:
                target = fix
                break

        if not target:
            target = fixtures[0]

        print(f"\n  STRUCTURE COMPLETE de la fixture :")
        print(json.dumps(target, indent=2, ensure_ascii=False, default=str))

    # 2. Structure ranking - cherche photo
    print("\n\n>>> 2. STRUCTURE RANKING (cherche photo URL)")
    ranking_files = [f for f in sorted(os.listdir(CACHE_DIR)) if "rankings" in f and "v2" in f]
    if ranking_files:
        with open(os.path.join(CACHE_DIR, ranking_files[0]), "r", encoding="utf-8") as f:
            cache = json.load(f)
        rankings = (cache.get("data") or {}).get("data") or []
        if rankings:
            first = rankings[0]
            print(f"  STRUCTURE 1ER ELEMENT (toutes les cles):")
            print(json.dumps(first, indent=2, ensure_ascii=False, default=str))

            # Cherche les cles qui pourraient etre des URLs photo
            print(f"\n  Recherche cles qui pourraient contenir une URL/photo :")
            def find_url_keys(obj, prefix=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        full_key = f"{prefix}.{k}" if prefix else k
                        if isinstance(v, str) and ("http" in v or "image" in k.lower() or "photo" in k.lower() or "url" in k.lower()):
                            print(f"    {full_key} = {v[:100]}")
                        elif isinstance(v, dict):
                            find_url_keys(v, full_key)
            find_url_keys(first)

    # 3. Structure past_matches (cherche surface, opponent, score)
    print("\n\n>>> 3. STRUCTURE PAST_MATCHES (forme recente)")
    past_files = [f for f in sorted(os.listdir(CACHE_DIR)) if "past" in f]
    if past_files:
        # Cherche celui de Mannarino (id 7806) ou prend le 1er
        target_file = None
        for f in past_files:
            if "7806" in f:
                target_file = f
                break
        if not target_file:
            target_file = past_files[0]

        print(f"  Fichier : {target_file}")
        with open(os.path.join(CACHE_DIR, target_file), "r", encoding="utf-8") as f:
            cache = json.load(f)
        past = (cache.get("data") or {}).get("data") or []
        print(f"  Nb past matches : {len(past)}")

        if past:
            sorted_p = sorted(past, key=lambda m: m.get("date") or "", reverse=True)
            print(f"\n  STRUCTURE 1ER MATCH (le plus recent) :")
            print(json.dumps(sorted_p[0], indent=2, ensure_ascii=False, default=str))

            # Cherche un champ surface
            print(f"\n  Recherche champ 'surface' ou 'court' dans les 3 premiers matchs :")
            for m in sorted_p[:3]:
                p1n = (m.get("player1") or {}).get("name", "?")
                p2n = (m.get("player2") or {}).get("name", "?")
                surf_keys = {}
                for k in ["surface", "court", "courtId", "tournament", "venue"]:
                    if k in m:
                        surf_keys[k] = m[k]
                print(f"    {p1n} vs {p2n} ({m.get('date', '?')[:10]}) : {surf_keys}")


if __name__ == "__main__":
    main()
