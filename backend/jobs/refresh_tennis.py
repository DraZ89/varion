"""
Job de refresh tennis.

Workflow optimise pour ~80 req/run :
1. Rankings ATP + WTA (cache 24h)        -> 2 req
2. Fixtures jour J + J+1 + J+2, ATP+WTA  -> 6 req
3. Pour chaque joueur impliquant un match : surface-summary (cache 7j) + past-matches (cache 7j)
   -> ~30-50 req au premier run, 0-5 ensuite
4. Pour chaque match : H2H (cache 30j)   -> ~5-10 req
5. Calcul predictions + value bets + ecriture data_tennis.json

Usage :
    python -m jobs.refresh_tennis
    python -m jobs.refresh_tennis --force   # vide le cache
"""

import os
import sys
import json
import argparse
import time as _time

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from providers.api_rapidapi_tennis import TennisAPI, TennisAPIError, TennisAPIRateLimit
from providers import tennis_mapper
from providers import cache
from engine.tennis.predictions import predict_match
from engine.tennis.value_bets import (
    detect_tennis_value_bets,
    generate_model_picks,
    generate_tennis_summary,
    confidence_score_match,
)


# Limiter pour ne pas exploser le quota
MAX_PLAYERS_TO_FETCH = 120  # max joueurs dont on fetch surface+past-matches (etait 80)
DAYS_AHEAD = 5              # combien de jours en avant on fetch les fixtures
TOURS = ["atp", "wta"]
TOP_N_RANKING = 300         # rankings : on couvre le Top 300 (etait 200)
MAX_TENNIS_MATCHES_DISPLAY = 5  # nb matchs a garder pour affichage final (top edges)
MIN_EDGE_TO_SHOW = 0.0      # edge minimum pour qu'un match soit considere


def main(force: bool = False, test_output: bool = False):
    print("=" * 60)
    if test_output:
        print("VARION TENNIS - MODE TEST OUTPUT (1 match)")
    else:
        print("VARION TENNIS - Refresh data")
    print("=" * 60)

    if force:
        print("Mode FORCE : on vide le cache")
        cache.clear()

    api = TennisAPI()
    cache_stats = cache.stats()
    print(f"Cache : {cache_stats['entries']} entrees, {cache_stats['size_kb']} KB")

    # The Odds API (optionnel : si pas de cle, on continue sans)
    odds_api_client = None
    try:
        if os.environ.get("ODDS_API_KEY"):
            from providers.the_odds_api import TheOddsAPI
            odds_api_client = TheOddsAPI()
            print("The Odds API : active (cotes reelles bookmakers)")
        else:
            print("The Odds API : inactif (ODDS_API_KEY non definie)")
    except Exception as e:
        print(f"The Odds API : inactif ({e})")
    print()

    output = {
        "matches": [],
        "value_bets": [],
        "tours": {},
        "generated_at": None,
    }

    quota_hit = False
    total_matches_analyzed = 0  # cap global ATP+WTA
    odds_api_hits = 0  # compteur : matchs avec vraies cotes
    odds_api_misses = 0  # matchs sans cotes API (fallback estimation)

    for tour in TOURS:
        if quota_hit:
            break
        # Cap global : on s'arrete des qu'on a MAX_TENNIS_MATCHES_DISPLAY matchs au total
        if total_matches_analyzed >= MAX_TENNIS_MATCHES_DISPLAY:
            print(f"\n[STOP] {MAX_TENNIS_MATCHES_DISPLAY} matchs deja analyses (cap), pas besoin d'aller plus loin")
            break

        print(f">>> {tour.upper()}")

        # === 1. Rankings ===
        try:
            rankings_raw = api.get_rankings(tour, top_n=TOP_N_RANKING)
            print(f"  Rankings : {len(rankings_raw)} joueurs Top {TOP_N_RANKING}")
        except TennisAPIRateLimit as e:
            print(f"  STOP : {e}")
            quota_hit = True
            break
        except Exception as e:
            print(f"  KO rankings : {e}")
            continue

        # Mapper les joueurs Top 200 (sans ELO pour l'instant)
        top_players = {}
        for entry in rankings_raw:
            mapped = tennis_mapper.map_player_from_ranking(entry, tour)
            if mapped:
                top_players[mapped["id"]] = mapped

        # === 2. Fixtures (jours J, J+1, J+2) ===
        try:
            all_fixtures = api.get_matches_recent_days(tour, days=DAYS_AHEAD)
            print(f"  Fixtures J a J+{DAYS_AHEAD-1} : {len(all_fixtures)} matchs")
        except TennisAPIRateLimit as e:
            print(f"  STOP : {e}")
            quota_hit = True
            break
        except Exception as e:
            print(f"  KO fixtures : {e}")
            continue

        # Filtrer : matchs FUTURS avec au moins 1 joueur dans le Top N
        from datetime import datetime as _dt, timezone as _tz
        now_utc = _dt.now(_tz.utc)
        candidate_matches = []
        skipped_past = 0
        skipped_no_top = 0

        for fix in all_fixtures:
            p1 = fix.get("player1Id")
            p2 = fix.get("player2Id")
            if not p1 or not p2:
                continue
            p1_str, p2_str = str(p1), str(p2)

            # FILTRE 1 : seulement les matchs FUTURS
            date_str = fix.get("date") or ""
            try:
                if date_str.endswith("Z"):
                    match_dt = _dt.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    match_dt = _dt.fromisoformat(date_str)
                if match_dt.tzinfo is None:
                    match_dt = match_dt.replace(tzinfo=_tz.utc)
                # On garde les matchs qui demarrent dans plus de 5 minutes
                if (match_dt - now_utc).total_seconds() < 300:
                    skipped_past += 1
                    continue
            except Exception:
                skipped_past += 1
                continue

            # FILTRE 2 : au moins UN joueur dans le Top N (sinon match peu pertinent)
            p1_in_top = p1_str in top_players
            p2_in_top = p2_str in top_players
            if not (p1_in_top or p2_in_top):
                skipped_no_top += 1
                continue

            # Annoter le fixture pour usage ulterieur
            fix["_p1_in_top"] = p1_in_top
            fix["_p2_in_top"] = p2_in_top
            fix["_match_dt_iso"] = match_dt.isoformat()
            candidate_matches.append(fix)

        # === SELECTION TOP N CHRONOLOGIQUEMENT ===
        # Tri par date croissante (le match le plus proche en premier)
        candidate_matches.sort(key=lambda f: f.get("date", ""))

        # On garde STRICTEMENT le nb restant (cap global ATP+WTA combine)
        remaining_slots = MAX_TENNIS_MATCHES_DISPLAY - total_matches_analyzed
        relevant_matches = candidate_matches[:remaining_slots]

        # Determiner les joueurs qu'on doit reellement fetcher
        # (uniquement ceux dans le Top N : on ne fetch JAMAIS un outsider)
        relevant_player_ids = set()
        for fix in relevant_matches:
            p1_str = str(fix.get("player1Id"))
            p2_str = str(fix.get("player2Id"))
            if fix.get("_p1_in_top"):
                relevant_player_ids.add(p1_str)
            if fix.get("_p2_in_top"):
                relevant_player_ids.add(p2_str)
            # Pour les outsiders : creer le minimal_player tout de suite
            # (sans fetch, juste depuis les donnees fixture)
            if not fix.get("_p1_in_top") and p1_str not in top_players:
                top_players[p1_str] = tennis_mapper.create_minimal_player(
                    p1_str, fix.get("player1") or {}, tour
                )
            if not fix.get("_p2_in_top") and p2_str not in top_players:
                top_players[p2_str] = tennis_mapper.create_minimal_player(
                    p2_str, fix.get("player2") or {}, tour
                )

        print(f"  Candidates futurs : {len(candidate_matches)} (skipped {skipped_past} passes, {skipped_no_top} sans Top {TOP_N_RANKING})")
        print(f"  Selection chronologique : {len(relevant_matches)} matchs (Top {MAX_TENNIS_MATCHES_DISPLAY} premiers)")
        for m in relevant_matches:
            p1_top = "T" if m.get("_p1_in_top") else "OUT"
            p2_top = "T" if m.get("_p2_in_top") else "OUT"
            p1n = (m.get("player1") or {}).get("name", "?")
            p2n = (m.get("player2") or {}).get("name", "?")
            print(f"    [{p1_top} vs {p2_top}] {p1n} vs {p2n} @ {m.get('date', '?')[:16]}")
        print(f"  Joueurs Top {TOP_N_RANKING} a fetcher : {len(relevant_player_ids)} (outsiders skip API)")

        if not relevant_matches:
            output["tours"][tour] = {
                "rankings_count": len(rankings_raw),
                "fixtures_total": len(all_fixtures),
                "matches_analyzed": 0,
            }
            continue

        # === 3. Pour chaque joueur : surface-summary + past-matches ===
        # On utilise le cache persistant (DB) pour le profile bio (TTL 365j).
        from data.bets_db import BetsDB
        bets_db = BetsDB()

        max_to_fetch = MAX_PLAYERS_TO_FETCH  # plus besoin de limite test (relevant_matches deja capped)
        print(f"  Fetch enrichi pour {len(relevant_player_ids)} joueur(s) Top {TOP_N_RANKING}...")
        fetched = 0
        profile_cache_hits = 0
        profile_cache_misses = 0

        for pid in list(relevant_player_ids)[:max_to_fetch]:
            if quota_hit:
                break
            try:
                # Surface summary (ELO calcule depuis ca)
                surface_data = api.get_player_surface_summary(tour, pid)
                if surface_data:
                    top_players[pid] = tennis_mapper.enrich_player_with_surface_data(
                        top_players[pid], surface_data
                    )

                # Past matches (forme recente)
                past = api.get_player_past_matches(tour, pid)
                if past:
                    top_players[pid] = tennis_mapper.enrich_player_with_recent_results(
                        top_players[pid], past
                    )

                # === Profile bio : cache persistant DB (TTL 365j) ===
                api_id_int = top_players[pid].get("api_id")
                cached_profile = None
                if api_id_int:
                    cached_profile = bets_db.get_cached_profile(api_id_int, tour)

                if cached_profile is not None:
                    # Hit cache : pas de req API
                    top_players[pid]["profile"] = cached_profile
                    profile_cache_hits += 1
                else:
                    # Miss : fetch API et stocker
                    profile_raw = api.get_player_profile(tour, pid)
                    profile = tennis_mapper.map_player_profile(profile_raw)
                    top_players[pid]["profile"] = profile
                    profile_cache_misses += 1
                    # Persist en cache
                    if api_id_int:
                        bets_db.cache_profile(
                            api_id=api_id_int, tour=tour,
                            name=top_players[pid].get("name", ""),
                            country=top_players[pid].get("country", ""),
                            profile=profile,
                        )

                # NOUVEAU : Perf breakdown sur les 3 dernieres annees
                perf_raw = api.get_player_perf_breakdown(tour, pid)
                top_players[pid]["perf_breakdown"] = tennis_mapper.aggregate_perf_breakdown(
                    perf_raw, last_n_years=3
                )

                # NOUVEAU : Career stats avec stats serve/return/mental
                vs_all_raw = api.get_h2h_vs_all_stats(tour, pid)
                top_players[pid]["career_stats"] = tennis_mapper.map_career_stats(vs_all_raw)

                fetched += 1
                if fetched % 10 == 0:
                    print(f"    {fetched} joueurs traites...")
            except TennisAPIRateLimit as e:
                print(f"    STOP : {e}")
                quota_hit = True
                break
            except Exception as e:
                print(f"    KO joueur {pid} : {e}")

        print(f"  {fetched} joueurs enrichis (ELO + forme + profile + perf + career)")
        print(f"  Cache profile : {profile_cache_hits} hits, {profile_cache_misses} miss (TTL 365j)")

        # === 4. Analyser chaque match ===
        # relevant_matches est deja limite a MAX_TENNIS_MATCHES_DISPLAY (5) par tri chronologique.
        # Plus besoin de filtre supplementaire ici.
        analyzed_count = 0
        for fix in relevant_matches:
            mapped_match = tennis_mapper.map_match(fix, top_players, tour)
            if not mapped_match:
                continue

            try:
                p_a = mapped_match["player_a"]
                p_b = mapped_match["player_b"]

                # NOUVEAU : Tournament info pour avoir la vraie surface + tier + nom
                tournament_id = mapped_match.get("tournament_id")
                if tournament_id and not quota_hit:
                    try:
                        tour_raw = api.get_tournament_info(tour, tournament_id)
                        tour_info = tennis_mapper.map_tournament_info(tour_raw)
                        if tour_info:
                            # Override la surface hardcodee + nom + tier
                            mapped_match["tournament"] = tour_info.get("name", "")
                            mapped_match["tournament_type"] = tour_info.get("tier", "Other")
                            real_surface = tour_info.get("surface")
                            if real_surface:
                                mapped_match["surface"] = real_surface
                            mapped_match["tournament_country"] = tour_info.get("country", "")
                    except TennisAPIRateLimit:
                        quota_hit = True
                    except Exception as e:
                        print(f"    [WARN] Tournament info {tournament_id} : {e}")

                # H2H matches (last 5 details)
                if not quota_hit:
                    try:
                        h2h_raw = api.get_h2h_matches(tour, p_a["api_id"], p_b["api_id"])
                        h2h_data = tennis_mapper.map_h2h(h2h_raw, p_a["api_id"])
                    except TennisAPIRateLimit:
                        quota_hit = True
                        h2h_data = {"wins_a": 0, "wins_b": 0, "last_5_matches": []}
                    except Exception:
                        h2h_data = {"wins_a": 0, "wins_b": 0, "last_5_matches": []}
                else:
                    h2h_data = {"wins_a": 0, "wins_b": 0, "last_5_matches": []}

                # NOUVEAU : H2H stats specifiques (par surface, mental, tiebreak)
                h2h_specific = {}
                if not quota_hit:
                    try:
                        h2h_stats_raw = api.get_h2h_stats(tour, p_a["api_id"], p_b["api_id"])
                        h2h_specific = tennis_mapper.map_h2h_specific_stats(
                            h2h_stats_raw, p_a["api_id"]
                        )
                    except TennisAPIRateLimit:
                        quota_hit = True
                    except Exception:
                        pass

                # Injecter H2H dans players pour le moteur
                p_a["h2h_wins_vs_opponent"] = h2h_data["wins_a"]
                p_b["h2h_wins_vs_opponent"] = h2h_data["wins_b"]

                # Predictions
                preds = predict_match(
                    p_a, p_b,
                    mapped_match["surface"],
                    mapped_match["tournament_type"],
                    max_sets=mapped_match["max_sets"],
                )

                # === COTES : The Odds API en priorite 1 ===
                # On essaie TOUJOURS The Odds API d'abord (rare que RapidAPI Tennis donne des cotes)
                real_odds = None
                if odds_api_client is not None:
                    try:
                        real_odds = odds_api_client.find_match_odds(
                            p_a["name"], p_b["name"],
                            tour=tour.lower(),
                            match_date_iso=mapped_match.get("date"),
                        )
                    except Exception as e:
                        print(f"  [WARN] OddsAPI find_match : {e}")

                if real_odds:
                    # Priorite 1 : cotes bookmaker reelles via The Odds API
                    mapped_match["odds"] = {
                        "1": real_odds["odd1"],
                        "2": real_odds["odd2"],
                        "_source": "the_odds_api",
                        "_bookmaker": real_odds["bookmaker"],
                        "_bookmaker_key": real_odds["bookmaker_key"],
                        "_last_update": real_odds["last_update"],
                        "_alternates": real_odds.get("alternates", []),
                    }
                    odds_api_hits += 1
                elif mapped_match["odds"].get("_source") == "api":
                    # Priorite 2 : cotes deja fournies par RapidAPI Tennis (rare)
                    pass
                else:
                    # Pas de cotes du tout : on NE met PAS de fallback estimation
                    # → odds vide, on affichera "Cote indisponible"
                    # → pas de value_bet, mais model_pick OK (base sur stats joueurs)
                    mapped_match["odds"] = {"_source": "none"}
                    odds_api_misses += 1

                # Value bets (cotes API uniquement)
                bets = detect_tennis_value_bets(
                    preds, mapped_match["odds"],
                    p_a["name"], p_b["name"],
                )

                # Si pas de value bets API, generer des model_picks (confiance >= 70%)
                # pour pouvoir tracker la fiabilite du modele meme sans cotes reelles
                if not bets:
                    model_picks = generate_model_picks(
                        preds, mapped_match["odds"],
                        p_a["name"], p_b["name"],
                        player_a_id=p_a.get("api_id"),
                        player_b_id=p_b.get("api_id"),
                    )
                    bets = model_picks  # ces "picks" remplacent les value bets manquants

                # Summaries en 3 langues (FR / EN / ES)
                summary_fr = generate_tennis_summary(preds, p_a, p_b, h2h_data, bets, lang="fr")
                summary_en = generate_tennis_summary(preds, p_a, p_b, h2h_data, bets, lang="en")
                summary_es = generate_tennis_summary(preds, p_a, p_b, h2h_data, bets, lang="es")
                summaries = {"fr": summary_fr, "en": summary_en, "es": summary_es}

                conf = confidence_score_match(preds, bets)

                output["matches"].append({
                    **mapped_match,
                    "predictions": preds,
                    "h2h": h2h_data,
                    "h2h_specific": h2h_specific,
                    "value_bets": bets,
                    "summary": summary_fr,           # garde rétro-compat
                    "summaries": summaries,           # nouveau : 3 langues
                    "confidence_score": conf,
                })

                analyzed_count += 1
                total_matches_analyzed += 1

                for b in bets:
                    if b["edge_pct"] >= 5:
                        output["value_bets"].append({
                            **b,
                            "match_id": mapped_match["id"],
                            "match_label": f"{p_a['name']} vs {p_b['name']}",
                            "tournament": mapped_match.get("tournament", ""),
                            "tour": tour.upper(),
                            "date": mapped_match["date"],
                        })
            except Exception as e:
                print(f"  KO analyse : {e}")

        output["tours"][tour] = {
            "rankings_count": len(rankings_raw),
            "fixtures_total": len(all_fixtures),
            "matches_analyzed": analyzed_count,
        }

    # Tri value bets par edge
    output["value_bets"].sort(key=lambda b: -b["edge_pct"])
    output["generated_at"] = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())

    # NOTE : la selection des matchs est faite chronologiquement EN AMONT
    # (top 5 chronologiques dans la boucle tour). Plus de re-tri ici.
    # On s'assure juste que l'ordre final est chronologique pour l'affichage.
    output["matches"].sort(key=lambda m: m.get("start_timestamp_ms") or 0)

    # === PUSH PARIS DANS LA DB DE TRACKING ===
    try:
        from data.bets_db import BetsDB
        db = BetsDB()
        total_added = 0
        for m in output["matches"]:
            added = db.add_bets_for_match(m)
            total_added += added
        print(f"\n  Tracking DB : {total_added} nouveaux paris ajoutes")

        # Export ai_stats.json pour le frontend statique
        ai_stats_path = os.path.normpath(os.path.join(BACKEND_DIR, "..", "frontend", "ai_stats.json"))
        with open(ai_stats_path, "w", encoding="utf-8") as f:
            json.dump(db.export_to_dict(), f, default=str, ensure_ascii=False)
        print(f"  ai_stats.json exporte ({os.path.getsize(ai_stats_path) / 1024:.1f} KB)")
    except Exception as e:
        print(f"  [WARN] Tracking DB : {e}")

    # Ecrire data_tennis.json sur disque (legacy fallback)
    output_path = os.path.normpath(os.path.join(BACKEND_DIR, "..", "frontend", "data_tennis.json"))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, default=str, ensure_ascii=False)

    size_kb = os.path.getsize(output_path) / 1024

    # Ecrire AUSSI dans Turso DB (persistant à vie, survit aux redeploys)
    try:
        from data.bets_db import get_conn, USE_TURSO
        if USE_TURSO:
            json_str = json.dumps(output, default=str, ensure_ascii=False)
            with get_conn() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS kv_store (
                        key TEXT PRIMARY KEY,
                        data_json TEXT NOT NULL,
                        updated_at TEXT
                    )
                """)
                conn.execute("""
                    INSERT INTO kv_store (key, data_json, updated_at)
                    VALUES ('data_tennis', ?, datetime('now'))
                    ON CONFLICT(key) DO UPDATE SET
                        data_json = excluded.data_json,
                        updated_at = excluded.updated_at
                """, (json_str,))
            print(f"  data_tennis.json sauve dans Turso DB ({len(json_str)//1024} KB)")
    except Exception as e:
        print(f"  [WARN] Sauvegarde Turso : {e}")

    # === ENVOI DISCORD (si webhook configure) ===
    try:
        from integrations import discord_notifier
        discord_notifier.send_daily_picks(output["matches"])
    except Exception as e:
        print(f"  [WARN] Discord : {e}")

    print("\n" + "=" * 60)
    print("OK Refresh tennis termine")
    print(f"  ATP : {output['tours'].get('atp', {}).get('matches_analyzed', 0)} matchs")
    print(f"  WTA : {output['tours'].get('wta', {}).get('matches_analyzed', 0)} matchs")
    print(f"  Total value bets : {len(output['value_bets'])}")
    print(f"  Fichier : {output_path} ({size_kb:.1f} KB)")
    print(f"  Requetes API Tennis : {api.calls_made}")
    if odds_api_client is not None:
        total_attempts = odds_api_hits + odds_api_misses
        if total_attempts > 0:
            print(f"  The Odds API : {odds_api_hits}/{total_attempts} matchs avec vraies cotes ({100*odds_api_hits//total_attempts}%)")
            if odds_api_client.quota_remaining:
                print(f"  Quota Odds API restant : {odds_api_client.quota_remaining}")
    print(f"  Cache : {cache.stats()}")
    if quota_hit:
        print(f"\n  ! Quota epuise pendant le run, certaines donnees manquent.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Vider cache et tout retelecharger")
    parser.add_argument("--test-output", action="store_true", help="Test 1 match seulement (economise quota)")
    args = parser.parse_args()
    main(force=args.force, test_output=args.test_output)
