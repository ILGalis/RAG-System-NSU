
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RagSpaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    owner_id: int = Field(gt=0)
    access_mode: Literal["private", "public"] = "private"


class RagSpaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    access_mode: Literal["private", "public"] | None = None


class RagSpaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int
    access_mode: str
    created_at: datetime
