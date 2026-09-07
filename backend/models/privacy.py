from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel


class DataExport(BaseModel):
    schema_version: str = '1.0'
    exported_at: datetime
    user_id: str
    data: dict[str, list[dict[str, Any]]]
    exclusions: list[str]


class DataSummary(BaseModel):
    is_guest: bool
    counts: dict[str, int]
    retention: str


class DeletionResult(BaseModel):
    deleted: bool = True
    scope: Literal['account', 'guest', 'session']
    counts: dict[str, int]
    message: str