"""Database module for caching API and AI responses with market-aware expiration."""

import json
import logging
from datetime import datetime, time
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

# Database file location
DB_FILE = Path(__file__).parent / "cache.db"

# US Stock Market hours: 9:30 AM - 4:00 PM ET on weekdays
MARKET_OPEN_TIME = time(9, 30)
MARKET_CLOSE_TIME = time(16, 0)


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                symbol TEXT NOT NULL,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                market_aware BOOLEAN DEFAULT 1,
                UNIQUE(endpoint, symbol)
            )
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_endpoint_symbol 
            ON cache(endpoint, symbol)
        """)
        
        logger.info("Database initialized successfully")


def _is_market_open_now():
    """Check if the US stock market is currently open."""
    now = datetime.now()
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    is_weekday = now.weekday() < 5
    
    if not is_weekday:
        return False
    
    # Check if current time is within market hours (ET)
    current_time = now.time()
    return MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME


def _should_expire_cache(cached_at_str: str) -> bool:
    """
    Determine if cache should expire based on market status.
    
    Market-aware logic (current behavior):
    - If market is currently open: expire cache older than 1 hour
    - If market is closed: never expire (keep indefinitely)
    
    Note:
    This replaces the previous implementation, which used a 24-hour expiration
    policy with market-open awareness. Callers relying on the older behavior
    should be aware that cache entries may now be retained longer when the
    market is closed and may expire more aggressively (after 1 hour) while
    the market is open.
    """
    try:
        cached_at = datetime.fromisoformat(cached_at_str)
        now = datetime.now()

        # Always expire cache older than 24 hours
        cache_age_seconds = (now - cached_at).total_seconds()
        if cache_age_seconds > 86400:  # 24 hours
            logger.debug(f"Cache expired: {cache_age_seconds/3600:.1f} hours old")
            return True

        # If market is currently open, be more aggressive: expire if older than 1 hour
        if _is_market_open_now():
            if cache_age_seconds > 3600:
                logger.debug(f"Cache expired: {cache_age_seconds/60:.1f} minutes old (market open)")
                return True

        # Otherwise, keep the cache
        logger.debug(f"Cache kept: age {cache_age_seconds/60:.1f} minutes, market open={_is_market_open_now()}")
        return False
    except Exception as e:
        logger.error(f"Error checking cache expiration: {e}")
        # On error, expire the cache to be safe
        return True


def get_cached_data(endpoint: str, symbol: str):
    """
    Get cached data if it exists and hasn't expired.
    
    Args:
        endpoint: API endpoint name (e.g., 'price-history', 'news')
        symbol: Stock ticker symbol
        
    Returns:
        Cached data dict or None if cache miss/expired
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT data, cached_at, market_aware FROM cache WHERE endpoint = ? AND symbol = ?",
                (endpoint, symbol)
            )
            row = cursor.fetchone()
            
            if row is None:
                logger.debug(f"Cache miss: {endpoint}/{symbol}")
                return None
            
            data_str, cached_at, market_aware = row[0], row[1], row[2]
            
            # Check if cache should be expired
            if market_aware and _should_expire_cache(cached_at):
                logger.info(f"Cache expired (market-aware): {endpoint}/{symbol}")
                # Delete expired cache
                conn.execute("DELETE FROM cache WHERE endpoint = ? AND symbol = ?", (endpoint, symbol))
                return None
            
            logger.info(f"Cache hit: {endpoint}/{symbol} (cached at {cached_at})")
            return json.loads(data_str)
            
    except Exception as e:
        logger.error(f"Error retrieving cached data: {e}")
        return None


def set_cached_data(endpoint: str, data: dict, symbol: str, market_aware: bool = True) -> bool:
    """
    Cache data in the database.
    
    Args:
        endpoint: API endpoint name
        data: Data to cache (will be JSON serialized)
        symbol: Stock ticker symbol
        market_aware: If True, cache expires when market opens (default: True)
        
    Returns:
        True if successful, False otherwise
    """
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
                (endpoint, symbol, data_str, 1 if market_aware else 0)
            )
            logger.info(f"Cached data: {endpoint}/{symbol}")
            return True
    except Exception as e:
        logger.error(f"Error caching data: {e}")
        return False


def clear_cache(endpoint: str = None, symbol: str = None) -> int:
    """
    Clear cache entries.
    
    Args:
        endpoint: If specified, only clear this endpoint. If None, clear all.
        symbol: If specified, only clear this symbol. If None, clear all.
        
    Returns:
        Number of rows deleted
    """
    try:
        with get_db_connection() as conn:
            if endpoint and symbol:
                cursor = conn.execute(
                    "DELETE FROM cache WHERE endpoint = ? AND symbol = ?",
                    (endpoint, symbol)
                )
            elif endpoint:
                cursor = conn.execute(
                    "DELETE FROM cache WHERE endpoint = ?",
                    (endpoint,)
                )
            elif symbol:
                cursor = conn.execute(
                    "DELETE FROM cache WHERE symbol = ?",
                    (symbol,)
                )
            else:
                cursor = conn.execute("DELETE FROM cache")
            
            count = cursor.rowcount
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
            
            # Count expired entries
            cursor = conn.execute("""
                SELECT COUNT(*) FROM cache 
                WHERE market_aware = 1 
                AND (
                    (julianday('now') - julianday(cached_at)) * 24 * 3600 > 86400
                    OR (
                        DATE('now') != DATE(cached_at)
                        AND strftime('%H:%M', 'now', '+4 hours') < '09:30'
                    )
                )
            """)
            expired = cursor.fetchone()[0]
            
            cursor = conn.execute(
                "SELECT endpoint, COUNT(*) as count FROM cache GROUP BY endpoint"
            )
            by_endpoint = [{"endpoint": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            return {
                "total_entries": total,
                "valid_entries": total - expired,
                "expired_entries": expired,
                "by_endpoint": by_endpoint
            }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}


def clear_symbol_cache(symbol: str) -> int:
    """Clear cache for a specific symbol."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM cache WHERE symbol = ?", (symbol,))
            count = cursor.rowcount
            logger.info(f"Cleared {count} cache entries for symbol {symbol}")
            return count
    except Exception as e:
        logger.error(f"Error clearing cache for symbol {symbol}: {e}")
        return 0


def clear_expired_cache() -> int:
    """Clear all expired cache entries."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM cache 
                WHERE market_aware = 1 
                AND (
                    (julianday('now') - julianday(cached_at)) * 24 * 3600 > 86400
                    OR (
                        DATE('now') != DATE(cached_at)
                        AND strftime('%H:%M', 'now', '+4 hours') < '09:30'
                    )
                )
            """)
            count = cursor.rowcount
            logger.info(f"Cleared {count} expired cache entries")
            return count
    except Exception as e:
        logger.error(f"Error clearing expired cache: {e}")
        return 0


# Initialize database on module load
init_db()
