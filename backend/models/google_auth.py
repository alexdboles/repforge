"""Managed identity exchange, not a second application session mechanism."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StrictBool
from models.schemas import SessionResponse


class GoogleStartResponse(BaseModel):
    state: str
    verifier: str = Field(repr=False)
    expires_at: datetime


class GoogleFlowProof(BaseModel):
    model_config = ConfigDict(extra='forbid')
    state: str = Field(min_length=32, max_length=128)
    verifier: str = Field(min_length=32, max_length=128, repr=False)


class GoogleExchangeRequest(GoogleFlowProof):
    session_id: str = Field(min_length=8, max_length=2048, repr=False)


class GoogleLinkRequest(GoogleFlowProof):
    password: str = Field(min_length=1, max_length=200, repr=False)


class GoogleExchangeResponse(BaseModel):
    status: Literal['authenticated', 'link_required']
    session: SessionResponse | None = None
    email: str | None = None
    password_available: bool | None = None


class GoogleRecoveryResponse(BaseModel):
    reference: str
    status: Literal['pending', 'approved']
    expires_at: datetime


class ManagedGoogleIdentity(BaseModel):
    """Only trusted server-to-server data enters this model. Provider token discarded."""
    model_config = ConfigDict(extra='ignore')
    id: str = Field(min_length=1, max_length=256)
    email: EmailStr
    name: str = Field(default='Sales professional', max_length=256)
    email_verified: StrictBool | None = None