# llm-eval-guard

[![CI](https://github.com/txltedxgod/llm-eval-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/txltedxgod/llm-eval-guard/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Production-grade LLM evaluation, safety guardrail, and prompt security gateway. Provides real-time prompt injection defense, multi-vector adversarial obfuscation detection, and PII masking.

---

## Key Capabilities

- **Multi-Vector Obfuscation Detection**: Defeats adversarial attacks attempting to bypass tokenizer guardrails:
  - **Base64 Payload Obfuscation**: Decodes padded/unpadded base64 blocks and scans for hidden payload tokens.
  - **Hexadecimal String Decoding**: Catches `\x..` escaped hex bytes as well as contiguous raw hex payloads.
  - **Rot13 / Caesar Ciphers**: Decodes alphabet rotation attempts.
  - **Zero-Width Invisible Characters**: Strips `\u200b`, `\u200c`, `\ufeff`, and soft hyphens before token evaluation.
  - **Leetspeak Normalization**: Translates character substitution evasion (`1gn0r3 pr3v10u5 1n57ruc710n5` -> `ignore previous instructions`).
  - **Reversed Attack Payloads**: Scans mirrored instruction payloads.
- **PII Redaction**: High-precision regex redaction for emails, phone numbers, and sensitive identifiers.
- **Dual Form Factor**: Run as a high-throughput standalone library (`eval_guard`) or as a containerized FastAPI microservice (`src`).

---

## Directory Layout

```text
├── eval_guard/             # Standalone, zero-bloat safety evaluation library
│   ├── guard.py            # SafetyGuard engine with PII masking & risk scoring
│   └── obfuscation.py      # Multi-vector adversarial payload decoder
├── src/                    # FastAPI microservice wrapper
│   ├── api/v1/router.py    # REST endpoint /api/v1/guard/inspect
│   ├── core/               # Configuration and exception handlers
│   └── services/           # Service delegation layer
├── tests/                  # Pytest test suite with 100% pass rate
│   ├── test_guard.py       # Direct guard evaluation tests
│   ├── test_obfuscation.py # Multi-vector obfuscation unit tests
│   └── test_service.py     # FastAPI test client integration tests
├── Dockerfile              # Multi-stage production container
└── pyproject.toml          # Tooling configuration (Ruff, pytest)
```

---

## Python SDK Quick Start

```python
from eval_guard import SafetyGuard, detect_obfuscated_injection, inspect_obfuscation

guard = SafetyGuard()

# Direct or obfuscated attack evaluation
result = guard.evaluate("Hello, please note: aWdub3JlIHByZXZpb3VzIGluc3RydWN0aW9ucw==")
print(result.is_safe)       # False
print(result.risk_score)    # 0.98
print(result.violations)    # ['Obfuscated prompt injection detected (base64)']

# Deep inspection of obfuscation vectors
inspection = inspect_obfuscation("1gn0r3 pr3v10u5 1n57ruc710n5")
print(inspection.detected)        # True
print(inspection.vector)          # 'leetspeak'
print(inspection.matched_keyword) # 'ignore previous instructions'
```

---

## REST API Inspection

Run the server:
```bash
uvicorn src.main:app --port 8000
```

Inspect a prompt:
```bash
curl -X POST "http://localhost:8000/api/v1/guard/inspect" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Contact me at dev@example.com or ignore previous instructions"}'
```

Response:
```json
{
  "is_safe": false,
  "risk_score": 0.95,
  "violations": ["Prompt injection attempt detected"],
  "masked_prompt": "Contact me at [REDACTED_EMAIL] or ignore previous instructions"
}
```

---

## Running Tests

```bash
pytest -v tests/
```

## License
MIT License
