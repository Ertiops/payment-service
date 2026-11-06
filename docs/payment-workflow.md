# Payment workflow contract

Approved through Grill Me Q1-Q14, all option A, against the owner's original
payment-service assignment. Baseline: b1b422d83fda2b6b572ddceb7a8b7eaacad02d48.
This document describes the implementation contract, not a deployment approval.

## Boundaries

- api accepts requests and commits payment + initial outbox event.
- worker runs one consumer and the publishing/recovery relay.
- payments owns immutable creation data, the business result and its single
  notification lifecycle. outbox owns durable outbound envelopes.
- FastAPI/FastStream adapters validate transport shapes and invoke use cases.
  Use cases decide transitions. Storages execute one query per method.
- Gateway and webhook adapters perform one external attempt; retries belong to
  the workflow, with RabbitMQ providing delays.

## State and budget

Business status: pending -> succeeded | failed. A 10% emulated business decline
is final. Technical exhaustion before a known result leaves pending.

Processing status: ready -> running -> completed | retrying | exhausted.
Only an atomic claim for the expected envelope number increments
processing_attempts. Its range is 0..3. A durably started attempt is spent even
if its process dies before an external request.

Notification status: not_sent -> sending -> delivered | retrying | failed.
Legacy delivery evidence is unknown. webhook_attempts counts durable starts
of sending, is at most processing_attempts, and does not prove client receipt.
The status of a notification never overwrites the business status.

A known gateway result is committed before starting the webhook. Retrying
therefore skips the gateway and reuses payment_id, status and processed_at.

## Transactions

1. Creation: INSERT ON CONFLICT DO NOTHING; on conflict, separately read the
   winner in the same Read Committed transaction and compare creation fields.
   A new payment alone gets one initial outbox envelope. Return the original
   accepted DTO, with pending status, for every matching replay.
2. Claim: compare expected attempt number and runnable state, then set a fresh
   token, lease and increment processing_attempts in one UPDATE.
3. Gateway result: token/lease-fenced UPDATE of pending to a terminal result.
4. Webhook start: fenced UPDATE of notification state and webhook_attempts.
5. Failure: fenced completion and next retry/DLQ outbox envelope in one UoW.
   Success commits delivered state. Broker ACK follows successful UoW exit.
6. Recovery: lock one expired running row with SKIP LOCKED, fence its token,
   complete it as unknown and write the next envelope in the same UoW.
   Recovery schedules work; only the next consumer claim increments its count.

Stale and duplicate envelopes cannot claim an already started number. A stale
executor cannot mutate the new workflow state after recovery. An external HTTP
request already sent cannot be revoked; receiver deduplication remains required.

## RabbitMQ and outbox

One handler consumes payments.new. Retry after failed start 1 routes through
payments.retry.1 (TTL 1 second), then after failed start 2 through
payments.retry.2 (TTL 2 seconds). Both use safe quorum DLX back to payments.new.
After start 3 the next durable intent targets payments.new.dlq with attempt=3.
No nested HTTP retry loop is present.

Publisher confirms, mandatory routing, persistent messages and return errors
are enabled. DLQ is declared before consumers start. Broker connection/storage
failures before durable completion keep the AMQP delivery unacknowledged.
Malformed envelopes are quarantined; they cannot claim a payment attempt.

Outbox failures keep the event pending, with an independently increasing
publication counter and capped transport backoff. The consumer's three-start
budget is unaffected. An outbox intent and a confirmed DLQ publication are
different states; pending publication is never reported as confirmed arrival.

## API and acceptance

POST /api/v1/payments/ requires X-API-Key and Idempotency-Key. Same normalized
creation fields return the original 202 snapshot. Different fields return 409.
Keys do not expire while the payment exists. GET returns current business and
workflow state with separate processing_attempts and notification.webhook_attempts.

Acceptance covers concurrent create/claim, changed payloads, stable replay after
completion, one gateway result, shared three-attempt budget, real 1/2-second
retry delays, all webhook non-2xx/timeout/network errors, DLQ publication,
unknown outcomes, crash recovery, stale-token fencing and eventual outbox
publication after transient broker failure. Migration checks cover schema
agreement, legacy unknown delivery and downgrade protection.

A real payment provider, an exactly-once HTTP protocol, redrive API, multi-tenant
key scoping and additional notification consumers are outside this assignment.
