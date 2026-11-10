"""
Core Safety Guardrail Engine
Inspects LLM inputs for direct and obfuscated prompt injections while masking
PII (emails, phone numbers, US SSNs, Luhn-validated payment cards) and leaked secrets.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, Field

from eval_guard.obfuscation import inspect_obfuscation


def _is_luhn_valid(digits: str) -> bool:
    """Validate payment card digit sequences using the Luhn mod-10 checksum."""
    if not digits.isdigit() or not 13 <= len(digits) <= 19:
        return False
    total = 0
    for idx, ch in enumerate(reversed(digits)):
        val = int(ch)
        if idx % 2 == 1:
            val *= 2
            if val > 9:
                val -= 9
        total += val
    return total % 10 == 0


class EvalResult(BaseModel):
    is_safe: bool
    risk_score: float
    violations: list[str]
    masked_text: str
    redacted_entities: dict[str, int] = Field(default_factory=dict)


class SafetyGuard:
    def __init__(self) -> None:
        self.injection_patterns = [
            re.compile(
                r"(?i)(ignore previous instructions|system override|disregard all prior|you are now in developer mode)"
            ),
            re.compile(
                r"(?i)(bypass security filters|reveal secret key|drop tables|act as sudo)"
            ),
        ]
        self.secret_pattern = re.compile(
            r"(?:\bsk-[A-Za-z0-9_-]{20,}\b|\bgh[pou]_[A-Za-z0-9]{20,}\b|\bAKIA[0-9A-Z]{16}\b|(?i:\bBearer)\s+[A-Za-z0-9\-._~+/]+=*)"
        )
        self.card_candidate = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
        self.ssn_pattern = re.compile(r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")
        self.pii_email = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
        self.pii_phone = re.compile(
            r"(?<![\d.-])(?:\+\d{1,3}[-.\s]?(?:\(\d{2,4}\)|\d{2,4})[-.\s]\d{3,4}(?:[-.\s]\d{3,4})?|\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4})(?![\d.-])"
        )

    def _redact_pii_and_secrets(self, text: str) -> tuple[str, dict[str, int]]:
        counts: dict[str, int] = {}

        def _count_sub(pattern: re.Pattern[str], label: str, tag: str, s: str) -> str:
            hits = 0

            def _repl(_: re.Match[str]) -> str:
                nonlocal hits
                hits += 1
                return tag

            updated = pattern.sub(_repl, s)
            if hits:
                counts[label] = counts.get(label, 0) + hits
            return updated

        masked = _count_sub(self.secret_pattern, "secret", "[REDACTED_SECRET]", text)

        card_hits = 0

        def _card_repl(match: re.Match[str]) -> str:
            nonlocal card_hits
            digits = re.sub(r"\D", "", match.group(0))
            if _is_luhn_valid(digits):
                card_hits += 1
                return "[REDACTED_CARD]"
            return match.group(0)

        masked = self.card_candidate.sub(_card_repl, masked)
        if card_hits:
            counts["card"] = card_hits

        masked = _count_sub(self.ssn_pattern, "ssn", "[REDACTED_SSN]", masked)
        masked = _count_sub(self.pii_email, "email", "[REDACTED_EMAIL]", masked)
        masked = _count_sub(self.pii_phone, "phone", "[REDACTED_PHONE]", masked)
        return masked, counts

    def evaluate(self, text: str) -> EvalResult:
        violations: list[str] = []

        # 1. Check direct prompt injection patterns
        for p in self.injection_patterns:
            if p.search(text):
                violations.append("Prompt injection attempt detected")
                break

        # 2. Check multi-vector adversarial obfuscation
        obf = inspect_obfuscation(text)
        if obf.detected:
            violations.append(f"Obfuscated prompt injection detected ({obf.vector})")

        # 3. Mask PII and leaked API secrets (order prevents SSN/card collisions with phone regex)
        masked, redacted_entities = self._redact_pii_and_secrets(text)

        score = 0.0 if not violations else (0.98 if obf.detected else 0.95)
        return EvalResult(
            is_safe=len(violations) == 0,
            risk_score=score,
            violations=violations,
            masked_text=masked,
            redacted_entities=redacted_entities,
        )
