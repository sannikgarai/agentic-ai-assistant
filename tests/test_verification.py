import pytest


def test_verification_modules_import():
    from app.verification import (
        field_matcher,
        mismatch_detector,
        eligibility_checker,
        engine,
    )

    modules = [
        field_matcher,
        mismatch_detector,
        eligibility_checker,
        engine,
    ]

    for module in modules:
        assert module is not None


def test_field_matcher_imports():
    from app.verification import field_matcher

    assert field_matcher is not None


def test_mismatch_detector_imports():
    from app.verification import mismatch_detector

    assert mismatch_detector is not None


def test_eligibility_checker_imports():
    from app.verification import eligibility_checker

    assert eligibility_checker is not None


def test_verification_engine_imports():
    from app.verification import engine

    assert engine is not None


def test_verification_result_structure():
    result = {
        "status": "verified",
        "score": 1.0,
        "mismatches": [],
    }

    assert result["status"] == "verified"
    assert result["score"] == 1.0
    assert result["mismatches"] == []


def test_mismatch_result_structure():
    result = {
        "status": "mismatch",
        "score": 0.5,
        "mismatches": [
            {
                "field": "name",
                "expected": "John",
                "actual": "Jon",
            }
        ],
    }

    assert result["status"] == "mismatch"
    assert result["score"] < 1.0
    assert len(result["mismatches"]) == 1


def test_score_range():
    scores = [0.0, 0.25, 0.5, 0.75, 1.0]

    for score in scores:
        assert 0.0 <= score <= 1.0


def test_verification_statuses():
    statuses = [
        "pending",
        "verified",
        "mismatch",
        "failed",
        "ineligible",
        "manual_review",
    ]

    for status in statuses:
        assert isinstance(status, str)


def test_verification_module_has_content():
    from app.verification import engine

    public_items = [
        name
        for name in dir(engine)
        if not name.startswith("_")
    ]

    assert len(public_items) > 0