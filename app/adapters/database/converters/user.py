from app.adapters.database.tables import UserTable
from app.domain.entities.user import User


def convert_user_table_to_dto(
    *,
    result: UserTable,
) -> User:
    return User(
        id=result.id,
        username=result.username,
        email=result.email,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
