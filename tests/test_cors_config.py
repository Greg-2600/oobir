"""Unit tests for configurable CORS origins in flow_api."""

import os
import unittest

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

import flow_api


def _cors_test_app(origins, allow_credentials):
    """Build a minimal app using the resolved CORS settings."""
    test_app = FastAPI()
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @test_app.get("/ping")
    def ping():
        return {"ok": True}

    return test_app


class TestCORSOriginsFromEnv(unittest.TestCase):
    """Verify parsing of OOBIR_CORS_ORIGINS."""

    def test_default_origins_when_unset_or_empty(self):
        for raw in (None, "", "   ", " , "):
            with self.subTest(raw=raw):
                origins, credentials = flow_api.cors_origins_from_env(raw)
                self.assertEqual(origins, flow_api.DEFAULT_ALLOWED_ORIGINS)
                self.assertTrue(credentials)

    def test_custom_origins_trim_whitespace_and_drop_empty_entries(self):
        origins, credentials = flow_api.cors_origins_from_env(
            " https://app.example.com , ,https://admin.example.com  "
        )
        self.assertEqual(
            origins, ["https://app.example.com", "https://admin.example.com"]
        )
        self.assertTrue(credentials)

    def test_wildcard_disables_credentials(self):
        origins, credentials = flow_api.cors_origins_from_env(" * ")
        self.assertEqual(origins, ["*"])
        self.assertFalse(credentials)

    def test_wildcard_among_other_origins_disables_credentials(self):
        origins, credentials = flow_api.cors_origins_from_env(
            "https://app.example.com, *"
        )
        self.assertEqual(origins, ["https://app.example.com", "*"])
        self.assertFalse(credentials)

    @unittest.skipIf(
        bool(os.getenv("OOBIR_CORS_ORIGINS")), "API imported with custom origins"
    )
    def test_app_uses_default_cors_settings(self):
        cors = next(
            middleware
            for middleware in flow_api.app.user_middleware
            if middleware.cls is CORSMiddleware
        )
        self.assertEqual(cors.kwargs["allow_origins"], flow_api.DEFAULT_ALLOWED_ORIGINS)
        self.assertTrue(cors.kwargs["allow_credentials"])


class TestCORSHeaders(unittest.TestCase):
    """Verify resolved settings produce the expected CORS response headers."""

    def test_custom_origin_is_allowed_with_credentials(self):
        origins, credentials = flow_api.cors_origins_from_env(
            "https://app.example.com, "
        )
        with TestClient(_cors_test_app(origins, credentials)) as client:
            response = client.get(
                "/ping", headers={"Origin": "https://app.example.com"}
            )
        self.assertEqual(
            response.headers["access-control-allow-origin"], "https://app.example.com"
        )
        self.assertEqual(response.headers["access-control-allow-credentials"], "true")

    def test_wildcard_origin_is_allowed_without_credentials(self):
        origins, credentials = flow_api.cors_origins_from_env("*")
        with TestClient(_cors_test_app(origins, credentials)) as client:
            response = client.get("/ping", headers={"Origin": "https://other.example"})
        self.assertEqual(response.headers["access-control-allow-origin"], "*")
        self.assertNotIn("access-control-allow-credentials", response.headers)
