"""
utils/cache.py
Cache TTL simple basé sur cachetools.
Décorateur @timed_cache(ttl=N) applicable sur n'importe quelle fonction.
"""
import time
import functools
import logging

logger = logging.getLogger(__name__)

# Cache global simple : { (func_name, args_key) → (timestamp, result) }
_cache: dict = {}


def timed_cache(ttl: int = 300):
    """
    Décorateur de cache avec expiration en secondes.
    ttl=300 → résultats mis en cache 5 minutes.
    Clé de cache = (nom_fonction, repr(args), repr(sorted(kwargs))).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (func.__name__, repr(args), repr(sorted(kwargs.items())))
            now = time.monotonic()

            if key in _cache:
                ts, value = _cache[key]
                if now - ts < ttl:
                    logger.debug(f"Cache HIT: {func.__name__}{args}")
                    return value
                else:
                    del _cache[key]

            logger.debug(f"Cache MISS: {func.__name__}{args} — appel Neo4j")
            result = func(*args, **kwargs)
            _cache[key] = (now, result)
            return result
        return wrapper
    return decorator


def invalidate_all():
    """Vide intégralement le cache (à appeler après run_all_algorithms)."""
    count = len(_cache)
    _cache.clear()
    logger.info(f"Cache vidé : {count} entrées supprimées.")


def cache_stats() -> dict:
    """Retourne des infos sur l'état du cache."""
    now = time.monotonic()
    return {
        "total_entries": len(_cache),
        "keys": [
            {
                "func": k[0],
                "args": k[1],
                "age_seconds": round(now - v[0], 1),
            }
            for k, v in _cache.items()
        ],
    }
