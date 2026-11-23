from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class InvitationCreate(BaseModel):
    ttl_hours: int = 168  #это в часах, по умолчанию 7 дней


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