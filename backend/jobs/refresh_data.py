"""
Job de rafraîchissement des données.

Workflow :
1. Récupère les standings + matchs à venir pour les 5 ligues
2. Identifie les équipes qui jouent dans les 7 prochains jours
3. Récupère les stats détaillées + effectif de ces équipes uniquement
4. Calcule les analyses Varion
5. Écrit le tout dans frontend/data.json

Optimisation quota :
- Cache 24h sur tous les endpoints
- On ne récupère pas les stats de TOUTES les équipes, seulement celles qui jouent
- Estimation : 50-70 requêtes/jour pour 5 ligues

Usage :
    python -m jobs.refresh_data           # mode normal (utilise le cache)
    python -m jobs.refresh_data --force   # ignore le cache, redownload tout
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, List

# Ajouter le repertoire backend au path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from providers.api_football import APIFootball, LEAGUES
from providers import mapper, cache


# Limites pour optimiser les requetes
# Plan payant : 7500 req/jour, pas de limite minute -> tu peux monter MAX_TEAMS plus haut
MAX_TEAMS_PER_LEAGUE = 8  # nb equipes prises en compte par ligue
MAX_PLAYERS_PER_TEAM = 0  # 0 = on ne fetch pas les joueurs encore (a faire plus tard)

# Mode demo : pour le free tier qui n'a pas acces a la saison actuelle
# Plan payant : laisser False, on utilise les vrais matchs a venir
DEMO_MODE = False


def main(force: bool = False):
    print("=" * 60)
    print("VARION - Refresh data depuis API-Football")
    print("=" * 60)

    if force:
        print("Mode FORCE : on ignore le cache")
        cache.clear()

    api = APIFootball()
    cache_stats = cache.stats()
    print(f"Cache : {cache_stats['entries']} entrees, {cache_stats['size_kb']} KB")
    print()

    teams_internal = {}        # id_internal -> data team mappee
    matches_internal = []      # liste fixtures mappees
    team_id_map = {}           # api_id -> id_internal

    # Etape 1 : standings + matchs a venir pour chaque ligue
    print(">>> Etape 1 : Standings + matchs a venir des 5 ligues")
    league_standings = {}
    league_fixtures = {}

    for league_short, info in LEAGUES.items():
        print(f"  - {info['name']} ({league_short})")
        try:
            standings = api.get_standings(info["id"])
            if DEMO_MODE:
                # Mode demo : derniers matchs joues (saison terminee)
                fixtures = api.get_fixtures_recent(info["id"], last=8)
                print(f"    [DEMO] {len(standings)} equipes au classement, {len(fixtures)} derniers matchs joues")
            else:
                fixtures = api.get_fixtures_upcoming(info["id"], days_ahead=7)
                print(f"    {len(standings)} equipes au classement, {len(fixtures)} matchs a venir")
            league_standings[league_short] = standings
            league_fixtures[league_short] = fixtures
        except Exception as e:
            print(f"    ERREUR : {e}")
            league_standings[league_short] = []
            league_fixtures[league_short] = []

    # Etape 2 : pour chaque ligue, identifier les equipes qui jouent
    print("\n>>> Etape 2 : Identification des equipes prioritaires")
    teams_to_fetch = {}  # league_short -> set of (team_api_id, team_name)

    for league_short, fixtures in league_fixtures.items():
        team_ids = set()
        for fix in fixtures[:10]:  # 10 premiers matchs max
            home = fix.get("teams", {}).get("home", {}).get("id")
            away = fix.get("teams", {}).get("away", {}).get("id")
            if home: team_ids.add(home)
            if away: team_ids.add(away)
        teams_to_fetch[league_short] = list(team_ids)[:MAX_TEAMS_PER_LEAGUE]
        print(f"  {league_short} : {len(teams_to_fetch[league_short])} equipes")

    # Etape 3 : recuperer stats detaillees de chaque equipe
    print("\n>>> Etape 3 : Stats detaillees par equipe")
    daily_quota_hit = False
    for league_short, team_api_ids in teams_to_fetch.items():
        if daily_quota_hit:
            break
        league_id = LEAGUES[league_short]["id"]
        for team_api_id in team_api_ids:
            if daily_quota_hit:
                break
            try:
                stats_resp = api.get_team_statistics(team_api_id, league_id)
                if not stats_resp:
                    continue

                # Trouver l'entry dans standings pour avoir rank/points/form
                standing_entry = None
                for s in league_standings.get(league_short, []):
                    if s.get("team", {}).get("id") == team_api_id:
                        standing_entry = s
                        break
                if not standing_entry:
                    standing_entry = {"rank": 0, "points": 0, "form": ""}

                team_data = mapper.map_team(stats_resp, standing_entry, league_short)
                # Generer un id court interne (3 lettres du nom)
                short_id = team_data["short"][:3].upper().replace(" ", "")
                # Eviter les collisions
                while short_id in teams_internal:
                    short_id = short_id + "X"
                team_data["id"] = short_id
                teams_internal[short_id] = team_data
                team_id_map[team_api_id] = short_id
                print(f"  OK {team_data['name']} (#{team_data['rank']})")
            except Exception as e:
                err_msg = str(e)
                if "Quota journalier" in err_msg or "RateLimitDaily" in type(e).__name__:
                    print(f"  STOP : quota journalier epuise. On arrete les requetes.")
                    daily_quota_hit = True
                    break
                print(f"  KO team {team_api_id} : {e}")

    # Etape 4 : mapper les fixtures
    print("\n>>> Etape 4 : Mapping des matchs a venir")
    for league_short, fixtures in league_fixtures.items():
        for fix in fixtures:
            mapped = mapper.map_fixture(fix, team_id_map)
            if mapped:
                matches_internal.append(mapped)
    print(f"  {len(matches_internal)} matchs mappes")

    # Etape 5 : H2H pour chaque match
    print("\n>>> Etape 5 : H2H pour chaque match")
    h2h_data = {}
    for m in matches_internal[:10]:  # limite pour eviter trop de requetes
        # Retrouver les API IDs
        home_api = teams_internal[m["home"]].get("api_id")
        away_api = teams_internal[m["away"]].get("api_id")
        if home_api and away_api:
            try:
                h2h_resp = api.get_h2h(home_api, away_api, last=5)
                h2h_data[(m["home"], m["away"])] = mapper.map_h2h(h2h_resp, home_api)
            except Exception as e:
                print(f"  H2H {m['home']} vs {m['away']} : {e}")

    # Etape 6 : Calculer les analyses Varion (engine)
    print("\n>>> Etape 6 : Calcul des analyses Varion")

    # Injecter les donnees dans les modules data/ pour que l'engine les utilise
    from data import teams as teams_module
    from data import matches as matches_module

    teams_module.TEAMS = teams_internal
    matches_module.UPCOMING_MATCHES = matches_internal
    matches_module.H2H = h2h_data

    # Joueurs : on les laisse vides pour l'instant (free tier)
    from data import players as players_module
    players_module.PLAYERS = []

    # Now run the analysis
    from engine.football.team_analysis import calculate_team_overall
    from engine.football.predictions import predict_match
    from engine.football.value_bets import detect_value_bets
    from engine.football.summary import generate_match_summary, confidence_score
    from engine.football.player_analysis import analyze_team_players, analyze_goalkeeper, detect_key_players_to_watch
    from data.players import get_lineup_starters

    output = {
        "teams": [],
        "matches_summary": [],
        "matches_full": {},
        "value_bets": [],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    for tid, t in teams_internal.items():
        output["teams"].append({
            "id": tid,
            "name": t["name"],
            "short": t["short"],
            "rank": t["rank"],
            "points": t["points"],
            "logo_color": t["logo_color"],
            "logo_url": t.get("logo_url"),
        })

    all_value_bets = []
    for m in matches_internal:
        home_id, away_id = m["home"], m["away"]
        if home_id not in teams_internal or away_id not in teams_internal:
            continue
        home, away = teams_internal[home_id], teams_internal[away_id]

        try:
            home_overall = calculate_team_overall(home_id, True)
            away_overall = calculate_team_overall(away_id, False)
            ctx = {
                "ref_yellow_avg": m["ref_yellow_avg"],
                "is_derby": m["is_derby"],
                "stakes": m["stakes"],
            }
            preds = predict_match(home_id, away_id, ctx)
            home_players = analyze_team_players(home_id, away_overall["defense_score"], True)
            away_players = analyze_team_players(away_id, home_overall["defense_score"], False)
            bets = detect_value_bets(preds, m["odds"], home_players + away_players)
            key_h = detect_key_players_to_watch(home_id, away_overall["defense_score"], True, 4)
            key_a = detect_key_players_to_watch(away_id, home_overall["defense_score"], False, 4)
            summary = generate_match_summary(home_id, away_id, home_overall, away_overall, preds, bets, key_h, key_a)
            conf = confidence_score(preds, bets)

            output["matches_summary"].append({
                "id": m["id"],
                "date": m["date"],
                "kickoff": m["kickoff"],
                "competition": m["competition"],
                "venue": m["venue"],
                "is_derby": m["is_derby"],
                "stakes": m["stakes"],
                "home": {"id": home_id, "name": home["name"], "short": home["short"],
                         "logo_color": home["logo_color"], "logo_url": home.get("logo_url"),
                         "rank": home["rank"]},
                "away": {"id": away_id, "name": away["name"], "short": away["short"],
                         "logo_color": away["logo_color"], "logo_url": away.get("logo_url"),
                         "rank": away["rank"]},
                "odds_main": {"1": m["odds"]["1"], "X": m["odds"]["X"], "2": m["odds"]["2"]},
                "predictions_summary": {
                    "prob_home": preds["result"]["prob_home_win"],
                    "prob_draw": preds["result"]["prob_draw"],
                    "prob_away": preds["result"]["prob_away_win"],
                    "expected_goals": preds["over_under_25"]["expected_total"],
                    "expected_corners": preds["corners"]["expected_total"],
                    "expected_cards": preds["cards"]["expected_total"],
                    "btts_prob": preds["btts"]["prob_yes"],
                    "intensity": preds["intensity_score"],
                    "most_likely_score": preds["result"]["most_likely_score"],
                },
                "top_value_bet": bets[0] if bets else None,
                "value_bets_count": len(bets),
                "confidence_score": conf,
            })

            starters_home = get_lineup_starters(home_id, 11)
            starters_away = get_lineup_starters(away_id, 11)
            gk_home = analyze_goalkeeper(home_id)
            gk_away = analyze_goalkeeper(away_id)
            h2h = h2h_data.get((home_id, away_id), [])

            output["matches_full"][m["id"]] = {
                "id": m["id"], "date": m["date"], "kickoff": m["kickoff"],
                "venue": m["venue"], "competition": m["competition"],
                "referee": m["referee"], "is_derby": m["is_derby"], "stakes": m["stakes"],
                "summary": summary, "confidence_score": conf,
                "teams": {
                    "home": {"info": home, "scores": home_overall, "goalkeeper": gk_home,
                             "starters": [{"id": p["id"], "name": p["name"], "pos": p["pos"], "starts": p["starts"]} for p in starters_home],
                             "key_players": key_h, "all_players": home_players},
                    "away": {"info": away, "scores": away_overall, "goalkeeper": gk_away,
                             "starters": [{"id": p["id"], "name": p["name"], "pos": p["pos"], "starts": p["starts"]} for p in starters_away],
                             "key_players": key_a, "all_players": away_players},
                },
                "predictions": preds, "odds": m["odds"], "value_bets": bets, "h2h": h2h,
            }

            for b in bets:
                if b["edge_pct"] >= 5:
                    all_value_bets.append({**b,
                        "match_id": m["id"],
                        "match_label": f"{home['short']} vs {away['short']}",
                        "match_date": m["date"], "match_kickoff": m["kickoff"]})

        except Exception as e:
            print(f"  KO analyse {home_id} vs {away_id} : {e}")

    all_value_bets.sort(key=lambda b: -b["edge_pct"])
    output["value_bets"] = all_value_bets

    # Etape 7 : ecrire data.json
    output_path = os.path.join(BACKEND_DIR, "..", "frontend", "data.json")
    output_path = os.path.normpath(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, default=str, ensure_ascii=False)

    size_kb = os.path.getsize(output_path) / 1024

    print("\n" + "=" * 60)
    print(f"OK Refresh termine")
    print(f"   {len(output['teams'])} equipes")
    print(f"   {len(output['matches_summary'])} matchs analyses")
    print(f"   {len(output['value_bets'])} value bets detectes")
    print(f"   Fichier : {output_path} ({size_kb:.1f} KB)")
    print(f"   Requetes API : {api.calls_made}")
    print(f"   Cache : {cache.stats()}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Vider le cache et tout retelecharger")
    args = parser.parse_args()
    main(force=args.force)
