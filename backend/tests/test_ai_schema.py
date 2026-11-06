import pytest
from pydantic import ValidationError

from app.schemas.ai import AIClassification


def test_ai_response_validation():
    payload = AIClassification(category="Passenger Details", subcategory="Incorrect name", severity="High", summary="Name is wrong.", recommended_action="Correct the PNR.")
    assert payload.severity == "High"
    with pytest.raises(ValidationError):
        AIClassification(category="Other", subcategory="Other", severity="Urgent", summary="x", recommended_action="y")
