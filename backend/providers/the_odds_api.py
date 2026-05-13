"""
Provider The Odds API - https://the-odds-api.com

Free tier : 500 credits/mois
Sports utilises : tennis_atp, tennis_wta

Cle API : variable d'env ODDS_API_KEY
"""

import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from typing import Optional

from providers import cache
from providers.name_matcher import normalize_player_name, match_player_names


BASE_URL = "https://api.the-odds-api.com/v4"

# TTL cache : 1h (cotes peuvent changer, mais 1h est un bon compromis pour eco quota)
TTL_ODDS = 60 * 60


class TheOddsAPI:
    """Client The Odds API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ODDS_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "ODDS_API_KEY manquante. Definis-la : "
                "$env:ODDS_API_KEY = 'ta_cle' (Windows) "
                "ou Render env vars"
            )
        self.quota_remaining = None

    def _fetch(self, path: str, params: dict = None) -> Optional[dict]:
        """Appel API avec cache. Retourne la reponse JSON ou None."""
        params = params or {}
        params["apiKey"] = self.api_key

        # Cache key : path + params (sauf apiKey)
        cache_params = {k: v for k, v in params.items() if k != "apiKey"}
        cache_key = f"odds_api_{path}_{urllib.parse.urlencode(sorted(cache_params.items()))}"
        cache_key = cache_key.replace("/", "_").replace("?", "_").replace("&", "_")

        cached = cache.get(cache_key, ttl=TTL_ODDS)
        if cached is not None:
            return cached

        # Fetch reel
        url = f"{BASE_URL}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Varion-AI/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                # Track quota restant (header retourne par l'API)
                self.quota_remaining = resp.headers.get("x-requests-remaining")
                quota_used = resp.headers.get("x-requests-used")
                if self.quota_remaining and quota_used:
                    print(f"  [OddsAPI] Quota : {quota_used} used, {self.quota_remaining} remaining")
                data = json.loads(resp.read().decode("utf-8"))
                cache.set(cache_key, data)
                return data
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")[:200] if e.fp else ""
            print(f"  [OddsAPI] HTTPError {e.code} : {body}")
            return None
        except Exception as e:
            print(f"  [OddsAPI] Erreur : {e}")
            return None

    def get_active_tennis_sports(self) -> list:
        """Retourne la liste des sport_keys tennis actifs en ce moment.

        Tennis a plusieurs keys : tennis_atp_french_open, tennis_atp_us_open,
        tennis_atp_wimbledon, tennis_atp_aus_open, tennis_atp, tennis_wta, etc.
        On les liste tous via /v4/sports (gratuit, pas de cout quota).
        """
        cache_key = "odds_api_active_sports"
        cached = cache.get(cache_key, ttl=24 * 3600)  # cache 1 jour (rare que ca change)
        if cached is not None:
            return cached

        sports = self._fetch("/sports", {})
        if not isinstance(sports, list):
            return []

        # Filtrer : tennis uniquement, actif
        tennis_keys = [
            s["key"] for s in sports
            if s.get("group") == "Tennis" and s.get("active")
        ]
        cache.set(cache_key, tennis_keys)
        return tennis_keys

    def get_tennis_odds(self, tour: str = "atp",
                        regions: str = "eu,uk",
                        markets: str = "h2h") -> list:
        """Recupere tous les matchs tennis avec cotes h2h, sur tous les tournois actifs.

        Args:
            tour : 'atp' ou 'wta' (filtre par prefixe sport_key)
            regions : 'eu,uk' (Europe + UK), separes par virgule
            markets : 'h2h' (1-2 pour tennis)

        Returns:
            Liste de matchs aggregue (tous les tournois ATP ou WTA actifs).
        """
        # Lister les sports tennis actifs
        active_sports = self.get_active_tennis_sports()
        # Filtrer par tour (atp / wta)
        tour_prefix = f"tennis_{tour.lower()}"
        matching_sports = [s for s in active_sports if s.startswith(tour_prefix)]

        if not matching_sports:
            print(f"  [OddsAPI] Aucun sport tennis_{tour} actif")
            return []

        # Fetch les cotes pour chaque sport actif
        all_matches = []
        for sport_key in matching_sports:
            path = f"/sports/{sport_key}/odds"
            params = {
                "regions": regions,
                "markets": markets,
                "oddsFormat": "decimal",
            }
            data = self._fetch(path, params)
            if isinstance(data, list):
                all_matches.extend(data)
                if len(data) > 0:
                    print(f"  [OddsAPI] {sport_key}: {len(data)} matchs avec cotes")

        return all_matches

    def find_match_odds(self, player_a_name: str, player_b_name: str,
                        tour: str = "atp",
                        match_date_iso: str = None) -> Optional[dict]:
        """Cherche les cotes pour un match specifique via matching flexible des noms.

        Args:
            player_a_name : Nom du joueur A (RapidAPI Tennis)
            player_b_name : Nom du joueur B
            tour : 'atp' ou 'wta'
            match_date_iso : Date ISO du match (filtre temporel pour eviter ambiguites)

        Returns:
            Dict avec :
            {
              "odd1": 1.85,        # cote joueur A
              "odd2": 2.05,        # cote joueur B
              "bookmaker": "Unibet",
              "bookmaker_key": "unibet",
              "last_update": "2026-05-13T07:00:00Z",
              "alternates": [      # autres bookmakers pour ce meme match
                {"bookmaker": "Pinnacle", "odd1": 1.83, "odd2": 2.10},
                ...
              ]
            }
            ou None si pas trouve.
        """
        all_odds = self.get_tennis_odds(tour=tour)
        if not all_odds:
            return None

        # Chercher le match qui matche les 2 joueurs
        match_event = None
        for event in all_odds:
            home = event.get("home_team", "")
            away = event.get("away_team", "")
            # On accepte les 2 ordres : A=home/B=away OU A=away/B=home
            if (match_player_names(player_a_name, home) and
                match_player_names(player_b_name, away)):
                match_event = event
                a_is_home = True
                break
            if (match_player_names(player_a_name, away) and
                match_player_names(player_b_name, home)):
                match_event = event
                a_is_home = False
                break

        if not match_event:
            return None

        # Filtre date si fourni
        if match_date_iso:
            try:
                event_dt = datetime.fromisoformat(match_event.get("commence_time", "").replace("Z", "+00:00"))
                target_dt = datetime.fromisoformat(match_date_iso.replace("Z", "+00:00"))
                if target_dt.tzinfo is None:
                    target_dt = target_dt.replace(tzinfo=timezone.utc)
                # Tolerance : 12h d'ecart
                diff_h = abs((event_dt - target_dt).total_seconds()) / 3600
                if diff_h > 12:
                    return None
            except Exception:
                pass  # filtre date impossible, on garde

        # Recuperer les cotes de chaque bookmaker
        bookmakers = match_event.get("bookmakers") or []
        if not bookmakers:
            return None

        odds_list = []
        for bm in bookmakers:
            for market in bm.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                outcomes = market.get("outcomes", [])
                if len(outcomes) < 2:
                    continue
                # Trouver les cotes home/away
                home_odd = None
                away_odd = None
                for o in outcomes:
                    if o.get("name") == match_event.get("home_team"):
                        home_odd = o.get("price")
                    elif o.get("name") == match_event.get("away_team"):
                        away_odd = o.get("price")
                if home_odd and away_odd:
                    # Mapper sur A/B selon l'ordre
                    odd1 = home_odd if a_is_home else away_odd
                    odd2 = away_odd if a_is_home else home_odd
                    odds_list.append({
                        "bookmaker": bm.get("title", bm.get("key", "?")),
                        "bookmaker_key": bm.get("key", ""),
                        "odd1": float(odd1),
                        "odd2": float(odd2),
                        "last_update": bm.get("last_update", ""),
                    })

        if not odds_list:
            return None

        # Choisir le bookmaker principal :
        # Priorite 1 : bookmakers FR ANJ (Unibet, Winamax, Betclic, etc.)
        # Priorite 2 : Pinnacle (reference sharp)
        # Sinon : moyenne des cotes
        PRIORITY = ["unibet_fr", "unibet", "winamax_fr", "betclic_fr", "betclic",
                    "parionssport_fr", "pinnacle", "bet365"]
        primary = None
        for pkey in PRIORITY:
            for o in odds_list:
                if o["bookmaker_key"] == pkey:
                    primary = o
                    break
            if primary:
                break
        if not primary:
            # Fallback : moyenne des cotes
            avg_odd1 = sum(o["odd1"] for o in odds_list) / len(odds_list)
            avg_odd2 = sum(o["odd2"] for o in odds_list) / len(odds_list)
            primary = {
                "bookmaker": "Moyenne marche",
                "bookmaker_key": "average",
                "odd1": round(avg_odd1, 2),
                "odd2": round(avg_odd2, 2),
                "last_update": "",
            }

        return {
            "odd1": primary["odd1"],
            "odd2": primary["odd2"],
            "bookmaker": primary["bookmaker"],
            "bookmaker_key": primary["bookmaker_key"],
            "last_update": primary["last_update"],
            "alternates": [
                {"bookmaker": o["bookmaker"], "odd1": o["odd1"], "odd2": o["odd2"]}
                for o in odds_list if o["bookmaker_key"] != primary["bookmaker_key"]
            ][:5],  # top 5 alternates
        }
