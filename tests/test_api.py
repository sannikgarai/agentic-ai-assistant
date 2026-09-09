import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_application_starts(client):
    response = client.get("/")

    assert response.status_code in {200, 404}


def test_openapi_available(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    data = response.json()

    assert "openapi" in data
    assert "paths" in data


def test_docs_available(client):
    response = client.get("/docs")

    assert response.status_code == 200


def test_chat_route_exists(client):
    routes = {route.path for route in app.routes}

    assert any(
        path.startswith("/chat") or path.endswith("/chat")
        for path in routes
    )


def test_voice_route_exists(client):
    routes = {route.path for route in app.routes}

    assert any(
        path.startswith("/voice") or path.endswith("/voice")
        for path in routes
    )


def test_documents_route_exists(client):
    routes = {route.path for route in app.routes}

    assert any(
        path.startswith("/documents") or path.endswith("/documents")
        for path in routes
    )


def test_verification_route_exists(client):
    routes = {route.path for route in app.routes}

    assert any(
        path.startswith("/verification") or path.endswith("/verification")
        for path in routes
    )


def test_applications_route_exists(client):
    routes = {route.path for route in app.routes}

    assert any(
        path.startswith("/applications") or path.endswith("/applications")
        for path in routes
    )


def test_history_route_exists(client):
    routes = {route.path for route in app.routes}

    assert any(
        path.startswith("/history") or path.endswith("/history")
        for path in routes
    )