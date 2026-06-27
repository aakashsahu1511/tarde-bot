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

`KITE_API_SECRET` is used to validate the incoming Kite checksum.

### Kite auth flow

- `GET /kite/auth/login` redirects the user to the Kite Connect login page.
- Kite sends the user back to `GET /kite/auth/callback` after login.
- The callback exchanges `request_token` for an access token via Kite Connect.
- Set `KITE_AUTO_SAVE_TOKEN=true` to persist the generated token back into `.env`.
- Use `GET /kite/auth/status` to verify whether a token is saved and the user is authenticated.

### What belongs in `.env`

Put only sensitive Kite credentials and application-level defaults in `.env`.

- `KITE_API_KEY`
- `KITE_API_SECRET`
- `KITE_ACCESS_TOKEN`
- `KITE_USER_ID`
- `KITE_DEFAULT_PRODUCT`
- `KITE_DEFAULT_VARIETY`
- `KITE_ORDER_VALIDITY`
- `KITE_STOP_LOSS_MINIMUM_AMOUNT`
- `KITE_STOP_LOSS_PERCENTAGE`

### What can be JSON payload data instead

Order-specific request values from the Kite curl example should typically be passed as JSON or form data for each order, not stored as environment variables.

Example order payload fields:

- `variety`
- `exchange`
- `tradingsymbol`
- `transaction_type`
- `order_type`
- `quantity`
- `price`
- `product`
- `validity`
- `disclosed_quantity`
- `trigger_price`
- `squareoff`
- `stoploss`
- `trailing_stoploss`
- `tag`

These values may change per order and should be maintained in your order request body.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
pytest -q
```
