from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class SLAState(str, Enum):
    OK = "ok"
    ALERT = "alert"
    BREACH = "breach"


class TicketEvent(BaseModel):
    id: str
    priority: str
    created_at: datetime
    updated_at: datetime
    status: str
    customer_tier: str

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "priority": "high",
                "created_at": "2025-06-17T12:00:00Z",
                "updated_at": "2025-06-17T12:05:00Z",
                "status": "open",
                "customer_tier": "gold"
            }
        }


class TicketBase(BaseModel):
    id: str
    priority: str
    customer_tier: str
    created_at: datetime
    updated_at: datetime
    escalation_level: int

    class Config:
        orm_mode = True


class TicketCreate(TicketBase):
    pass


class StatusHistorySchema(BaseModel):
    status: str
    timestamp: datetime

    class Config:
        orm_mode = True


class AlertSchema(BaseModel):
    sla_type: str = Field(..., description="Type of SLA: response or resolution")
    state: SLAState
    created_at: datetime
    details: dict

    class Config:
        orm_mode = True


class TicketSchema(TicketBase):
    status_history: List[StatusHistorySchema] = []
    alerts: List[AlertSchema] = []
