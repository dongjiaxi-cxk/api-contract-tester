# API Contract Tester

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-35%20passed-brightgreen.svg)](tests/)
[![PyPI](https://img.shields.io/badge/pypi-v0.4.0-blue.svg)](https://pypi.org/project/act-tester/)
[![Code style](https://img.shields.io/badge/code%20style-clean-success.svg)]()

**Automated API contract testing from OpenAPI specs.** Point it at an OpenAPI 3.x file, and it generates + executes tests for every endpoint.

```
act openapi.yaml -c 5 --retry 2 --md-report -o REPORT.md
```

## Why this exists

Manually verifying every API endpoint is slow and error-prone. This tool reads your OpenAPI spec and:
- Auto-generates test cases with sample data
- Validates status codes, response schemas, Content-Type
- Runs tests concurrently
- Generates console / JSON / HTML / Markdown reports
- Works in CI pipelines

## Quick Start

```bash
pip install act-tester
act https://petstore3.swagger.io/api/v3/openapi.json
```

Or from source:
```bash
pip install git+https://github.com/dongjiaxi-cxk/api-contract-tester.git
```

## Features

| Feature | Description |
|---------|-------------|
| OpenAPI 3.x | YAML & JSON spec support |
| Env vars | `${API_KEY}` auto-resolved from environment |
| Concurrency | `-c 5` for 5 parallel workers |
| Retry | `--retry 2` on network failures |
| SSL control | `--no-ssl` to skip verification |
| Custom headers | `-H "Authorization: Bearer $TOKEN"` |
| Dry run | `--dry-run` to preview without executing |
| Reports | Console, JSON, HTML, Markdown |
| Config file | `.act.toml` for default options |
| Response time | `--max-response-time 500` hard assertion |

## Usage

```bash
# Basic
act openapi.yaml

# Concurrent with retry and custom headers
act openapi.yaml -c 5 --retry 2 -H "Authorization: Bearer $TOKEN"

# Dry run (see what would be tested without making requests)
act openapi.yaml --dry-run

# Markdown report saved to file
act openapi.yaml --md-report -o REPORT.md

# HTML report
act openapi.yaml --html-report -o report.html

# JSON output for programmatic use
act openapi.yaml -j
```

## Config file (`.act.toml`)

```toml
[act]
base_url = "https://api.example.com/v1"
timeout = 30
concurrency = 5
retry = 2
max_response_time = 500

[act.headers]
Authorization = "Bearer ${API_TOKEN}"
```

## Project Structure

```
api-contract-tester/
  src/api_contract_tester/
    cli.py            # Click CLI entry point
    spec_loader.py    # OpenAPI 3.x parser (YAML/JSON + env vars)
    test_generator.py # TestCase dataclass, auto-generates from spec
    runner.py         # HTTP executor with concurrency + retry
    validator.py      # Status code, schema, response time assertions
    reporter.py       # Console / JSON / HTML / Markdown reports
  tests/              # 35 pytest tests
  examples/           # Sample OpenAPI specs
```

## Running Tests

```bash
pip install -e .
pytest tests/ -v
```

## License

MIT - see [LICENSE](LICENSE)