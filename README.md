# llm-eval-guard

[![CI](https://github.com/txltedxgod/llm-eval-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/txltedxgod/llm-eval-guard/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Production-grade LLM evaluation, safety guardrail, and prompt security gateway. Provides deterministic hallucination & groundedness evaluation, prompt injection defense, multi-vector adversarial obfuscation decoding, and Luhn-validated PII/secret redaction.

---

## 🎬 Feature Demo

<p align="center">
  <img src="assets/demo.gif" alt="LLM Eval Guard Feature Demo — Claim-Level Hallucination Detection & Prompt Injection Defense" width="840" />
</p>
<p align="center">
  <sub><a href="assets/demo.mp4">Watch / Download 1080p60 MP4</a></sub>
</p>

---
---

## Key Capabilities

- **Claim-Level Hallucination & Groundedness Detection (`eval_guard/hallucination.py`)**:
  - Segments LLM outputs into verifiable atomic claims and evaluates faithfulness against source retrieval context in sub-millisecond synchronous execution.
  - Detects **fabricated numbers/percentages/years**, **unsupported named entities**, and **polarity/negation contradictions** against the highest-overlap source statement.
- **Multi-Vector Obfuscation Detection (`eval_guard/obfuscation.py`)**:
  - **Base64 Payload Obfuscation**, **Hexadecimal Escaped & Raw Strings**, **Rot13 / Caesar Ciphers**, **Zero-Width Invisible Characters**, **Leetspeak Normalization**, and **Reversed Attack Payloads**.
- **PII & Secret Redaction (`eval_guard/guard.py`)**:
  - Redacts **leaked API/Bearer secrets** (`sk-...`, `ghp_...`, `AKIA...`, `Bearer ...`), **US SSNs**, **Luhn-validated payment cards** (leaving invalid card-like order IDs intact), emails, and phone numbers with per-category audit counts.
- **Dual Form Factor**: Run as a zero-bloat Python SDK (`eval_guard`) or as a containerized FastAPI microservice (`src`).

---

## Directory Layout

```text
├── eval_guard/              # Standalone safety & evaluation library
│   ├── guard.py             # SafetyGuard engine with injection defense & Luhn PII/secret masking
│   ├── hallucination.py     # Claim-level groundedness & faithfulness verifier
│   └── obfuscation.py       # Multi-vector adversarial payload decoder
├── src/                     # FastAPI microservice wrapper
│   ├── api/v1/router.py     # REST endpoints (/api/v1/guard/inspect, /api/v1/guard/groundedness)
│   ├── core/                # Configuration and exception handlers
│   └── services/            # Service delegation layer
├── tests/                   # Pytest unit & FastAPI integration suite
│   ├── test_guard.py        # Prompt injection & Luhn/PII/secret masking tests
│   ├── test_hallucination.py# Groundedness, numeric fabrication & polarity contradiction tests
│   ├── test_obfuscation.py  # Multi-vector obfuscation unit tests
│   └── test_service.py      # FastAPI TestClient integration tests
├── Dockerfile               # Multi-stage production container
└── pyproject.toml           # Tooling configuration (Ruff, pytest, mypy)
```

---

## Python SDK Quick Start

```python
from eval_guard import SafetyGuard, evaluate_groundedness, inspect_obfuscation

guard = SafetyGuard()

# Direct/obfuscated attack & PII inspection
result = guard.evaluate("Email dev@example.com; card 4111-1111-1111-1111")
print(result.masked_text)        # Email [REDACTED_EMAIL]; card [REDACTED_CARD]
print(result.redacted_entities)  # {'card': 1, 'email': 1}

# Claim-level hallucination verification against retrieval documents
report = evaluate_groundedness(
    context=["Quarterly revenue grew 12% in Q3 2025."],
    response="Quarterly revenue grew 87% in Q3 2025.",
)
print(report.is_grounded)        # False
print(report.hallucination_risk) # > 0.7
print(report.ungrounded_claims[0].missing_anchors)  # ['87%']
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

Verify groundedness against source documents:
```bash
curl -X POST "http://localhost:8000/api/v1/guard/groundedness" \
  -H "Content-Type: application/json" \
  -d '{"context": ["FastAPI uses ASGI."], "response": "FastAPI uses ASGI."}'
```

---

## Running Lint & Tests

```bash
ruff check .
pytest -v tests/
```

## License
MIT License
