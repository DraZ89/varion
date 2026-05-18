"""
Fetch des donnees meteo historiques via Open-Meteo Archive API (gratuit, no key).

Pour chaque tournoi, on recupere les normales climatiques de la meme periode l'an dernier.
On utilise un cache local de 7 jours pour eviter les appels redondants.
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


# Cache fichier local (TTL 7 jours)
CACHE_DIR = Path(__file__).parent.parent / "data" / "weather_cache"
CACHE_TTL_DAYS = 7


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(lat: float, lon: float, month: int, day: int) -> Path:
    """Cle de cache : par coord (1 dec) + mois/jour. Pas l'annee (on normalise sur 2024)."""
    return CACHE_DIR / f"{lat:.1f}_{lon:.1f}_{month:02d}{day:02d}.json"


def _read_cache(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        # TTL
        age_days = (datetime.now().timestamp() - path.stat().st_mtime) / 86400
        if age_days > CACHE_TTL_DAYS:
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_cache(path: Path, data: dict):
    try:
        _ensure_cache_dir()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def fetch_weather(lat: float, lon: float, match_date: str, lookback_year: int = 2024) -> Optional[dict]:
    """Fetch meteo pour la periode (match_date - 3j -> match_date + 3j) en lookback_year.

    Args:
        lat, lon : coordonnees du tournoi
        match_date : date du match (format 'YYYY-MM-DD')
        lookback_year : annee de reference pour les normales climatiques

    Returns: dict {
        "temp_mean_c": float,        # Temperature moyenne (°C)
        "temp_max_c": float,         # Temperature max (°C)
        "humidity_pct": float,       # Humidite moyenne (%)
        "wind_max_kmh": float,       # Vent max (km/h)
        "precipitation_mm": float,   # Precipitations cumulees (mm sur 7j)
        "source": "open-meteo-archive"
    } ou None si erreur.
    """
    try:
        # Parser la date
        if "T" in match_date:
            match_date = match_date.split("T")[0]
        dt = datetime.strptime(match_date, "%Y-%m-%d")

        # Cache check
        cache_p = _cache_path(lat, lon, dt.month, dt.day)
        cached = _read_cache(cache_p)
        if cached is not None:
            return cached

        # Construire les dates de lookup (meme mois/jour, annee lookback)
        start_dt = datetime(lookback_year, dt.month, dt.day) - timedelta(days=3)
        end_dt = datetime(lookback_year, dt.month, dt.day) + timedelta(days=3)

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_mean,temperature_2m_max,relative_humidity_2m_mean,wind_speed_10m_max,precipitation_sum",
            "timezone": "auto",
            "wind_speed_unit": "kmh",
        }
        url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(params)

        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        daily = raw.get("daily") or {}
        if not daily:
            return None

        # Moyennes sur la fenetre 7j
        def _avg(key):
            vals = [v for v in (daily.get(key) or []) if v is not None]
            return sum(vals) / len(vals) if vals else None

        def _max(key):
            vals = [v for v in (daily.get(key) or []) if v is not None]
            return max(vals) if vals else None

        def _sum(key):
            vals = [v for v in (daily.get(key) or []) if v is not None]
            return sum(vals) if vals else 0

        result = {
            "temp_mean_c": _avg("temperature_2m_mean"),
            "temp_max_c": _max("temperature_2m_max"),
            "humidity_pct": _avg("relative_humidity_2m_mean"),
            "wind_max_kmh": _max("wind_speed_10m_max"),
            "precipitation_mm": _sum("precipitation_sum"),
            "source": "open-meteo-archive",
            "lookback_year": lookback_year,
            "lat": lat,
            "lon": lon,
        }

        # Filtrer si trop de None (data manquante)
        if result["temp_mean_c"] is None and result["temp_max_c"] is None:
            return None

        _write_cache(cache_p, result)
        return result

    except Exception as e:
        print(f"[weather] fetch_weather error: {e}")
        return None


def get_match_weather(tournament_name: str, match_date: str) -> Optional[dict]:
    """Pour un match, retourne la meteo + altitude du tournoi.

    Returns: dict avec {temp_mean_c, temp_max_c, humidity_pct, wind_max_kmh, precipitation_mm, altitude_m}
    ou None si tournoi inconnu ou erreur API.
    """
    try:
        from .tournaments_coords import get_coords
    except ImportError:
        from tournaments_coords import get_coords

    coords = get_coords(tournament_name)
    if not coords:
        return None
    lat, lon, alt = coords

    w = fetch_weather(lat, lon, match_date)
    if not w:
        return None

    w["altitude_m"] = alt
    return w


if __name__ == "__main__":
    # Test Roland Garros
    print("Test Roland Garros 2026-05-25:")
    w = get_match_weather("Roland Garros", "2026-05-25")
    print(json.dumps(w, indent=2, ensure_ascii=False))
