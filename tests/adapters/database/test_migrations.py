from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncEngine

from app.adapters.database.tables import BaseTable
from tests.utils.db import get_diff_db_metadata


async def test__up_to_date(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        diff = await connection.run_sync(
            get_diff_db_metadata,
            metadata=(BaseTable.metadata,),
        )
    assert not diff


def test__single_initial_revision(
    alembic_config: AlembicConfig,
) -> None:
    script = ScriptDirectory.from_config(alembic_config)
    revisions = list(script.walk_revisions(base="base", head="heads"))
    assert (script.get_heads(), [(r.revision, r.down_revision) for r in revisions]) == (
        ["0001"],
        [("0001", None)],
    )
