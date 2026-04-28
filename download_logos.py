#!/usr/bin/env python3
"""
Télécharge les logos SVG officiels des clubs de Premier League depuis Wikipedia.

Améliorations :
- Délai entre requêtes (anti rate-limit Wikipedia)
- Retries automatiques en cas d'erreur 429
- URLs de secours si la principale ne marche pas
- Vérification que le fichier téléchargé est bien un SVG valide

Usage : python download_logos.py
"""

import urllib.request
import urllib.error
import os
import sys
import time

# URLs principales + URLs de secours pour chaque club
LOGOS = {
    "MCI": [
        "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    ],
    "ARS": [
        "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    ],
    "LIV": [
        "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
    ],
    "CHE": [
        "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    ],
    "TOT": [
        "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg",
        "https://upload.wikimedia.org/wikipedia/commons/b/b4/Tottenham_Hotspur.svg",
    ],
    "MUN": [
        "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    ],
    "NEW": [
        "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
    ],
    "AVL": [
        # URL alternatives - la principale a renvoye 404
        "https://upload.wikimedia.org/wikipedia/en/9/9f/Aston_Villa_FC_new_crest.svg",
        "https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg",
        "https://upload.wikimedia.org/wikipedia/en/b/b9/Aston_Villa_FC_crest.svg",
    ],
    "BHA": [
        "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg",
    ],
    "WHU": [
        "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg",
    ],
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = os.path.join(SCRIPT_DIR, "frontend", "logos")
os.makedirs(DEST_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Varion-BettingApp/1.0 (educational project)"
}

DELAY_BETWEEN_REQUESTS = 1.5
MAX_RETRIES = 3
RETRY_BACKOFF = 5


def is_valid_svg(data: bytes) -> bool:
    head = data[:200].decode("utf-8", errors="ignore").strip().lower()
    return "<svg" in head or "<?xml" in head


def fetch_url(url: str, max_retries: int = MAX_RETRIES) -> bytes:
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429 and attempt < max_retries:
                wait = RETRY_BACKOFF * attempt
                print(f"      rate limit, attente {wait}s avant retry {attempt + 1}/{max_retries}...")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(2)
                continue
            raise
    if last_err:
        raise last_err


def download(team_id: str, urls: list) -> bool:
    filename = f"{team_id}.svg"
    dest_path = os.path.join(DEST_DIR, filename)

    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100:
        with open(dest_path, "rb") as f:
            existing = f.read()
        if is_valid_svg(existing):
            print(f"  OK {filename} (deja present)")
            return True

    for i, url in enumerate(urls):
        try:
            label = "" if i == 0 else f" [URL alt {i}]"
            data = fetch_url(url)

            if not is_valid_svg(data):
                print(f"  WARN {filename}: contenu pas SVG valide{label}")
                continue

            with open(dest_path, "wb") as f:
                f.write(data)

            size_kb = len(data) / 1024
            print(f"  OK {filename}  ({size_kb:.1f} KB){label}")
            return True
        except urllib.error.HTTPError as e:
            print(f"  KO {filename}{label}  HTTP {e.code}")
        except Exception as e:
            print(f"  KO {filename}{label}  {e}")

    print(f"  ECHEC {filename}  toutes les URLs ont echoue")
    return False


def main():
    print(f"Telechargement des {len(LOGOS)} logos officiels Premier League")
    print(f"Destination : {DEST_DIR}")
    print(f"Delai anti rate-limit : {DELAY_BETWEEN_REQUESTS}s entre requetes\n")

    success = 0
    failed_teams = []
    items = list(LOGOS.items())

    for i, (team_id, urls) in enumerate(items):
        if download(team_id, urls):
            success += 1
        else:
            failed_teams.append(team_id)

        if i < len(items) - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    print(f"\n{success}/{len(LOGOS)} logos telecharges.")

    if failed_teams:
        print(f"\nEchec pour : {', '.join(failed_teams)}")
        print("\nSolutions :")
        print("  1. Relance le script (souvent ca suffit apres quelques minutes)")
        print("     python download_logos.py")
        print("\n  2. Ou telecharge manuellement depuis ton navigateur :")
        for tid in failed_teams:
            for url in LOGOS[tid]:
                print(f"     {tid}: {url}")
                break
        print(f"\n  Place les fichiers dans : {DEST_DIR}")
        print(f"  Renomme-les {failed_teams[0]}.svg, etc.")


if __name__ == "__main__":
    main()
