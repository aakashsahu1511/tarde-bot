# Kite Stop Loss Service

A small FastAPI application that receives Kite order status postbacks and places a sell stop-loss limit order when a completed buy order is detected.

## Technical architecture

- `app/main.py` — FastAPI app factory and router registration
- `app/config.py` — environment-backed settings using `pydantic-settings`
- `app/routes/health.py` — `GET /health`
- `app/routes/kite_webhook.py` — `POST /kite/postback`
- `app/services/kite_client.py` — Kite Connect wrapper for placing orders
- `app/models/schemas.py` — request validation for Kite postback payloads

## Functional behavior

- Health endpoint confirms service availability
- Webhook endpoint accepts Kite order status postbacks at `POST /kite/postback`
- Only `BUY` orders with status `COMPLETE` or `CANCELLED` and filled quantity are processed
- Stop-loss trigger is calculated as the greater of:
  - 10 INR
  - 10% of executed buy price
- A sell stop-loss limit order is created through Kite Connect

## Configuration

1. Copy `.env.example` to `.env`
2. Set your Kite credentials and optional defaults

Required variables:

- `KITE_API_KEY`
- `KITE_API_SECRET`
- `KITE_ACCESS_TOKEN`
- `KITE_USER_ID`

`KITE_API_SECRET` is used to validate the incoming Kite checksum

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
pytest -q
```
