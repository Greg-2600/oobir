"""Database module for caching API and AI responses with market-aware expiration."""

import json
import logging
import sqlite3
import threading
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime, time
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

# Database file location
DB_FILE = Path(__file__).parent / "cache.db"

# US Stock Market hours: 9:30 AM - 4:00 PM ET on weekdays
MARKET_OPEN_TIME = time(9, 30)
MARKET_CLOSE_TIME = time(16, 0)

# In-memory LRU cache to avoid SQLite hits for hot entries
_LRU_MAX_SIZE = 500
_lru_cache: OrderedDict[str, tuple[str, str]] = (
    OrderedDict()
)  # key -> (data_str, cached_at)
_lru_lock = threading.RLock()

# Persistent SQLite connection (thread-safe via lock)
_conn_lock = threading.RLock()
_conn = None


def _get_conn():
    """Get or create the persistent SQLite connection with optimized settings."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_FILE), timeout=30.0, isolation_level="DEFERRED")
        _conn.execute("PRAGMA journal_mode = WAL")
        _conn.execute("PRAGMA synchronous = NORMAL")
        _conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        _conn.execute("PRAGMA temp_store = MEMORY")
        _conn.row_factory = sqlite3.Row
        _conn.execute(
            "CREATE TABLE IF NOT EXISTS cache ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "endpoint TEXT NOT NULL, "
            "symbol TEXT NOT NULL, "
            "data TEXT NOT NULL, "
            "cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "market_aware BOOLEAN DEFAULT 1, "
            "UNIQUE(endpoint, symbol)"
            ")"
        )
        _conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_endpoint_symbol ON cache(endpoint, symbol)"
        )
        _conn.commit()
    return _conn


@contextmanager
def get_db_connection():
    """Context manager for database connections using the shared connection."""
    conn = _get_conn()
    with _conn_lock:
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise


def init_db():
    """Initialize database schema (called on module load via _get_conn)."""
    _get_conn()
    logger.info("Database initialized successfully")


def _is_market_open_now():
    """Check if the US stock market is currently open."""
    now = datetime.now()
    is_weekday = now.weekday() < 5
    if not is_weekday:
        return False
    current_time = now.time()
    return MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME


def _should_expire_cache(cached_at_str: str) -> bool:
    """Determine if cache should expire based on market status."""
    try:
        cached_at = datetime.fromisoformat(cached_at_str)
        now = datetime.now()
        cache_age_seconds = (now - cached_at).total_seconds()
        if cache_age_seconds > 86400:
            return True
        return bool(_is_market_open_now() and cache_age_seconds > 3600)
    except Exception:
        return True


def get_cached_data(endpoint: str, symbol: str):
    """Get cached data if it exists and hasn't expired."""
    cache_key = f"{endpoint}:{symbol}"

    # Fast path: check in-memory LRU first
    with _lru_lock:
        if cache_key in _lru_cache:
            data_str, cached_at = _lru_cache[cache_key]
            if not _should_expire_cache(cached_at):
                _lru_cache.move_to_end(cache_key)
                return json.loads(data_str)
            else:
                del _lru_cache[cache_key]

    # Slow path: hit SQLite
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT data, cached_at, market_aware FROM cache WHERE endpoint = ? AND symbol = ?",
                (endpoint, symbol),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            data_str, cached_at, market_aware = row[0], row[1], row[2]

            if market_aware and _should_expire_cache(cached_at):
                # Fire-and-forget: expire in background
                conn.execute(
                    "DELETE FROM cache WHERE endpoint = ? AND symbol = ?",
                    (endpoint, symbol),
                )
                return None

            # Populate LRU
            with _lru_lock:
                _lru_cache[cache_key] = (data_str, cached_at)
                if len(_lru_cache) > _LRU_MAX_SIZE:
                    _lru_cache.popitem(last=False)

            return json.loads(data_str)

    except Exception as e:
        logger.error(f"Error retrieving cached data: {e}")
        return None


def set_cached_data(
    endpoint: str, data: dict, symbol: str, market_aware: bool = True
) -> bool:
    """Cache data in the database and update LRU."""
    cache_key = f"{endpoint}:{symbol}"
    try:
        with get_db_connection() as conn:
            data_str = json.dumps(data)
            conn.execute(
                """
                INSERT INTO cache (endpoint, symbol, data, market_aware)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(endpoint, symbol) DO UPDATE SET
                    data = excluded.data,
                    cached_at = CURRENT_TIMESTAMP,
                    market_aware = excluded.market_aware
                """,
                (endpoint, symbol, data_str, 1 if market_aware else 0),
            )

        # Update LRU
        with _lru_lock:
            _lru_cache[cache_key] = (data_str, datetime.now().isoformat())
            if len(_lru_cache) > _LRU_MAX_SIZE:
                _lru_cache.popitem(last=False)

        return True
    except Exception as e:
        logger.error(f"Error caching data: {e}")
        return False


def clear_cache(endpoint: str | None = None, symbol: str | None = None) -> int:
    """Clear cache entries."""
    try:
        with get_db_connection() as conn:
            if endpoint and symbol:
                cursor = conn.execute(
                    "DELETE FROM cache WHERE endpoint = ? AND symbol = ?",
                    (endpoint, symbol),  # type: ignore[arg-type]
                )
            elif endpoint:
                cursor = conn.execute("DELETE FROM cache WHERE endpoint = ?", (endpoint,))  # type: ignore[arg-type]
            elif symbol:
                cursor = conn.execute("DELETE FROM cache WHERE symbol = ?", (symbol,))  # type: ignore[arg-type]
            else:
                cursor = conn.execute("DELETE FROM cache")
            count = cursor.rowcount

        # Clear LRU
        with _lru_lock:
            if not endpoint and not symbol:
                _lru_cache.clear()
            else:
                keys_to_remove = [
                    k
                    for k in _lru_cache
                    if (endpoint and k.startswith(f"{endpoint}:"))  # noqa: W504
                    or (symbol and k.endswith(f":{symbol}"))
                ]
                for k in keys_to_remove:
                    del _lru_cache[k]

        logger.info(f"Cleared {count} cache entries")
        return count
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return 0


def get_cache_stats() -> dict:
    """Get cache statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM cache")
            total = cursor.fetchone()[0]
            cursor = conn.execute(
                "SELECT endpoint, COUNT(*) as count FROM cache GROUP BY endpoint"
            )
            by_endpoint = [
                {"endpoint": row[0], "count": row[1]} for row in cursor.fetchall()
            ]
            with _lru_lock:
                lru_size = len(_lru_cache)
            return {
                "total_entries": total,
                "lru_cache_entries": lru_size,
                "by_endpoint": by_endpoint,
            }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}


def clear_symbol_cache(symbol: str) -> int:
    """Clear cache for a specific symbol."""
    return clear_cache(symbol=symbol)


def clear_expired_cache() -> int:
    """Clear all expired cache entries."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM cache
                WHERE market_aware = 1
                AND (julianday('now') - julianday(cached_at)) * 86400 > 86400
            """)
            count = cursor.rowcount
        with _lru_lock:
            expired_keys = [
                k
                for k, (_, cached_at) in _lru_cache.items()
                if _should_expire_cache(cached_at)
            ]
            for k in expired_keys:
                del _lru_cache[k]
        logger.info(f"Cleared {count} expired cache entries")
        return count
    except Exception as e:
        logger.error(f"Error clearing expired cache: {e}")
        return 0


# Initialize database on module load
init_db()
