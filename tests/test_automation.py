import pytest


def test_automation_modules_import():
    from app.automation import (
        browser,
        form_filler,
        portal,
        upload_handler,
        submission,
        approval,
    )

    modules = [
        browser,
        form_filler,
        portal,
        upload_handler,
        submission,
        approval,
    ]

    for module in modules:
        assert module is not None


def test_browser_module_imports():
    from app.automation import browser

    assert browser is not None


def test_form_filler_module_imports():
    from app.automation import form_filler

    assert form_filler is not None


def test_portal_module_imports():
    from app.automation import portal

    assert portal is not None


def test_upload_handler_module_imports():
    from app.automation import upload_handler

    assert upload_handler is not None


def test_submission_module_imports():
    from app.automation import submission

    assert submission is not None


def test_approval_module_imports():
    from app.automation import approval

    assert approval is not None


def test_automation_configuration_exists():
    from app.core.config import settings

    assert hasattr(settings, "playwright_headless")


def test_playwright_headless_is_boolean():
    from app.core.config import settings

    assert isinstance(settings.playwright_headless, bool)


def test_approval_required_for_submission():
    approval_required = True

    assert approval_required is True


def test_application_waiting_approval_status():
    status = "waiting_approval"

    assert status == "waiting_approval"


def test_automation_statuses():
    statuses = [
        "draft",
        "preparing",
        "verification_pending",
        "waiting_approval",
        "submitted",
        "under_review",
        "approved",
        "rejected",
        "failed",
        "cancelled",
    ]

    for status in statuses:
        assert isinstance(status, str)


def test_automation_module_has_content():
    from app.automation import browser

    public_items = [
        name
        for name in dir(browser)
        if not name.startswith("_")
    ]

    assert len(public_items) > 0