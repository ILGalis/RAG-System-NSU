from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    space_id: str
    source_name: str
    file_type: str
    file_size: int
    status: str
    error_message: str | None
    created_at: datetime

    @field_validator("id", "space_id", mode="before")
    @classmethod
    def _as_str(cls, v):
        return str(v)