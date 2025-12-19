"""Database caching layer for OOBIR.

Caches API responses to reduce external API calls and improve performance.
Data is considered fresh if less than 1 day old.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool

logger = logging.getLogger(__name__)

# Database connection pool
_connection_pool = None

# Cache expiry: 1 day
CACHE_EXPIRY_HOURS = 24


def get_db_config() -> Dict[str, str]:
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('POSTGRES_HOST', 'postgres'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'oobir'),
        'user': os.getenv('POSTGRES_USER', 'oobir'),
        'password': os.getenv('POSTGRES_PASSWORD', 'oobir_password')
    }


def init_db_pool():
    """Initialize database connection pool."""
    global _connection_pool
    if _connection_pool is None:
        config = get_db_config()
        try:
            _connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **config
            )
            logger.info("Database connection pool initialized")
            init_schema()
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            _connection_pool = None


def get_connection():
    """Get a connection from the pool."""
    if _connection_pool is None:
        init_db_pool()
    if _connection_pool is None:
        return None
    try:
        return _connection_pool.getconn()
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        return None


def return_connection(conn):
    """Return a connection to the pool."""
    if _connection_pool and conn:
        _connection_pool.putconn(conn)


def init_schema():
    """Initialize database schema if it doesn't exist."""
    conn = get_connection()
    if not conn:
        logger.warning("Cannot initialize schema: no database connection")
        return
    
    try:
        with conn.cursor() as cur:
            # Create cache table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS api_cache (
                    id SERIAL PRIMARY KEY,
                    cache_key VARCHAR(512) UNIQUE NOT NULL,
                    endpoint VARCHAR(256) NOT NULL,
                    symbol VARCHAR(20),
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            # Create index on cache_key for fast lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_key 
                ON api_cache(cache_key)
            """)
            
            # Create index on expires_at for cleanup
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON api_cache(expires_at)
            """)
            
            # Create index on symbol for queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol 
                ON api_cache(symbol)
            """)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")
        conn.rollback()
    finally:
        return_connection(conn)


def generate_cache_key(endpoint: str, symbol: Optional[str] = None, **kwargs) -> str:
    """Generate a unique cache key for the request."""
    parts = [endpoint]
    if symbol:
        parts.append(symbol.upper())
    if kwargs:
        # Sort kwargs for consistent key generation
        for key in sorted(kwargs.keys()):
            parts.append(f"{key}={kwargs[key]}")
    return ":".join(parts)


def get_cached_data(endpoint: str, symbol: Optional[str] = None, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached data if available and not expired.
    
    Args:
        endpoint: API endpoint name (e.g., 'fundamentals', 'price_history')
        symbol: Stock ticker symbol
        **kwargs: Additional parameters for cache key generation
        
    Returns:
        Cached data dict or None if not found/expired
    """
    cache_key = generate_cache_key(endpoint, symbol, **kwargs)
    conn = get_connection()
    
    if not conn:
        logger.warning("No database connection, skipping cache")
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT data, expires_at 
                FROM api_cache 
                WHERE cache_key = %s 
                AND expires_at > NOW()
                LIMIT 1
            """, (cache_key,))
            
            row = cur.fetchone()
            if row:
                logger.info(f"Cache HIT for {cache_key}")
                return row['data']
            else:
                logger.info(f"Cache MISS for {cache_key}")
                return None
    except Exception as e:
        logger.error(f"Error retrieving cached data: {e}")
        return None
    finally:
        return_connection(conn)


def set_cached_data(
    endpoint: str, 
    data: Dict[str, Any], 
    symbol: Optional[str] = None,
    expiry_hours: int = CACHE_EXPIRY_HOURS,
    **kwargs
) -> bool:
    """
    Store data in cache with expiry.
    
    Args:
        endpoint: API endpoint name
        data: Data to cache (must be JSON-serializable)
        symbol: Stock ticker symbol
        expiry_hours: Hours until cache expires (default: 24)
        **kwargs: Additional parameters for cache key generation
        
    Returns:
        True if successful, False otherwise
    """
    cache_key = generate_cache_key(endpoint, symbol, **kwargs)
    conn = get_connection()
    
    if not conn:
        logger.warning("No database connection, skipping cache write")
        return False
    
    try:
        expires_at = datetime.now() + timedelta(hours=expiry_hours)
        json_data = json.dumps(data)
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO api_cache (cache_key, endpoint, symbol, data, expires_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (cache_key) 
                DO UPDATE SET 
                    data = EXCLUDED.data,
                    updated_at = NOW(),
                    expires_at = EXCLUDED.expires_at
            """, (cache_key, endpoint, symbol, json_data, expires_at))
            
            conn.commit()
            logger.info(f"Cached data for {cache_key} (expires: {expires_at})")
            return True
    except Exception as e:
        logger.error(f"Error caching data: {e}")
        conn.rollback()
        return False
    finally:
        return_connection(conn)


def clear_expired_cache():
    """Remove expired cache entries."""
    conn = get_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM api_cache WHERE expires_at <= NOW()")
            deleted_count = cur.rowcount
            conn.commit()
            logger.info(f"Cleared {deleted_count} expired cache entries")
            return deleted_count
    except Exception as e:
        logger.error(f"Error clearing expired cache: {e}")
        conn.rollback()
        return 0
    finally:
        return_connection(conn)


def clear_symbol_cache(symbol: str):
    """Clear all cached data for a specific symbol."""
    conn = get_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM api_cache WHERE symbol = %s", (symbol.upper(),))
            deleted_count = cur.rowcount
            conn.commit()
            logger.info(f"Cleared {deleted_count} cache entries for symbol {symbol}")
            return deleted_count
    except Exception as e:
        logger.error(f"Error clearing symbol cache: {e}")
        conn.rollback()
        return 0
    finally:
        return_connection(conn)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    conn = get_connection()
    if not conn:
        return {"error": "No database connection"}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Total entries
            cur.execute("SELECT COUNT(*) as total FROM api_cache")
            total = cur.fetchone()['total']
            
            # Valid entries (not expired)
            cur.execute("SELECT COUNT(*) as valid FROM api_cache WHERE expires_at > NOW()")
            valid = cur.fetchone()['valid']
            
            # Expired entries
            expired = total - valid
            
            # Entries by endpoint
            cur.execute("""
                SELECT endpoint, COUNT(*) as count 
                FROM api_cache 
                WHERE expires_at > NOW()
                GROUP BY endpoint 
                ORDER BY count DESC
            """)
            by_endpoint = [dict(row) for row in cur.fetchall()]
            
            return {
                "total_entries": total,
                "valid_entries": valid,
                "expired_entries": expired,
                "by_endpoint": by_endpoint
            }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}
    finally:
        return_connection(conn)
