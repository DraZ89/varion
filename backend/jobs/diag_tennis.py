"""
Diagnostic direct API Tennis Matchstat.
Fait 1 seul appel API minimal pour valider l'auth.

Usage : python -m jobs.diag_tennis
"""

import os
import sys
import urllib.request
import urllib.error
import json

API_HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
API_BASE = f"https://{API_HOST}/tennis/v2"


def main():
    print("=" * 60)
    print("DIAG Tennis API Matchstat")
    print("=" * 60)

    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("ERREUR : RAPIDAPI_KEY non definie")
        return

    # Afficher les 8 premiers + 4 derniers caracteres pour confirmer la cle (sans l'exposer)
    masked = f"{api_key[:8]}...{api_key[-4:]}"
    print(f"Cle utilisee : {masked} (longueur {len(api_key)})")
    print(f"Host : {API_HOST}")
    print()

    # Test : ranking ATP singles (le 1er endpoint qui plante)
    url = f"{API_BASE}/atp/ranking/singles/"
    print(f">>> Test : GET {url}")
    print(f"    Headers :")
    print(f"      X-RapidAPI-Key: {masked}")
    print(f"      X-RapidAPI-Host: {API_HOST}")

    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": API_HOST,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"\n    OK Status : {resp.status}")
            data = json.loads(resp.read().decode("utf-8"))
            print(f"    Response keys : {list(data.keys())}")
            rankings = data.get("data", [])
            print(f"    {len(rankings)} joueurs dans le ranking")
            if rankings:
                first = rankings[0]
                player = first.get("player", {})
                print(f"    #1 : {player.get('name')} ({player.get('countryAcr')})")
            print("\n    >> CLE VALIDE pour Tennis API")

    except urllib.error.HTTPError as e:
        print(f"\n    KO Status : {e.code} {e.reason}")
        # Lire le body de l'erreur
        try:
            body = e.read().decode("utf-8")
            print(f"    Response body :")
            print(f"    {body[:500]}")
        except Exception:
            pass

        if e.code == 401:
            print("\n    >> 401 Unauthorized : la cle est rejetee")
        elif e.code == 403:
            print("\n    >> 403 Forbidden :")
            print("       - Soit pas d'abonnement actif sur cette API")
            print("       - Soit cle d'une autre app que celle abonnee")
            print("       - Soit quota epuise (verifier les 500 req/mois)")
        elif e.code == 429:
            print("\n    >> 429 : rate limit hit (1000 req/heure)")

    except Exception as e:
        print(f"\n    KO erreur reseau : {e}")


if __name__ == "__main__":
    main()
