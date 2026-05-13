"""
Plan B : tester variantes d'URLs pour les endpoints joueur.
Cout : ~6 req max
Usage : python -m jobs.diag_tennis_endpoints_v2
"""

import os
import urllib.request
import urllib.error
import json

API_HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
API_BASE = f"https://{API_HOST}/tennis/v2"
API_BASE_V1 = f"https://{API_HOST}/tennis/v1"
PLAYER_ID = 7806  # Mannarino


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


def test(name, url, api_key):
    print(f"\n>>> {name}")
    print(f"    URL : {url}")
    status, body = fetch(url, api_key)
    print(f"    Status : {status}")
    if status == 200:
        try:
            d = json.loads(body)
            if isinstance(d, dict):
                print(f"    [OK] keys = {list(d.keys())[:10]}")
                # Print first 500 chars of body
                preview = json.dumps(d, ensure_ascii=False, default=str)[:500]
                print(f"    Body preview : {preview}")
        except Exception:
            print(f"    Body : {body[:300]}")
    else:
        print(f"    Body : {body[:150]}")


def main():
    print("=" * 60)
    print("DIAG v2 : variantes URL")
    print("=" * 60)

    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("ERREUR : RAPIDAPI_KEY non definie")
        return

    # Variantes "players" plural
    test("players plural", f"{API_BASE}/atp/players/{PLAYER_ID}", api_key)

    # Tour-summary endpoint suspect
    test("tour-summary", f"{API_BASE}/atp/tour-summary/{PLAYER_ID}", api_key)

    # Stats endpoint suspect
    test("year-stats", f"{API_BASE}/atp/year-stats/{PLAYER_ID}", api_key)

    # Career endpoint
    test("career direct", f"{API_BASE}/atp/career/{PLAYER_ID}", api_key)

    # Tournaments endpoint
    test("tournaments list", f"{API_BASE}/atp/tournaments", api_key)

    # V1 ?
    test("v1 player", f"{API_BASE_V1}/atp/player/{PLAYER_ID}", api_key)


if __name__ == "__main__":
    main()
