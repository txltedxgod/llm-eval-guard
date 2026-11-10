from eval_guard.guard import EvalResult, SafetyGuard
from eval_guard.hallucination import HallucinationDetector, HallucinationReport
from src.core.exceptions import ValidationError


class SafetyGuardService:
    def __init__(self) -> None:
        self._guard = SafetyGuard()
        self._hallucination = HallucinationDetector()

    def inspect_full(self, text: str) -> EvalResult:
        return self._guard.evaluate(text)

    def inspect(self, text: str) -> tuple[bool, float, list[str], str]:
        res = self._guard.evaluate(text)
        return (res.is_safe, res.risk_score, res.violations, res.masked_text)

    def check_groundedness(
        self,
        context: str | list[str],
        response: str,
        min_groundedness: float = 0.6,
    ) -> HallucinationReport:
        try:
            return self._hallucination.evaluate(
                context=context,
                response=response,
                min_groundedness=min_groundedness,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
