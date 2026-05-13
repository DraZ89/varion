"""
Diagnostic complet API Tennis :
1. Quelle structure exacte renvoie /ranking/singles/ ?
2. Quelle structure exacte renvoie /fixtures/{date} ?
3. Pourquoi 11 joueurs au lieu de 200 ?

Cout : 2 req API (ranking ATP + fixtures du 5 mai)
Usage : python -m jobs.diag_tennis_full
"""

import os
import sys
import urllib.request
import urllib.error
import json

API_HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
API_BASE = f"https://{API_HOST}/tennis/v2"


def fetch(url, api_key):
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": API_HOST,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return e.code, {"_error": e.reason, "_body": body}


def main():
    print("=" * 60)
    print("DIAG Tennis API - Rankings + Fixtures")
    print("=" * 60)

    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("ERREUR : RAPIDAPI_KEY non definie")
        return

    masked = f"{api_key[:8]}...{api_key[-4:]}"
    print(f"Cle : {masked}\n")

    # === TEST 1 : Rankings ATP ===
    print(">>> TEST 1 : GET /atp/ranking/singles/")
    status, data = fetch(f"{API_BASE}/atp/ranking/singles/", api_key)
    print(f"  Status : {status}")

    if status != 200:
        print(f"  KO : {data}")
        return

    print(f"  Cles top-niveau : {list(data.keys())}")

    rankings = data.get("data") or []
    has_next = data.get("hasNextPage")
    print(f"  data : LIST de {len(rankings)} elements")
    print(f"  hasNextPage : {has_next}")

    if rankings:
        first = rankings[0]
        print(f"\n  STRUCTURE DU 1ER ELEMENT :")
        print(f"  Cles : {list(first.keys())}")
        print(f"  Dump :")
        print(f"  {json.dumps(first, indent=2, ensure_ascii=False)[:500]}")

        # Verifier la presence de player.id
        player = first.get("player")
        if isinstance(player, dict):
            print(f"\n  player.id = {player.get('id')}")
            print(f"  player.name = {player.get('name')}")
        else:
            print(f"\n  player n'est pas un dict : {type(player).__name__} = {repr(player)[:100]}")

    # Afficher les 5 premiers
    print(f"\n  Top 5 du ranking :")
    for i, r in enumerate(rankings[:5], 1):
        player = r.get("player", {})
        rank = r.get("position") or r.get("rank") or "?"
        name = player.get("name") if isinstance(player, dict) else "?"
        pid = player.get("id") if isinstance(player, dict) else "?"
        print(f"    #{rank}: {name} (id={pid})")

    # === TEST 2 : Fixtures du 5 mai 2026 ===
    print(f"\n{'=' * 60}")
    print(">>> TEST 2 : GET /atp/fixtures/2026-05-05")
    status, data = fetch(f"{API_BASE}/atp/fixtures/2026-05-05", api_key)
    print(f"  Status : {status}")

    if status != 200:
        print(f"  KO : {data}")
        return

    print(f"  Cles top-niveau : {list(data.keys())}")

    fixtures = data.get("data") or []
    print(f"  data : LIST de {len(fixtures)} fixtures")

    if fixtures:
        first = fixtures[0]
        print(f"\n  STRUCTURE DU 1ER FIXTURE :")
        print(f"  Cles : {list(first.keys())[:25]}")
        print(f"  Dump complet :")
        print(f"  {json.dumps(first, indent=2, ensure_ascii=False)[:1500]}")

        # On cherche les IDs des joueurs
        print(f"\n  Recherche IDs joueurs dans le 1er fixture...")
        candidates = ["player1Id", "player2Id", "first_player_key", "second_player_key",
                      "homeId", "awayId", "playerOneId", "playerTwoId"]
        for k in candidates:
            if k in first:
                print(f"    {k} = {first[k]}")

        # Cherche aussi dans les sub-objects
        for key in first.keys():
            val = first[key]
            if isinstance(val, dict):
                if "id" in val:
                    print(f"    {key}.id = {val['id']} (dans {key})")
                if "playerId" in val:
                    print(f"    {key}.playerId = {val['playerId']}")
                if "name" in val:
                    print(f"    {key}.name = {val['name']}")

    # Afficher les 3 premiers (vue compacte)
    print(f"\n  3 premiers fixtures (vue compacte) :")
    for i, f in enumerate(fixtures[:3], 1):
        keys = list(f.keys())[:8]
        print(f"    #{i} keys : {keys}")


if __name__ == "__main__":
    main()
