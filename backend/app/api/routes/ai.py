from fastapi import APIRouter, HTTPException

from app.schemas.ai import AIClassificationRequest
from app.services.ai_classifier import ai_enabled, classify_issue

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
def status():
    return {"enabled": ai_enabled()}


@router.post("/classify")
async def classify(payload: AIClassificationRequest):
    try:
        return await classify_issue(payload.issue)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc

