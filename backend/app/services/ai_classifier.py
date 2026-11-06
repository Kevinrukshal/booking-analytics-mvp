import json

import httpx

from app.core.config import settings
from app.schemas.ai import AIClassification


ALLOWED_CATEGORIES = [
    "Passenger Details", "Flight / PNR", "Hotel", "Documentation", "Payment", "Deposit",
    "Pricing", "Product Availability", "Special Request", "Transfer", "Insurance",
    "Booking Process", "Communication", "Other",
]


def ai_enabled() -> bool:
    return bool(settings.allow_external_ai and settings.gemini_api_key and settings.gemini_model)


async def classify_issue(issue: str) -> AIClassification:
    if not ai_enabled():
        raise RuntimeError("AI classification is disabled. Configure the provider and explicitly allow external AI processing.")
    prompt = (
        "Classify one travel-booking operations issue. Return JSON only with keys category, subcategory, "
        "severity, summary, recommended_action. Category must be one of: " + ", ".join(ALLOWED_CATEGORIES) +
        ". Severity must be Low, Medium, High, or Critical. Do not invent facts. Issue: " + issue
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers={"x-goog-api-key": settings.gemini_api_key},
                json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}},
            )
            response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return AIClassification.model_validate(json.loads(text))

    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError):
        raise RuntimeError("AI provider request failed. Try again later.") from None
