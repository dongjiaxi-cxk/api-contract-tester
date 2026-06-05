"""Generate test cases from OpenAPI endpoint definitions."""

import os
import re
from dataclasses import dataclass, field


@dataclass
class TestCase:
    """A single API test case."""

    name: str
    method: str
    path: str
    base_url: str
    params: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    path_params: dict = field(default_factory=dict)
    body: dict | None = None
    expected_status: int = 200
    expected_content_type: str = ""
    response_schema: dict | None = None
    verify_ssl: bool = True


_ENV_RE = re.compile(r"\$\{(\w+)\}|\$(\w+)")


def resolve_env(value: str) -> str:
    """Replace ${VAR} or $VAR with environment variable values."""
    def _replacer(m):
        name = m.group(1) or m.group(2)
        return os.environ.get(name, "")

    return _ENV_RE.sub(_replacer, value)


def resolve_env_in_dict(data: dict) -> dict:
    """Recursively resolve env vars in dict values."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = resolve_env(value)
        elif isinstance(value, dict):
            result[key] = resolve_env_in_dict(value)
        elif isinstance(value, list):
            result[key] = [
                resolve_env_in_dict(item) if isinstance(item, dict) else
                resolve_env(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


class TestGenerator:
    """Generates test cases from OpenAPI spec endpoints."""

    def __init__(self, base_url: str, endpoints: list, default_headers: dict | None = None):
        self.base_url = base_url.rstrip("/")
        self.endpoints = endpoints
        self.default_headers = default_headers or {}

    def generate(self) -> list:
        """Generate test cases for all endpoints."""
        test_cases = []

        for endpoint in self.endpoints:
            method = endpoint["method"]
            path = endpoint["path"]
            operation_id = endpoint["operation_id"] or f"{method}{path}"

            expected_status = 200
            response_schema = None
            responses = endpoint.get("responses", {})
            for status_code in responses:
                if status_code.startswith("2"):
                    expected_status = int(status_code)
                    response = responses[status_code]
                    content = response.get("content", {})
                    json_content = content.get("application/json", {})
                    response_schema = json_content.get("schema")
                    break

            params = {}
            path_params = {}
            for param in endpoint.get("parameters", []):
                if param.get("in") == "query" and param.get("required"):
                    params[param["name"]] = self._sample_value(param)
                elif param.get("in") == "path":
                    path_params[param["name"]] = self._sample_value(param)

            body = None
            request_body = endpoint.get("request_body")
            if request_body and method in ("POST", "PUT", "PATCH"):
                content = request_body.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    body = self._generate_body(schema)

            test_cases.append(TestCase(
                name=operation_id,
                method=method,
                path=path,
                base_url=self.base_url,
                params=params,
                path_params=path_params,
                body=body,
                headers=dict(self.default_headers),
                expected_status=expected_status,
                response_schema=response_schema,
            ))

        return test_cases

    def _sample_value(self, param: dict):
        schema = param.get("schema", {})
        schema_type = schema.get("type", "string")
        if schema_type == "integer":
            return 1
        elif schema_type == "boolean":
            return "true"
        return "sample"

    def _generate_body(self, schema: dict) -> dict:
        if not schema or "properties" not in schema:
            return {}

        body = {}
        required_fields = schema.get("required", [])
        for field_name in required_fields:
            prop = schema["properties"].get(field_name, {})
            prop_type = prop.get("type", "string")
            if prop_type == "integer":
                body[field_name] = 1
            elif prop_type == "string":
                body[field_name] = f"sample_{field_name}"
            elif prop_type == "boolean":
                body[field_name] = False

        return body