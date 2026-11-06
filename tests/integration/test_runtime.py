import asyncio
import json
import os
import socket
import sys
import time
from collections import defaultdict
from pathlib import Path
from uuid import uuid4

import pytest
from aio_pika import DeliveryMode, Message, connect_robust
from aiohttp import web
from httpx import AsyncClient, HTTPError
from sqlalchemy.ext.asyncio import create_async_engine

from app.adapters.database.config import DatabaseConfig
from app.adapters.database.tables import BaseTable
from tests.utils.durable_database import runtime_database
from tests.utils.rabbit import isolated_rabbit

ROOT = Path(__file__).resolve().parents[2]


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


async def drain_output(stream: asyncio.StreamReader, log: list[str]) -> None:
    async for line in stream:
        log.append(line.decode(errors="replace"))


async def start_role(
    role: str,
    environment: dict[str, str],
    log: list[str],
) -> tuple[asyncio.subprocess.Process, asyncio.Task]:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "app",
        role,
        cwd=ROOT,
        env=environment,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    return process, asyncio.create_task(drain_output(process.stdout, log))


async def stop_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is None:
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=8)
        except TimeoutError:
            process.kill()
            await process.wait()


async def wait_api(client: AsyncClient) -> None:
    for _ in range(100):
        try:
            response = await client.get(f"/api/v1/payments/{uuid4()}/")
            if response.status_code == 404:
                return
        except HTTPError:
            pass
        await asyncio.sleep(0.1)
    raise AssertionError("API did not become ready")


async def wait_payment(client: AsyncClient, payment_id: str, state: str) -> dict:
    last = None
    for _ in range(150):
        response = await client.get(f"/api/v1/payments/{payment_id}/")
        response.raise_for_status()
        last = response.json()
        if last["processing_status"] == state:
            return last
        await asyncio.sleep(0.1)
    raise AssertionError(f"Payment did not reach {state}: {last}")


async def exercise_runtime(
    db_config: DatabaseConfig,
) -> None:
    engine = create_async_engine(db_config.dsn)
    async with engine.begin() as connection:
        await connection.run_sync(BaseTable.metadata.create_all)
    await engine.dispose()

    calls: dict[str, list[tuple[float, dict]]] = defaultdict(list)
    received_before_crash = asyncio.Event()
    release_response = asyncio.Event()

    async def callback(request: web.Request) -> web.Response:
        path = request.match_info["scenario"]
        payload = await request.json()
        calls[path].append((time.monotonic(), payload))
        if path == "recover" and len(calls[path]) == 1:
            received_before_crash.set()
            await release_response.wait()
        if path == "permanent":
            return web.Response(status=400)
        if path == "eventual" and len(calls[path]) < 3:
            return web.Response(status=503)
        return web.Response(status=204)

    receiver = web.Application()
    receiver.router.add_post("/{scenario}", callback)
    runner = web.AppRunner(receiver)
    await runner.setup()
    callback_port = available_port()
    site = web.TCPSite(runner, "127.0.0.1", callback_port)
    await site.start()
    processes: list[asyncio.subprocess.Process] = []
    drains: list[asyncio.Task] = []
    log: list[str] = []
    try:
        async with isolated_rabbit() as rabbit:
            api_port = available_port()
            environment = {
                **os.environ,
                "APP_DB_DSN": db_config.dsn,
                "APP_RABBITMQ_DSN": rabbit.dsn,
                "APP_X_API_KEY": "integration-only",
                "APP_REST_HOST": "127.0.0.1",
                "APP_REST_PORT": str(api_port),
                "APP_DEBUG": "False",
                "APP_OUTBOX_POLL_INTERVAL": "0.05",
                "APP_PROCESSING_LEASE_SECONDS": "4",
                "APP_GATEWAY_TIMEOUT_SECONDS": "1",
                "APP_WEBHOOK_TIMEOUT_SECONDS": "2",
                "APP_RETRY_INITIAL_DELAY_SECONDS": "1",
                "APP_PAYMENT_GATEWAY_MIN_DELAY_SECONDS": "0.01",
                "APP_PAYMENT_GATEWAY_MAX_DELAY_SECONDS": "0.01",
                "APP_PAYMENT_GATEWAY_SUCCESS_RATE": "1",
            }
            for role in ("api", "worker"):
                process, drain = await start_role(role, environment, log)
                processes.append(process)
                drains.append(drain)
            async with AsyncClient(
                base_url=f"http://127.0.0.1:{api_port}",
                headers={"X-API-Key": "integration-only"},
                timeout=5,
            ) as client:
                await wait_api(client)

                async def create(scenario: str) -> tuple[dict, dict, str]:
                    body = {
                        "amount": "10.50",
                        "currency": "USD",
                        "description": "runtime integration",
                        "meta_data": {"scenario": scenario},
                        "webhook_url": f"http://127.0.0.1:{callback_port}/{scenario}",
                    }
                    headers = {"Idempotency-Key": uuid4().hex}
                    response = await client.post(
                        "/api/v1/payments/",
                        headers=headers,
                        json=body,
                    )
                    response.raise_for_status()
                    return response.json(), body, headers["Idempotency-Key"]

                accepted, body, key = await create("eventual")
                eventual = await wait_payment(
                    client, accepted["payment_id"], "completed"
                )
                replay = await client.post(
                    "/api/v1/payments/",
                    headers={"Idempotency-Key": key},
                    json=body,
                )
                permanent_accepted, _, _ = await create("permanent")
                permanent = await wait_payment(
                    client,
                    permanent_accepted["payment_id"],
                    "exhausted",
                )
                async with await connect_robust(rabbit.dsn) as connection:
                    channel = await connection.channel()
                    queue = await channel.get_queue("payments.new.dlq")
                    dead_letter = None
                    for _ in range(60):
                        message = await queue.get(fail=False)
                        if message is not None:
                            dead_letter = json.loads(message.body)
                            await message.ack()
                            break
                        await asyncio.sleep(0.1)

                recovery_accepted, _, _ = await create("recover")
                await asyncio.wait_for(received_before_crash.wait(), timeout=10)
                worker = processes[-1]
                worker.kill()
                await worker.wait()
                release_response.set()
                restarted, drain = await start_role("worker", environment, log)
                processes.append(restarted)
                drains.append(drain)
                recovered = await wait_payment(
                    client,
                    recovery_accepted["payment_id"],
                    "completed",
                )
                poisons = [b"[]", b'"text"', b"not-json"]
                quarantined = []
                async with await connect_robust(rabbit.dsn) as connection:
                    channel = await connection.channel()
                    for index, body in enumerate(poisons):
                        await channel.default_exchange.publish(
                            Message(
                                body=body,
                                content_type="application/json",
                                message_id=f"malformed-{index}",
                                delivery_mode=DeliveryMode.PERSISTENT,
                            ),
                            routing_key="payments.new",
                            mandatory=True,
                        )
                    queue = await channel.get_queue("payments.new.dlq")
                    for _ in range(80):
                        message = await queue.get(fail=False)
                        if message is not None:
                            quarantined.append(message.body)
                            await message.ack()
                        if len(quarantined) == len(poisons):
                            break
                        await asyncio.sleep(0.1)
                after_poison_accepted, _, _ = await create("after-poison")
                after_poison = await wait_payment(
                    client, after_poison_accepted["payment_id"], "completed"
                )
                await asyncio.sleep(0.2)
                timing = [
                    calls["eventual"][i + 1][0] - calls["eventual"][i][0]
                    for i in (0, 1)
                ]
                observed = {
                    "eventual": (
                        eventual["status"],
                        eventual["processing_attempts"],
                        eventual["notification"]["webhook_attempts"],
                    ),
                    "stable_replay": (replay.status_code, replay.json() == accepted),
                    "backoff": (timing[0] >= 0.9, timing[1] >= 1.9),
                    "same_payload": len(
                        {
                            json.dumps(payload, sort_keys=True)
                            for _, payload in calls["eventual"]
                        }
                    )
                    == 1,
                    "permanent": (
                        permanent["status"],
                        permanent["processing_attempts"],
                        permanent["notification"]["webhook_attempts"],
                        len(calls["permanent"]),
                    ),
                    "dlq": dead_letter,
                    "recovered": (
                        recovered["status"],
                        recovered["processing_attempts"],
                        recovered["notification"]["webhook_attempts"],
                        len(calls["recover"]),
                        calls["recover"][0][1] == calls["recover"][1][1],
                    ),
                    "quarantined": sorted(quarantined),
                    "after_poison": (
                        after_poison["processing_attempts"],
                        after_poison["notification"]["webhook_attempts"],
                    ),
                }
                assert observed == {
                    "eventual": ("succeeded", 3, 3),
                    "stable_replay": (202, True),
                    "backoff": (True, True),
                    "same_payload": True,
                    "permanent": ("succeeded", 3, 3, 3),
                    "dlq": {
                        "payment_id": permanent_accepted["payment_id"],
                        "attempt": 3,
                    },
                    "recovered": ("succeeded", 2, 2, 2, True),
                    "quarantined": sorted(poisons),
                    "after_poison": (1, 1),
                }
            for process in reversed(processes):
                await stop_process(process)
    except Exception as exc:
        exc.add_note("".join(log[-80:]))
        raise
    finally:
        release_response.set()
        for process in reversed(processes):
            await stop_process(process)
        await asyncio.gather(*drains)
        await runner.cleanup()


async def test_actual_api_worker_retry_dlq_and_crash_recovery(
    db_config: DatabaseConfig,
) -> None:
    if not os.getenv("APP_TEST_RABBITMQ_DSN") or not os.getenv(
        "APP_TEST_RABBITMQ_MANAGEMENT_URL"
    ):
        pytest.skip("Runtime integration requires a disposable RabbitMQ")
    async with runtime_database(db_config.dsn) as dsn:
        await exercise_runtime(DatabaseConfig(dsn=dsn))
