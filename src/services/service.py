from typing import List, Tuple
from eval_guard.guard import SafetyGuard

class SafetyGuardService:
    def __init__(self):
        self._guard = SafetyGuard()

    def inspect(self, text: str) -> Tuple[bool, float, List[str], str]:
        res = self._guard.evaluate(text)
        return (res.is_safe, res.risk_score, res.violations, res.masked_text)
