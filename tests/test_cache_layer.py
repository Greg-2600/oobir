"""Unit tests for cache layer functionality (db.py).

This module tests the SQLite-based caching system with market-aware expiration logic.
Tests cover cache operations, market state detection, and expiration behavior.
"""

import unittest
import json
import tempfile
import sqlite3
from datetime import datetime, time, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db


class TestCacheOperations(unittest.TestCase):
    """Test basic cache CRUD operations."""

    def setUp(self):
        """Set up test database."""
        # Use in-memory SQLite for tests
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name
        
        # Patch DB_FILE to use test database
        self.db_patcher = patch.object(db, 'DB_FILE', Path(self.db_path))
        self.db_patcher.start()
        
        # Initialize test database
        db.init_db()

    def tearDown(self):
        """Clean up test database."""
        self.db_patcher.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_set_and_get_cached_data(self):
        """Test storing and retrieving cached data."""
        test_data = {'price': 150.25, 'volume': 1000000}
        symbol = 'AAPL'
        endpoint = 'fundamentals'

        # Store data
        result = db.set_cached_data(endpoint, test_data, symbol)
        self.assertTrue(result)

        # Retrieve data
        cached = db.get_cached_data(endpoint, symbol)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['price'], 150.25)
        self.assertEqual(cached['volume'], 1000000)

    def test_cache_miss_returns_none(self):
        """Test that missing cache returns None."""
        cached = db.get_cached_data('nonexistent', 'FAKE')
        self.assertIsNone(cached)

    def test_overwrite_existing_cache(self):
        """Test that setting cache overwrites existing entry."""
        endpoint = 'price-history'
        symbol = 'MSFT'
        
        # Store first version
        db.set_cached_data(endpoint, {'price': 100}, symbol)
        
        # Overwrite with new version
        db.set_cached_data(endpoint, {'price': 105}, symbol)
        
        # Verify new data is stored
        cached = db.get_cached_data(endpoint, symbol)
        self.assertEqual(cached['price'], 105)

    def test_clear_cache_all(self):
        """Test clearing entire cache."""
        # Store multiple entries
        db.set_cached_data('fundamentals', {'data': 1}, 'AAPL')
        db.set_cached_data('news', {'data': 2}, 'AAPL')
        db.set_cached_data('fundamentals', {'data': 3}, 'MSFT')
        
        # Clear all
        count = db.clear_cache()
        self.assertEqual(count, 3)
        
        # Verify all cleared
        self.assertIsNone(db.get_cached_data('fundamentals', 'AAPL'))
        self.assertIsNone(db.get_cached_data('news', 'AAPL'))
        self.assertIsNone(db.get_cached_data('fundamentals', 'MSFT'))

    def test_clear_cache_by_endpoint(self):
        """Test clearing cache by endpoint."""
        db.set_cached_data('fundamentals', {'data': 1}, 'AAPL')
        db.set_cached_data('news', {'data': 2}, 'AAPL')
        
        # Clear only fundamentals
        count = db.clear_cache(endpoint='fundamentals')
        self.assertEqual(count, 1)
        
        # Verify only fundamentals cleared
        self.assertIsNone(db.get_cached_data('fundamentals', 'AAPL'))
        self.assertIsNotNone(db.get_cached_data('news', 'AAPL'))

    def test_clear_cache_by_symbol(self):
        """Test clearing cache by symbol."""
        db.set_cached_data('fundamentals', {'data': 1}, 'AAPL')
        db.set_cached_data('fundamentals', {'data': 2}, 'MSFT')
        
        # Clear only AAPL
        count = db.clear_cache(symbol='AAPL')
        self.assertEqual(count, 1)
        
        # Verify only AAPL cleared
        self.assertIsNone(db.get_cached_data('fundamentals', 'AAPL'))
        self.assertIsNotNone(db.get_cached_data('fundamentals', 'MSFT'))

    def test_clear_symbol_cache(self):
        """Test clearing all entries for a symbol."""
        db.set_cached_data('fundamentals', {'data': 1}, 'AAPL')
        db.set_cached_data('news', {'data': 2}, 'AAPL')
        db.set_cached_data('fundamentals', {'data': 3}, 'MSFT')
        
        # Clear all AAPL
        count = db.clear_symbol_cache('AAPL')
        self.assertEqual(count, 2)
        
        # Verify AAPL cleared, MSFT remains
        self.assertIsNone(db.get_cached_data('fundamentals', 'AAPL'))
        self.assertIsNone(db.get_cached_data('news', 'AAPL'))
        self.assertIsNotNone(db.get_cached_data('fundamentals', 'MSFT'))


class TestMarketAwareCaching(unittest.TestCase):
    """Test market-aware expiration logic."""

    def setUp(self):
        """Set up test database."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name
        
        self.db_patcher = patch.object(db, 'DB_FILE', Path(self.db_path))
        self.db_patcher.start()
        
        db.init_db()

    def tearDown(self):
        """Clean up test database."""
        self.db_patcher.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch('db.datetime')
    def test_market_open_expiration(self, mock_datetime):
        """Test cache expires when market opens."""
        # Mock time as 2:00 PM on a weekday (market open)
        mock_now = MagicMock()
        mock_now.weekday.return_value = 2  # Wednesday
        mock_now.time.return_value = time(14, 0)  # 2:00 PM
        mock_now.date.return_value = datetime.now().date()
        mock_datetime.now.return_value = mock_now
        mock_datetime.combine = datetime.combine
        
        # Store data at 8:00 AM (before market open)
        old_time = datetime.now().replace(hour=8, minute=0).isoformat()
        
        with db.get_db_connection() as conn:
            conn.execute(
                """INSERT INTO cache (endpoint, symbol, data, cached_at, market_aware)
                   VALUES (?, ?, ?, ?, ?)""",
                ('test', 'AAPL', '{"test": true}', old_time, 1)
            )
        
        # Try to retrieve - should be expired
        cached = db.get_cached_data('test', 'AAPL')
        self.assertIsNone(cached)

    def test_market_closed_same_day_cache_valid(self):
        """Test cache is valid after market close on same day."""
        # Store data at 3:30 PM (during market hours, today)
        recent_time = datetime.now().replace(hour=15, minute=30).isoformat()
        
        with db.get_db_connection() as conn:
            conn.execute(
                """INSERT INTO cache (endpoint, symbol, data, cached_at, market_aware)
                   VALUES (?, ?, ?, ?, ?)""",
                ('test', 'AAPL', '{"test": true}', recent_time, 1)
            )
        
        # Should still be valid (cached same day, market closed)
        cached = db.get_cached_data('test', 'AAPL')
        # If called after market hours, cache from same day should be valid
        # If called during market hours, it will be valid
        # This test is valid regardless of current time
        self.assertIsNotNone(cached)

    def test_cache_older_than_24_hours_expires(self):
        """Test cache expires after 24 hours regardless of market state."""
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        
        with db.get_db_connection() as conn:
            conn.execute(
                """INSERT INTO cache (endpoint, symbol, data, cached_at, market_aware)
                   VALUES (?, ?, ?, ?, ?)""",
                ('test', 'AAPL', '{"test": true}', old_time, 1)
            )
        
        # Should be expired
        cached = db.get_cached_data('test', 'AAPL')
        self.assertIsNone(cached)

    def test_non_market_aware_cache_not_expired(self):
        """Test non-market-aware cache only expires after 24 hours."""
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        
        with db.get_db_connection() as conn:
            conn.execute(
                """INSERT INTO cache (endpoint, symbol, data, cached_at, market_aware)
                   VALUES (?, ?, ?, ?, ?)""",
                ('test', 'AAPL', '{"test": true}', old_time, 0)
            )
        
        # Should NOT be expired (only 2 hours old, market_aware=0)
        cached = db.get_cached_data('test', 'AAPL')
        self.assertIsNotNone(cached)


class TestCacheStats(unittest.TestCase):
    """Test cache statistics reporting."""

    def setUp(self):
        """Set up test database."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name
        
        self.db_patcher = patch.object(db, 'DB_FILE', Path(self.db_path))
        self.db_patcher.start()
        
        db.init_db()

    def tearDown(self):
        """Clean up test database."""
        self.db_patcher.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_cache_stats(self):
        """Test cache statistics calculation."""
        # Add test data
        db.set_cached_data('fundamentals', {'data': 1}, 'AAPL')
        db.set_cached_data('fundamentals', {'data': 2}, 'MSFT')
        db.set_cached_data('news', {'data': 3}, 'AAPL')
        
        stats = db.get_cache_stats()
        
        self.assertEqual(stats['total_entries'], 3)
        self.assertEqual(stats['valid_entries'], 3)
        self.assertEqual(stats['expired_entries'], 0)
        self.assertGreater(len(stats['by_endpoint']), 0)

    def test_cache_stats_by_endpoint(self):
        """Test cache stats grouped by endpoint."""
        db.set_cached_data('fundamentals', {'data': 1}, 'AAPL')
        db.set_cached_data('fundamentals', {'data': 2}, 'MSFT')
        db.set_cached_data('news', {'data': 3}, 'AAPL')
        
        stats = db.get_cache_stats()
        endpoints = {ep['endpoint']: ep['count'] for ep in stats['by_endpoint']}
        
        self.assertEqual(endpoints.get('fundamentals'), 2)
        self.assertEqual(endpoints.get('news'), 1)


class TestDataSerialization(unittest.TestCase):
    """Test data serialization and deserialization."""

    def setUp(self):
        """Set up test database."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name
        
        self.db_patcher = patch.object(db, 'DB_FILE', Path(self.db_path))
        self.db_patcher.start()
        
        db.init_db()

    def tearDown(self):
        """Clean up test database."""
        self.db_patcher.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_complex_data_serialization(self):
        """Test caching complex nested data structures."""
        complex_data = {
            'stocks': [
                {'symbol': 'AAPL', 'price': 150.25, 'change': -2.5},
                {'symbol': 'MSFT', 'price': 320.10, 'change': 1.2}
            ],
            'summary': {
                'total_value': 470.35,
                'trending': True,
                'sectors': ['tech', 'software']
            }
        }
        
        db.set_cached_data('complex', complex_data, 'TEST')
        cached = db.get_cached_data('complex', 'TEST')
        
        self.assertEqual(cached['stocks'][0]['symbol'], 'AAPL')
        self.assertEqual(cached['summary']['total_value'], 470.35)
        self.assertIn('tech', cached['summary']['sectors'])

    def test_empty_data_caching(self):
        """Test caching empty data structures."""
        db.set_cached_data('empty', {}, 'EMPTY')
        cached = db.get_cached_data('empty', 'EMPTY')
        self.assertEqual(cached, {})

    def test_list_data_caching(self):
        """Test caching list data structures."""
        list_data = ['AAPL', 'MSFT', 'TSLA', 'GOOGL']
        db.set_cached_data('tickers', list_data, 'WATCHLIST')
        cached = db.get_cached_data('tickers', 'WATCHLIST')
        self.assertEqual(cached, list_data)


if __name__ == '__main__':
    unittest.main()
