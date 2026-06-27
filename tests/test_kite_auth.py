import os
import sys
import types

from fastapi.testclient import TestClient

from app.main import app


def _ensure_test_settings():
    os.environ.setdefault("KITE_API_KEY", "test-key")
    os.environ.setdefault("KITE_API_SECRET", "test-secret")
    os.environ.setdefault("KITE_USER_ID", "test-user-id")


def test_kite_auth_login_callback_success(monkeypatch):
    _ensure_test_settings()
    os.environ.setdefault("KITE_ACCESS_TOKEN", "")
    os.environ.setdefault("KITE_AUTO_SAVE_TOKEN", "false")

    expected_session = {"access_token": "new-access-token", "user_id": "NR5684"}

    class DummyKiteConnect:
        def __init__(self, api_key):
            assert api_key == "test-key"

        def generate_session(self, request_token, api_secret):
            assert request_token == "test-request-token"
            assert api_secret == "test-secret"
            return expected_session

    kiteconnect_module = types.ModuleType("kiteconnect")
    setattr(kiteconnect_module, "KiteConnect", DummyKiteConnect)
    monkeypatch.setitem(sys.modules, "kiteconnect", kiteconnect_module)

    client = TestClient(app)
    response = client.get(
        "/kite/auth/login",
        params={"status": "success", "request_token": "test-request-token", "action": "login"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["kite_session"] == expected_session
    assert data["redirect_action"] == "login"


def test_kite_auth_login_missing_token():
    _ensure_test_settings()
    client = TestClient(app)
    response = client.get("/kite/auth/login", params={"status": "success"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Missing request_token in Kite redirect callback"


def test_kite_auth_login_redirect(monkeypatch):
    _ensure_test_settings()

    class DummyKiteConnect:
        def __init__(self, api_key):
            assert api_key == "test-key"

        def login_url(self):
            return "https://kite.trade/connect/login?api_key=test-key&v=3"

    kiteconnect_module = types.ModuleType("kiteconnect")
    setattr(kiteconnect_module, "KiteConnect", DummyKiteConnect)
    monkeypatch.setitem(sys.modules, "kiteconnect", kiteconnect_module)

    client = TestClient(app)
    response = client.get("/kite/auth/login", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://kite.trade/connect/login?api_key=test-key&v=3"



