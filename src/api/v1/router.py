from fastapi import APIRouter

from src.schemas.models import (
    ClaimVerdictSchema,
    GroundednessCheckRequest,
    GroundednessCheckResponse,
    GuardCheckRequest,
    GuardCheckResponse,
)
from src.services.service import SafetyGuardService

router = APIRouter(prefix="/api/v1/guard", tags=["Safety Guard"])
guard = SafetyGuardService()


@router.post("/inspect", response_model=GuardCheckResponse)
def inspect_prompt(payload: GuardCheckRequest) -> GuardCheckResponse:
    res = guard.inspect_full(payload.prompt)
    return GuardCheckResponse(
        is_safe=res.is_safe,
        risk_score=res.risk_score,
        violations=res.violations,
        masked_prompt=res.masked_text,
        redacted_entities=res.redacted_entities,
    )


@router.post("/groundedness", response_model=GroundednessCheckResponse)
def evaluate_response_groundedness(
    payload: GroundednessCheckRequest,
) -> GroundednessCheckResponse:
    report = guard.check_groundedness(
        context=payload.context,
        response=payload.response,
        min_groundedness=payload.min_groundedness,
    )
    return GroundednessCheckResponse(
        is_grounded=report.is_grounded,
        groundedness_score=report.groundedness_score,
        hallucination_risk=report.hallucination_risk,
        total_claims=report.total_claims,
        grounded_claims=report.grounded_claims,
        ungrounded_claims=[
            ClaimVerdictSchema(
                claim=c.claim,
                supported=c.supported,
                support_score=c.support_score,
                missing_anchors=c.missing_anchors,
                reason=c.reason,
            )
            for c in report.ungrounded_claims
        ],
    )
