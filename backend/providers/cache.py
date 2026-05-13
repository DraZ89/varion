"""
Cache simple sur fichier pour éviter de gaspiller les requêtes API-Football.

Stratégie :
- Chaque réponse est sauvegardée dans cache/{key}.json avec un timestamp
- Si le cache existe et n'a pas expiré, on retourne directement le cache
- Sinon on fait l'appel et on met à jour le cache

TTL par défaut : 24h (parfait pour notre refresh quotidien à l'aube)
"""

import json
import os
import time
import hashlib
from typing import Any, Optional, Callable

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_TTL = 24 * 60 * 60  # 24 heures


def _key_to_filename(key: str) -> str:
    """Convertit une clé en nom de fichier sûr."""
    safe = hashlib.md5(key.encode()).hexdigest()[:16]
    # Garder un peu de la clé originale pour debug
    readable = "".join(c if c.isalnum() else "_" for c in key)[:50]
    return f"{readable}_{safe}.json"


def get(key: str, ttl: int = DEFAULT_TTL) -> Optional[Any]:
    """
    Récupère une valeur du cache si elle existe et n'a pas expiré.
    Retourne None sinon.
    """
    path = os.path.join(CACHE_DIR, _key_to_filename(key))
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)

        age = time.time() - entry.get("timestamp", 0)
        if age > ttl:
            return None  # expiré

        return entry.get("data")
    except Exception:
        return None


def set(key: str, data: Any) -> None:
    """Stocke une valeur dans le cache avec timestamp actuel."""
    path = os.path.join(CACHE_DIR, _key_to_filename(key))
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.time(),
                "key": key,
                "data": data,
            }, f, ensure_ascii=False)
    except Exception as e:
        print(f"Cache write failed for {key}: {e}")


def get_or_fetch(key: str, fetcher: Callable[[], Any], ttl: int = DEFAULT_TTL, force_refresh: bool = False) -> Any:
    """
    Pattern principal : retourne le cache si valide, sinon fetch et met en cache.

    Usage :
        teams = get_or_fetch("standings_PL", lambda: api.get_standings(39))
    """
    if not force_refresh:
        cached = get(key, ttl)
        if cached is not None:
            return cached

    data = fetcher()
    if data is not None:
        set(key, data)
    return data


def clear() -> int:
    """Vide tout le cache. Retourne le nombre de fichiers supprimés."""
    count = 0
    if os.path.exists(CACHE_DIR):
        for fname in os.listdir(CACHE_DIR):
            if fname.endswith(".json"):
                try:
                    os.remove(os.path.join(CACHE_DIR, fname))
                    count += 1
                except Exception:
                    pass
    return count


def clear_pattern(prefix: str) -> int:
    """Vide les entrees du cache dont la cle commence par `prefix`.
    Retourne le nombre de fichiers supprimes.
    Ex : clear_pattern("tennis_past_") supprime tous les past_matches caches.
    """
    count = 0
    if not os.path.exists(CACHE_DIR):
        return 0
    # Le filename est un hash de la cle, donc on doit lire chaque fichier pour
    # retrouver sa cle source. Plus simple : on stocke aussi la key dans le json.
    for fname in os.listdir(CACHE_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(CACHE_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cached_key = data.get("key", "")
            if cached_key.startswith(prefix):
                os.remove(path)
                count += 1
        except Exception:
            pass
    return count


def stats() -> dict:
    """Retourne des stats sur le cache (pour monitoring)."""
    if not os.path.exists(CACHE_DIR):
        return {"entries": 0, "size_kb": 0}

    files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    total_size = sum(
        os.path.getsize(os.path.join(CACHE_DIR, f)) for f in files
    )
    return {
        "entries": len(files),
        "size_kb": round(total_size / 1024, 1),
    }
