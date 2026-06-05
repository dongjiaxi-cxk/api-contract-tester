"""Generate test cases from OpenAPI endpoint definitions."""

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


class TestGenerator:
    """Generates test cases from OpenAPI spec endpoints."""

    def __init__(self, base_url: str, endpoints: list):
        self.base_url = base_url.rstrip("/")
        self.endpoints = endpoints

    def generate(self) -> list:
        """Generate test cases for all endpoints."""
        test_cases = []

        for endpoint in self.endpoints:
            method = endpoint["method"]
            path = endpoint["path"]
            operation_id = endpoint["operation_id"] or f"{method}{path}"

            # Determine expected status code and response schema
            expected_status = 200
            response_schema = None
            responses = endpoint.get("responses", {})
            for status_code in responses:
                if status_code.startswith("2"):
                    expected_status = int(status_code)
                    # Extract JSON response schema
                    response = responses[status_code]
                    content = response.get("content", {})
                    json_content = content.get("application/json", {})
                    response_schema = json_content.get("schema")
                    break

            # Build query params
            params = {}
            # Build path params (e.g. /pet/{petId})
            path_params = {}
            for param in endpoint.get("parameters", []):
                if param.get("in") == "query" and param.get("required"):
                    params[param["name"]] = self._sample_value(param)
                elif param.get("in") == "path":
                    path_params[param["name"]] = self._sample_value(param)

            # Build minimal body for POST/PUT
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
                expected_status=expected_status,
                response_schema=response_schema,
            ))

        return test_cases

    def _sample_value(self, param: dict):
        """Generate a sample value based on parameter schema."""
        schema = param.get("schema", {})
        schema_type = schema.get("type", "string")
        if schema_type == "integer":
            return 1
        elif schema_type == "boolean":
            return "true"
        return "sample"

    def _generate_body(self, schema: dict) -> dict:
        """Generate a minimal request body from schema."""
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