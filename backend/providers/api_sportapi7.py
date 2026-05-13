"""
Client SportAPI7 (RapidAPI).

Documentation : https://rapidapi.com/fluis.lacasse/api/sportapi7
RapidAPI Host : sportapi7.p.rapidapi.com

Plans :
- Basic gratuit : variable (100 req/jour souvent)
- Pro $15/mois : 15 000 req/mois
- Plans superieurs : plus de quota

Variables d'environnement requises :
- RAPIDAPI_KEY : ta cle X-RapidAPI-Key (meme cle que celle utilisee pour Tennis Matchstat)

URLs validees (apres test playground) :
- /api/v1/sport/football/scheduled-events/{date}              -> matchs du jour, sport global
- /api/v1/category/{id}/scheduled-events/{date}                -> matchs d'une ligue
- /api/v1/event/{id}                                           -> details match (deja riche!)
- /api/v1/event/{id}/statistics                                -> stats match (xG, possession, etc.)
- /api/v1/event/{id}/lineups                                   -> compositions + box score
- /api/v1/event/{id}/incidents                                 -> buts/cartons/subs/VAR
- /api/v1/event/{id}/odds/{providerId}/all                     -> cotes bookmaker
- /api/v1/event/{id}/h2h                                       -> historique entre les 2 equipes
- /api/v1/event/{id}/pregame-form                              -> forme pre-match
- /api/v1/unique-tournament/{id}/season/{sid}/standings/total  -> classement
- /api/v1/team/{id}/details                                    -> infos equipe
- /api/v1/team/{id}/performance                                -> derniers resultats

Category IDs confirmes :
- England : 1
- Spain : ? (a decouvrir au runtime)
- Italy : ? (a decouvrir au runtime)
- Germany : ? (a decouvrir au runtime)
- France : ? (a decouvrir au runtime)

Tournament uniqueIDs confirmes :
- Premier League : 17
"""

import os
import time
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Optional
from datetime import date as _date, timedelta

from providers import cache

API_HOST = "sportapi7.p.rapidapi.com"
API_BASE = f"https://{API_HOST}/api/v1"

# Rate limit : on adapte selon le plan
# Basic gratuit : 4-5s entre calls pour rester safe
# Pro $15/mo : on peut descendre a 1s
MIN_DELAY_BETWEEN_CALLS = 4.0

# TTL caches (en secondes)
TTL_SCHEDULED_EVENTS = 2 * 60 * 60       # 2h (matchs du jour, peut bouger)
TTL_EVENT_DETAILS = 12 * 60 * 60         # 12h (details match)
TTL_EVENT_STATS = 4 * 60 * 60            # 4h (stats post-match stables)
TTL_EVENT_LINEUPS = 1 * 60 * 60          # 1h (compositions changent au dernier moment)
TTL_EVENT_INCIDENTS = 4 * 60 * 60        # 4h
TTL_EVENT_ODDS = 4 * 60 * 60             # 4h
TTL_H2H = 30 * 24 * 60 * 60              # 30 jours (historique stable)
TTL_STANDINGS = 24 * 60 * 60             # 24h
TTL_TEAM_STATS = 7 * 24 * 60 * 60        # 7 jours
TTL_PLAYER_STATS = 7 * 24 * 60 * 60      # 7 jours
TTL_PREGAME_FORM = 4 * 60 * 60           # 4h


# Mapping HARDCODE des Top 5 europeens par leur uniqueTournament.id (stables chez SportSorts/SofaScore)
# Source : URLs sofascore.com/tournament/{country}/{league}/{id}
KNOWN_LEAGUES = {
    "PL":   {"unique_tournament_id": 17, "name": "Premier League", "country": "England"},
    "LIGA": {"unique_tournament_id": 8,  "name": "LaLiga", "country": "Spain"},
    "SA":   {"unique_tournament_id": 23, "name": "Serie A", "country": "Italy"},
    "BL":   {"unique_tournament_id": 35, "name": "Bundesliga", "country": "Germany"},
    "L1":   {"unique_tournament_id": 34, "name": "Ligue 1", "country": "France"},
}


# (legacy, garde pour compat)
KNOWN_CATEGORY_IDS = {
    "PL": {"category_id": 1, "name": "Premier League", "country": "England", "unique_tournament_id": 17},
    "LIGA": {"category_id": None, "name": "La Liga", "country": "Spain", "unique_tournament_id": None},
    "SA": {"category_id": None, "name": "Serie A", "country": "Italy", "unique_tournament_id": None},
    "BL": {"category_id": None, "name": "Bundesliga", "country": "Germany", "unique_tournament_id": None},
    "L1": {"category_id": None, "name": "Ligue 1", "country": "France", "unique_tournament_id": None},
}


class SportAPI7Error(Exception):
    pass


class SportAPI7RateLimit(SportAPI7Error):
    pass


class SportAPI7QuotaExceeded(SportAPI7Error):
    pass


class SportAPI7:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("RAPIDAPI_KEY")
        if not self.api_key:
            raise SportAPI7Error(
                "RAPIDAPI_KEY manquante. "
                "Definis-la : $env:RAPIDAPI_KEY = 'ta_cle' (Windows)"
            )
        self._calls_made = 0
        self._last_call_time = 0.0

    def _wait_for_rate_limit(self):
        if self._last_call_time == 0:
            return
        elapsed = time.time() - self._last_call_time
        if elapsed < MIN_DELAY_BETWEEN_CALLS:
            time.sleep(MIN_DELAY_BETWEEN_CALLS - elapsed)

    def _request(self, endpoint: str, params: dict = None) -> dict:
        params = params or {}
        query = urllib.parse.urlencode(params)
        url = f"{API_BASE}{endpoint}?{query}" if query else f"{API_BASE}{endpoint}"

        self._wait_for_rate_limit()

        req = urllib.request.Request(url, headers={
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": API_HOST,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        })

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                self._calls_made += 1
                self._last_call_time = time.time()
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            self._last_call_time = time.time()
            if e.code == 429:
                raise SportAPI7RateLimit(
                    "Rate limit atteint (429). Quota epuise ou trop de requetes."
                )
            if e.code in (401, 403):
                raise SportAPI7Error(f"Auth echouee (HTTP {e.code}). Verifier ta cle RapidAPI.")
            if e.code == 404:
                # 404 = donnee absente (ex: pas de stats pour ce match), normal
                return {}
            raise SportAPI7Error(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise SportAPI7Error(f"Erreur reseau: {e.reason}")

    def _cached_request(self, cache_key: str, endpoint: str, params: dict = None,
                        ttl: int = TTL_EVENT_STATS) -> dict:
        cached = cache.get(cache_key, ttl)
        if cached is not None:
            return cached
        data = self._request(endpoint, params)
        if data is not None:
            cache.set(cache_key, data)
        return data

    # ============ DECOUVERTE DES IDS DE LIGUES ============

    def get_scheduled_events_by_sport(self, sport: str, date_str: str) -> list:
        """
        Tous les matchs d'un sport pour une date.
        URL : /api/v1/sport/{sport}/scheduled-events/{date}
        Retourne la liste events avec tournament/category info.
        """
        key = f"sportapi7_sport_{sport}_{date_str}"
        data = self._cached_request(
            key,
            f"/sport/{sport}/scheduled-events/{date_str}",
            ttl=TTL_SCHEDULED_EVENTS,
        )
        return data.get("events") or []

    def get_scheduled_events_by_category(self, category_id: int, date_str: str) -> list:
        """
        Matchs d'une ligue pour une date.
        URL : /api/v1/category/{id}/scheduled-events/{date}
        """
        key = f"sportapi7_cat_{category_id}_{date_str}"
        data = self._cached_request(
            key,
            f"/category/{category_id}/scheduled-events/{date_str}",
            ttl=TTL_SCHEDULED_EVENTS,
        )
        return data.get("events") or []

    def get_unique_tournament_seasons(self, unique_tournament_id: int) -> list:
        """
        Liste des saisons d'une ligue (la 1re est la plus recente).
        URL : /api/v1/unique-tournament/{id}/seasons
        """
        key = f"sportapi7_seasons_{unique_tournament_id}"
        data = self._cached_request(
            key,
            f"/unique-tournament/{unique_tournament_id}/seasons",
            ttl=24 * 60 * 60,
        )
        return data.get("seasons") or []

    def discover_leagues(self) -> dict:
        """
        Decouvre les IDs courants pour le Top 5 europeen.
        Strategie : on connait les uniqueTournament.id (stables chez SportSorts).
        On a besoin de recuperer dynamiquement le seasonId courant via /seasons.

        Cout : 5 requetes (1 par ligue).
        """
        discovered = {}

        for short, info in KNOWN_LEAGUES.items():
            ut_id = info["unique_tournament_id"]
            try:
                seasons = self.get_unique_tournament_seasons(ut_id)
                if not seasons:
                    continue
                # Prendre la 1re (la plus recente)
                current_season = seasons[0]
                # Note : on n'a pas le category.id, mais on pourra l'inferer
                # si besoin via /unique-tournament/{id}
                discovered[short] = {
                    "category_id": None,  # on le recuperera dans un event si besoin
                    "unique_tournament_id": ut_id,
                    "season_id": current_season.get("id"),
                    "season_name": current_season.get("name") or current_season.get("year"),
                    "name": info["name"],
                    "country": info["country"],
                }
            except Exception as e:
                print(f"  KO discover {short}: {e}")
                continue

        return discovered

    def discover_leagues_legacy(self) -> dict:
        """
        ANCIENNE VERSION : decouverte par scan de scheduled-events.
        Conservee pour reference, ne plus utiliser car elle attrape de fausses ligues
        (ex: Egyptian Premier League ou Frauen-Bundesliga).
        """
        # On essaie aujourd'hui, puis si vide, samedi prochain
        candidates = [_date.today(), self._next_saturday()]
        events = []
        for d in candidates:
            try:
                events = self.get_scheduled_events_by_sport("football", d.isoformat())
                if events:
                    break
            except Exception:
                continue

        # Mapping STRICT par uniqueTournament.id connus
        discovered = {}
        for event in events:
            tournament = event.get("tournament", {}) or {}
            unique_tournament = tournament.get("uniqueTournament", {}) or {}
            category = tournament.get("category", {}) or {}
            season = event.get("season", {}) or {}

            ut_id = unique_tournament.get("id")
            if not ut_id:
                continue

            for short, known in KNOWN_LEAGUES.items():
                if short in discovered:
                    continue
                if ut_id == known["unique_tournament_id"]:
                    discovered[short] = {
                        "category_id": category.get("id"),
                        "unique_tournament_id": ut_id,
                        "season_id": season.get("id"),
                        "name": tournament.get("name"),
                        "country": category.get("name"),
                    }
                    break

        return discovered

    def _next_saturday(self) -> _date:
        today = _date.today()
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        return today + timedelta(days=days_until_saturday)

    # ============ EVENTS ============

    def get_event_details(self, event_id: int) -> dict:
        """URL : /api/v1/event/{id}"""
        key = f"sportapi7_event_{event_id}"
        data = self._cached_request(
            key,
            f"/event/{event_id}",
            ttl=TTL_EVENT_DETAILS,
        )
        return data.get("event") or data

    def get_event_statistics(self, event_id: int) -> dict:
        """URL : /api/v1/event/{id}/statistics"""
        key = f"sportapi7_event_stats_{event_id}"
        data = self._cached_request(
            key,
            f"/event/{event_id}/statistics",
            ttl=TTL_EVENT_STATS,
        )
        return data.get("statistics") or []

    def get_event_lineups(self, event_id: int) -> dict:
        """URL : /api/v1/event/{id}/lineups"""
        key = f"sportapi7_event_lineups_{event_id}"
        data = self._cached_request(
            key,
            f"/event/{event_id}/lineups",
            ttl=TTL_EVENT_LINEUPS,
        )
        return data

    def get_event_incidents(self, event_id: int) -> list:
        """URL : /api/v1/event/{id}/incidents"""
        key = f"sportapi7_event_inc_{event_id}"
        data = self._cached_request(
            key,
            f"/event/{event_id}/incidents",
            ttl=TTL_EVENT_INCIDENTS,
        )
        return data.get("incidents") or []

    def get_event_odds(self, event_id: int, provider_id: int = 1) -> dict:
        """URL : /api/v1/event/{id}/odds/{providerId}/all"""
        key = f"sportapi7_event_odds_{event_id}_{provider_id}"
        data = self._cached_request(
            key,
            f"/event/{event_id}/odds/{provider_id}/all",
            ttl=TTL_EVENT_ODDS,
        )
        return data.get("markets") or []

    def get_event_h2h_summary(self, event_id: int) -> dict:
        """
        Stats agregees H2H : {teamDuel: {homeWins, awayWins, draws}}
        URL : /api/v1/event/{id}/h2h
        Cout : 1 req (cache 30j)
        """
        key = f"sportapi7_event_h2h_summary_{event_id}"
        data = self._cached_request(
            key,
            f"/event/{event_id}/h2h",
            ttl=TTL_H2H,
        )
        return data

    def get_event_h2h_events(self, event_id: int) -> list:
        """
        Liste detaillee des matchs historiques entre les 2 equipes.
        URL : /api/v1/event/{id}/h2h/events
        Cout : 1 req (cache 30j)
        """
        key = f"sportapi7_event_h2h_events_{event_id}"
        data = self._cached_request(
            key,
            f"/event/{event_id}/h2h/events",
            ttl=TTL_H2H,
        )
        return data.get("events") or []

    def get_event_h2h(self, event_id: int) -> dict:
        """
        ALIAS LEGACY : conservee pour compat. Pointe vers h2h_summary.
        Pour la liste detaillee, utiliser get_event_h2h_events().
        """
        return self.get_event_h2h_summary(event_id)

    def get_event_pregame_form(self, event_id: int) -> dict:
        """URL : /api/v1/event/{id}/pregame-form"""
        key = f"sportapi7_event_pregame_{event_id}"
        data = self._cached_request(
            key,
            f"/event/{event_id}/pregame-form",
            ttl=TTL_PREGAME_FORM,
        )
        return data

    # ============ STANDINGS ============

    def get_standings(self, unique_tournament_id: int, season_id: int) -> list:
        """URL : /api/v1/unique-tournament/{id}/season/{sid}/standings/total"""
        key = f"sportapi7_standings_{unique_tournament_id}_{season_id}"
        data = self._cached_request(
            key,
            f"/unique-tournament/{unique_tournament_id}/season/{season_id}/standings/total",
            ttl=TTL_STANDINGS,
        )
        # Structure : data.standings = liste de groupes, chaque groupe.rows = liste equipes
        standings_groups = data.get("standings") or []
        if standings_groups and len(standings_groups) > 0:
            return standings_groups[0].get("rows") or []
        return []

    # ============ TEAM ============

    def get_team_details(self, team_id: int) -> dict:
        """URL : /api/v1/team/{id}"""
        key = f"sportapi7_team_{team_id}"
        data = self._cached_request(
            key,
            f"/team/{team_id}",
            ttl=TTL_TEAM_STATS,
        )
        return data.get("team") or data

    def get_team_performance(self, team_id: int) -> dict:
        """URL : /api/v1/team/{id}/performance"""
        key = f"sportapi7_team_perf_{team_id}"
        data = self._cached_request(
            key,
            f"/team/{team_id}/performance",
            ttl=TTL_STANDINGS,
        )
        return data

    @property
    def calls_made(self) -> int:
        return self._calls_made
