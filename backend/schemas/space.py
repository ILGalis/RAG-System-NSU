
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict,EmailStr, Field

class SpaceOwnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    #поле под вопросом, нужно ли знать емеил создателя?
    email: EmailStr
    first_name: str
    last_name: str

class RagSpaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    owner_id: int = Field(gt=0)
    access_mode: Literal["private", "public"] = "private"
    faculty: str = Field(default="", max_length=200)
    #в теории можно сделать NULL чтобы например ученик создавал приватные раги без факультета


class RagSpaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    access_mode: Literal["private", "public"] | None = None
    faculty: str = Field(default="", max_length=200)
    #АНАЛОГИЧНО с RagSpaceCreate

class RagSpaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    faculty : str
    owner_id: int
    owner : SpaceOwnerOut
    access_mode: str
    created_at: datetime

