import re
from typing import Dict, Any, List
from pydantic import BaseModel
from eval_guard.obfuscation import inspect_obfuscation, ObfuscationCheckResult

class EvalResult(BaseModel):
    is_safe: bool
    risk_score: float
    violations: List[str]
    masked_text: str

class SafetyGuard:
    def __init__(self):
        self.injection_patterns = [
            re.compile(r"(?i)(ignore previous instructions|system override|disregard all prior|you are now in developer mode)"),
            re.compile(r"(?i)(bypass security filters|reveal secret key|drop tables|act as sudo)")
        ]
        self.pii_email = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
        self.pii_phone = re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}")

    def evaluate(self, text: str) -> EvalResult:
        violations: List[str] = []
        
        # 1. Check direct prompt injection patterns
        for p in self.injection_patterns:
            if p.search(text):
                violations.append("Prompt injection attempt detected")
                break
        
        # 2. Check multi-vector adversarial obfuscation
        obf = inspect_obfuscation(text)
        if obf.detected:
            violations.append(f"Obfuscated prompt injection detected ({obf.vector})")

        # 3. Mask PII
        masked = self.pii_email.sub("[REDACTED_EMAIL]", text)
        masked = self.pii_phone.sub("[REDACTED_PHONE]", masked)

        score = 0.0 if not violations else (0.98 if obf.detected else 0.95)
        return EvalResult(
            is_safe=len(violations) == 0,
            risk_score=score,
            violations=violations,
            masked_text=masked
        )
