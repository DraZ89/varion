"""
Diagnostic : trouver le bon parametre pour recuperer le Top 200 ATP.
On teste plusieurs noms de parametres courants : limit, size, top, count, etc.

Cout : 4 req max, on s'arrete au 1er qui marche.
Usage : python -m jobs.diag_tennis_pagination
"""

import os
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
        return e.code, {"_error": e.reason, "_body": body[:200]}


def main():
    print("=" * 60)
    print("DIAG Tennis - Recherche du parametre Top N")
    print("=" * 60)

    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("ERREUR : RAPIDAPI_KEY non definie")
        return

    # On teste les variantes les plus courantes
    test_urls = [
        ("Sans parametre", f"{API_BASE}/atp/ranking/singles/"),
        ("?top=200", f"{API_BASE}/atp/ranking/singles/?top=200"),
        ("?limit=200", f"{API_BASE}/atp/ranking/singles/?limit=200"),
        ("?size=200", f"{API_BASE}/atp/ranking/singles/?size=200"),
        ("?count=200", f"{API_BASE}/atp/ranking/singles/?count=200"),
        ("?page=1&limit=200", f"{API_BASE}/atp/ranking/singles/?page=1&limit=200"),
        ("?pageSize=200", f"{API_BASE}/atp/ranking/singles/?pageSize=200"),
        ("/200", f"{API_BASE}/atp/ranking/singles/200"),
        ("/top/200", f"{API_BASE}/atp/ranking/singles/top/200"),
    ]

    for label, url in test_urls:
        print(f"\n>>> {label}")
        print(f"   URL : {url}")
        status, data = fetch(url, api_key)
        print(f"   Status : {status}")
        if status == 200 and isinstance(data, dict):
            d = data.get("data") or []
            count = len(d) if isinstance(d, list) else 0
            print(f"   data : {count} elements")
            if count > 11:
                print(f"   *** WIN ! On a > 11 elements avec '{label}' ***")
                if d:
                    last = d[-1]
                    pos = last.get("position") or last.get("rank")
                    pname = (last.get("player") or {}).get("name", "?")
                    print(f"   Dernier element : #{pos} {pname}")
                return
            elif count > 0:
                last = d[-1]
                pos = last.get("position") or last.get("rank")
                print(f"   Dernier rank : {pos}")
        else:
            err = data.get("_error", "?") if isinstance(data, dict) else str(data)
            body = data.get("_body", "") if isinstance(data, dict) else ""
            print(f"   KO : {err}")
            if body:
                print(f"   Body : {body}")

    print("\n>>> Aucun parametre n'a permis d'avoir plus de 11 joueurs")
    print(">>> Probable : limite imposee par le plan free")


if __name__ == "__main__":
    main()
