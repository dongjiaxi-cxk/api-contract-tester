"""Tests for SpecLoader."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from api_contract_tester.spec_loader import SpecLoader


FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "test_api.yaml")


class TestSpecLoader:
    def test_load_yaml(self):
        loader = SpecLoader(FIXTURE)
        assert loader.spec["info"]["title"] == "Test API"

    def test_get_base_url(self):
        loader = SpecLoader(FIXTURE)
        assert loader.get_base_url() == "http://localhost:8000"

    def test_get_endpoints_count(self):
        loader = SpecLoader(FIXTURE)
        endpoints = loader.get_endpoints()
        assert len(endpoints) == 3

    def test_get_endpoints_methods(self):
        loader = SpecLoader(FIXTURE)
        endpoints = loader.get_endpoints()
        methods = [e["method"] for e in endpoints]
        assert "GET" in methods
        assert "POST" in methods

    def test_get_endpoints_paths(self):
        loader = SpecLoader(FIXTURE)
        endpoints = loader.get_endpoints()
        paths = [e["path"] for e in endpoints]
        assert "/users" in paths
        assert "/users/{userId}" in paths