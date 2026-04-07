# Payment Service

Asynchronous payment processing service.

The service accepts payment requests, stores them in PostgreSQL, writes an outbox
event in the same transaction, publishes `payments.new` events to RabbitMQ,
processes payments in a consumer, and sends result notifications to client
webhooks.

## Architecture

- REST API is implemented with FastAPI and Pydantic v2.
- Persistence uses async SQLAlchemy 2 and PostgreSQL.
- Dependency injection is handled by Dishka.
- Runtime processes are aiomisc services started from one `python -m app` entrypoint.
- Payment creation uses idempotency by `Idempotency-Key`.
- API access is protected by static `X-API-Key`.
- Outbox pattern guarantees that payment creation and event creation happen in one DB transaction.
- Outbox relay publishes pending outbox messages to RabbitMQ.
- RabbitMQ queue `payments.new` uses quorum queue delivery limit and dead-letters failed messages to `payments.new.dlq`.
- Payment consumer emulates external gateway processing and updates only `pending` payments.
- Webhook delivery uses asyncly/aiohttp and retries failed deliveries via `aiomisc.asyncretry`.

## Current Flow

1. `POST /api/v1/payments/` creates a `pending` payment.
2. `CreatePaymentUC` writes `payment + outbox` in one DB transaction.
3. `outbox-relay` publishes pending outbox events to RabbitMQ queue `payments.new`.
4. `payment-consumer` reads `payments.new`.
5. The consumer emulates payment gateway processing: `2-5` seconds, `90%` success.
6. The consumer atomically updates only `pending` payments to `succeeded` or `failed`.
7. The consumer sends a webhook notification with retry.
8. RabbitMQ moves messages to `payments.new.dlq` after `3` failed deliveries.

## API

All `/api/v1/*` endpoints require `X-API-Key`.

```http
POST /api/v1/payments/
Idempotency-Key: payment-key
X-API-Key: secret
Content-Type: application/json

{
  "amount": "10.50",
  "currency": "USD",
  "description": "test payment",
  "metadata": {"order_id": "order-1"},
  "webhook_url": "https://example.com/webhook"
}
```

```http
GET /api/v1/payments/{payment_id}/
X-API-Key: secret
```

## Environment

Required:

```bash
APP_DB_DSN=postgresql+asyncpg://app:app@127.0.0.1:5432/app
APP_X_API_KEY=secret
APP_RABBITMQ_DSN=amqp://guest:guest@127.0.0.1:5672/
```

Useful defaults:

```bash
APP_REST_HOST=127.0.0.1
APP_REST_PORT=8000
APP_OUTBOX_POLL_INTERVAL=1
APP_OUTBOX_MAX_ATTEMPTS=3
APP_PAYMENT_GATEWAY_MIN_DELAY_SECONDS=2
APP_PAYMENT_GATEWAY_MAX_DELAY_SECONDS=5
APP_PAYMENT_GATEWAY_SUCCESS_RATE=0.9
APP_WEBHOOK_TIMEOUT_SECONDS=5
APP_WEBHOOK_MAX_ATTEMPTS=3
APP_WEBHOOK_INITIAL_DELAY_SECONDS=1
APP_WEBHOOK_BASE_URL=http://webhook.site
```

## Run Locally

Start local infrastructure:

```bash
make local
```

Run the application:

```bash
python -m app
```

This starts REST API, outbox relay, and payment consumer in one aiomisc
entrypoint.

## Docker Compose

Full runtime stack:

```bash
make prod
```

Apply migrations inside the production compose stack:

```bash
make prod-apply-migrations
```

Services:

- `db`: PostgreSQL
- `rabbitmq`: RabbitMQ with management UI on `15672`
- `app`: REST API, outbox relay, and payment consumer

## Tests And Checks

```bash
make lint-ci
make test-ci
```

Targeted checks used during development:

```bash
.venv/bin/ruff check ./app
.venv/bin/mypy ./app
.venv/bin/python -m pytest ./tests -q
```

## Migrations

Migrations are maintained manually in this repository. After model changes, create
or adjust Alembic migrations manually.
