import asyncio
import logging
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from notisense_api.domain.entities.notification import Notification
from notisense_api.domain.enums.notification_status import NotificationStatus
from notisense_api.domain.utilities.config import settings
from notisense_api.infrastructure.persistence.database import async_session
from notisense_api.infrastructure.providers.default.email import send_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Worker settings
WORKER_SLEEP_INTERVAL = 10  # seconds
BATCH_SIZE = 50  # Number of notifications to fetch per batch


async def process_batch(db: AsyncSession, batch: list[Notification]):
    """Sends emails for a batch of notifications concurrently."""
    sem = asyncio.Semaphore(settings.NOTIFICATION_MAX_CONCURRENCY)

    async def _send_one(notification: Notification):
        async with sem:
            try:
                # In a real app, you'd use a template engine with notification.payload
                await asyncio.gather(
                    *[
                        send_email(email=r, subject=notification.subject, body=notification.message)
                        for r in notification.recipients
                    ]
                )
                return notification, True, None
            except Exception as exc:
                logging.error(f"Failed to send notification {notification.id}: {exc}")
                return notification, False, str(exc)

    results = await asyncio.gather(*[_send_one(n) for n in batch])

    # --- Update statuses in bulk --- #
    now = datetime.now(timezone.utc)
    for notification, ok, err_msg in results:
        notification.last_attempt_at = now
        notification.attempt_count += 1
        if ok:
            notification.status = NotificationStatus.SENT
            notification.sent_at = now
            notification.last_error = None
        else:
            # Simple failure case. A real app might have retries with backoff.
            notification.status = NotificationStatus.FAILED
            notification.last_error = err_msg

    await db.commit()
    logging.info(f"Processed batch of {len(batch)} notifications.")


async def main_loop():
    """The main worker loop to poll for and process notifications."""
    logging.info("Notification worker started.")
    while True:
        try:
            async with async_session() as db:
                # --- Fetch and Lock a Batch of Pending Notifications ---
                # This query finds due notifications, locks the rows to prevent other workers
                # from picking them up, and skips any rows that are already locked.
                subquery = (
                    sa.select(Notification.id)
                    .where(
                        Notification.status == NotificationStatus.PENDING,
                        Notification.scheduled_at <= datetime.now(timezone.utc),
                    )
                    .order_by(Notification.priority.desc(), Notification.created_at.asc())
                    .limit(BATCH_SIZE)
                    .with_for_update(skip_locked=True)
                    .subquery()
                )

                # Fetch the full notification objects for the locked rows
                stmt = sa.select(Notification).where(Notification.id.in_(sa.select(subquery)))
                result = await db.execute(stmt)
                batch_to_process = result.scalars().all()

                if not batch_to_process:
                    await asyncio.sleep(WORKER_SLEEP_INTERVAL)
                    continue

                # --- Mark as Processing ---
                # This immediately commits the status change so other workers know these are handled.
                for notif in batch_to_process:
                    notif.status = NotificationStatus.PROCESSING
                await db.commit()

                # --- Process the batch --- #
                await process_batch(db, batch_to_process)

        except Exception as e:
            logging.error(f"An error occurred in the main worker loop: {e}", exc_info=True)
            await asyncio.sleep(WORKER_SLEEP_INTERVAL * 2)  # Longer sleep on error


if __name__ == "__main__":
    asyncio.run(main_loop())
