import os


def get_worker_name() -> str:
    return os.environ.get("PYTEST_XDIST_WORKER", "master")


def get_worker_schema_name() -> str:
    return f"test_{get_worker_name()}"


def get_worker_index() -> int:
    w = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    return int(w[2:]) if w.startswith("gw") else 0
