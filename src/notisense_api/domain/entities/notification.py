from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import (
    Integer,
    SmallInteger,
    String,
    Text,
    Enum,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB  # <- correct import for JSONB
from sqlalchemy.orm import Mapped, mapped_column, deferred

from notisense_api.domain.entities.root_model import RootModel
from notisense_api.domain.enums.notification_status import NotificationStatus


class Notification(RootModel):
    """
    High-volume notification row optimized for queue scans and status updates.

    RootModel is assumed to provide:
    - id (UUID, server-generated), created_at, last_updated_at
    - is_deleted (soft delete flag) + partial BRIN/time indexes via RootModel.__table_args__
    """

    __tablename__ = "notifications"
    __mapper_args__ = {"eager_defaults": True}  # efficient INSERT ... RETURNING

    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = deferred(mapped_column(Text, nullable=False))
    recipients: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=sa.text("'[]'::jsonb"))

    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status", inherit_schema=True),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=sa.text("0")
    )  # 0=normal, higher=sooner
    scheduled_at: Mapped[sa.DateTime | None] = mapped_column(sa.DateTime(timezone=True))
    sent_at: Mapped[sa.DateTime | None] = mapped_column(sa.DateTime(timezone=True))

    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=sa.text("0")
    )
    last_attempt_at: Mapped[sa.DateTime | None] = mapped_column(sa.DateTime(timezone=True))

    # === Provider I/O & diagnostics ===
    provider_message_id: Mapped[str | None] = mapped_column(String(160))
    last_error: Mapped[str | None] = deferred(mapped_column(Text))

    # Optional templating/metadata for idempotency & auditing
    template_code: Mapped[str | None] = mapped_column(String(120))
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )

    __table_args__ = (
        # --- Data quality guards (cheap, prevent bad writes) ---
        CheckConstraint("priority BETWEEN -10 AND 100", name="ck_notifications_priority_range"),
        CheckConstraint("attempt_count >= 0", name="ck_notifications_attempt_count_nonneg"),

        # --- Hot-path indexes ---
        # Quickly pick due jobs: filter by status + schedule time (partial to keep small & hot)
        sa.Index(
            "ix_notifications_status_scheduled",
            "status", "scheduled_at",
            postgresql_where=sa.text("is_deleted = false"),
        ),
        # Fast lookups by status alone for dashboards/workers
        sa.Index(
            "ix_notifications_status_active",
            "status",
            postgresql_where=sa.text("is_deleted = false"),
        ),
        # Provider webhook/retry correlation
        sa.Index(
            "ix_notifications_provider_msg",
            "provider_message_id",
            postgresql_where=sa.text("provider_message_id IS NOT NULL AND is_deleted = false"),
        ),
        # JSONB containment / membership queries on recipients (optional but great at scale)
        sa.Index(
            "ix_notifications_recipients_gin",
            sa.text("recipients"),
            postgresql_using="gin",
        ),
        # If you frequently search by subject with LIKE/ILIKE, consider pg_trgm:
        # sa.Index(
        #     "ix_notifications_subject_trgm",
        #     sa.text("subject gin_trgm_ops"),
        #     postgresql_using="gin",
        #     postgresql_where=sa.text("is_deleted = false"),
        # ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notification id={self.id} status={self.status}>"