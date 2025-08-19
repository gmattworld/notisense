from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status

from notisense_api.application.v1.notifications.schema import CreateNotificationSchema, CreateBulkNotificationSchema
from notisense_api.application.v1.notifications.service import (
    NotificationService,
    notification_service,
)
from notisense_api.domain.schemas.common_schema import BaseResponseSchema

router = APIRouter(
    prefix="/setup",
    tags=["Setup"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not Found"},
        500: {"description": "Internal Server Error"},
    },
)


@router.post(
    "/send-email",
    response_model=BaseResponseSchema[str],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue an email notification for sending",
    description="Accepts an email notification request and queues it for processing.",
    responses={
        202: {
            "description": "Accepted for processing",
            "content": {
                "application/json": {
                    "example": {
                        "data": "Notification '...' has been queued.",
                        "success": True,
                        "message": "Notification accepted",
                    }
                }
            },
        }
    },
)
async def queue_email_notification(
    request: CreateNotificationSchema,
    background_tasks: BackgroundTasks,
    _service: NotificationService = Depends(notification_service),
) -> BaseResponseSchema[str]:
    """
    Validates and persists a notification request to the queue.
    A separate worker process will handle the actual sending.
    """
    notification = await _service.queue_notification(request, background_tasks)
    return BaseResponseSchema(
        data=f"Notification '{notification.id}' has been queued.",
        success=True,
        message="Notification accepted",
    )


@router.post(
    "/send-emails-bulk",
    response_model=BaseResponseSchema[list[str]],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue multiple email notifications for sending",
    description="Accepts a batch of email notification requests and queues them for processing.",
    responses={
        202: {
            "description": "Accepted for processing",
            "content": {
                "application/json": {
                    "example": {
                        "data": ["id1", "id2"],
                        "success": True,
                        "message": "Notifications accepted",
                    }
                }
            },
        }
    },
)
async def queue_bulk_email_notifications(
    request: CreateBulkNotificationSchema,
    background_tasks: BackgroundTasks,
    _service: NotificationService = Depends(notification_service),
) -> BaseResponseSchema[list[str]]:
    """
    Validates and persists multiple notification requests to the queue in a single transaction.
    A separate worker process will handle the actual sending.
    """
    notification_ids = await _service.queue_bulk_notifications(request, background_tasks)
    return BaseResponseSchema(
        data=notification_ids,
        success=True,
        message="Notifications accepted",
    )
