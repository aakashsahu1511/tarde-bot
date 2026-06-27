import hashlib
import os

from fastapi.testclient import TestClient

from app.main import app


def _ensure_test_settings():
    os.environ.setdefault("KITE_API_KEY", "test-key")
    os.environ.setdefault("KITE_API_SECRET", "test-secret")
    os.environ.setdefault("KITE_ACCESS_TOKEN", "test-access-token")
    os.environ.setdefault("KITE_USER_ID", "test-user-id")


def test_webhook_ignores_non_complete_order():
    _ensure_test_settings()
    client = TestClient(app)
    order_payload = {
        "order_id": "12345",
        "status": "OPEN",
        "transaction_type": "BUY",
        "tradingsymbol": "TEST1234CE",
        "exchange": "NFO",
        "product": "MIS",
        "quantity": 1,
        "average_price": 120.0,
        "order_timestamp": "2026-06-27 09:24:25",
    }
    order_payload["checksum"] = hashlib.sha256(
        f"{order_payload['order_id']}{order_payload['order_timestamp']}{os.environ['KITE_API_SECRET']}".encode("utf-8")
    ).hexdigest()
    payload = {
        "type": "order_update",
        "payload": order_payload,
    }

    response = client.post("/kite/postback", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert response.json()["reason"] == "order status is not COMPLETE or CANCELLED"


def test_webhook_ignores_non_buy_order():
    _ensure_test_settings()
    client = TestClient(app)
    order_payload = {
        "order_id": "12346",
        "status": "COMPLETE",
        "transaction_type": "SELL",
        "tradingsymbol": "TEST1234CE",
        "exchange": "NFO",
        "product": "MIS",
        "quantity": 1,
        "average_price": 120.0,
        "order_timestamp": "2026-06-27 09:25:00",
    }
    order_payload["checksum"] = hashlib.sha256(
        f"{order_payload['order_id']}{order_payload['order_timestamp']}{os.environ['KITE_API_SECRET']}".encode("utf-8")
    ).hexdigest()
    payload = {
        "type": "order_update",
        "payload": order_payload,
    }

    response = client.post("/kite/postback", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert response.json()["reason"] == "only BUY orders trigger stop-loss creation"


def test_webhook_creates_stop_loss_order(monkeypatch):
    _ensure_test_settings()

    captured = {}

    class DummyKiteClient:
        def __init__(self, settings):
            captured["settings"] = settings

        def place_sell_stop_loss(self, order, trigger_price, limit_price):
            captured["order_id"] = order.order_id
            captured["trigger_price"] = trigger_price
            captured["limit_price"] = limit_price
            captured["tradingsymbol"] = order.tradingsymbol
            return {"order_id": "stop-loss-1", "status": "success"}

    monkeypatch.setattr("app.routes.kite_webhook.KiteClient", DummyKiteClient)
    client = TestClient(app)
    order_payload = {
        "order_id": "12347",
        "status": "COMPLETE",
        "transaction_type": "BUY",
        "tradingsymbol": "TEST1234PE",
        "exchange": "NFO",
        "product": "MIS",
        "quantity": 1,
        "average_price": 100.0,
        "order_timestamp": "2026-06-27 09:26:00",
    }
    order_payload["checksum"] = hashlib.sha256(
        f"{order_payload['order_id']}{order_payload['order_timestamp']}{os.environ['KITE_API_SECRET']}".encode("utf-8")
    ).hexdigest()
    payload = {
        "type": "order_update",
        "payload": order_payload,
    }

    response = client.post("/kite/postback", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert data["original_order_id"] == "12347"
    assert captured["trigger_price"] == 90.0
    assert captured["limit_price"] == 89.95
    assert captured["tradingsymbol"] == "TEST1234PE"
    assert data["kite_response"]["order_id"] == "stop-loss-1"


def test_webhook_creates_stop_loss_order_on_cancelled_filled_buy_order(monkeypatch):
    _ensure_test_settings()

    captured = {}

    class DummyKiteClient:
        def __init__(self, settings):
            captured["settings"] = settings

        def place_sell_stop_loss(self, order, trigger_price, limit_price):
            captured["order_id"] = order.order_id
            captured["trigger_price"] = trigger_price
            captured["limit_price"] = limit_price
            captured["tradingsymbol"] = order.tradingsymbol
            return {"order_id": "stop-loss-2", "status": "success"}

    monkeypatch.setattr("app.routes.kite_webhook.KiteClient", DummyKiteClient)
    client = TestClient(app)
    order_payload = {
        "order_id": "12348",
        "status": "CANCELLED",
        "transaction_type": "BUY",
        "tradingsymbol": "TEST1234PE",
        "exchange": "NFO",
        "product": "MIS",
        "quantity": 1,
        "average_price": 100.0,
        "filled_quantity": 1,
        "order_timestamp": "2026-06-27 09:27:00",
    }
    order_payload["checksum"] = hashlib.sha256(
        f"{order_payload['order_id']}{order_payload['order_timestamp']}{os.environ['KITE_API_SECRET']}".encode("utf-8")
    ).hexdigest()
    payload = {
        "type": "order_update",
        "payload": order_payload,
    }

    response = client.post("/kite/postback", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert data["original_order_id"] == "12348"
    assert captured["trigger_price"] == 90.0
    assert captured["limit_price"] == 89.95
    assert captured["tradingsymbol"] == "TEST1234PE"
    assert data["kite_response"]["order_id"] == "stop-loss-2"
