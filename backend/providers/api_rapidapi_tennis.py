"""
Client API Tennis (Matchstat via RapidAPI).

URLs corrigees apres tests playground :
- /tennis/v2/{tour}/ranking/singles/                       -> classement Top
- /tennis/v2/{tour}/fixtures/{date}                        -> matchs d'une date
- /tennis/v2/{tour}/player/past-matches/{id}               -> historique joueur
- /tennis/v2/{tour}/h2h/matches/{id1}/{id2}/               -> H2H entre 2 joueurs
- /tennis/v2/{tour}/player/surface-summary/{id}            -> stats par surface

Variables d'environnement requises :
- RAPIDAPI_KEY : ta cle X-RapidAPI-Key
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

API_HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
API_BASE = f"https://{API_HOST}/tennis/v2"

TOP_N_PLAYERS = 200
MIN_DELAY_BETWEEN_CALLS = 4.0

TTL_RANKINGS = 24 * 60 * 60
TTL_FIXTURES = 2 * 60 * 60
TTL_PAST_MATCHES = 7 * 24 * 60 * 60
TTL_H2H = 30 * 24 * 60 * 60
TTL_SURFACE = 7 * 24 * 60 * 60
TTL_PLAYER_INFO = 30 * 24 * 60 * 60     # Bio info ne change quasi jamais
TTL_TOURNAMENT_INFO = 30 * 24 * 60 * 60  # Surface/tier d'un tournoi sont stables
TTL_PERF_BREAKDOWN = 7 * 24 * 60 * 60    # Stats par saison evoluent semaine par semaine
TTL_H2H_STATS = 30 * 24 * 60 * 60        # Stats career bougent peu


class TennisAPIError(Exception):
    pass


class TennisAPIRateLimit(TennisAPIError):
    pass


class TennisAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("RAPIDAPI_KEY")
        if not self.api_key:
            raise TennisAPIError(
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
                raise TennisAPIRateLimit(
                    "Rate limit atteint (429). Quota mensuel ou horaire depasse."
                )
            if e.code in (401, 403):
                raise TennisAPIError(f"Auth echouee (HTTP {e.code}). Verifier ta cle RapidAPI.")
            if e.code == 404:
                # 404 sur fixtures vide = normal
                return {"data": []}
            raise TennisAPIError(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise TennisAPIError(f"Erreur reseau: {e.reason}")

    def _cached_request(self, cache_key: str, endpoint: str, params: dict = None,
                        ttl: int = TTL_PAST_MATCHES) -> dict:
        cached = cache.get(cache_key, ttl)
        if cached is not None:
            return cached
        data = self._request(endpoint, params)
        if data is not None:
            cache.set(cache_key, data)
        return data

    # ============ ENDPOINTS ============

    def get_rankings(self, tour: str = "atp", top_n: int = TOP_N_PLAYERS) -> list:
        """URL : /tennis/v2/{tour}/ranking/singles/?pageSize=200
        Le pageSize est CRITIQUE : sans lui l'API renvoie seulement 11 joueurs.
        """
        tour = tour.lower()
        # Note : nouvelle cache key v2 pour invalider l'ancien cache (qui contenait 11 joueurs)
        key = f"tennis_rankings_{tour}_singles_v2"
        data = self._cached_request(
            key,
            f"/{tour}/ranking/singles/",
            params={"pageSize": top_n},
            ttl=TTL_RANKINGS,
        )
        rankings = data.get("data") or []
        return rankings[:top_n]

    def get_fixtures_by_date(self, tour: str, date_str: str) -> list:
        """URL : /tennis/v2/{tour}/fixtures/{date}?pageSize=200"""
        tour = tour.lower()
        # Cache key v2 pour invalider l'ancien
        key = f"tennis_fixtures_{tour}_{date_str}_v2"
        data = self._cached_request(
            key,
            f"/{tour}/fixtures/{date_str}",
            params={"pageSize": 200},
            ttl=TTL_FIXTURES,
        )
        return data.get("data") or []

    def get_matches_today(self, tour: str = "atp") -> list:
        today = _date.today().isoformat()
        return self.get_fixtures_by_date(tour, today)

    def get_matches_recent_days(self, tour: str = "atp", days: int = 3) -> list:
        """Matchs des N prochains jours (utile car certains jours sont vides)."""
        all_matches = []
        for i in range(days):
            d = (_date.today() + timedelta(days=i)).isoformat()
            try:
                matches = self.get_fixtures_by_date(tour, d)
                all_matches.extend(matches)
            except TennisAPIRateLimit:
                raise
            except Exception:
                continue
        return all_matches

    def get_player_past_matches(self, tour: str, player_id) -> list:
        """URL : /tennis/v2/{tour}/player/past-matches/{id}"""
        tour = tour.lower()
        key = f"tennis_past_{tour}_{player_id}"
        data = self._cached_request(
            key,
            f"/{tour}/player/past-matches/{player_id}",
            ttl=TTL_PAST_MATCHES,
        )
        return data.get("data") or []

    def get_h2h_matches(self, tour: str, player1_id, player2_id) -> list:
        """URL : /tennis/v2/{tour}/h2h/matches/{id1}/{id2}/"""
        tour = tour.lower()
        ids = sorted([str(player1_id), str(player2_id)], key=int)
        key = f"tennis_h2h_{tour}_{ids[0]}_{ids[1]}"
        data = self._cached_request(
            key,
            f"/{tour}/h2h/matches/{player1_id}/{player2_id}/",
            ttl=TTL_H2H,
        )
        return data.get("data") or []

    def get_player_surface_summary(self, tour: str, player_id) -> list:
        """URL : /tennis/v2/{tour}/player/surface-summary/{id}"""
        tour = tour.lower()
        key = f"tennis_surface_{tour}_{player_id}"
        data = self._cached_request(
            key,
            f"/{tour}/player/surface-summary/{player_id}",
            ttl=TTL_SURFACE,
        )
        return data.get("data") or []

    # ========== NOUVEAUX ENDPOINTS ENRICHIS (validés via playground) ==========

    def get_player_profile(self, tour: str, player_id) -> dict:
        """URL : /tennis/v2/{tour}/player/profile/{id}
        Retourne : { id, name, country, information: { turnedPro, weight, height,
                     birthplace, residence, plays, coach } }
        """
        tour = tour.lower()
        key = f"tennis_profile_{tour}_{player_id}"
        data = self._cached_request(
            key,
            f"/{tour}/player/profile/{player_id}",
            ttl=TTL_PLAYER_INFO,
        )
        return data.get("data") or {}

    def get_tournament_info(self, tour: str, tournament_id) -> dict:
        """URL : /tennis/v2/{tour}/tournament/info/{id}
        Retourne : { id, name, court: {id, name}, tier, country, ... }
        """
        tour = tour.lower()
        key = f"tennis_tournament_{tour}_{tournament_id}"
        data = self._cached_request(
            key,
            f"/{tour}/tournament/info/{tournament_id}",
            ttl=TTL_TOURNAMENT_INFO,
        )
        return data.get("data") or {}

    def get_player_perf_breakdown(self, tour: str, player_id) -> dict:
        """URL : /tennis/v2/{tour}/player/perf-breakdown/{id}
        Retourne par annee : { year: { court, round, rank, level, levelFinals } }
        """
        tour = tour.lower()
        key = f"tennis_perf_{tour}_{player_id}"
        data = self._cached_request(
            key,
            f"/{tour}/player/perf-breakdown/{player_id}",
            ttl=TTL_PERF_BREAKDOWN,
        )
        return data.get("data") or {}

    def get_h2h_vs_all_stats(self, tour: str, player_id) -> dict:
        """URL : /tennis/v2/{tour}/h2h/vs-all-stats/{id}/
        Retourne : { matchesCount, playerStats, opponentStats }
        playerStats contient TOUTES les stats career deja calculees (% serve, etc.)
        """
        tour = tour.lower()
        key = f"tennis_vs_all_{tour}_{player_id}"
        data = self._cached_request(
            key,
            f"/{tour}/h2h/vs-all-stats/{player_id}/",
            ttl=TTL_H2H_STATS,
        )
        return data.get("data") or {}

    def get_h2h_stats(self, tour: str, player1_id, player2_id) -> dict:
        """URL : /tennis/v2/{tour}/h2h/stats/{id1}/{id2}/
        Retourne : { matchesCount, player1Stats, player2Stats }
        Stats H2H specifiques entre les 2 joueurs (% serve, surface wins, etc.)
        """
        tour = tour.lower()
        # Cle ordonnee pour eviter doublon (5/10 == 10/5)
        ids = sorted([str(player1_id), str(player2_id)])
        key = f"tennis_h2h_stats_{tour}_{ids[0]}_{ids[1]}"
        data = self._cached_request(
            key,
            f"/{tour}/h2h/stats/{player1_id}/{player2_id}/",
            ttl=TTL_H2H_STATS,
        )
        return data.get("data") or {}

    @property
    def calls_made(self) -> int:
        return self._calls_made
