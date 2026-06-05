"""Tests for ResponseValidator."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from api_contract_tester.validator import ResponseValidator
from api_contract_tester.test_generator import TestCase


class TestResponseValidator:
    def setup_method(self):
        self.validator = ResponseValidator()

    def test_pass_on_correct_status(self):
        tc = TestCase(name="test", method="GET", path="/", base_url="http://x")
        result = {"test_case": tc, "status_code": 200, "response_time_ms": 100, "error": None}
        validated = self.validator.validate(result)
        assert validated["passed"] is True

    def test_fail_on_wrong_status(self):
        tc = TestCase(name="test", method="GET", path="/", base_url="http://x")
        result = {"test_case": tc, "status_code": 500, "response_time_ms": 100, "error": None}
        validated = self.validator.validate(result)
        assert validated["passed"] is False

    def test_fail_on_error(self):
        tc = TestCase(name="test", method="GET", path="/", base_url="http://x")
        result = {"test_case": tc, "status_code": None, "response_time_ms": 0, "error": "Connection failed"}
        validated = self.validator.validate(result)
        assert validated["passed"] is False

    def test_slow_response_warning(self):
        tc = TestCase(name="test", method="GET", path="/", base_url="http://x")
        result = {"test_case": tc, "status_code": 200, "response_time_ms": 5000, "error": None}
        validated = self.validator.validate(result)
        messages = validated["messages"]
        assert any("WARN" in m for m in messages)

    def test_schema_validation_pass(self):
        tc = TestCase(
            name="test", method="GET", path="/", base_url="http://x",
            response_schema={"type": "object", "properties": {"id": {"type": "integer"}}}
        )
        import requests
        resp = requests.Response()
        resp.status_code = 200
        resp._content = b'{"id": 123}'
        result = {"test_case": tc, "status_code": 200, "response_time_ms": 100, "error": None, "response": resp}
        validated = self.validator.validate(result)
        assert validated["passed"] is True