"""
Inspecte le cache des past_matches d'un joueur pour comprendre la structure
exacte de match_winner et debugger pourquoi Mannarino a 5 defaites consecutives.

Aucune requete API.
Usage : python -m jobs.inspect_past_matches
"""

import os
import sys
import json

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BACKEND_DIR, "cache")


def main():
    print("=" * 60)
    print("INSPECT cache past_matches")
    print("=" * 60)

    # Mannarino api_id = 7806
    target_pid = "7806"

    # Cherche le cache past_matches pour ce joueur
    files = []
    for fname in sorted(os.listdir(CACHE_DIR)):
        if "past" in fname and target_pid in fname:
            files.append(os.path.join(CACHE_DIR, fname))

    if not files:
        # Fallback : prend n'importe quel cache past_matches
        for fname in sorted(os.listdir(CACHE_DIR)):
            if "tennis_past_" in fname:
                files.append(os.path.join(CACHE_DIR, fname))
                break

    if not files:
        print("Aucun cache past_matches trouve.")
        print("\nFichiers cache tennis dispo :")
        for fname in sorted(os.listdir(CACHE_DIR)):
            if fname.startswith("tennis_"):
                print(f"  - {fname}")
        return

    path = files[0]
    print(f"Fichier inspecte : {os.path.basename(path)}\n")

    with open(path, "r", encoding="utf-8") as f:
        cache_entry = json.load(f)

    data = cache_entry.get("data", {})
    matches = data.get("data") or []

    print(f"Nb past_matches : {len(matches)}\n")

    if not matches:
        print("Liste vide.")
        return

    # Tri par date desc
    sorted_m = sorted(matches, key=lambda m: m.get("date") or "", reverse=True)

    print(">>> 3 PREMIERS MATCHS (les plus recents) :")
    for i, m in enumerate(sorted_m[:3], 1):
        print(f"\n--- MATCH {i} ---")
        print(f"  Cles dispo : {list(m.keys())[:20]}")
        print(f"  date : {m.get('date')}")
        print(f"  match_winner : {repr(m.get('match_winner'))} (type: {type(m.get('match_winner')).__name__})")
        print(f"  player1Id : {m.get('player1Id')}")
        print(f"  player2Id : {m.get('player2Id')}")

        p1 = m.get("player1") or {}
        p2 = m.get("player2") or {}
        print(f"  player1 : {p1.get('name', '?')} (id={p1.get('id')})")
        print(f"  player2 : {p2.get('name', '?')} (id={p2.get('id')})")

        # Champs lies au resultat
        for k in ["result", "score", "winner", "winnerId", "outcome"]:
            if k in m:
                print(f"  {k} : {repr(m[k])}")


if __name__ == "__main__":
    main()
