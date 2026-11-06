# Payment Service

Asynchronous payment processing with FastAPI/Pydantic v2, async SQLAlchemy 2,
PostgreSQL, RabbitMQ/FastStream, Alembic, Dishka and aiomisc.

The application has two runtime roles, sharing one image:

- `python -m app api`: authenticated create/get API; PostgreSQL is sufficient.
- `python -m app worker`: one payment consumer and the outbox/recovery relay.

See [the workflow contract](docs/payment-workflow.md) for state transitions,
transaction boundaries and the approved failure semantics.

## Create and read a payment

All `/api/v1/*` endpoints require `X-API-Key`. Creation also requires
`Idempotency-Key`. The metadata field is named **meta_data**.

```bash
curl -i http://127.0.0.1:8000/api/v1/payments/ \
  -H 'X-API-Key: secret' \
  -H 'Idempotency-Key: order-1' \
  -H 'Content-Type: application/json' \
  -d '{
    "amount": "10.50",
    "currency": "USD",
    "description": "order-1",
    "meta_data": {"order_id": "order-1"},
    "webhook_url": "https://example.com/webhook"
  }'
```

The response is `202 Accepted` with `payment_id`, `status: pending` and
`created_at`. Identical replays, including concurrent requests, return the
original response. A completed payment still replays its original pending
response; GET supplies the current state. Changing any creation field with the
same key returns `409 Conflict`. Amounts such as `10.5` and `10.50` compare equally;
JSON object key order does not matter. Keys remain reserved while their payment
exists, including soft-deleted payments.

```bash
curl http://127.0.0.1:8000/api/v1/payments/PAYMENT_ID/ \
  -H 'X-API-Key: secret'
```

GET includes the original fields plus `processing_status`, `processing_attempts`
and a `notification` object with `status`, `webhook_attempts`, `delivered_at`
and a bounded error category. Two gateway errors followed by one failed webhook
produce `processing_attempts=3`, `webhook_attempts=1`. These are durable starts,
including starts lost during a crash; they are not confirmed HTTP deliveries.

## Processing and delivery

1. Creation inserts payment and outbox in one transaction.
2. Relay publishes `payments.new` with publisher confirms and mandatory routing.
3. Consumer reserves a logical attempt in the database, then calls the gateway
   outside the transaction. Default emulation: 2-5 seconds, 90% succeeded,
   10% business failed.
4. The terminal gateway result is saved before one webhook call. Subsequent
   attempts reuse this result and the same webhook payload.
5. A failure atomically saves the attempt outcome and an outbox event for retry
   or DLQ. The original AMQP delivery is acknowledged after this commit.
6. Retry queues `payments.retry.1` and `payments.retry.2` wait 1 and 2 seconds
   using TTL/DLX and return the envelope to `payments.new`.
7. After three total starts, an outbox event targets `payments.new.dlq`.
   There is no nested HTTP retry loop and no fourth logical attempt.

Any non-2xx webhook response, network error or timeout uses this same budget,
including 4xx responses. Webhook failure never reverses the known payment result.
Redirects are not followed: 3xx is also a failed attempt, and the redirect target
receives no implicit request.
If no gateway result was obtained, the payment stays pending with processing
exhausted and notification not sent.

Expired claims are recovered by the relay. Recovery fences the old executor,
then schedules the next attempt or DLQ without incrementing the counter a second
time. Duplicate/stale envelopes cannot reserve the same attempt again.

An unknown HTTP outcome may be retried in the remaining budget. Receivers must
deduplicate by payment_id. There is one final notification per payment. The
service provides bounded at-least-once attempts, not exactly-once HTTP delivery.

Outbox publication failures have an independent counter and an increasing,
capped retry delay. They remain pending until the broker recovers. An exhausted
workflow with a pending DLQ outbox event does not yet prove arrival in DLQ.

## Run locally

Install Python 3.12 and uv, then:

```bash
uv sync --frozen --dev
docker compose -f docker-compose.dev.yaml up -d
export APP_DB_DSN='postgresql+asyncpg://app:app@127.0.0.1:5432/app'
export APP_RABBITMQ_DSN='amqp://guest:guest@127.0.0.1:5672/'
export APP_X_API_KEY='secret'
.venv/bin/python -m app.adapters.database upgrade head
.venv/bin/python -m app api
# In another terminal, with the same environment:
.venv/bin/python -m app worker
```

Swagger: `http://127.0.0.1:8000/docs/swagger`.

Use a separate Compose project and ports when another local stack already owns
5432/5672/8000.

## Docker stack

Compose defines PostgreSQL, RabbitMQ, api and worker. API does not depend on
RabbitMQ availability.

```bash
docker compose build
docker compose up -d db rabbitmq
docker compose run --rm api python -m app.adapters.database upgrade head
docker compose up -d api worker
```

Compose targets RabbitMQ **3.13**. Quorum retry queues explicitly use
`x-dead-letter-strategy=at-least-once` and `x-overflow=reject-publish`.
The broker delivery limit is unset: RabbitMQ 3.13 has no default limit, and
application claims enforce the business budget. RabbitMQ 4.x has different
delivery-limit defaults and is outside the tested configuration.

Queue arguments differ from the previous version. For an existing installation,
drain/archive its queues and prepare a fresh vhost before switching consumers.
Do not delete old queues as an automatic upgrade step. API/database state and
old broker messages must be reconciled before any real cutover.

Migration `7ab0a8efff9f` adds workflow fields, claim metadata, counter constraints,
recovery/publishing indexes and outbox availability. Previously completed payments
have notification status unknown because delivery was not recorded. Old failed
publication events become pending again. Downgrade refuses to discard retry/DLQ
outbox records; archive/drain them before a separately planned rollback.

There is no automatic redrive after workflow exhaustion. DLQ and GET expose the
outcome for diagnosis; replaying an old envelope does not reset its budget.

## Configuration

| Variable | Default |
| --- | --- |
| APP_REST_HOST / APP_REST_PORT | 127.0.0.1 / 8000 |
| APP_OUTBOX_POLL_INTERVAL | 1 second |
| APP_OUTBOX_INITIAL_DELAY_SECONDS | 1 second |
| APP_OUTBOX_MAX_DELAY_SECONDS | 30 seconds |
| APP_RETRY_INITIAL_DELAY_SECONDS | 1 second; second step is twice this |
| APP_PROCESSING_LEASE_SECONDS | 30 seconds |
| APP_GATEWAY_TIMEOUT_SECONDS | 10 seconds |
| APP_WEBHOOK_TIMEOUT_SECONDS | 5 seconds |
| APP_PUBLISH_TIMEOUT_SECONDS | 5 seconds |
| APP_PAYMENT_GATEWAY_MIN_DELAY_SECONDS | 2 seconds |
| APP_PAYMENT_GATEWAY_MAX_DELAY_SECONDS | 5 seconds |
| APP_PAYMENT_GATEWAY_SUCCESS_RATE | 0.9 |

The lease must exceed the combined gateway and webhook timeouts.
`APP_OUTBOX_MAX_ATTEMPTS`, `APP_WEBHOOK_MAX_ATTEMPTS` and
`APP_WEBHOOK_INITIAL_DELAY_SECONDS` are removed: processing has one fixed budget
of three, and RabbitMQ owns processing delays.

## Tests

Run against a dedicated test PostgreSQL, never a database containing user data:

```bash
APP_DB_DSN='postgresql+asyncpg://app:app@127.0.0.1:5432/payment_test' \
  .venv/bin/pytest tests -q
.venv/bin/ruff check app tests
.venv/bin/mypy app
```

For real broker and subprocess checks also set:

```bash
export APP_TEST_RABBITMQ_DSN='amqp://guest:guest@127.0.0.1:5672/'
export APP_TEST_RABBITMQ_MANAGEMENT_URL='http://127.0.0.1:15672'
.venv/bin/pytest tests/integration -q
```

Without those two variables the real-broker tests explicitly skip. The runtime
test requires a local disposable payment_* database and a role able to create
test databases. Each run owns a separate database and RabbitMQ vhost and removes
them afterwards. It starts actual API/worker processes, receives real HTTP
webhooks, measures both TTL delays, reads DLQ, kills the worker during an unknown
webhook outcome and verifies recovery. Gateway delays are shortened in that
test only; processing delays remain 1/2 seconds.
Malformed JSON/array/string envelopes are checked through the actual subscriber
and must reach quarantine without blocking the next valid payment. Additional
regressions cover HTTP 302/307 and a lost response to a committed webhook start.

These automated checks are developer/integration evidence. Owner-facing visual
QA uses a continuous MP4 recording; no screenshot artifacts are generated.
