from fastapi import FastAPI
from pydantic import BaseModel
from eval_guard.guard import SafetyGuard

app = FastAPI(title="LLM Eval Guard", version="0.1.0")
guard = SafetyGuard()

class CheckRequest(BaseModel):
    prompt: str

@app.post("/api/v1/guard")
def check_safety(req: CheckRequest):
    return guard.evaluate(req.prompt)

@app.get("/health")
def health():
    return {"status": "ok", "service": "llm-eval-guard"}
