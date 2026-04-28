#!/usr/bin/env python3
"""
Vérifie et répare les logos invalides dans frontend/logos/.

Détecte :
- Les fichiers qui ne sont pas des SVG (ex: PNG renommé)
- Les fichiers manquants
- Les fichiers vides ou corrompus

Usage : python fix_logos.py
"""

import urllib.request
import urllib.error
import os
import time

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
    ],
    "MUN": [
        "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    ],
    "NEW": [
        "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
    ],
    "AVL": [
        # Plusieurs URLs alternatives - on essaie jusqu'a en trouver une qui marche
        "https://upload.wikimedia.org/wikipedia/en/9/9f/Aston_Villa_FC_new_crest.svg",
        "https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg",
        "https://upload.wikimedia.org/wikipedia/en/b/b9/Aston_Villa_FC_crest.svg",
        "https://upload.wikimedia.org/wikipedia/en/0/0a/Aston_Villa_FC_crest.svg",
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


def is_valid_svg_file(filepath):
    """Verifie qu'un fichier est un SVG valide (pas un PNG renomme)."""
    if not os.path.exists(filepath):
        return False, "fichier manquant"

    size = os.path.getsize(filepath)
    if size < 100:
        return False, f"trop petit ({size} octets)"

    try:
        with open(filepath, "rb") as f:
            head = f.read(500)
    except Exception as e:
        return False, f"lecture impossible: {e}"

    # Detecter PNG (commence par 89 50 4E 47)
    if head.startswith(b"\x89PNG"):
        return False, "c'est un PNG, pas un SVG"

    # Detecter JPEG (FF D8 FF)
    if head.startswith(b"\xff\xd8\xff"):
        return False, "c'est un JPEG, pas un SVG"

    # Doit commencer par <?xml ou <svg
    head_str = head.decode("utf-8", errors="ignore").strip().lower()
    if not (head_str.startswith("<?xml") or head_str.startswith("<svg")):
        return False, "ne commence pas par <?xml ou <svg"

    return True, "OK"


def fetch_url(url, max_retries=3):
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429 and attempt < max_retries:
                wait = 5 * attempt
                print(f"      rate limit, attente {wait}s...")
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


def download_logo(team_id, urls):
    """Telecharge un logo en essayant les URLs successives."""
    dest_path = os.path.join(DEST_DIR, f"{team_id}.svg")

    for i, url in enumerate(urls):
        try:
            label = "" if i == 0 else f" [URL alt {i}]"
            data = fetch_url(url)

            # Verifier que ce n'est pas un PNG/JPEG
            if data[:4] == b"\x89PNG":
                print(f"  KO {team_id}.svg{label} : URL renvoie un PNG")
                continue
            if data[:3] == b"\xff\xd8\xff":
                print(f"  KO {team_id}.svg{label} : URL renvoie un JPEG")
                continue

            head_str = data[:200].decode("utf-8", errors="ignore").strip().lower()
            if not (head_str.startswith("<?xml") or head_str.startswith("<svg")):
                print(f"  KO {team_id}.svg{label} : pas un SVG")
                continue

            with open(dest_path, "wb") as f:
                f.write(data)

            size_kb = len(data) / 1024
            print(f"  OK {team_id}.svg ({size_kb:.1f} KB){label}")
            return True

        except urllib.error.HTTPError as e:
            print(f"  KO {team_id}.svg{label} : HTTP {e.code}")
        except Exception as e:
            print(f"  KO {team_id}.svg{label} : {e}")

    return False


def main():
    print(f"Verification de {DEST_DIR}\n")

    to_fix = []
    ok = 0

    for team_id in LOGOS.keys():
        path = os.path.join(DEST_DIR, f"{team_id}.svg")
        valid, reason = is_valid_svg_file(path)
        if valid:
            print(f"  OK {team_id}.svg")
            ok += 1
        else:
            print(f"  KO {team_id}.svg : {reason}")
            to_fix.append(team_id)

    print(f"\n{ok}/{len(LOGOS)} logos valides.")

    if not to_fix:
        print("\nTout est en ordre, rien a reparer.")
        return

    print(f"\nReparation de {len(to_fix)} logo(s) : {', '.join(to_fix)}\n")

    for i, team_id in enumerate(to_fix):
        # Supprimer le fichier invalide
        path = os.path.join(DEST_DIR, f"{team_id}.svg")
        if os.path.exists(path):
            os.remove(path)

        download_logo(team_id, LOGOS[team_id])

        # Delai entre requetes (anti rate-limit)
        if i < len(to_fix) - 1:
            time.sleep(1.5)

    # Re-verification finale
    print("\nVerification finale :")
    final_ok = 0
    final_failed = []
    for team_id in to_fix:
        path = os.path.join(DEST_DIR, f"{team_id}.svg")
        valid, reason = is_valid_svg_file(path)
        if valid:
            print(f"  OK {team_id}.svg")
            final_ok += 1
        else:
            print(f"  KO {team_id}.svg : {reason}")
            final_failed.append(team_id)

    if final_failed:
        print(f"\n{len(final_failed)} logo(s) toujours en echec : {', '.join(final_failed)}")
        print("\nSolution manuelle :")
        print("1. Va sur https://en.wikipedia.org/wiki/" + final_failed[0].replace("_", "%20"))
        print("2. Click droit sur le crest -> 'Enregistrer l'image sous'")
        print("3. Format SVG, place dans frontend/logos/ avec le nom " + final_failed[0] + ".svg")
    else:
        print(f"\nTous les logos sont maintenant valides !")


if __name__ == "__main__":
    main()
