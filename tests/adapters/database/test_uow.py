from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.uow import SqlalchemyUow


async def test_session_closes_when_commit_fails() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.begin = AsyncMock()
    session.commit.side_effect = OSError("commit response lost")
    uow = SqlalchemyUow(session)
    failed = False
    try:
        async with uow:
            pass
    except OSError:
        failed = True
    assert (failed, session.close.await_count) == (True, 1)
