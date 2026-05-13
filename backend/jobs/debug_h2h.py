"""
Debug : inspecte le cache pour voir la VRAIE structure de /h2h/events.

On a vu dans le test multi :
- /h2h (summary) marche : { teamDuel: { homeWins, awayWins, draws } }
- /h2h/events retourne 0 matchs alors qu'il devrait en avoir

Probablement ma fonction map_h2h_events cherche au mauvais endroit.

Aucune requete API : on lit le cache local.
"""

import os
import sys
import json

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

CACHE_DIR = os.path.join(BACKEND_DIR, "cache")


def main():
    print("=" * 60)
    print("DEBUG - Inspection cache /h2h/events")
    print("=" * 60)

    if not os.path.exists(CACHE_DIR):
        print("Pas de dossier cache.")
        return

    # On cherche specifiquement les fichiers h2h_events
    h2h_events_files = []
    h2h_summary_files = []

    for fname in os.listdir(CACHE_DIR):
        if not fname.endswith(".json"):
            continue
        if "h2h_events" in fname:
            h2h_events_files.append(os.path.join(CACHE_DIR, fname))
        elif "h2h_summary" in fname or ("h2h" in fname and "events" not in fname):
            h2h_summary_files.append(os.path.join(CACHE_DIR, fname))

    print(f"\nCaches trouves :")
    print(f"  /h2h/events : {len(h2h_events_files)} fichiers")
    print(f"  /h2h (summary) : {len(h2h_summary_files)} fichiers")

    if not h2h_events_files:
        print("\nKO : aucun cache h2h_events trouve.")
        print("    Liste de tous les fichiers cache :")
        for fname in sorted(os.listdir(CACHE_DIR)):
            if fname.endswith(".json"):
                print(f"      - {fname}")
        return

    # Inspecter chaque cache /h2h/events
    for path in h2h_events_files[:3]:
        fname = os.path.basename(path)
        print(f"\n{'='*60}")
        print(f"FICHIER : {fname}")
        print(f"{'='*60}")

        with open(path, "r", encoding="utf-8") as f:
            cache_entry = json.load(f)

        data = cache_entry.get("data", {})

        print(f"\nType de 'data' : {type(data).__name__}")

        if isinstance(data, dict):
            print(f"Cles de niveau 1 : {list(data.keys())}")
            print()
            for key, value in data.items():
                if isinstance(value, list):
                    print(f"  '{key}' : LIST de {len(value)} elements")
                    if value:
                        first = value[0]
                        if isinstance(first, dict):
                            print(f"    1er element keys : {list(first.keys())[:15]}")
                            # Verifier si c'est bien un event (a des champs typiques)
                            if "homeTeam" in first or "startTimestamp" in first:
                                print(f"    -> C'EST BIEN UN EVENT")
                                home = first.get("homeTeam", {}).get("name", "?")
                                away = first.get("awayTeam", {}).get("name", "?")
                                ts = first.get("startTimestamp", 0)
                                print(f"    Sample : {home} vs {away} (ts={ts})")
                        else:
                            print(f"    type 1er element : {type(first).__name__}")
                elif isinstance(value, dict):
                    sub_keys = list(value.keys())[:10]
                    print(f"  '{key}' : DICT avec keys {sub_keys}")
                else:
                    print(f"  '{key}' : {type(value).__name__} = {repr(value)[:60]}")
        elif isinstance(data, list):
            print(f"data est une LISTE de {len(data)} elements")
            if data:
                first = data[0]
                if isinstance(first, dict):
                    print(f"  1er element keys : {list(first.keys())[:15]}")
                    if "homeTeam" in first:
                        home = first.get("homeTeam", {}).get("name", "?")
                        away = first.get("awayTeam", {}).get("name", "?")
                        print(f"  Sample : {home} vs {away}")
        else:
            print(f"Type unexpected : {type(data)}")

        # Dump JSON tronque
        print(f"\n--- DUMP JSON (premiers 2000 chars) ---")
        dump = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        print(dump[:2000])
        if len(dump) > 2000:
            print(f"\n... ({len(dump) - 2000} chars supplementaires)")


if __name__ == "__main__":
    main()
