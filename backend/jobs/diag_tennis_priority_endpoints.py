"""
Diag : teste les 6 endpoints prioritaires identifies sur le playground
RapidAPI (jjrm365). On veut voir leur structure de reponse pour decider
quoi en faire.

Cout : ~6-8 req sur le quota free (500/mois).
Usage : python -m jobs.diag_tennis_priority_endpoints
"""

import os
import urllib.request
import urllib.error
import json

API_HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"

# Cible : Mannarino (id 7806) FRA, Top 50
PLAYER_ID = 7806
OPPONENT_ID = 13447  # Dzumhur
TOURNAMENT_ID = 21326  # Rome ATP


def fetch(url, api_key):
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": API_HOST,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body


def show_keys(obj, indent=0, max_depth=3):
    """Affiche les cles d'un objet JSON jusqu'a max_depth."""
    sp = "    " * indent
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:20]:
            if isinstance(v, list):
                if v and isinstance(v[0], dict):
                    print(f"{sp}{k} : list[{len(v)}] de dicts")
                    if indent < max_depth - 1:
                        print(f"{sp}    [0] cles : {list(v[0].keys())[:15]}")
                        # 1 niveau de plus
                        for k2, v2 in list(v[0].items())[:5]:
                            if isinstance(v2, dict):
                                print(f"{sp}        {k2} : dict cles={list(v2.keys())[:8]}")
                            elif not isinstance(v2, list):
                                preview = repr(v2)[:50]
                                print(f"{sp}        {k2} = {preview}")
                else:
                    sample = v[0] if v else None
                    print(f"{sp}{k} : list[{len(v)}] = {repr(sample)[:50]}")
            elif isinstance(v, dict):
                print(f"{sp}{k} : dict cles={list(v.keys())[:10]}")
                if indent < max_depth - 1:
                    show_keys(v, indent + 1, max_depth)
            else:
                preview = repr(v)[:60]
                print(f"{sp}{k} : {type(v).__name__} = {preview}")


def test_endpoint(name, paths_to_try, api_key, params=None):
    """Teste plusieurs URLs (variantes) jusqu'a trouver celle qui marche."""
    print(f"\n{'=' * 70}")
    print(f">>> {name}")
    if params:
        print(f"    params suggested : {params}")

    for path in paths_to_try:
        full_url = f"https://{API_HOST}{path}"
        if params:
            from urllib.parse import urlencode
            full_url += "?" + urlencode(params)
        print(f"    Try : {path}")
        status, body = fetch(full_url, api_key)
        print(f"    Status : {status}")

        if status == 200:
            try:
                data = json.loads(body)
                print(f"    *** SUCCES ***")
                print(f"    Body preview (first 800 chars):")
                print(f"    {json.dumps(data, ensure_ascii=False)[:800]}")
                print(f"\n    Structure :")
                show_keys(data, indent=1, max_depth=3)
                return  # Premier qui marche, on stop
            except Exception as e:
                print(f"    [WARN] JSON parse fail : {e}")
                print(f"    Body : {body[:200]}")
                return
        elif status == 404:
            print(f"    [404]")
        else:
            print(f"    [FAIL] : {body[:100]}")

    print(f"    Aucune variante n'a marche pour {name}")


def main():
    print("=" * 70)
    print("DIAG : 6 endpoints prioritaires Matchstat")
    print("=" * 70)

    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("ERREUR : RAPIDAPI_KEY non definie")
        return

    # 1. getPlayerInfo - profil complet (priorite top)
    test_endpoint("getPlayerInfo (profil)",
        [
            f"/tennis/v2/atp/player/{PLAYER_ID}/info",
            f"/tennis/v2/atp/players/{PLAYER_ID}/info",
            f"/tennis/v2/atp/player-info/{PLAYER_ID}",
            f"/tennis/v2/atp/info/{PLAYER_ID}",
            f"/tennis/v2/atp/player/{PLAYER_ID}",
        ],
        api_key)

    # 2. getPlayerMatchStats - stats detaillees
    test_endpoint("getPlayerMatchStats",
        [
            f"/tennis/v2/atp/player/{PLAYER_ID}/match-stats",
            f"/tennis/v2/atp/player/{PLAYER_ID}/matchstats",
            f"/tennis/v2/atp/match-stats/{PLAYER_ID}",
            f"/tennis/v2/atp/player-match-stats/{PLAYER_ID}",
        ],
        api_key)

    # 3. getPlayerPerformanceBreakdown
    test_endpoint("getPlayerPerformanceBreakdown",
        [
            f"/tennis/v2/atp/player/{PLAYER_ID}/performance",
            f"/tennis/v2/atp/player/{PLAYER_ID}/performance-breakdown",
            f"/tennis/v2/atp/performance/{PLAYER_ID}",
            f"/tennis/v2/atp/player-performance/{PLAYER_ID}",
            f"/tennis/v2/atp/performance-breakdown/{PLAYER_ID}",
        ],
        api_key)

    # 4. getH2HVsAllOppStats
    test_endpoint("getH2HVsAllOppStats",
        [
            f"/tennis/v2/atp/h2h/{PLAYER_ID}/vs-all",
            f"/tennis/v2/atp/h2h-all/{PLAYER_ID}",
            f"/tennis/v2/atp/h2h/all-opponents/{PLAYER_ID}",
            f"/tennis/v2/atp/player/{PLAYER_ID}/h2h-stats",
            f"/tennis/v2/atp/h2h-vs-all/{PLAYER_ID}",
        ],
        api_key)

    # 5. getH2HStats - H2H detaille entre 2 joueurs
    test_endpoint("getH2HStats",
        [
            f"/tennis/v2/atp/h2h/{PLAYER_ID}/{OPPONENT_ID}/stats",
            f"/tennis/v2/atp/h2h-stats/{PLAYER_ID}/{OPPONENT_ID}",
            f"/tennis/v2/atp/h2h/{PLAYER_ID}/{OPPONENT_ID}",
            f"/tennis/v2/atp/h2h/stats/{PLAYER_ID}/{OPPONENT_ID}",
        ],
        api_key)

    # 6. getTourInfo - info tournoi
    test_endpoint("getTourInfo",
        [
            f"/tennis/v2/atp/tour/{TOURNAMENT_ID}",
            f"/tennis/v2/atp/tour-info/{TOURNAMENT_ID}",
            f"/tennis/v2/atp/tournament-info/{TOURNAMENT_ID}",
            f"/tennis/v2/atp/info/tournament/{TOURNAMENT_ID}",
            f"/tennis/v2/atp/tournament/{TOURNAMENT_ID}/info",
        ],
        api_key)


if __name__ == "__main__":
    main()
