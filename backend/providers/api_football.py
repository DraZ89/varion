"""
Client API-Football (api-sports.io).

Documentation : https://www.api-football.com/documentation-v3
Free tier :
  - 100 requêtes/jour MAXIMUM
  - 10 requêtes/MINUTE MAXIMUM
  - Saisons accessibles : 2022-2024 uniquement
  - Parametre 'last' interdit

IDs des ligues (saison 2024/25, dernière dispo en free tier) :
- Premier League : 39
- La Liga : 140
- Serie A : 135
- Bundesliga : 78
- Ligue 1 : 61

Variables d'environnement requises :
- API_FOOTBALL_KEY : ta clé personnelle
"""

import os
import time
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Optional

from providers import cache

API_BASE = "https://v3.football.api-sports.io"

# Top 5 européens
LEAGUES = {
    "PL": {"id": 39, "name": "Premier League", "country": "England"},
    "LIGA": {"id": 140, "name": "La Liga", "country": "Spain"},
    "SA": {"id": 135, "name": "Serie A", "country": "Italy"},
    "BL": {"id": 78, "name": "Bundesliga", "country": "Germany"},
    "L1": {"id": 61, "name": "Ligue 1", "country": "France"},
}

# Saison en cours (calendrier sportif)
# Plan payant : saison 2025/26 actuelle
# Plan free : utilise 2024 (et change DEMO_MODE = True dans refresh_data.py)
CURRENT_SEASON = 2025  # API-Football utilise l'année de début de saison

# Rate limiting free tier : max 10 req/minute
# On laisse 7 secondes entre chaque requete (8.5 req/min, marge de securite)
MIN_DELAY_BETWEEN_CALLS = 7.0


class APIFootballError(Exception):
    pass


class APIFootballRateLimitMinute(APIFootballError):
    """Rate limit par minute - on peut retry apres delai."""
    pass


class APIFootballRateLimitDaily(APIFootballError):
    """Quota journalier epuise - on ne peut plus rien faire avant minuit UTC."""
    pass


class APIFootball:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("API_FOOTBALL_KEY")
        if not self.api_key:
            raise APIFootballError(
                "API_FOOTBALL_KEY manquante. "
                "Définis-la dans les variables d'environnement Render, "
                "ou en local : $env:API_FOOTBALL_KEY = 'ta_cle'"
            )
        self._calls_made = 0  # compteur local pour debug
        self._last_call_time = 0.0  # timestamp du dernier appel reseau

    def _wait_for_rate_limit(self):
        """Attendre si necessaire pour respecter le rate limit minute."""
        if self._last_call_time == 0:
            return
        elapsed = time.time() - self._last_call_time
        if elapsed < MIN_DELAY_BETWEEN_CALLS:
            wait = MIN_DELAY_BETWEEN_CALLS - elapsed
            print(f"      [rate-limit] attente {wait:.1f}s...")
            time.sleep(wait)

    def _request(self, endpoint: str, params: dict = None, max_retries: int = 2) -> dict:
        """Effectue une requête à l'API. Retourne le JSON brut."""
        params = params or {}
        query = urllib.parse.urlencode(params)
        url = f"{API_BASE}{endpoint}?{query}" if query else f"{API_BASE}{endpoint}"

        for attempt in range(1, max_retries + 1):
            # Respecter le rate limit minute
            self._wait_for_rate_limit()

            req = urllib.request.Request(url, headers={
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": "v3.football.api-sports.io",
            })

            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    self._calls_made += 1
                    self._last_call_time = time.time()
                    data = json.loads(resp.read().decode("utf-8"))

                    # API-Football retourne ses erreurs dans le body, pas en HTTP code
                    errors = data.get("errors")
                    if errors:
                        if isinstance(errors, dict) and errors:
                            # Differencier les erreurs
                            err_str = str(errors)
                            if "rateLimit" in errors or "10 requests per minute" in err_str:
                                if attempt < max_retries:
                                    print(f"      [rate-limit minute] retry dans 15s (tentative {attempt}/{max_retries})...")
                                    time.sleep(15)
                                    continue
                                raise APIFootballRateLimitMinute(f"Rate limit minute: {errors}")
                            if "requests" in err_str.lower() and "day" in err_str.lower():
                                raise APIFootballRateLimitDaily(f"Quota journalier epuise: {errors}")
                            raise APIFootballError(f"API error: {errors}")
                        if isinstance(errors, list) and errors:
                            raise APIFootballError(f"API error: {errors}")

                    return data

            except urllib.error.HTTPError as e:
                self._last_call_time = time.time()
                if e.code == 429:
                    if attempt < max_retries:
                        print(f"      [HTTP 429] retry dans 15s...")
                        time.sleep(15)
                        continue
                    raise APIFootballRateLimitMinute("HTTP 429 (rate limit)")
                raise APIFootballError(f"HTTP {e.code}: {e.reason}")
            except urllib.error.URLError as e:
                raise APIFootballError(f"Erreur réseau: {e.reason}")

    def _cached_request(self, cache_key: str, endpoint: str, params: dict = None,
                        ttl: int = 24 * 60 * 60) -> dict:
        """Wrapper avec cache. NE CACHE PAS les erreurs."""
        cached = cache.get(cache_key, ttl)
        if cached is not None:
            return cached

        # Faire l'appel - si ca leve une exception, on ne cache rien
        data = self._request(endpoint, params)
        if data is not None:
            cache.set(cache_key, data)
        return data

    # ============== ENDPOINTS ==============

    def get_standings(self, league_id: int, season: int = CURRENT_SEASON) -> list:
        """Classement d'une ligue. Coût : 1 requête."""
        key = f"standings_{league_id}_{season}"
        data = self._cached_request(key, "/standings", {
            "league": league_id, "season": season
        })
        # Structure : response[0].league.standings[0] = liste des équipes
        try:
            standings = data["response"][0]["league"]["standings"][0]
            return standings
        except (KeyError, IndexError):
            return []

    def get_fixtures_upcoming(self, league_id: int, days_ahead: int = 7,
                              season: int = CURRENT_SEASON) -> list:
        """
        Matchs à venir dans les N prochains jours.
        Coût : 1 requête.
        """
        from datetime import date, timedelta
        today = date.today()
        end = today + timedelta(days=days_ahead)

        key = f"fixtures_{league_id}_{season}_{today.isoformat()}_{end.isoformat()}"
        data = self._cached_request(key, "/fixtures", {
            "league": league_id,
            "season": season,
            "from": today.isoformat(),
            "to": end.isoformat(),
            "status": "NS-TBD",  # Not Started uniquement
        })
        return data.get("response", [])

    def get_fixtures_recent(self, league_id: int, last: int = 10,
                            season: int = CURRENT_SEASON) -> list:
        """
        Derniers matchs joués (saison terminée, mode démo free tier).
        Utilise from/to (compatible free tier) au lieu de last= (interdit).
        Coût : 1 requête.
        """
        from datetime import date, timedelta
        # Saison 2024 = aout 2024 -> mai 2025
        # On prend les 90 derniers jours de la saison
        if season == 2024:
            end_date = date(2025, 5, 31)
            start_date = date(2025, 3, 1)
        elif season == 2023:
            end_date = date(2024, 5, 31)
            start_date = date(2024, 3, 1)
        else:
            # Pour les saisons en cours (plan payant)
            today = date.today()
            end_date = today
            start_date = today - timedelta(days=90)

        key = f"fixtures_recent_{league_id}_{season}_{start_date.isoformat()}_{end_date.isoformat()}"
        data = self._cached_request(key, "/fixtures", {
            "league": league_id,
            "season": season,
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
        })

        # Filtrer pour ne garder que les matchs joues (status FT)
        all_fixtures = data.get("response", [])
        played = [f for f in all_fixtures
                  if (f.get("fixture", {}).get("status", {}) or {}).get("short") == "FT"]

        # Trier par date decroissante et garder les N derniers
        played.sort(key=lambda f: f.get("fixture", {}).get("date", ""), reverse=True)
        return played[:last] if last > 0 else played

    def get_team_statistics(self, team_id: int, league_id: int,
                            season: int = CURRENT_SEASON) -> dict:
        """
        Stats agrégées d'une équipe sur la saison (buts, possession, cartons, etc.).
        Coût : 1 requête.
        """
        key = f"team_stats_{team_id}_{league_id}_{season}"
        data = self._cached_request(key, "/teams/statistics", {
            "team": team_id, "league": league_id, "season": season
        })
        return data.get("response", {})

    def get_team_last_matches(self, team_id: int, last: int = 10) -> list:
        """
        Les N derniers matchs joués par une équipe.
        Utile pour calculer la forme récente.
        Coût : 1 requête.
        """
        key = f"team_last_{team_id}_{last}"
        data = self._cached_request(key, "/fixtures", {
            "team": team_id, "last": last
        })
        return data.get("response", [])

    def get_squad(self, team_id: int) -> list:
        """
        Effectif complet d'une équipe.
        Coût : 1 requête.
        """
        key = f"squad_{team_id}"
        data = self._cached_request(key, "/players/squads", {"team": team_id})
        try:
            return data["response"][0]["players"]
        except (KeyError, IndexError):
            return []

    def get_player_stats(self, player_id: int, season: int = CURRENT_SEASON) -> dict:
        """
        Stats détaillées d'un joueur (buts, passes, xG si dispo, etc.).
        Coût : 1 requête.
        """
        key = f"player_{player_id}_{season}"
        data = self._cached_request(key, "/players", {
            "id": player_id, "season": season
        })
        try:
            return data["response"][0]
        except (KeyError, IndexError):
            return {}

    def get_h2h(self, team1_id: int, team2_id: int, last: int = 5) -> list:
        """
        Historique des confrontations entre deux équipes.
        Note : sur free tier, le parametre 'last' est interdit.
        On filtre cote client.
        Coût : 1 requête.
        """
        key = f"h2h_{min(team1_id, team2_id)}_{max(team1_id, team2_id)}"
        data = self._cached_request(key, "/fixtures/headtohead", {
            "h2h": f"{team1_id}-{team2_id}",
        })
        all_h2h = data.get("response", [])
        # Garder seulement les matchs joues, plus recents en premier
        played = [f for f in all_h2h
                  if (f.get("fixture", {}).get("status", {}) or {}).get("short") == "FT"]
        played.sort(key=lambda f: f.get("fixture", {}).get("date", ""), reverse=True)
        return played[:last] if last > 0 else played

    def get_lineups(self, fixture_id: int) -> list:
        """
        Compositions probables/officielles d'un match.
        Coût : 1 requête.
        Note : disponible seulement quelques heures avant le match.
        """
        key = f"lineups_{fixture_id}"
        data = self._cached_request(key, "/fixtures/lineups", {
            "fixture": fixture_id
        }, ttl=2 * 60 * 60)  # TTL plus court (2h) car ça change souvent
        return data.get("response", [])

    @property
    def calls_made(self) -> int:
        return self._calls_made
