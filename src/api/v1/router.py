from fastapi import APIRouter
from src.schemas.models import GuardCheckRequest, GuardCheckResponse
from src.services.service import SafetyGuardService

router = APIRouter(prefix="/api/v1/guard", tags=["Safety Guard"])
guard = SafetyGuardService()

@router.post("/inspect", response_model=GuardCheckResponse)
def inspect_prompt(payload: GuardCheckRequest):
    is_safe, risk, violations, masked = guard.inspect(payload.prompt)
    return GuardCheckResponse(is_safe=is_safe, risk_score=risk, violations=violations, masked_prompt=masked)
