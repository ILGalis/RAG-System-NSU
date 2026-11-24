from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


#class InvitationCreate(BaseModel):
#   ttl_hours: int = 168  #это в часах, по умолчанию 7 дней
class InvitationCreate(BaseModel):
    # от 1 часа до двух недель
    ttl_hours: int = Field(default=168, gt=0, le=320)

class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    status: Literal["active", "expired", "revoked", "used"]
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None
    used_by: int | None


class InvitationCreatedResponse(InvitationResponse):
    code: str  # plaintext показывается ОДИН раз


class AcceptInvitationRequest(BaseModel):
    code: str