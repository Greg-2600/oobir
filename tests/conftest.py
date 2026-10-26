"""pytest configuration: configure test environment and shared fixtures."""

import os
import sys
from pathlib import Path

TEST_API_KEY = "test-api-key-12345"
os.environ.setdefault("OOBIR_API_KEYS", TEST_API_KEY)
os.environ.setdefault("OOBIR_ENV", "test")
os.environ["OOBIR_AUTH_ENABLED"] = "true"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import flow_api

flow_api.API_KEYS.add(TEST_API_KEY)

# ---------------------------------------------------------------------------
# Patch TestClient so every test client automatically gets the test API key.
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient as _TC

_original_tc_init = _TC.__init__


def _patched_tc_init(self, app, **kwargs):
    headers = dict(kwargs.get("headers") or {})
    if "x-api-key" not in {k.lower() for k in headers}:
        headers["X-API-Key"] = TEST_API_KEY
    kwargs["headers"] = headers
    _original_tc_init(self, app, **kwargs)


_TC.__init__ = _patched_tc_init


# ---------------------------------------------------------------------------
# db module global state — use a temp file so tests don't hit real cache.db
# ---------------------------------------------------------------------------
import tempfile

_test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db_path = Path(_test_db_file.name)
_test_db_file.close()

import db as _db_module

_db_module.DB_FILE = _test_db_path
_db_module._conn = None


@pytest.fixture(scope="session")
def api_key_header():
    """Return the X-API-Key header dict for test authentication."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture(scope="function", autouse=True)
def reset_test_db():
    """Reset the SQLite connection and clear cache before each test."""
    _db_module._conn = None
    try:
        conn = _db_module.get_db_conn()
        conn.execute("DELETE FROM cache")
        conn.commit()
    except Exception:
        pass
    yield
    _db_module._conn = None
