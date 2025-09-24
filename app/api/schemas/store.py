from pydantic import BaseModel, Field


class StoreItem(BaseModel):
    name: str = Field(max_length=255)
    description: str
    price: int = Field(ge=0)
    image: str | None = None
    exists: bool


class StoreListResponse(BaseModel):
    items: list[StoreItem]


class StoreBuyRequest(BaseModel):
    name: str = Field(..., max_length=255)
