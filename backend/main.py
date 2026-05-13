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

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from typing import Optional

# Path du dossier frontend (au meme niveau que backend)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.teams import get_team, get_all_teams
from data.players import get_team_players, get_lineup_starters
from data.matches import get_match, get_all_matches, get_h2h
from engine.football.team_analysis import calculate_team_overall
from engine.football.player_analysis import (
    analyze_team_players,
    analyze_goalkeeper,
    detect_key_players_to_watch,
)
from engine.football.predictions import predict_match
from engine.football.value_bets import detect_value_bets
from engine.football.summary import generate_match_summary, confidence_score


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


# =============== TENNIS ENDPOINTS ===============

def _load_tennis_data():
    """Charge data_tennis.json (genere par jobs/refresh_tennis.py)."""
    import json
    path = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "frontend", "data_tennis.json"
    ))
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


@app.get("/api/tennis/matches")
def tennis_matches(tour: str = None):
    """Matchs tennis du jour. Filtrable par tour (atp/wta)."""
    data = _load_tennis_data()
    if not data:
        raise HTTPException(404, "Tennis data not yet generated. Run python -m jobs.refresh_tennis")

    matches = data.get("matches", [])
    if tour:
        matches = [m for m in matches if m.get("tour", "").lower() == tour.lower()]
    return matches


@app.get("/api/tennis/match/{match_id}")
def tennis_match_detail(match_id: str):
    """Detail d'un match tennis."""
    data = _load_tennis_data()
    if not data:
        raise HTTPException(404, "Tennis data not yet generated")
    for m in data.get("matches", []):
        if m["id"] == match_id:
            return m
    raise HTTPException(404, f"Match {match_id} not found")


@app.get("/api/tennis/value-bets")
def tennis_value_bets(min_edge: float = 5.0, tour: str = None):
    """Top value bets tennis."""
    data = _load_tennis_data()
    if not data:
        return []
    bets = [b for b in data.get("value_bets", []) if b["edge_pct"] >= min_edge]
    if tour:
        bets = [b for b in bets if b.get("tour", "").lower() == tour.lower()]
    return bets


@app.get("/api/tennis/stats")
def tennis_stats():
    """Stats globales tennis."""
    data = _load_tennis_data()
    if not data:
        return {"available": False}
    return {
        "available": True,
        "generated_at": data.get("generated_at"),
        "tours": data.get("tours", {}),
        "total_matches": len(data.get("matches", [])),
        "total_value_bets": len(data.get("value_bets", [])),
    }


# =============== AI STATS / TRACKING DES PARIS ===============

@app.get("/api/ai-stats")
def ai_stats():
    """Stats de fiabilite de l'IA Varion (paris valides/perdus)."""
    try:
        from data.bets_db import BetsDB
        db = BetsDB()
        return db.export_to_dict()
    except Exception as e:
        return {"error": str(e), "global": {"total": 0, "won": 0, "lost": 0,
                "settled": 0, "win_rate_pct": 0, "roi_pct": 0}}


@app.get("/api/tennis-data")
def get_tennis_data():
    """Renvoie le contenu de data_tennis.json (genere par refresh_tennis).
    Endpoint utile quand le frontend est heberge separement (GitHub Pages, etc.)
    """
    import json as _json
    data_path = os.path.join(FRONTEND_DIR, "data_tennis.json")
    if not os.path.exists(data_path):
        return {"matches": [], "generated_at": None, "error": "Pas encore de donnees. Lancez /api/admin/refresh-tennis"}
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/football-data")
def get_football_data():
    """Renvoie le contenu de data.json (foot, actuellement inactif)."""
    import json as _json
    data_path = os.path.join(FRONTEND_DIR, "data.json")
    if not os.path.exists(data_path):
        return {"matches": [], "error": "Foot inactif"}
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai-stats/resolve")
def resolve_pending_bets(authorization: Optional[str] = Header(None)):
    """Trigger manuel pour resoudre les paris pending (admin).
    Necessite un header Authorization: Bearer <ADMIN_TOKEN>
    """
    _check_admin_auth(authorization)
    try:
        from jobs.resolve_bets import main as resolve_main
        resolve_main()
        from data.bets_db import BetsDB
        return BetsDB().get_global_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/refresh-tennis")
def admin_refresh_tennis(authorization: Optional[str] = Header(None)):
    """Trigger refresh tennis (appelable depuis cron-job.org).
    Necessite un header Authorization: Bearer <ADMIN_TOKEN>
    """
    _check_admin_auth(authorization)
    try:
        from jobs.refresh_tennis import main as refresh_main
        result = refresh_main()
        return {"status": "ok", "result": result if result else "completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/resolve-bets")
def admin_resolve_bets(authorization: Optional[str] = Header(None)):
    """Alias public de /api/ai-stats/resolve pour cron-job.org"""
    return resolve_pending_bets(authorization)


# =============== GOOGLE SHEETS SYNC ENDPOINTS ===============

def _check_sheets_auth(authorization: str):
    """Verifie le token sheets. Format attendu : 'Bearer <SHEETS_TOKEN>'"""
    sheets_token = os.environ.get("SHEETS_TOKEN")
    if not sheets_token:
        return  # dev local : pas de token configure
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    provided = authorization.replace("Bearer ", "").strip()
    if provided != sheets_token:
        raise HTTPException(status_code=403, detail="Invalid sheets token")


@app.get("/api/sheets/pending-bets")
def sheets_get_pending_bets(authorization: Optional[str] = Header(None)):
    """Retourne les paris IA generes mais pas encore syncs sur Google Sheets.
    Format simplifie pour Apps Script :
    [
      {
        "match_id": "T_1234",
        "date": "2026-05-12",
        "tour": "ATP",
        "tournament": "Madrid Open",
        "surface": "Clay",
        "player_a": "Carlos Alcaraz",
        "player_b": "Jannik Sinner",
        "predicted_winner": "Carlos Alcaraz",
        "predicted_score": "2-1",
        "predicted_games": 23,
        "type": "Principale",
        "bet_label": "",
        "odds": "",
        "model_prob": 58
      },
      ...
    ]
    """
    _check_sheets_auth(authorization)
    import json as _json
    data_path = os.path.join(FRONTEND_DIR, "data_tennis.json")
    if not os.path.exists(data_path):
        return []
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = _json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    output = []
    for m in data.get("matches", []):
        pa = m.get("player_a") or {}
        pb = m.get("player_b") or {}
        preds = m.get("predictions") or {}
        winner_obj = preds.get("winner") or {}
        prob_a = winner_obj.get("prob_a", 50)
        prob_b = winner_obj.get("prob_b", 50)

        # Predit vainqueur = joueur avec proba max
        predicted_winner_name = pa.get("name") if prob_a >= prob_b else pb.get("name")
        predicted_winner_prob = max(prob_a, prob_b)

        # Score predit (a partir du score model si dispo, sinon "2-0" pour favori, "2-1" si serre)
        score_obj = preds.get("score") or {}
        if score_obj.get("predicted"):
            predicted_score = score_obj.get("predicted")
        elif predicted_winner_prob >= 65:
            predicted_score = "2-0"
        else:
            predicted_score = "2-1"

        # Nb total jeux predit (si dispo)
        games_obj = preds.get("total_games") or {}
        predicted_games = games_obj.get("predicted", 0)

        # === Bet PRINCIPALE (vainqueur predit) ===
        output.append({
            "match_id": m.get("id", ""),
            "api_match_id": m.get("api_id"),
            "date": (m.get("date") or "")[:10],
            "time": (m.get("date") or "")[11:16] if len(m.get("date") or "") >= 16 else "",
            "tour": m.get("tour", ""),
            "tournament": m.get("tournament", ""),
            "round": m.get("round", ""),
            "surface": (m.get("surface") or "").capitalize(),
            "player_a": pa.get("name", ""),
            "player_b": pb.get("name", ""),
            "predicted_winner": predicted_winner_name,
            "predicted_score": predicted_score,
            "predicted_games": predicted_games,
            "type": "Principale",
            "bet_label": "",
            "odds": "",
            "model_prob": predicted_winner_prob,
        })

        # === Bet RECOMMANDEES (value bets) ===
        for bet in (m.get("value_bets") or []):
            output.append({
                "match_id": m.get("id", ""),
                "api_match_id": m.get("api_id"),
                "date": (m.get("date") or "")[:10],
                "time": (m.get("date") or "")[11:16] if len(m.get("date") or "") >= 16 else "",
                "tour": m.get("tour", ""),
                "tournament": m.get("tournament", ""),
                "round": m.get("round", ""),
                "surface": (m.get("surface") or "").capitalize(),
                "player_a": pa.get("name", ""),
                "player_b": pb.get("name", ""),
                "predicted_winner": "",
                "predicted_score": "",
                "predicted_games": "",
                "type": "Recommandée",
                "bet_label": bet.get("market", ""),
                "odds": bet.get("odds", 0),
                "model_prob": bet.get("model_prob", 0),
            })

    return output


@app.post("/api/sheets/submit-results")
def sheets_submit_results(payload: dict, authorization: Optional[str] = Header(None)):
    """Recoit une liste de resultats depuis Apps Script et les enregistre en DB.

    Payload format :
    {
      "results": [
        {
          "match_id": "T_1234",
          "type": "Principale",         // ou "Recommandée"
          "real_winner": "Carlos Alcaraz",
          "real_score": "2-0",
          "real_games": 19,
          "bet_result": ""              // pour "Recommandée" : Gagné / Perdu
        },
        ...
      ]
    }

    Retourne le nb de paris mis a jour + erreurs.
    """
    _check_sheets_auth(authorization)
    results = payload.get("results") or []
    if not isinstance(results, list):
        raise HTTPException(status_code=400, detail="results must be a list")

    from data.bets_db import BetsDB, get_conn
    db = BetsDB()
    updated = 0
    errors = []

    with get_conn() as conn:
        for r in results:
            match_id = r.get("match_id", "")
            type_str = r.get("type", "Principale")
            if not match_id:
                continue

            try:
                if type_str == "Recommandée":
                    # Pari recommandee : bet_result donne Gagné/Perdu directement
                    bet_result = r.get("bet_result", "").lower()
                    if bet_result in ("gagné", "gagne", "won", "win"):
                        status = "won"
                    elif bet_result in ("perdu", "lost", "loss"):
                        status = "lost"
                    else:
                        continue
                    # Update tous les value bets pending de ce match
                    conn.execute("""
                        UPDATE bets SET status = ?, resolved_at = datetime('now')
                        WHERE match_id = ? AND status = 'pending' AND bet_type = 'value_bet'
                    """, (status, match_id))
                    if conn.total_changes > 0:
                        updated += 1
                else:
                    # Pari principale : real_winner determine le winner
                    real_winner = r.get("real_winner", "")
                    if not real_winner:
                        continue
                    # Chercher le pari pour determiner si winner correspond a la selection
                    row = conn.execute("""
                        SELECT id, selection, player_a_name, player_b_name FROM bets
                        WHERE match_id = ? AND status = 'pending'
                        LIMIT 1
                    """, (match_id,)).fetchone()
                    if not row:
                        errors.append(f"{match_id}: no pending bet found")
                        continue
                    # Si real_winner = selection → won, sinon lost
                    selection = (row["selection"] or "").strip().lower()
                    rw = real_winner.strip().lower()
                    if rw in selection or selection in rw:
                        status = "won"
                    else:
                        status = "lost"
                    conn.execute("""
                        UPDATE bets SET status = ?, resolved_at = datetime('now')
                        WHERE match_id = ? AND status = 'pending'
                    """, (status, match_id))
                    if conn.total_changes > 0:
                        updated += 1
            except Exception as e:
                errors.append(f"{match_id}: {e}")

    return {"updated": updated, "errors": errors, "total_received": len(results)}


# =============== END GOOGLE SHEETS SYNC ===============


def _check_admin_auth(authorization: str):
    """Verifie le token admin. Format attendu : 'Bearer <TOKEN>'"""
    admin_token = os.environ.get("ADMIN_TOKEN")
    if not admin_token:
        # En dev local : pas de token configure, on laisse passer (utile pour tests)
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    provided = authorization.replace("Bearer ", "").strip()
    if provided != admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")


# =============== FRONTEND STATIC FILES ===============
# Le backend sert aussi le frontend statique en production
# (1 seul service Render au lieu de 2)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

if os.path.exists(FRONTEND_DIR):
    # Servir les fichiers statiques (js, css, assets)
    app.mount("/src", StaticFiles(directory=os.path.join(FRONTEND_DIR, "src")), name="src")
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets"), check_dir=False), name="assets")

    # Route catch-all : sert index.html pour toutes les autres URLs (SPA)
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        # Si le fichier existe dans frontend/, on le sert
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Sinon fallback sur index.html (single-page app)
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
