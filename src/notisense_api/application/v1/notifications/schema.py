from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, constr, Field


class NotificationBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CreateNotificationSchema(NotificationBaseSchema):
    subject: str = Field(..., min_length=1, max_length=160)
    recipients: List[EmailStr] = Field(..., min_items=1, description="List of email recipients")
    message: str = Field(..., min_length=1, description="Notification message body")

    # Optional advanced fields
    priority: int = Field(0, ge=0, le=10, description="Priority (0 = normal, higher = urgent)")
    scheduled_at: Optional[datetime] = Field(None, description="Optional future send time")
    payload: Optional[Dict[str, Any]] = Field(None, description="Template/context data for rendering")


class CreateBulkNotificationSchema(NotificationBaseSchema):
    notifications: List[CreateNotificationSchema] = Field(..., min_items=1, description="List of notifications to create")
