from datetime import datetime
from enum import Enum
from typing import List, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


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

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Return a dict where datetime fields are ISO‐formatted,
        so TestClient.json(...) can serialize them.
        """
        data = super().model_dump(*args, **kwargs)
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        if isinstance(data.get("updated_at"), datetime):
            data["updated_at"] = data["updated_at"].isoformat()
        return data

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "priority": "high",
                "created_at": "2025-06-17T12:00:00Z",
                "updated_at": "2025-06-17T12:05:00Z",
                "status": "open",
                "customer_tier": "gold"
            }
        }
    )


class StatusHistorySchema(BaseModel):
    status: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertSchema(BaseModel):
    sla_type: str = Field(..., description="Type of SLA: response or resolution")
    state: SLAState
    created_at: datetime
    details: dict

    model_config = ConfigDict(from_attributes=True)


class TicketBase(BaseModel):
    id: str
    priority: str
    customer_tier: str
    created_at: datetime
    updated_at: datetime
    escalation_level: int

    model_config = ConfigDict(from_attributes=True)


class TicketCreate(TicketBase):
    pass


class TicketSchema(TicketBase):
    status_history: List[StatusHistorySchema] = []
    alerts: List[AlertSchema] = []
