"""
Verification rapide du contenu de data.json et data_tennis.json.
Aucune requete API.

Usage : python -m jobs.check_data_files
"""

import os
import sys
import json

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.normpath(os.path.join(BACKEND_DIR, "..", "frontend"))


def show_keys(obj, indent=0, max_depth=2, current_depth=0):
    if current_depth >= max_depth:
        return
    sp = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, list):
                if v and isinstance(v[0], dict):
                    print(f"{sp}{k} : liste de {len(v)} dicts")
                    if current_depth + 1 < max_depth:
                        print(f"{sp}  [0] keys : {list(v[0].keys())[:10]}")
                else:
                    print(f"{sp}{k} : liste de {len(v)} {type(v[0]).__name__ if v else 'rien'}")
            elif isinstance(v, dict):
                print(f"{sp}{k} : dict avec keys {list(v.keys())[:8]}")
                if current_depth + 1 < max_depth:
                    show_keys(v, indent + 1, max_depth, current_depth + 1)
            else:
                val_str = repr(v)[:50]
                print(f"{sp}{k} : {type(v).__name__} = {val_str}")


def check_file(label, path, expected_match_keys=None):
    print(f"\n{'=' * 60}")
    print(f"{label} : {path}")
    print('=' * 60)

    if not os.path.exists(path):
        print(f"KO : fichier inexistant")
        return None

    size_kb = os.path.getsize(path) / 1024
    print(f"Taille : {size_kb:.1f} KB")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nCles de niveau 1 :")
    show_keys(data, max_depth=1)

    return data


def main():
    print("=" * 60)
    print("CHECK data.json + data_tennis.json")
    print("=" * 60)

    # Foot
    foot_data = check_file("FOOT data.json", os.path.join(FRONTEND_DIR, "data.json"))

    if foot_data:
        matches = foot_data.get("matches_summary") or []
        print(f"\nFOOT matches_summary : {len(matches)} match(s)")
        if matches:
            m = matches[0]
            print(f"  Cles 1er match : {list(m.keys())[:15]}")
            print(f"  date : {repr(m.get('date'))}")
            print(f"  kickoff : {repr(m.get('kickoff'))}")
            home = m.get("home") or {}
            away = m.get("away") or {}
            print(f"  home : {home.get('name')} (short={home.get('short')}, color={home.get('logo_color')})")
            print(f"  away : {away.get('name')} (short={away.get('short')}, color={away.get('logo_color')})")
            print(f"  competition : {m.get('competition')}")
            print(f"  value_bets_count : {m.get('value_bets_count')}")

    # Tennis
    tennis_data = check_file("TENNIS data_tennis.json", os.path.join(FRONTEND_DIR, "data_tennis.json"))

    if tennis_data:
        matches = tennis_data.get("matches") or []
        print(f"\nTENNIS matches : {len(matches)} match(s)")
        if matches:
            m = matches[0]
            print(f"  Cles 1er match : {list(m.keys())[:20]}")
            print(f"  date : {repr(m.get('date'))}")
            print(f"  time : {repr(m.get('time'))}")
            print(f"  tour : {repr(m.get('tour'))}")
            print(f"  tournament : {repr(m.get('tournament'))}")
            p_a = m.get("player_a") or {}
            p_b = m.get("player_b") or {}
            print(f"  player_a : {p_a.get('name')} (id={p_a.get('id')}, country={p_a.get('country_code')})")
            print(f"  player_b : {p_b.get('name')} (id={p_b.get('id')}, country={p_b.get('country_code')})")
            print(f"  value_bets count : {len(m.get('value_bets') or [])}")
        else:
            print(f"  KO : matches est vide ou absent")
            print(f"  Cles top : {list(tennis_data.keys())}")


if __name__ == "__main__":
    main()
