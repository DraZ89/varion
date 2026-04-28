"""
API FastAPI - Sports Betting Analytics

Endpoints :
- GET  /api/teams                  -> liste des équipes
- GET  /api/teams/{id}             -> détail équipe + score
- GET  /api/teams/{id}/players     -> joueurs d'une équipe
- GET  /api/matches                -> liste des matchs à venir + prédictions résumées
- GET  /api/matches/{id}           -> analyse complète d'un match
- GET  /api/value-bets             -> top value bets tous matchs confondus
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.teams import get_team, get_all_teams
from data.players import get_team_players, get_lineup_starters
from data.matches import get_match, get_all_matches, get_h2h
from engine.team_analysis import calculate_team_overall
from engine.player_analysis import (
    analyze_team_players,
    analyze_goalkeeper,
    detect_key_players_to_watch,
)
from engine.predictions import predict_match
from engine.value_bets import detect_value_bets
from engine.summary import generate_match_summary, confidence_score


app = FastAPI(
    title="Sports Betting Analytics API",
    description="Analyse statistique avancée et détection de value bets",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============== ROOT ===============

@app.get("/")
def root():
    return {
        "name": "Sports Betting Analytics API",
        "version": "1.0.0",
        "endpoints": [
            "/api/teams",
            "/api/teams/{id}",
            "/api/teams/{id}/players",
            "/api/matches",
            "/api/matches/{id}",
            "/api/value-bets",
        ],
    }


# =============== EQUIPES ===============

@app.get("/api/teams")
def list_teams():
    teams = get_all_teams()
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "short": t["short"],
            "rank": t["rank"],
            "points": t["points"],
            "logo_color": t["logo_color"],
            "logo_url": t.get("logo_url"),
        }
        for t in teams
    ]


@app.get("/api/teams/{team_id}")
def team_detail(team_id: str):
    team = get_team(team_id)
    if not team:
        raise HTTPException(404, f"Team {team_id} not found")

    overall_home = calculate_team_overall(team_id, is_home=True)
    overall_away = calculate_team_overall(team_id, is_home=False)
    gk = analyze_goalkeeper(team_id)

    return {
        "team": team,
        "scores_home": overall_home,
        "scores_away": overall_away,
        "goalkeeper": gk,
    }


@app.get("/api/teams/{team_id}/players")
def team_players(team_id: str):
    team = get_team(team_id)
    if not team:
        raise HTTPException(404, f"Team {team_id} not found")

    players = analyze_team_players(team_id)
    starters = [p["id"] for p in get_lineup_starters(team_id, top_n=11)]
    gk = analyze_goalkeeper(team_id)

    return {
        "team_id": team_id,
        "team_name": team["name"],
        "starters_ids": starters,
        "players": players,
        "goalkeeper": gk,
    }


# =============== MATCHS ===============

@app.get("/api/matches")
def list_matches():
    """Liste tous les matchs à venir avec un résumé prédictif."""
    matches = get_all_matches()
    out = []

    for m in matches:
        home_id = m["home"]
        away_id = m["away"]
        home = get_team(home_id)
        away = get_team(away_id)

        # Prédictions complètes
        match_ctx = {
            "ref_yellow_avg": m["ref_yellow_avg"],
            "is_derby": m["is_derby"],
            "stakes": m["stakes"],
        }
        predictions = predict_match(home_id, away_id, match_ctx)

        # Joueurs clés pour scorer betting
        away_def = calculate_team_overall(away_id, is_home=False)["defense_score"]
        home_def = calculate_team_overall(home_id, is_home=True)["defense_score"]
        all_scorers = (
            analyze_team_players(home_id, away_def, is_home=True)
            + analyze_team_players(away_id, home_def, is_home=False)
        )

        # Value bets
        value_bets = detect_value_bets(predictions, m["odds"], all_scorers)
        confidence = confidence_score(predictions, value_bets)

        # Top value bet
        top_bet = value_bets[0] if value_bets else None

        out.append({
            "id": m["id"],
            "date": m["date"],
            "kickoff": m["kickoff"],
            "competition": m["competition"],
            "venue": m["venue"],
            "is_derby": m["is_derby"],
            "stakes": m["stakes"],
            "home": {
                "id": home_id,
                "name": home["name"],
                "short": home["short"],
                "logo_color": home["logo_color"],
                "logo_url": home.get("logo_url"),
                "rank": home["rank"],
            },
            "away": {
                "id": away_id,
                "name": away["name"],
                "short": away["short"],
                "logo_color": away["logo_color"],
                "logo_url": away.get("logo_url"),
                "rank": away["rank"],
            },
            "odds_main": {
                "1": m["odds"]["1"],
                "X": m["odds"]["X"],
                "2": m["odds"]["2"],
            },
            "predictions_summary": {
                "prob_home": predictions["result"]["prob_home_win"],
                "prob_draw": predictions["result"]["prob_draw"],
                "prob_away": predictions["result"]["prob_away_win"],
                "expected_goals": predictions["over_under_25"]["expected_total"],
                "expected_corners": predictions["corners"]["expected_total"],
                "expected_cards": predictions["cards"]["expected_total"],
                "btts_prob": predictions["btts"]["prob_yes"],
                "intensity": predictions["intensity_score"],
                "most_likely_score": predictions["result"]["most_likely_score"],
            },
            "top_value_bet": top_bet,
            "value_bets_count": len(value_bets),
            "confidence_score": confidence,
        })

    return out


@app.get("/api/matches/{match_id}")
def match_detail(match_id: str):
    """Analyse complète et exhaustive d'un match."""
    m = get_match(match_id)
    if not m:
        raise HTTPException(404, f"Match {match_id} not found")

    home_id = m["home"]
    away_id = m["away"]
    home = get_team(home_id)
    away = get_team(away_id)

    # ----- Scores équipes -----
    home_overall = calculate_team_overall(home_id, is_home=True)
    away_overall = calculate_team_overall(away_id, is_home=False)

    # ----- Prédictions -----
    match_ctx = {
        "ref_yellow_avg": m["ref_yellow_avg"],
        "is_derby": m["is_derby"],
        "stakes": m["stakes"],
    }
    predictions = predict_match(home_id, away_id, match_ctx)

    # ----- Joueurs -----
    home_players = analyze_team_players(home_id, away_overall["defense_score"], is_home=True)
    away_players = analyze_team_players(away_id, home_overall["defense_score"], is_home=False)

    # Joueurs clés à surveiller (4 par équipe)
    key_home = detect_key_players_to_watch(home_id, away_overall["defense_score"], True, 4)
    key_away = detect_key_players_to_watch(away_id, home_overall["defense_score"], False, 4)

    # Gardiens
    gk_home = analyze_goalkeeper(home_id)
    gk_away = analyze_goalkeeper(away_id)

    # Lineups (XI type)
    starters_home = get_lineup_starters(home_id, 11)
    starters_away = get_lineup_starters(away_id, 11)

    # ----- H2H -----
    h2h = get_h2h(home_id, away_id)

    # ----- Value Bets -----
    all_scorers = home_players + away_players
    value_bets = detect_value_bets(predictions, m["odds"], all_scorers)

    # ----- Résumé IA + confiance -----
    summary = generate_match_summary(
        home_id, away_id,
        home_overall, away_overall,
        predictions,
        value_bets,
        key_home, key_away,
    )
    confidence = confidence_score(predictions, value_bets)

    return {
        "id": m["id"],
        "date": m["date"],
        "kickoff": m["kickoff"],
        "venue": m["venue"],
        "competition": m["competition"],
        "referee": m["referee"],
        "is_derby": m["is_derby"],
        "stakes": m["stakes"],
        "summary": summary,
        "confidence_score": confidence,
        "teams": {
            "home": {
                "info": home,
                "scores": home_overall,
                "goalkeeper": gk_home,
                "starters": [{"id": p["id"], "name": p["name"], "pos": p["pos"], "starts": p["starts"]} for p in starters_home],
                "key_players": key_home,
                "all_players": home_players,
            },
            "away": {
                "info": away,
                "scores": away_overall,
                "goalkeeper": gk_away,
                "starters": [{"id": p["id"], "name": p["name"], "pos": p["pos"], "starts": p["starts"]} for p in starters_away],
                "key_players": key_away,
                "all_players": away_players,
            },
        },
        "predictions": predictions,
        "odds": m["odds"],
        "value_bets": value_bets,
        "h2h": h2h,
    }


# =============== VALUE BETS ===============

@app.get("/api/value-bets")
def all_value_bets(min_edge: float = 5.0):
    """Top value bets de tous les matchs à venir, triés par edge."""
    matches = get_all_matches()
    all_bets = []

    for m in matches:
        home_id = m["home"]
        away_id = m["away"]
        home = get_team(home_id)
        away = get_team(away_id)

        match_ctx = {
            "ref_yellow_avg": m["ref_yellow_avg"],
            "is_derby": m["is_derby"],
            "stakes": m["stakes"],
        }
        predictions = predict_match(home_id, away_id, match_ctx)

        away_def = calculate_team_overall(away_id, is_home=False)["defense_score"]
        home_def = calculate_team_overall(home_id, is_home=True)["defense_score"]
        all_scorers = (
            analyze_team_players(home_id, away_def, is_home=True)
            + analyze_team_players(away_id, home_def, is_home=False)
        )

        bets = detect_value_bets(predictions, m["odds"], all_scorers)
        for b in bets:
            if b["edge_pct"] >= min_edge:
                b["match_id"] = m["id"]
                b["match_label"] = f"{home['short']} vs {away['short']}"
                b["match_date"] = m["date"]
                b["match_kickoff"] = m["kickoff"]
                all_bets.append(b)

    all_bets.sort(key=lambda b: -b["edge_pct"])
    return all_bets


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
