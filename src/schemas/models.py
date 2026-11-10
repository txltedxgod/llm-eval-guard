from pydantic import BaseModel, Field


class GuardCheckRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=20000)


class GuardCheckResponse(BaseModel):
    is_safe: bool
    risk_score: float
    violations: list[str]
    masked_prompt: str
    redacted_entities: dict[str, int] = Field(default_factory=dict)


class GroundednessCheckRequest(BaseModel):
    context: str | list[str]
    response: str = Field(..., min_length=1, max_length=40000)
    min_groundedness: float = Field(0.6, ge=0.0, le=1.0)


class ClaimVerdictSchema(BaseModel):
    claim: str
    supported: bool
    support_score: float
    missing_anchors: list[str] = Field(default_factory=list)
    reason: str


class GroundednessCheckResponse(BaseModel):
    is_grounded: bool
    groundedness_score: float
    hallucination_risk: float
    total_claims: int
    grounded_claims: int
    ungrounded_claims: list[ClaimVerdictSchema] = Field(default_factory=list)
