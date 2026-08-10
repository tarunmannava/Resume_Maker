import pytest
from backend.app.services.industry_detector import (
    detect_industry_from_text,
    normalize_industry,
)


def test_industry_detection_disabled():
    result = detect_industry_from_text("Build secure banking APIs, payment processing.")
    assert result.industry is None
    assert result.confidence == 0.0


def test_normalize_industry_disabled():
    assert normalize_industry("financial services") is None
