# src/infrastructure/providers/default/email.py
from __future__ import annotations

import asyncio
import random
from typing import Iterable, Sequence

from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, MessageSchema, FastMail, MessageType

from notisense_api.domain.utilities.config import settings


# ---- Connection (single, reused) -------------------------------------------
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    # Optional, but handy:
    # SUPPRESS_SEND=settings.MAIL_SUPPRESS_SEND,  # e.g., for non-prod
)

# Reuse the client to avoid re-creating connections each call
_fm = FastMail(conf)


# ---- Internal helpers -------------------------------------------------------
async def _send_one(subject: str, body: str, recipients: Sequence[str]) -> None:
    """
    Send a single message to a list of recipients.
    FastMail will open/close the SMTP connection per call; reusing _fm avoids config churn.
    """
    msg = MessageSchema(
        subject=subject,
        recipients=list(recipients),
        body=body,
        subtype=MessageType.html,  # change to .plain if body is text/plain
    )
    await _fm.send_message(msg)


async def _retry(
    coro_factory,
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
) -> None:
    """
    Simple exponential backoff w/ jitter for transient SMTP hiccups.
    """
    last_exc = None
    for i in range(attempts):
        try:
            return await coro_factory()
        except Exception as exc:  # noqa: BLE001 (we want to retry for any transport error)
            last_exc = exc
            if i == attempts - 1:
                break
            sleep_for = min(max_delay, base_delay * (2 ** i)) * (0.5 + random.random())
            await asyncio.sleep(sleep_for)
    raise last_exc  # bubble up after final attempt


# ---- Public API -------------------------------------------------------------
async def send_email(
    *,
    email: str,
    subject: str,
    body: str,
    background_tasks: BackgroundTasks | None = None,
    max_attempts: int = 3,
) -> None:
    """
    Send a single email to one recipient.
    - If `background_tasks` is provided, schedule and return immediately.
    - Otherwise, await the send (useful in workers).
    - Includes small retry for transient failures.
    """
    async def _do():
        await _send_one(subject, body, [email])

    if background_tasks is not None:
        background_tasks.add_task(_retry, _do, attempts=max_attempts)
    else:
        await _retry(_do, attempts=max_attempts)


async def send_email_to_many(
    *,
    recipients: Iterable[str],
    subject: str,
    body: str,
    background_tasks: BackgroundTasks | None = None,
    batch_size: int = 50,
    concurrency: int = 5,
    max_attempts: int = 3,
) -> None:
    """
    High-volume bulk sender for the *same* message to many recipients.

    - Splits recipients into batches (to keep message size and provider rate sane).
    - Sends batches concurrently (bounded).
    - Works with or without BackgroundTasks.
    """
    recips = [str(r).strip() for r in recipients if str(r).strip()]
    if not recips:
        return

    # chunk into batches
    batches: list[list[str]] = [recips[i : i + batch_size] for i in range(0, len(recips), batch_size)]
    sem = asyncio.Semaphore(concurrency)

    async def _send_batch(batch: list[str]):
        async with sem:
            async def _do():
                await _send_one(subject, body, batch)
            await _retry(_do, attempts=max_attempts)

    async def _run_all():
        await asyncio.gather(*[_send_batch(b) for b in batches])

    if background_tasks is not None:
        # schedule the whole multi-batch job
        background_tasks.add_task(_run_all)
    else:
        await _run_all()