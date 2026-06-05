# API Contract Tester

Automated API contract testing tool -- validates REST APIs against OpenAPI 3.x specifications.

## Features

- Load OpenAPI 3.x specs (YAML/JSON)
- Auto-generate test cases from endpoints
- Send HTTP requests with configurable timeout
- Validate status codes, response times, and content types
- Console and JSON report output

## Installation

```bash
git clone https://github.com/DJX/api-contract-tester.git
cd api-contract-tester
pip install -e .
```

## Usage

```bash
# Run against an OpenAPI spec
act path/to/openapi.yaml

# Override base URL
act path/to/openapi.yaml -b https://api.example.com

# JSON report + save to file
act path/to/openapi.yaml -j -o report.json
```

## Example

```bash
act examples/petstore.yaml
```

Output:
```
============================================================
  API Contract Test Report
============================================================
  Date: 2026-06-04 22:17:56
  Total: 4 | PASS: 3 | FAIL: 1
  Total response time: 4883ms
------------------------------------------------------------

  [PASS] GET /pet/findByStatus
     [PASS] Status: 200 (expected 200)
     [PASS] Response time: 1278ms

  [FAIL] GET /pet/{petId}
     [FAIL] Status: 404 (expected 200)
     ...
============================================================
```

## Tech Stack

- Python 3.10+
- Click (CLI framework)
- Requests (HTTP client)
- PyYAML (OpenAPI spec parsing)

## Project Structure

```
src/api_contract_tester/
    cli.py              # CLI entry point
    spec_loader.py      # OpenAPI spec parser
    test_generator.py   # Test case generator
    runner.py           # HTTP request runner
    validator.py        # Response validator
    reporter.py         # Report generator
```