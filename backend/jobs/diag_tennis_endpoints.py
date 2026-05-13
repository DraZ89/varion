"""
Diag : teste systematiquement tous les endpoints connus de Matchstat Tennis API.
Identifie ceux qui sont disponibles + leur structure de reponse.

Cout : ~15 req max (1 par endpoint teste).
Usage : python -m jobs.diag_tennis_endpoints
"""

import os
import urllib.request
import urllib.error
import json

API_HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
API_BASE = f"https://{API_HOST}/tennis/v2"

# Cibles : Sinner (47275), Mannarino (7806)
PLAYER_ID = 47275
TOURNAMENT_ID = 21326  # Rome ATP


def fetch(url, api_key, params=None):
    """Retourne (status, headers, body_text)."""
    if params:
        from urllib.parse import urlencode
        url = url + "?" + urlencode(params)
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": API_HOST,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, dict(e.headers), body


def show_keys(data, prefix="", depth=0, max_depth=3):
    """Affiche recursivement les cles d'un objet JSON."""
    if depth >= max_depth:
        return
    sp = "    " * depth
    if isinstance(data, dict):
        for k, v in list(data.items())[:15]:
            full = f"{prefix}.{k}" if prefix else k
            if isinstance(v, list):
                if v and isinstance(v[0], dict):
                    print(f"{sp}{k} : list[{len(v)}] de dicts")
                    if depth < max_depth - 1:
                        print(f"{sp}    [0] cles : {list(v[0].keys())[:12]}")
                else:
                    sample = v[0] if v else "?"
                    print(f"{sp}{k} : list[{len(v)}] = {repr(sample)[:40]}")
            elif isinstance(v, dict):
                print(f"{sp}{k} : dict cles={list(v.keys())[:8]}")
            else:
                print(f"{sp}{k} : {type(v).__name__} = {repr(v)[:60]}")


def test_endpoint(name, url, api_key, params=None):
    print(f"\n{'=' * 70}")
    print(f">>> {name}")
    print(f"    URL : {url}")
    if params:
        print(f"    params : {params}")
    status, headers, body = fetch(url, api_key, params=params)
    print(f"    Status : {status}")

    if status == 200:
        try:
            data = json.loads(body)
            print(f"    [OK] Reponse JSON :")
            show_keys(data, depth=1, max_depth=3)
        except Exception as e:
            print(f"    [WARN] JSON parse fail : {e}")
            print(f"    Body : {body[:300]}")
    elif status == 404:
        print(f"    [404] endpoint inexistant")
    else:
        print(f"    [FAIL] : {body[:200]}")


def main():
    print("=" * 70)
    print("DIAG : Tous les endpoints Matchstat Tennis API")
    print("=" * 70)

    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("ERREUR : RAPIDAPI_KEY non definie")
        return

    # ========== ENDPOINTS DEJA CONNUS (pour comparaison) ==========
    test_endpoint("[REF] ranking ATP", f"{API_BASE}/atp/ranking/singles/", api_key, params={"pageSize": 200})
    test_endpoint("[REF] fixtures ATP du jour", f"{API_BASE}/atp/fixtures/2026-05-06", api_key, params={"pageSize": 200})

    # ========== NOUVEAUX ENDPOINTS A TESTER ==========

    # PLAYER ENDPOINTS
    test_endpoint("Player profile complet",
        f"{API_BASE}/atp/player/{PLAYER_ID}/profile", api_key)

    test_endpoint("Player career stats",
        f"{API_BASE}/atp/player/{PLAYER_ID}/career", api_key)

    test_endpoint("Player titles",
        f"{API_BASE}/atp/player/{PLAYER_ID}/titles", api_key)

    test_endpoint("Player finals",
        f"{API_BASE}/atp/player/{PLAYER_ID}/finals", api_key)

    test_endpoint("Player matches",
        f"{API_BASE}/atp/player/{PLAYER_ID}/matches", api_key)

    test_endpoint("Player surface stats",
        f"{API_BASE}/atp/player/{PLAYER_ID}/surface", api_key)

    test_endpoint("Player stats serve",
        f"{API_BASE}/atp/player/{PLAYER_ID}/stats/serve", api_key)

    test_endpoint("Player stats return",
        f"{API_BASE}/atp/player/{PLAYER_ID}/stats/return", api_key)

    # TOURNAMENT ENDPOINTS
    test_endpoint("Tournament info",
        f"{API_BASE}/atp/tournament/{TOURNAMENT_ID}", api_key)

    test_endpoint("Tournament past champions",
        f"{API_BASE}/atp/tournament/{TOURNAMENT_ID}/champions", api_key)

    # H2H detail
    test_endpoint("H2H all-time entre 2 joueurs",
        f"{API_BASE}/atp/h2h/{PLAYER_ID}/7806", api_key)

    # MATCH STATS
    test_endpoint("Match stats (1ere fixture du jour)",
        f"{API_BASE}/atp/match/1237/stats", api_key)


if __name__ == "__main__":
    main()
