from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StatusResponseSchema(BaseSchema):
    ok: bool
    status_code: PositiveInt
    message: str


class PaginationSchema(BaseSchema):
    limit: PositiveInt = Field(le=100, default=10)
    offset: int = Field(ge=0, default=0)


class ItemListSchema[ItemType](BaseSchema):
    total: int
    items: Sequence[ItemType]
