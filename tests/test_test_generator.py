"""Tests for TestGenerator."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from api_contract_tester.spec_loader import SpecLoader
from api_contract_tester.test_generator import TestGenerator


FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "test_api.yaml")


class TestTestGenerator:
    def setup_method(self):
        loader = SpecLoader(FIXTURE)
        self.endpoints = loader.get_endpoints()
        self.generator = TestGenerator("http://localhost:8000", self.endpoints)

    def test_generates_correct_count(self):
        cases = self.generator.generate()
        assert len(cases) == 3

    def test_path_params_extracted(self):
        cases = self.generator.generate()
        user_case = [c for c in cases if "userId" in c.path][0]
        assert "userId" in user_case.path_params
        assert user_case.path_params["userId"] == 1

    def test_query_params_extracted(self):
        cases = self.generator.generate()
        users_case = [c for c in cases if c.name == "getUsers"][0]
        assert "limit" in users_case.params

    def test_post_generates_body(self):
        cases = self.generator.generate()
        create_case = [c for c in cases if c.method == "POST"][0]
        assert create_case.body is not None
        assert "name" in create_case.body
        assert "email" in create_case.body

    def test_expected_status(self):
        cases = self.generator.generate()
        create_case = [c for c in cases if c.method == "POST"][0]
        assert create_case.expected_status == 201

    def test_response_schema(self):
        cases = self.generator.generate()
        get_case = [c for c in cases if c.name == "getUsers"][0]
        assert get_case.response_schema is not None
        assert get_case.response_schema["type"] == "array"