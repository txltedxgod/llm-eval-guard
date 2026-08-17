import re
from typing import List, Tuple

class SafetyGuardService:
    def __init__(self):
        self._injection_patterns = [
            re.compile(r"(?i)(ignore previous instructions|system override|disregard all prior)"),
            re.compile(r"(?i)(you are now in developer mode|bypass safety filters|reveal internal prompt)")
        ]
        self._email_regex = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
        self._phone_regex = re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}")

    def inspect(self, text: str) -> Tuple[bool, float, List[str], str]:
        violations = []
        for p in self._injection_patterns:
            if p.search(text):
                violations.append("Prompt injection attack signature detected")
                break
        
        masked = self._email_regex.sub("[REDACTED_EMAIL]", text)
        masked = self._phone_regex.sub("[REDACTED_PHONE]", masked)
        risk = 0.95 if violations else 0.0
        return (len(violations) == 0, risk, violations, masked)
