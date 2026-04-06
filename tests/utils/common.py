from datetime import UTC, datetime, timedelta


def now_utc(
    days: float = 0,
    hours: float = 0,
    minutes: float = 0,
    seconds: float = 0,
    microseconds: float = 0,
    milliseconds: float = 0,
    weeks: float = 0,
) -> datetime:
    return datetime.now(tz=UTC) + timedelta(
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        microseconds=microseconds,
        milliseconds=milliseconds,
        weeks=weeks,
    )
