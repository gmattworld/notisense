# src/application/v1/notifications/service.py
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Sequence

from fastapi import BackgroundTasks, Depends
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from notisense_api.application.v1.notifications.schema import (
    CreateNotificationSchema,
    CreateBulkNotificationSchema,
)
from notisense_api.domain.entities.notification import Notification
from notisense_api.domain.enums.notification_status import NotificationStatus
from notisense_api.domain.exceptions.base_exception import AppBadRequestException
from notisense_api.infrastructure.persistence.database import get_db, async_session
from notisense_api.infrastructure.providers.default.email import (
    send_email,
    send_email_to_many,
)

# If you still want a global throttle on the background task, keep this.
# The mailer itself also handles batching/concurrency internally.
MAX_CONCURRENCY = 10


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- PUBLIC API ----------
    async def queue_notification(
        self,
        data: CreateNotificationSchema,
        background_tasks: BackgroundTasks | None = None,
    ) -> Notification:
        """
        Persist a notification (PENDING) and schedule background delivery.
        """
        recipients = [str(r).strip() for r in (data.recipients or []) if str(r).strip()]
        if not recipients:
            raise AppBadRequestException("At least one recipient is required.")

        vals = {
            "subject": data.subject,
            "message": data.message,
            "recipients": recipients,  # JSONB list[str]
            "status": NotificationStatus.PENDING,
            "priority": int(getattr(data, "priority", 0) or 0),
            "scheduled_at": getattr(data, "scheduled_at", None),
            "payload": getattr(data, "payload", {}) or {},
            "attempt_count": 0,
        }

        try:
            res = await self.db.execute(
                insert(Notification).values(**vals).returning(Notification)
            )
            notification: Notification = res.scalar_one()
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise AppBadRequestException(f"Could not queue notification: {e}") from e

        # Schedule background processing WITHOUT blocking response
        if background_tasks is not None:
            background_tasks.add_task(process_notifications_async, [str(notification.id)])
        else:
            asyncio.create_task(process_notifications_async([str(notification.id)]))

        return notification

    async def queue_bulk_notifications(
        self,
        request: CreateBulkNotificationSchema,
        background_tasks: BackgroundTasks | None = None,
    ) -> list[str]:
        """
        Persist many notifications (PENDING) and schedule background delivery.
        """
        if not request.notifications:
            return []

        values = []
        for item in request.notifications:
            recips = [str(r).strip() for r in (item.recipients or []) if str(r).strip()]
            if not recips:
                raise AppBadRequestException("All notifications must have at least one recipient.")
            values.append(
                {
                    "subject": item.subject,
                    "message": item.message,
                    "recipients": recips,
                    "status": NotificationStatus.PENDING,
                    "priority": int(getattr(item, "priority", 0) or 0),
                    "scheduled_at": getattr(item, "scheduled_at", None),
                    "payload": getattr(item, "payload", {}) or {},
                    "attempt_count": 0,
                }
            )

        try:
            res = await self.db.execute(
                insert(Notification).values(values).returning(Notification.id)
            )
            ids: list[str] = [str(x) for x in res.scalars().all()]
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise AppBadRequestException(f"Failed to queue bulk notifications: {e}") from e

        if background_tasks is not None:
            background_tasks.add_task(process_notifications_async, ids)
        else:
            asyncio.create_task(process_notifications_async(ids))

        return ids


# ---------- BACKGROUND RUNNER (new DB session per run) ----------
async def process_notifications_async(notification_ids: Sequence[str]) -> None:
    """
    Background processor: sends emails and updates status in bulk.
    Uses its own AsyncSession; never reuses the request-scoped session.
    """
    if not notification_ids:
        return

    async with async_session() as db:
        # Fetch minimal fields required to send
        result = await db.execute(
            select(
                Notification.id,
                Notification.subject,
                Notification.message,
                Notification.recipients,
            ).where(Notification.id.in_(notification_ids))
        )
        items = result.all()
        if not items:
            return

        # Use a semaphore as an outer guard if you want to cap total concurrent jobs
        sem = asyncio.Semaphore(MAX_CONCURRENCY)

        async def _send_one(_id: str, _subject: str, _message: str, _recipients: list[str]):
            async with sem:
                try:
                    # Use the optimized bulk sender — it applies batching, concurrency and retries internally.
                    # If you want to send one-by-one instead, use send_email(...) in a gather.
                    await send_email_to_many(
                        recipients=_recipients,
                        subject=_subject,
                        body=_message,
                        background_tasks=None,  # we're already in a background worker context
                        # Optional: tune these if needed (these are defaults in the mailer)
                        batch_size=50,
                        concurrency=5,
                        max_attempts=3,
                    )
                    return _id, True
                except Exception:
                    return _id, False

        results = await asyncio.gather(
            *[_send_one(str(nid), subject, message, recipients) for (nid, subject, message, recipients) in items]
        )

        success_ids = [nid for nid, ok in results if ok]
        failure_ids = [nid for nid, ok in results if not ok]
        now = datetime.now(timezone.utc)

        # Bulk status updates (1 write for all successes, 1 for all failures)
        if success_ids:
            await db.execute(
                update(Notification)
                .where(Notification.id.in_(success_ids))
                .values(
                    status=NotificationStatus.SENT,
                    sent_at=now,
                    last_attempt_at=now,
                    attempt_count=Notification.attempt_count + 1,
                    last_error=None,
                )
            )

        if failure_ids:
            await db.execute(
                update(Notification)
                .where(Notification.id.in_(failure_ids))
                .values(
                    status=NotificationStatus.FAILED,
                    last_attempt_at=now,
                    attempt_count=Notification.attempt_count + 1,
                    last_error="One or more recipient sends failed",
                )
            )

        await db.commit()


def notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db)