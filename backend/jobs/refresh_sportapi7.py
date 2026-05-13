"""
Job de refresh foot via SportAPI7 (RapidAPI).

MODES :
- TEST_MODE = True  : ~10-15 req/run (pour valider sur plan Basic 50 req/mois)
- TEST_MODE = False : ~200-300 req/run (mode production, plan Pro $15/mois requis)

En mode TEST :
1. Decouverte des IDs ligues (~5 req) - sauvegardee en local
2. Standings des 5 ligues (~5 req)
3. UN SEUL match analyse en pipeline complete (~5 req : details + odds + h2h + pregame-form)

Total mode TEST : ~15 req max -> tu peux relancer 3x avec ton quota de 50 req/mois.

Usage :
    python -m jobs.refresh_sportapi7              # mode TEST par defaut
    python -m jobs.refresh_sportapi7 --prod       # mode PRODUCTION (besoin plan Pro)
    python -m jobs.refresh_sportapi7 --force      # vide cache
"""

import os
import sys
import json
import time
import argparse
from datetime import date, timedelta

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from providers.api_sportapi7 import SportAPI7, SportAPI7Error, SportAPI7RateLimit
from providers import sportapi7_mapper as mapper
from providers import cache


# ========== CONFIG ==========
LEAGUES_CONFIG_FILE = os.path.join(BACKEND_DIR, "cache", "sportapi7_leagues.json")


def save_leagues_config(leagues: dict):
    """Sauvegarde les IDs decouverts pour eviter de les redecouvrir a chaque run."""
    try:
        with open(LEAGUES_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(leagues, f, indent=2, ensure_ascii=False)
        print(f"  IDs ligues sauvegardes dans {os.path.basename(LEAGUES_CONFIG_FILE)}")
    except Exception as e:
        print(f"  KO sauvegarde IDs : {e}")


def load_leagues_config() -> dict:
    """Charge les IDs sauvegardes en local pour eviter une nouvelle decouverte."""
    if not os.path.exists(LEAGUES_CONFIG_FILE):
        return {}
    try:
        with open(LEAGUES_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ========== MAIN TEST MODE ==========

def main_test(force: bool = False):
    """
    Mode TEST : ~10-15 req max.
    Valide la chaine complete avec 1 seul match.
    """
    print("=" * 60)
    print("VARION FOOT (SportAPI7) - MODE TEST")
    print(f"Quota cible : ~15 req max sur ce run")
    print("=" * 60)

    if force:
        print("Mode FORCE : on vide le cache")
        cache.clear()
        if os.path.exists(LEAGUES_CONFIG_FILE):
            os.remove(LEAGUES_CONFIG_FILE)

    api = SportAPI7()
    print(f"Cache : {cache.stats()}")
    print()

    # ========== 1. DECOUVERTE OU CHARGEMENT DES LIGUES ==========
    print(">>> Etape 1 : IDs des ligues (Top 5 europeen)")
    leagues = load_leagues_config()

    if leagues:
        print("  IDs charges depuis le cache local (0 req API)")
        for short, info in leagues.items():
            print(f"    {short}: cat={info['category_id']}, tournament={info['unique_tournament_id']}, season={info['season_id']}")
    else:
        print("  Decouverte via API...")
        try:
            leagues = api.discover_leagues()
        except SportAPI7RateLimit as e:
            print(f"  STOP : {e}")
            return
        except Exception as e:
            print(f"  KO discovery : {e}")
            return

        if not leagues:
            print("  Aucune ligue trouvee. Pas de matchs aujourd'hui ni samedi prochain ?")
            return

        for short, info in leagues.items():
            print(f"    {short}: cat={info['category_id']}, tournament={info['unique_tournament_id']}, season={info['season_id']} ({info['name']})")

        save_leagues_config(leagues)

    print(f"  Requetes API utilisees : {api.calls_made}")

    # ========== 2. STANDINGS (1 req par ligue, max 5) ==========
    print(f"\n>>> Etape 2 : Standings des 5 ligues")
    teams_internal = {}
    team_id_map = {}

    for short, league_info in leagues.items():
        ut_id = league_info.get("unique_tournament_id")
        s_id = league_info.get("season_id")
        if not ut_id or not s_id:
            print(f"  KO {short}: IDs manquants")
            continue

        try:
            standings = api.get_standings(ut_id, s_id)
            print(f"  {short}: {len(standings)} equipes")
            for row in standings:
                team = mapper.map_team_from_standings(row, short)
                if not team:
                    continue
                while team["id"] in teams_internal:
                    team["id"] = team["id"] + "X"
                teams_internal[team["id"]] = team
                team_id_map[team["api_id"]] = team["id"]
        except SportAPI7RateLimit as e:
            print(f"  STOP quota : {e}")
            print(f"  Requetes API utilisees : {api.calls_made}")
            return
        except Exception as e:
            print(f"  KO standings {short}: {e}")

    print(f"  Total equipes mappees : {len(teams_internal)}")
    print(f"  Requetes API utilisees : {api.calls_made}")

    # ========== 3. UN SEUL MATCH ANALYSE EN PIPELINE COMPLETE ==========
    print(f"\n>>> Etape 3 : Recherche d'1 match a tester (J a J+3)")
    test_event = None

    # Strategie : on fetch les events football du sport pour la date,
    # puis on filtre par uniqueTournament.id pour rester dans nos 5 ligues
    target_ut_ids = {info["unique_tournament_id"] for info in leagues.values() if info.get("unique_tournament_id")}

    today = date.today()
    for day_offset in range(4):
        if test_event:
            break
        d = today + timedelta(days=day_offset)
        try:
            events = api.get_scheduled_events_by_sport("football", d.isoformat())
            # Filtrer : seulement events des ligues du Top 5
            for e in events:
                ut = (e.get("tournament", {}).get("uniqueTournament", {}) or {}).get("id")
                if ut not in target_ut_ids:
                    continue
                home_api = (e.get("homeTeam") or {}).get("id")
                away_api = (e.get("awayTeam") or {}).get("id")
                if home_api in team_id_map and away_api in team_id_map:
                    test_event = e
                    print(f"  Match selectionne : {e.get('homeTeam', {}).get('name')} vs {e.get('awayTeam', {}).get('name')} ({e.get('tournament', {}).get('name')}, {d})")
                    break
        except SportAPI7RateLimit:
            print(f"  STOP quota")
            print(f"  Requetes API utilisees : {api.calls_made}")
            return
        except Exception as e:
            print(f"  KO date {d}: {e}")

    if not test_event:
        print("  Aucun match trouve avec equipes dans Top.")
        print(f"  Requetes API utilisees : {api.calls_made}")
        return

    # ========== 4. PIPELINE COMPLETE SUR 1 MATCH ==========
    print(f"\n>>> Etape 4 : Pipeline complete sur ce match")
    event_id = test_event["id"]

    # Map de base
    match = mapper.map_match(test_event, team_id_map)
    if not match:
        print("  KO mapping match")
        return

    print(f"  Match mappe : {match['home']} vs {match['away']} le {match['date']} {match['kickoff']}")

    # Odds
    print(f"  Fetch odds...")
    try:
        odds_data = api.get_event_odds(event_id, provider_id=1)
        match = mapper.enrich_match_with_odds(match, odds_data)
        print(f"    Cotes 1X2 : 1={match['odds']['1']:.2f}, X={match['odds']['X']:.2f}, 2={match['odds']['2']:.2f}")
        if "btts_yes" in match["odds"]:
            print(f"    BTTS : Y={match['odds']['btts_yes']:.2f}, N={match['odds']['btts_no']:.2f}")
        if "over_25" in match["odds"]:
            print(f"    O/U 2.5 : O={match['odds']['over_25']:.2f}, U={match['odds']['under_25']:.2f}")
    except SportAPI7RateLimit as e:
        print(f"    STOP quota : {e}")
        print(f"    Requetes API utilisees : {api.calls_made}")
        return
    except Exception as e:
        print(f"    KO odds : {e}")

    # Pregame form
    print(f"  Fetch pregame-form...")
    try:
        pregame = api.get_event_pregame_form(event_id)
        if pregame:
            home_team = teams_internal.get(match["home"])
            away_team = teams_internal.get(match["away"])
            if home_team:
                teams_internal[match["home"]] = mapper.enrich_team_with_pregame_form(home_team, pregame, is_home=True)
                print(f"    Forme {home_team['name']}: {teams_internal[match['home']]['form_10']}")
            if away_team:
                teams_internal[match["away"]] = mapper.enrich_team_with_pregame_form(away_team, pregame, is_home=False)
                print(f"    Forme {away_team['name']}: {teams_internal[match['away']]['form_10']}")
        else:
            print(f"    Pregame-form vide")
    except SportAPI7RateLimit as e:
        print(f"    STOP quota : {e}")
        return
    except Exception as e:
        print(f"    KO pregame-form : {e}")

    # H2H summary
    print(f"  Fetch H2H...")
    try:
        h2h_summary_raw = api.get_event_h2h_summary(event_id)
        h2h_summary = mapper.map_h2h_summary(h2h_summary_raw)
        if h2h_summary["total"] > 0:
            print(f"    {h2h_summary['home_wins']}W home / {h2h_summary['away_wins']}W away / {h2h_summary['draws']}D ({h2h_summary['total']} matchs historiques)")
        else:
            print(f"    Pas de confrontations historiques")
    except SportAPI7RateLimit as e:
        print(f"    STOP quota : {e}")
        return
    except Exception as e:
        print(f"    KO H2H : {e}")

    # ========== RESUME FINAL ==========
    print("\n" + "=" * 60)
    print("OK Mode TEST termine")
    print(f"  IDs ligues : {len(leagues)} sauvegardes")
    print(f"  Equipes mappees : {len(teams_internal)}")
    print(f"  1 match analyse complet : {match['home']} vs {match['away']}")
    print(f"  REQUETES API UTILISEES : {api.calls_made}")
    print(f"  Cache final : {cache.stats()}")
    print("=" * 60)
    print()
    print("Si tout est OK ci-dessus, tu peux passer en mode PROD :")
    print("  1. Upgrade ton plan SportAPI7 (~15$ pour 15000 req/mois)")
    print("  2. Lance : python -m jobs.refresh_sportapi7 --prod")
    print()


# ========== MAIN PROD MODE ==========

def main_prod(force: bool = False):
    """
    Mode PRODUCTION : ~200-300 req/run.
    Necessite le plan Pro ($15/mois pour 15000 req/mois).

    Note : on importe ici l'ancien code complet pour ne pas l'avoir charge en mode TEST.
    """
    print("=" * 60)
    print("VARION FOOT (SportAPI7) - MODE PRODUCTION")
    print("Quota necessaire : ~250 req/run, plan Pro recommande")
    print("=" * 60)

    if force:
        cache.clear()

    api = SportAPI7()
    print(f"Cache : {cache.stats()}\n")

    # 1. Charger ou decouvrir les ligues
    leagues = load_leagues_config()
    if not leagues:
        print(">>> Decouverte ligues...")
        try:
            leagues = api.discover_leagues()
            save_leagues_config(leagues)
        except Exception as e:
            print(f"KO discovery : {e}")
            return

    print(f">>> {len(leagues)} ligues chargees")

    # 2. Pipeline complete
    DAYS_AHEAD = 4
    MAX_MATCHES = 80
    today = date.today()
    quota_hit = False

    # Standings + matchs
    teams_internal = {}
    team_id_map = {}
    all_events = []

    for short, league_info in leagues.items():
        if quota_hit:
            break
        ut_id = league_info.get("unique_tournament_id")
        s_id = league_info.get("season_id")
        cat_id = league_info.get("category_id")
        if not (ut_id and s_id and cat_id):
            continue

        # Standings
        try:
            standings = api.get_standings(ut_id, s_id)
            for row in standings:
                team = mapper.map_team_from_standings(row, short)
                if not team:
                    continue
                while team["id"] in teams_internal:
                    team["id"] = team["id"] + "X"
                teams_internal[team["id"]] = team
                team_id_map[team["api_id"]] = team["id"]
        except SportAPI7RateLimit as e:
            print(f"STOP : {e}")
            quota_hit = True
            break
        except Exception as e:
            print(f"KO standings {short}: {e}")

        # Matchs J a J+3
        for day_offset in range(DAYS_AHEAD):
            if quota_hit:
                break
            d = today + timedelta(days=day_offset)
            try:
                events = api.get_scheduled_events_by_category(cat_id, d.isoformat())
                events = [e for e in events
                          if (e.get("tournament", {}).get("uniqueTournament", {}) or {}).get("id") == ut_id]
                for e in events:
                    e["_league_short"] = short
                all_events.extend(events)
            except SportAPI7RateLimit:
                quota_hit = True
                break
            except Exception:
                continue

    print(f">>> {len(teams_internal)} equipes, {len(all_events)} matchs trouves")

    # Limiter
    all_events = all_events[:MAX_MATCHES]

    # Analyse de chaque match
    matches_internal = []
    h2h_data = {}
    for event in all_events:
        if quota_hit:
            break
        try:
            match = mapper.map_match(event, team_id_map)
            if not match:
                continue
            event_id = event.get("id")

            try:
                odds = api.get_event_odds(event_id, 1)
                match = mapper.enrich_match_with_odds(match, odds)
            except SportAPI7RateLimit:
                quota_hit = True
            except Exception:
                pass

            try:
                pregame = api.get_event_pregame_form(event_id)
                if pregame:
                    home_team = teams_internal.get(match["home"])
                    away_team = teams_internal.get(match["away"])
                    if home_team:
                        teams_internal[match["home"]] = mapper.enrich_team_with_pregame_form(home_team, pregame, is_home=True)
                    if away_team:
                        teams_internal[match["away"]] = mapper.enrich_team_with_pregame_form(away_team, pregame, is_home=False)
            except SportAPI7RateLimit:
                quota_hit = True
            except Exception:
                pass

            try:
                # H2H : on ne fetch que le summary (suffisant pour le moteur)
                h2h_raw = api.get_event_h2h_summary(event_id)
                h2h_summary = mapper.map_h2h_summary(h2h_raw)
                # Expand vers fake events pour compat moteur Varion
                fake_events = mapper.expand_h2h_summary_to_fake_events(
                    h2h_summary, match["home"], match["away"]
                )
                if fake_events:
                    h2h_data[(match["home"], match["away"])] = fake_events
                # On stocke aussi le summary brut pour l'UI
                match["h2h_summary"] = h2h_summary
            except SportAPI7RateLimit:
                quota_hit = True
            except Exception:
                pass

            matches_internal.append(match)
        except Exception as e:
            print(f"KO event {event.get('id')}: {e}")

    print(f">>> {len(matches_internal)} matchs analyses")

    # Lancer le moteur Varion
    from data import teams as teams_module
    from data import matches as matches_module
    from data import players as players_module
    teams_module.TEAMS = teams_internal
    matches_module.UPCOMING_MATCHES = matches_internal
    matches_module.H2H = h2h_data
    players_module.PLAYERS = []

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
            "id": tid, "name": t["name"], "short": t["short"],
            "rank": t["rank"], "points": t["points"],
            "logo_color": t["logo_color"], "logo_url": t.get("logo_url"),
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
            ctx = {"ref_yellow_avg": m["ref_yellow_avg"], "is_derby": m["is_derby"], "stakes": m["stakes"]}
            preds = predict_match(home_id, away_id, ctx)
            home_players = analyze_team_players(home_id, away_overall["defense_score"], True)
            away_players = analyze_team_players(away_id, home_overall["defense_score"], False)
            bets = detect_value_bets(preds, m["odds"], home_players + away_players)
            key_h = detect_key_players_to_watch(home_id, away_overall["defense_score"], True, 4)
            key_a = detect_key_players_to_watch(away_id, home_overall["defense_score"], False, 4)
            summary = generate_match_summary(home_id, away_id, home_overall, away_overall, preds, bets, key_h, key_a)
            conf = confidence_score(preds, bets)

            output["matches_summary"].append({
                "id": m["id"], "date": m["date"], "kickoff": m["kickoff"],
                "competition": m["competition"], "venue": m["venue"],
                "is_derby": m["is_derby"], "stakes": m["stakes"],
                "home": {"id": home_id, "name": home["name"], "short": home["short"],
                         "logo_color": home["logo_color"], "logo_url": home.get("logo_url"), "rank": home["rank"]},
                "away": {"id": away_id, "name": away["name"], "short": away["short"],
                         "logo_color": away["logo_color"], "logo_url": away.get("logo_url"), "rank": away["rank"]},
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

            for b in bets:
                if b["edge_pct"] >= 5:
                    all_value_bets.append({**b,
                        "match_id": m["id"],
                        "match_label": f"{home['short']} vs {away['short']}",
                        "match_date": m["date"], "match_kickoff": m["kickoff"]})
        except Exception as e:
            print(f"KO analyse {home_id} vs {away_id} : {e}")

    all_value_bets.sort(key=lambda b: -b["edge_pct"])
    output["value_bets"] = all_value_bets

    output_path = os.path.normpath(os.path.join(BACKEND_DIR, "..", "frontend", "data.json"))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, default=str, ensure_ascii=False)

    size_kb = os.path.getsize(output_path) / 1024

    print("\n" + "=" * 60)
    print("OK Refresh PROD termine")
    print(f"  {len(output['teams'])} equipes")
    print(f"  {len(output['matches_summary'])} matchs analyses")
    print(f"  {len(output['value_bets'])} value bets")
    print(f"  Fichier : {output_path} ({size_kb:.1f} KB)")
    print(f"  Requetes API : {api.calls_made}")
    if quota_hit:
        print(f"  ! Quota epuise pendant le run")
    print("=" * 60)


# ========== MAIN TEST MULTI-MATCHES ==========

def main_test_multi(force: bool = False):
    """
    Test etendu : analyse 3 matchs de ligues differentes pour valider
    la robustesse cross-league de la pipeline.

    Cout : ~10-15 req (discovery + standings depuis cache, on ne paie que les events).
    Conditions : tu dois avoir deja lance main_test() au moins une fois pour
    avoir les IDs ligues sauvegardes en local.
    """
    print("=" * 60)
    print("VARION FOOT (SportAPI7) - MODE TEST MULTI")
    print("Test sur 3 matchs de ligues differentes")
    print("=" * 60)

    if force:
        print("Mode FORCE : on vide le cache")
        cache.clear()
        if os.path.exists(LEAGUES_CONFIG_FILE):
            os.remove(LEAGUES_CONFIG_FILE)

    api = SportAPI7()
    print(f"Cache : {cache.stats()}\n")

    # 1. Charger les IDs ligues
    leagues = load_leagues_config()
    if not leagues:
        print("KO : pas de fichier sportapi7_leagues.json")
        print("    Lance d'abord : python -m jobs.refresh_sportapi7")
        return
    print(f">>> {len(leagues)} ligues chargees depuis cache local (0 req)")

    # 2. Charger les standings (depuis cache 24h, idealement 0 req)
    print(f"\n>>> Chargement standings (cache 24h)")
    teams_internal = {}
    team_id_map = {}

    for short, league_info in leagues.items():
        ut_id = league_info.get("unique_tournament_id")
        s_id = league_info.get("season_id")
        if not (ut_id and s_id):
            continue
        try:
            standings = api.get_standings(ut_id, s_id)
            for row in standings:
                team = mapper.map_team_from_standings(row, short)
                if not team:
                    continue
                while team["id"] in teams_internal:
                    team["id"] = team["id"] + "X"
                teams_internal[team["id"]] = team
                team_id_map[team["api_id"]] = team["id"]
        except SportAPI7RateLimit as e:
            print(f"  STOP : {e}")
            return
        except Exception as e:
            print(f"  KO standings {short}: {e}")

    print(f"  {len(teams_internal)} equipes mappees")
    print(f"  Requetes API utilisees : {api.calls_made}")

    # 3. Trouver 3 matchs de ligues differentes
    print(f"\n>>> Recherche de 3 matchs de ligues DIFFERENTES (J a J+5)")
    target_ut_ids = {info["unique_tournament_id"]: short
                     for short, info in leagues.items()
                     if info.get("unique_tournament_id")}

    found_matches = []  # liste de (event, short_league)
    seen_leagues = set()

    today = date.today()
    for day_offset in range(6):
        if len(found_matches) >= 3:
            break
        d = today + timedelta(days=day_offset)
        try:
            events = api.get_scheduled_events_by_sport("football", d.isoformat())
            for e in events:
                if len(found_matches) >= 3:
                    break
                ut = (e.get("tournament", {}).get("uniqueTournament", {}) or {}).get("id")
                if ut not in target_ut_ids:
                    continue
                short = target_ut_ids[ut]
                if short in seen_leagues:
                    continue
                home_api = (e.get("homeTeam") or {}).get("id")
                away_api = (e.get("awayTeam") or {}).get("id")
                if home_api in team_id_map and away_api in team_id_map:
                    found_matches.append((e, short, d))
                    seen_leagues.add(short)
                    print(f"  [{short}] {e.get('homeTeam', {}).get('name')} vs {e.get('awayTeam', {}).get('name')} le {d}")
        except SportAPI7RateLimit:
            print(f"  STOP quota")
            print(f"  Requetes API utilisees : {api.calls_made}")
            return
        except Exception as ex:
            print(f"  KO date {d}: {ex}")

    if not found_matches:
        print("  Aucun match trouve.")
        return

    # 4. Pipeline complete sur chaque match
    print(f"\n>>> Pipeline complete sur {len(found_matches)} matchs")

    for i, (event, short, match_date) in enumerate(found_matches, 1):
        print(f"\n--- MATCH {i}/{len(found_matches)} : [{short}] ---")
        event_id = event.get("id")

        match = mapper.map_match(event, team_id_map)
        if not match:
            print(f"  KO mapping match")
            continue

        home_name = teams_internal[match["home"]]["name"]
        away_name = teams_internal[match["away"]]["name"]
        print(f"  {home_name} vs {away_name}")
        print(f"  Date : {match['date']} {match['kickoff']}")

        # Odds
        try:
            odds_data = api.get_event_odds(event_id, provider_id=1)
            match = mapper.enrich_match_with_odds(match, odds_data)
            print(f"  Cotes 1X2 : 1={match['odds']['1']:.2f} / X={match['odds']['X']:.2f} / 2={match['odds']['2']:.2f}")
            if "btts_yes" in match["odds"]:
                print(f"  BTTS Y/N : {match['odds']['btts_yes']:.2f} / {match['odds']['btts_no']:.2f}")
            if "over_25" in match["odds"]:
                print(f"  O/U 2.5  : {match['odds']['over_25']:.2f} / {match['odds']['under_25']:.2f}")
        except SportAPI7RateLimit as e:
            print(f"  STOP quota : {e}")
            return
        except Exception as e:
            print(f"  KO odds : {e}")

        # Pregame
        try:
            pregame = api.get_event_pregame_form(event_id)
            if pregame:
                home_team = teams_internal.get(match["home"])
                away_team = teams_internal.get(match["away"])
                if home_team:
                    teams_internal[match["home"]] = mapper.enrich_team_with_pregame_form(home_team, pregame, is_home=True)
                    print(f"  Forme {home_name[:20]} : {teams_internal[match['home']]['form_10']}")
                if away_team:
                    teams_internal[match["away"]] = mapper.enrich_team_with_pregame_form(away_team, pregame, is_home=False)
                    print(f"  Forme {away_name[:20]} : {teams_internal[match['away']]['form_10']}")
            else:
                print(f"  Pregame-form vide")
        except SportAPI7RateLimit as e:
            print(f"  STOP quota : {e}")
            return
        except Exception as e:
            print(f"  KO pregame : {e}")

        # H2H : on ne garde que le summary (suffisant pour le moteur)
        try:
            h2h_summary_raw = api.get_event_h2h_summary(event_id)
            h2h_summary = mapper.map_h2h_summary(h2h_summary_raw)
            if h2h_summary["total"] > 0:
                home_name = teams_internal.get(match["home"], {}).get("name", "?")[:20]
                away_name = teams_internal.get(match["away"], {}).get("name", "?")[:20]
                print(f"  H2H : {home_name} {h2h_summary['home_wins']}W - {h2h_summary['away_wins']}W {away_name}, {h2h_summary['draws']}D ({h2h_summary['total']} matchs)")
            else:
                print(f"  H2H : pas de confrontations historiques")
        except SportAPI7RateLimit as e:
            print(f"  STOP quota : {e}")
            return
        except Exception as e:
            print(f"  KO H2H : {e}")

    # Resume
    print("\n" + "=" * 60)
    print("OK Mode TEST MULTI termine")
    print(f"  Matchs analyses : {len(found_matches)} (ligues : {', '.join(seen_leagues)})")
    print(f"  REQUETES API UTILISEES : {api.calls_made}")
    print(f"  Cache final : {cache.stats()}")
    print("=" * 60)


# ========== MAIN TEST OUTPUT (test + ecriture data.json) ==========

def main_test_output(force: bool = False):
    """
    Mode TEST OUTPUT : analyse 1 match COMPLETEMENT (avec moteur Varion)
    et ECRIT data.json pour que le frontend puisse l'afficher.

    Cout : ~10-15 req max (proche du mode test simple).
    Difference avec mode test simple : on ecrit dans frontend/data.json
    avec le format complet attendu par le moteur.
    """
    print("=" * 60)
    print("VARION FOOT (SportAPI7) - MODE TEST OUTPUT")
    print("Analyse 1 match + ecrit data.json pour le frontend")
    print("=" * 60)

    if force:
        cache.clear()
        if os.path.exists(LEAGUES_CONFIG_FILE):
            os.remove(LEAGUES_CONFIG_FILE)

    api = SportAPI7()
    print(f"Cache : {cache.stats()}\n")

    # 1. Decouverte ligues (cache local)
    leagues = load_leagues_config()
    if not leagues:
        print(">>> Decouverte ligues...")
        try:
            leagues = api.discover_leagues()
            save_leagues_config(leagues)
        except Exception as e:
            print(f"KO discovery : {e}")
            return
    else:
        print(">>> 5 ligues chargees depuis cache local (0 req)")

    # 2. Standings 5 ligues
    print(">>> Standings 5 ligues")
    teams_internal = {}
    team_id_map = {}
    for short, league_info in leagues.items():
        ut_id = league_info.get("unique_tournament_id")
        s_id = league_info.get("season_id")
        if not (ut_id and s_id):
            continue
        try:
            standings = api.get_standings(ut_id, s_id)
            for row in standings:
                team = mapper.map_team_from_standings(row, short)
                if not team:
                    continue
                while team["id"] in teams_internal:
                    team["id"] = team["id"] + "X"
                teams_internal[team["id"]] = team
                team_id_map[team["api_id"]] = team["id"]
        except Exception as e:
            print(f"  KO standings {short}: {e}")
    print(f"  {len(teams_internal)} equipes mappees")

    # 3. Trouver 1 match FUTUR
    print(">>> Recherche d'1 match futur (J a J+7)")
    target_ut_ids = {info["unique_tournament_id"]: short
                     for short, info in leagues.items()
                     if info.get("unique_tournament_id")}
    test_event = None
    today = date.today()
    now_ts = int(time.time())  # timestamp actuel pour filtrer matchs futurs
    for day_offset in range(8):  # J a J+7
        if test_event:
            break
        d = today + timedelta(days=day_offset)
        try:
            events = api.get_scheduled_events_by_sport("football", d.isoformat())
            for e in events:
                ut = (e.get("tournament", {}).get("uniqueTournament", {}) or {}).get("id")
                if ut not in target_ut_ids:
                    continue
                # FILTRE : seulement matchs futurs (kick-off > maintenant)
                start_ts = e.get("startTimestamp", 0)
                if start_ts <= now_ts:
                    continue  # match passe ou en cours
                # FILTRE : status doit etre 'notstarted' (code 0)
                status_type = (e.get("status") or {}).get("type")
                if status_type and status_type != "notstarted":
                    continue
                home_api = (e.get("homeTeam") or {}).get("id")
                away_api = (e.get("awayTeam") or {}).get("id")
                if home_api in team_id_map and away_api in team_id_map:
                    test_event = e
                    home_name = e.get("homeTeam", {}).get("name")
                    away_name = e.get("awayTeam", {}).get("name")
                    print(f"  Match selectionne : {home_name} vs {away_name} ({d})")
                    break
        except Exception as ex:
            print(f"  KO date {d}: {ex}")

    if not test_event:
        print("  Aucun match trouve.")
        return

    # 4. Pipeline complete sur ce match
    print(">>> Pipeline complete + analyse Varion")
    matches_internal = []
    h2h_data = {}
    event_id = test_event["id"]

    match = mapper.map_match(test_event, team_id_map)
    if not match:
        print("  KO mapping match")
        return

    # Odds
    try:
        odds_data = api.get_event_odds(event_id, provider_id=1)
        match = mapper.enrich_match_with_odds(match, odds_data)
    except Exception as e:
        print(f"  KO odds : {e}")

    # Pregame
    try:
        pregame = api.get_event_pregame_form(event_id)
        if pregame:
            home_team = teams_internal.get(match["home"])
            away_team = teams_internal.get(match["away"])
            if home_team:
                teams_internal[match["home"]] = mapper.enrich_team_with_pregame_form(home_team, pregame, is_home=True)
            if away_team:
                teams_internal[match["away"]] = mapper.enrich_team_with_pregame_form(away_team, pregame, is_home=False)
    except Exception as e:
        print(f"  KO pregame : {e}")

    # H2H summary
    try:
        h2h_raw = api.get_event_h2h_summary(event_id)
        h2h_summary = mapper.map_h2h_summary(h2h_raw)
        fake_events = mapper.expand_h2h_summary_to_fake_events(
            h2h_summary, match["home"], match["away"]
        )
        if fake_events:
            h2h_data[(match["home"], match["away"])] = fake_events
        match["h2h_summary"] = h2h_summary
    except Exception as e:
        print(f"  KO H2H : {e}")

    matches_internal.append(match)

    # 5. Lancer le moteur Varion
    print(">>> Moteur Varion football")
    from data import teams as teams_module
    from data import matches as matches_module
    from data import players as players_module
    teams_module.TEAMS = teams_internal
    matches_module.UPCOMING_MATCHES = matches_internal
    matches_module.H2H = h2h_data
    players_module.PLAYERS = []

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
            "id": tid, "name": t["name"], "short": t["short"],
            "rank": t["rank"], "points": t["points"],
            "logo_color": t["logo_color"], "logo_url": t.get("logo_url"),
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
            ctx = {"ref_yellow_avg": m["ref_yellow_avg"], "is_derby": m["is_derby"], "stakes": m["stakes"]}
            preds = predict_match(home_id, away_id, ctx)
            home_players = analyze_team_players(home_id, away_overall["defense_score"], True)
            away_players = analyze_team_players(away_id, home_overall["defense_score"], False)
            bets = detect_value_bets(preds, m["odds"], home_players + away_players)
            key_h = detect_key_players_to_watch(home_id, away_overall["defense_score"], True, 4)
            key_a = detect_key_players_to_watch(away_id, home_overall["defense_score"], False, 4)
            summary = generate_match_summary(home_id, away_id, home_overall, away_overall, preds, bets, key_h, key_a)
            conf = confidence_score(preds, bets)

            output["matches_summary"].append({
                "id": m["id"], "date": m["date"], "kickoff": m["kickoff"],
                "competition": m["competition"], "venue": m["venue"],
                "is_derby": m["is_derby"], "stakes": m["stakes"],
                "home": {"id": home_id, "name": home["name"], "short": home["short"],
                         "logo_color": home["logo_color"], "logo_url": home.get("logo_url"), "rank": home["rank"]},
                "away": {"id": away_id, "name": away["name"], "short": away["short"],
                         "logo_color": away["logo_color"], "logo_url": away.get("logo_url"), "rank": away["rank"]},
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

            output["matches_full"][m["id"]] = {
                "id": m["id"], "date": m["date"], "kickoff": m["kickoff"],
                "venue": m["venue"], "competition": m["competition"],
                "referee": m["referee"], "is_derby": m["is_derby"], "stakes": m["stakes"],
                "summary": summary, "confidence_score": conf,
                "teams": {
                    "home": {"info": home, "scores": home_overall, "goalkeeper": None,
                             "starters": [], "key_players": key_h, "all_players": home_players},
                    "away": {"info": away, "scores": away_overall, "goalkeeper": None,
                             "starters": [], "key_players": key_a, "all_players": away_players},
                },
                "predictions": preds, "odds": m["odds"], "value_bets": bets, "h2h": [],
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

    # 6. Ecrire data.json
    output_path = os.path.normpath(os.path.join(BACKEND_DIR, "..", "frontend", "data.json"))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, default=str, ensure_ascii=False)

    size_kb = os.path.getsize(output_path) / 1024

    print("\n" + "=" * 60)
    print("OK Mode TEST OUTPUT termine")
    print(f"  {len(output['teams'])} equipes")
    print(f"  {len(output['matches_summary'])} match analyse")
    print(f"  {len(output['value_bets'])} value bets detectes")
    print(f"  Fichier : {output_path} ({size_kb:.1f} KB)")
    print(f"  REQUETES API UTILISEES : {api.calls_made}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prod", action="store_true", help="Mode production (besoin plan Pro)")
    parser.add_argument("--test-multi", action="store_true", help="Test sur 3 matchs de ligues differentes")
    parser.add_argument("--test-output", action="store_true", help="Test 1 match + ecrit data.json")
    parser.add_argument("--force", action="store_true", help="Vider cache avant run")
    args = parser.parse_args()
    if args.prod:
        main_prod(force=args.force)
    elif args.test_multi:
        main_test_multi(force=args.force)
    elif args.test_output:
        main_test_output(force=args.force)
    else:
        main_test(force=args.force)
