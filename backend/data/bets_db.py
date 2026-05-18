"""
Module de tracking des paris IA Varion.

Stocke l'historique des paris proposes par l'IA dans une base SQLite locale.
Permet de calculer les stats de fiabilite (win rate, ROI, edge moyen, etc.).

Schema :
- bets : 1 ligne par pari propose (won/lost/pending/void)
- match_results : 1 ligne par match (resultat, joueur winner, score)

Usage :
    from data.bets_db import BetsDB
    db = BetsDB()
    db.add_bet(match_id="T_1237", market="Vainqueur Mannarino", ...)
    db.resolve_bet(match_id="T_1237", winner_player_id=12345)
    stats = db.get_global_stats()
"""

import os
import sqlite3
import os


# =========== TURSO / LIBSQL ADAPTER ===========
# Si TURSO_DB_URL et TURSO_AUTH_TOKEN sont definis, on utilise Turso (DB cloud persistante).
# Sinon, fallback sur SQLite local (dev / Render free sans persistance).

TURSO_URL = os.environ.get("TURSO_DB_URL", "").strip()
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "").strip()
USE_TURSO = bool(TURSO_URL and TURSO_TOKEN)

if USE_TURSO:
    try:
        import libsql
        print(f"[BetsDB] Mode TURSO : {TURSO_URL[:50]}...")
    except ImportError:
        try:
            # Fallback : ancien nom du package
            import libsql_experimental as libsql
            print(f"[BetsDB] Mode TURSO (libsql_experimental) : {TURSO_URL[:50]}...")
        except ImportError:
            print("[BetsDB] libsql non installe, fallback SQLite local")
            USE_TURSO = False


class _TursoConnWrapper:
    """Wrapper qui imite l'interface sqlite3.Connection pour libsql.

    Permet de garder tout le code existant inchange (with get_conn() as conn: ...).
    """

    def __init__(self):
        self._conn = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
        # Active row_factory equivalent : retourner des dicts (acces par nom de colonne)

    def execute(self, sql, params=()):
        cursor = self._conn.execute(sql, params)
        return _TursoCursor(cursor)

    def executescript(self, script):
        # libsql ne supporte pas executescript directement, on split par ';'
        statements = [s.strip() for s in script.split(';') if s.strip()]
        for stmt in statements:
            try:
                self._conn.execute(stmt)
            except Exception as e:
                # IGNORE pour IF NOT EXISTS qui repete des declarations
                if "already exists" not in str(e).lower():
                    raise
        return self

    def commit(self):
        self._conn.commit()

    def close(self):
        # libsql n'a pas vraiment de close, c'est OK
        pass

    @property
    def total_changes(self):
        # libsql n'expose pas total_changes, on retourne -1 si pas disponible
        return getattr(self._conn, 'total_changes', -1)


class _TursoRow:
    """Imite sqlite3.Row : acces par index ou par nom de colonne."""
    def __init__(self, values, columns):
        self._values = values
        self._columns = columns
        self._map = {col: i for i, col in enumerate(columns)}

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._values[self._map[key]]
        return self._values[key]

    def keys(self):
        return list(self._columns)


class _TursoCursor:
    """Wrapper pour les curseurs libsql, expose rowcount + fetchone + fetchall."""

    def __init__(self, libsql_result):
        self._result = libsql_result
        self._columns = None
        try:
            # libsql expose les colonnes via .description
            desc = getattr(libsql_result, 'description', None)
            if desc:
                self._columns = [d[0] for d in desc]
        except Exception:
            pass

    @property
    def rowcount(self):
        return getattr(self._result, 'rowcount', -1)

    @property
    def lastrowid(self):
        return getattr(self._result, 'lastrowid', None)

    def fetchone(self):
        try:
            row = self._result.fetchone()
        except Exception:
            return None
        if row is None:
            return None
        if self._columns:
            return _TursoRow(row, self._columns)
        return row

    def fetchall(self):
        try:
            rows = self._result.fetchall()
        except Exception:
            return []
        if self._columns:
            return [_TursoRow(r, self._columns) for r in rows]
        return rows

# =========== END TURSO ADAPTER ===========


import json
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager


DB_PATH = Path(__file__).parent / "varion_bets.sqlite"


SCHEMA = """
CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    api_match_id INTEGER,
    sport TEXT NOT NULL DEFAULT 'tennis',
    tour TEXT,                          -- ATP / WTA / etc.
    tournament TEXT,
    surface TEXT,
    match_date TEXT,                    -- ISO YYYY-MM-DD
    match_timestamp_ms INTEGER,         -- UTC ms
    player_a_id INTEGER,
    player_a_name TEXT,
    player_b_id INTEGER,
    player_b_name TEXT,
    -- Pari lui-meme
    market TEXT NOT NULL,                -- "Vainqueur Mannarino"
    market_key TEXT,                     -- "1" / "2"
    selection TEXT,                      -- nom du joueur selectionne
    selection_player_id INTEGER,         -- id joueur selectionne
    odds REAL NOT NULL,                  -- cote (ex 1.95)
    edge_pct REAL,                       -- edge en %
    model_prob REAL,                     -- probabilite modele (0-100)
    implied_prob REAL,                   -- probabilite implicite cote
    confidence TEXT,                     -- strong / high / medium / model_only
    bet_type TEXT NOT NULL DEFAULT 'value_bet', -- value_bet (cote API) vs model_pick (sans cote)
    -- Resolution
    status TEXT NOT NULL DEFAULT 'pending', -- pending / won / lost / void
    settled_at TEXT,                     -- ISO datetime
    profit_units REAL,                   -- gain net en unites (1 unite mise)
    -- Tracking
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(match_id, market_key)         -- un seul pari par marche par match
);

CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(status);
CREATE INDEX IF NOT EXISTS idx_bets_match_id ON bets(match_id);
CREATE INDEX IF NOT EXISTS idx_bets_created ON bets(created_at);
CREATE INDEX IF NOT EXISTS idx_bets_surface ON bets(surface);
CREATE INDEX IF NOT EXISTS idx_bets_tour ON bets(tour);


CREATE TABLE IF NOT EXISTS match_results (
    match_id TEXT PRIMARY KEY,
    api_match_id INTEGER,
    winner_player_id INTEGER,           -- id du joueur vainqueur
    winner_name TEXT,
    final_score TEXT,                   -- ex "6-4 6-3"
    sets_a INTEGER,
    sets_b INTEGER,
    resolved_at TEXT NOT NULL DEFAULT (datetime('now'))
);


-- Cache persistant des profils joueurs (bio fige : taille/poids/main/lieu)
-- TTL : 365 jours (un joueur change pas son lieu de naissance ni sa main directrice)
CREATE TABLE IF NOT EXISTS players_cache (
    api_id INTEGER NOT NULL,
    tour TEXT NOT NULL,                  -- ATP / WTA
    name TEXT,
    country TEXT,
    profile_json TEXT,                   -- bio json (height, weight, plays, birthplace, ...)
    profile_fetched_at TEXT,             -- ISO datetime
    PRIMARY KEY (api_id, tour)
);

CREATE INDEX IF NOT EXISTS idx_players_fetched ON players_cache(profile_fetched_at);
"""


@contextmanager
def get_conn():
    """Context manager pour la connexion DB (Turso si configure, sinon SQLite local)."""
    if USE_TURSO:
        conn = _TursoConnWrapper()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


class BetsDB:
    """Wrapper haut-niveau pour gerer les paris et leurs stats."""

    def __init__(self, db_path: str = None):
        global DB_PATH
        if db_path:
            DB_PATH = Path(db_path)
        # Mkdir uniquement en mode SQLite local
        if not USE_TURSO:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self):
        with get_conn() as conn:
            conn.executescript(SCHEMA)
            # Migration : ajouter bet_type si la colonne n'existe pas
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(bets)").fetchall()]
                if "bet_type" not in cols:
                    conn.execute("ALTER TABLE bets ADD COLUMN bet_type TEXT NOT NULL DEFAULT 'value_bet'")
            except Exception as e:
                pass  # colonne deja la

    # ========== AJOUT DE PARIS ==========

    def add_bet(self, match: dict, bet: dict, player_a_id=None, player_b_id=None) -> bool:
        """Ajoute un pari propose par l'IA. Retourne True si insere, False si echec.

        Si un pari pending existe deja pour ce match, il est SUPPRIME et remplace
        (evite les contradictions quand l'IA change d'avis entre 2 refresh).

        match : dict du match (avec id, tour, tournament, surface, etc.)
        bet : dict du value bet (market, odds, edge_pct, model_prob, ...)
        """
        # Determine quel joueur est selectionne
        selection_id = None
        if bet.get("market_key") == "1":
            selection_id = player_a_id
        elif bet.get("market_key") == "2":
            selection_id = player_b_id

        match_id = match.get("id", "")
        if not match_id:
            return False

        try:
            with get_conn() as conn:
                # ETAPE 1 : Supprimer les anciens paris pending pour ce match
                # (evite les contradictions/doublons quand l'IA change d'avis)
                conn.execute(
                    "DELETE FROM bets WHERE match_id = ? AND status = 'pending'",
                    (match_id,)
                )

                # ETAPE 2 : Inserer le nouveau pari
                cur = conn.execute("""
                    INSERT OR IGNORE INTO bets (
                        match_id, api_match_id, sport, tour, tournament, surface,
                        match_date, match_timestamp_ms,
                        player_a_id, player_a_name, player_b_id, player_b_name,
                        market, market_key, selection, selection_player_id,
                        odds, edge_pct, model_prob, implied_prob, confidence, bet_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    match_id,
                    match.get("api_id"),
                    match.get("sport", "tennis"),
                    match.get("tour", ""),
                    match.get("tournament", ""),
                    match.get("surface", ""),
                    match.get("date", ""),
                    match.get("start_timestamp_ms"),
                    player_a_id,
                    (match.get("player_a") or {}).get("name", ""),
                    player_b_id,
                    (match.get("player_b") or {}).get("name", ""),
                    bet.get("market", ""),
                    bet.get("market_key", ""),
                    bet.get("selection", ""),
                    selection_id,
                    bet.get("odds", 0),
                    bet.get("edge_pct", 0),
                    bet.get("model_prob", 0),
                    bet.get("implied_prob", 0),
                    bet.get("confidence", "medium"),
                    ("model_pick_no_odds" if bet.get("no_real_odds")
                     else bet.get("type", "value_bet")),
                ))
                return cur.rowcount > 0
        except Exception as e:
            print(f"[BetsDB] Erreur add_bet : {e}")
            return False

    def add_bets_for_match(self, match: dict) -> int:
        """Ajoute tous les value bets d'un match. Retourne le nb de paris inseres."""
        bets = match.get("value_bets") or []
        if not bets:
            return 0
        p_a = match.get("player_a") or {}
        p_b = match.get("player_b") or {}
        count = 0
        for bet in bets:
            if self.add_bet(match, bet,
                            player_a_id=p_a.get("api_id"),
                            player_b_id=p_b.get("api_id")):
                count += 1
        return count

    # ========== RESOLUTION DES PARIS ==========

    def get_pending_bets(self) -> list:
        """Retourne tous les paris pending (matchs probablement deja joues)."""
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM bets WHERE status = 'pending'
                ORDER BY match_timestamp_ms ASC
            """).fetchall()
            return [dict(r) for r in rows]

    def store_match_result(self, match_id: str, api_match_id: int,
                           winner_player_id: int, winner_name: str,
                           final_score: str, sets_a: int = None, sets_b: int = None):
        """Stocke le resultat d'un match (utilise pour resolution + display)."""
        with get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO match_results
                (match_id, api_match_id, winner_player_id, winner_name, final_score, sets_a, sets_b, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (match_id, api_match_id, winner_player_id, winner_name, final_score,
                  sets_a, sets_b, datetime.now(timezone.utc).isoformat()))

    def resolve_bet(self, bet_id: int, won: bool, void: bool = False) -> bool:
        """Marque un pari comme won/lost/void. Calcule le profit_units.

        won=True : gain = (odds - 1) (ex cote 1.95 -> +0.95)
        won=False : perte = -1 (mise perdue)
        void=True : profit = 0 (match annule)
        """
        if void:
            status = "void"
            profit = 0.0
        elif won:
            status = "won"
            with get_conn() as conn:
                row = conn.execute("SELECT odds FROM bets WHERE id = ?", (bet_id,)).fetchone()
                if not row:
                    return False
                profit = float(row["odds"]) - 1.0
        else:
            status = "lost"
            profit = -1.0

        with get_conn() as conn:
            conn.execute("""
                UPDATE bets
                SET status = ?, settled_at = ?, profit_units = ?
                WHERE id = ?
            """, (status, datetime.now(timezone.utc).isoformat(), profit, bet_id))
        return True

    def resolve_match(self, match_id: str, winner_player_id: int) -> dict:
        """Resout TOUS les paris pending d'un match etant donne le winner.

        Retourne {won: int, lost: int, total: int}
        """
        if not winner_player_id:
            return {"won": 0, "lost": 0, "total": 0}

        with get_conn() as conn:
            pending = conn.execute("""
                SELECT id, market_key, selection_player_id, odds
                FROM bets
                WHERE match_id = ? AND status = 'pending'
            """, (match_id,)).fetchall()

        won_count, lost_count = 0, 0
        for row in pending:
            # Le pari gagne si selection_player_id == winner_player_id
            sel_id = row["selection_player_id"]
            if sel_id is None:
                continue  # On ne peut pas resoudre
            won = (int(sel_id) == int(winner_player_id))
            self.resolve_bet(row["id"], won=won)
            if won:
                won_count += 1
            else:
                lost_count += 1
        return {"won": won_count, "lost": lost_count, "total": len(pending)}

    # ========== STATS ==========

    def get_global_stats(self) -> dict:
        """Retourne les stats globales : win rate, ROI, etc.
        Filtre sur les paris Recommandes uniquement (value_bet, model_pick, model_pick_no_odds),
        car les paris Principaux (vainqueur match) ne sont pas des paris a valeur trackable.
        """
        with get_conn() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status='won' THEN 1 ELSE 0 END) AS won,
                    SUM(CASE WHEN status='lost' THEN 1 ELSE 0 END) AS lost,
                    SUM(CASE WHEN status='void' THEN 1 ELSE 0 END) AS void_count,
                    SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pending,
                    AVG(CASE WHEN status IN ('won','lost') THEN edge_pct END) AS avg_edge,
                    AVG(CASE WHEN status IN ('won','lost') THEN model_prob END) AS avg_model_prob,
                    SUM(CASE WHEN status IN ('won','lost') THEN profit_units ELSE 0 END) AS profit_units,
                    SUM(CASE WHEN status IN ('won','lost') THEN 1 ELSE 0 END) AS settled
                FROM bets
                WHERE bet_type IN ('value_bet', 'model_pick', 'model_pick_no_odds')
            """).fetchone()

            if not row or row["total"] == 0:
                return self._empty_stats()

            settled = row["settled"] or 0
            won = row["won"] or 0
            lost = row["lost"] or 0
            profit = float(row["profit_units"] or 0)

            win_rate = (won / settled * 100) if settled > 0 else 0
            roi = (profit / settled * 100) if settled > 0 else 0

            return {
                "total": row["total"],
                "won": won,
                "lost": lost,
                "void": row["void_count"] or 0,
                "pending": row["pending"] or 0,
                "settled": settled,
                "win_rate_pct": round(win_rate, 2),
                "roi_pct": round(roi, 2),
                "profit_units": round(profit, 2),
                "avg_edge_pct": round(row["avg_edge"] or 0, 2),
                "avg_model_prob": round(row["avg_model_prob"] or 0, 2),
            }

    def _empty_stats(self) -> dict:
        return {
            "total": 0, "won": 0, "lost": 0, "void": 0, "pending": 0, "settled": 0,
            "win_rate_pct": 0, "roi_pct": 0, "profit_units": 0,
            "avg_edge_pct": 0, "avg_model_prob": 0,
        }

    def get_breakdown_by(self, group_by: str) -> list:
        """Breakdown stats par : 'surface', 'tour', 'confidence', 'sport', 'bet_type'."""
        if group_by not in ("surface", "tour", "confidence", "sport", "bet_type"):
            return []

        # Pour les surfaces : normaliser (Hard/Dur, Clay/Terre Battue, Grass/Gazon)
        if group_by == "surface":
            group_expr = """
                CASE
                    WHEN LOWER(surface) IN ('hard','dur','dur (indoor)','indoor hard','hardcourt') THEN 'Hard'
                    WHEN LOWER(surface) IN ('clay','terre battue','terre','red clay') THEN 'Clay'
                    WHEN LOWER(surface) IN ('grass','gazon') THEN 'Grass'
                    WHEN LOWER(surface) IN ('carpet','moquette') THEN 'Carpet'
                    ELSE surface
                END
            """
        else:
            group_expr = group_by

        with get_conn() as conn:
            rows = conn.execute(f"""
                SELECT
                    {group_expr} AS group_value,
                    COUNT(*) AS total,
                    SUM(CASE WHEN status='won' THEN 1 ELSE 0 END) AS won,
                    SUM(CASE WHEN status='lost' THEN 1 ELSE 0 END) AS lost,
                    SUM(CASE WHEN status IN ('won','lost') THEN profit_units ELSE 0 END) AS profit_units,
                    SUM(CASE WHEN status IN ('won','lost') THEN 1 ELSE 0 END) AS settled
                FROM bets
                WHERE {group_by} IS NOT NULL AND {group_by} != ''
                GROUP BY {group_expr}
                ORDER BY total DESC
            """).fetchall()

        result = []
        for r in rows:
            settled = r["settled"] or 0
            won = r["won"] or 0
            profit = float(r["profit_units"] or 0)
            result.append({
                "group_value": r["group_value"],
                "total": r["total"],
                "settled": settled,
                "won": won,
                "lost": r["lost"] or 0,
                "win_rate_pct": round(won / settled * 100, 2) if settled > 0 else 0,
                "roi_pct": round(profit / settled * 100, 2) if settled > 0 else 0,
                "profit_units": round(profit, 2),
            })
        return result

    def get_recent_bets(self, limit: int = 30, status: str = None) -> list:
        """Retourne les N derniers paris (avec ou sans filtre status)."""
        with get_conn() as conn:
            if status:
                rows = conn.execute("""
                    SELECT * FROM bets
                    WHERE status = ?
                    ORDER BY COALESCE(settled_at, created_at) DESC
                    LIMIT ?
                """, (status, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM bets
                    ORDER BY COALESCE(settled_at, created_at) DESC
                    LIMIT ?
                """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_history_chart(self, last_n: int = 50) -> list:
        """Retourne les N derniers paris resolus avec courbe profit cumule pour graph."""
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    id, settled_at, status, profit_units, market, selection, odds, edge_pct
                FROM bets
                WHERE status IN ('won', 'lost')
                ORDER BY settled_at ASC
            """).fetchall()

        cumulative = 0.0
        history = []
        for r in rows:
            cumulative += float(r["profit_units"] or 0)
            history.append({
                "id": r["id"],
                "settled_at": r["settled_at"],
                "status": r["status"],
                "profit_units": round(float(r["profit_units"] or 0), 2),
                "cumulative_profit": round(cumulative, 2),
                "market": r["market"],
                "selection": r["selection"],
                "odds": r["odds"],
                "edge_pct": r["edge_pct"],
            })
        return history[-last_n:]

    def export_to_dict(self) -> dict:
        """Export complet pour serialiser dans un JSON (consomme par frontend)."""
        return {
            "global": self.get_global_stats(),
            "by_surface": self.get_breakdown_by("surface"),
            "by_tour": self.get_breakdown_by("tour"),
            "by_confidence": self.get_breakdown_by("confidence"),
            "by_sport": self.get_breakdown_by("sport"),
            "by_bet_type": self.get_breakdown_by("bet_type"),
            "recent_bets": self.get_recent_bets(limit=30),
            "history_chart": self.get_history_chart(last_n=50),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ========== CACHE PERSISTANT DES PROFILS JOUEURS ==========

    PROFILE_TTL_DAYS = 365  # un profil change quasi jamais (taille/poids/lieu)

    def get_cached_profile(self, api_id: int, tour: str) -> dict:
        """Recupere un profil depuis le cache. Retourne None si absent ou TTL expire."""
        if not api_id:
            return None
        with get_conn() as conn:
            row = conn.execute("""
                SELECT profile_json, profile_fetched_at
                FROM players_cache
                WHERE api_id = ? AND tour = ?
            """, (int(api_id), tour.upper())).fetchone()
        if not row or not row["profile_json"]:
            return None

        # Verifier TTL
        try:
            fetched = datetime.fromisoformat(row["profile_fetched_at"])
            age_days = (datetime.now(timezone.utc) - fetched).days
            if age_days > self.PROFILE_TTL_DAYS:
                return None  # TTL expire
        except Exception:
            return None

        try:
            return json.loads(row["profile_json"])
        except Exception:
            return None

    def cache_profile(self, api_id: int, tour: str, name: str = "",
                      country: str = "", profile: dict = None) -> bool:
        """Stocke un profil en cache. Retourne True si insere/maj."""
        if not api_id:
            return False
        try:
            with get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO players_cache
                    (api_id, tour, name, country, profile_json, profile_fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    int(api_id), tour.upper(), name, country,
                    json.dumps(profile or {}, default=str),
                    datetime.now(timezone.utc).isoformat(),
                ))
            return True
        except Exception as e:
            print(f"[BetsDB] cache_profile erreur : {e}")
            return False

    def cache_stats(self) -> dict:
        """Retourne stats du cache (combien de profils stockes)."""
        with get_conn() as conn:
            row = conn.execute("""
                SELECT COUNT(*) AS n,
                       COUNT(CASE WHEN tour='ATP' THEN 1 END) AS atp,
                       COUNT(CASE WHEN tour='WTA' THEN 1 END) AS wta
                FROM players_cache
            """).fetchone()
            return {"total": row["n"], "atp": row["atp"], "wta": row["wta"]}


# ========== CLI rapide pour debug ==========
if __name__ == "__main__":
    import sys
    db = BetsDB()
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(db.export_to_dict(), indent=2, default=str))
    else:
        print(f"DB : {DB_PATH}")
        stats = db.get_global_stats()
        print(f"\n=== STATS GLOBALES ===")
        print(f"Total paris : {stats['total']} (settled : {stats['settled']}, pending : {stats['pending']})")
        print(f"Won : {stats['won']} | Lost : {stats['lost']}")
        print(f"Win rate : {stats['win_rate_pct']}%")
        print(f"ROI : {stats['roi_pct']}% (profit : {stats['profit_units']:+.2f}u)")
        print(f"Avg edge : {stats['avg_edge_pct']}%")
