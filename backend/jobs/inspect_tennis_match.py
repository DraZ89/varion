"""
Inspecte EN DETAIL le contenu d'un match tennis pour debug.
Aucune requete API.

Usage : python -m jobs.inspect_tennis_match
"""

import os
import sys
import json

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.normpath(os.path.join(BACKEND_DIR, "..", "frontend"))


def main():
    print("=" * 60)
    print("INSPECT data_tennis.json en detail")
    print("=" * 60)

    path = os.path.join(FRONTEND_DIR, "data_tennis.json")
    if not os.path.exists(path):
        print(f"KO : {path} introuvable")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = data.get("matches") or []
    if not matches:
        print("KO : 0 match dans le fichier")
        return

    m = matches[0]
    print("\n>>> 1ER MATCH COMPLET (dump JSON pretty):")
    print(json.dumps(m, indent=2, ensure_ascii=False, default=str)[:5000])
    print()

    # Focus joueurs
    print("\n>>> FOCUS PLAYER A :")
    pa = m.get("player_a", {})
    print(json.dumps(pa, indent=2, ensure_ascii=False, default=str)[:1500])

    print("\n>>> FOCUS PLAYER B :")
    pb = m.get("player_b", {})
    print(json.dumps(pb, indent=2, ensure_ascii=False, default=str)[:1500])

    # Focus predictions
    print("\n>>> FOCUS PREDICTIONS :")
    preds = m.get("predictions", {})
    if preds:
        print(json.dumps(preds, indent=2, ensure_ascii=False, default=str)[:2000])
    else:
        print("AUCUNE prediction !")

    # Focus odds
    print("\n>>> FOCUS ODDS :")
    odds = m.get("odds", {})
    print(json.dumps(odds, indent=2, ensure_ascii=False, default=str))

    # Focus value bets
    print("\n>>> FOCUS VALUE BETS du match :")
    bets = m.get("value_bets", [])
    print(f"  Nb : {len(bets)}")
    for b in bets:
        print(f"  {json.dumps(b, indent=2, ensure_ascii=False, default=str)}")


if __name__ == "__main__":
    main()
