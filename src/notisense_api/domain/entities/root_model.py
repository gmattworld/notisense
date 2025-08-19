from __future__ import annotations
import datetime as dt

from sqlalchemy import Boolean, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
import sqlalchemy as sa

from notisense_api.infrastructure.persistence.database import Base
    
class RootModel(Base):
    __abstract__ = True
    __mapper_args__ = {"eager_defaults": True}

    # --- Identity ---
    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")  # or 'uuid_generate_v4()'
    )

    # --- Audit: created ---
    created_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now()
    )
    # created_by_id: Mapped[str | None] = mapped_column(
    #     PGUUID(as_uuid=True),
    #     ForeignKey("users.id"),
    #     nullable=True
    # )

    # @declared_attr
    # def created_by(cls):
    #     return relationship(
    #         "User",
    #         foreign_keys=lambda: [cls.created_by_id],
    #         viewonly=True,
    #         lazy="raise"
    #     )

    # --- Audit: updated ---
    last_updated_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        server_onupdate=sa.func.now()
    )
    # last_updated_by_id: Mapped[str | None] = mapped_column(
    #     PGUUID(as_uuid=True),
    #     ForeignKey("users.id"),
    #     nullable=True
    # )

    # @declared_attr
    # def last_updated_by(cls):
    #     return relationship(
    #         "User",
    #         foreign_keys=lambda: [cls.last_updated_by_id],
    #         viewonly=True,
    #         lazy="raise"
    #     )

    # --- Soft delete ---
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false")
    )
    deleted_at: Mapped[dt.datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    # deleted_by_id: Mapped[str | None] = mapped_column(
    #     PGUUID(as_uuid=True),
    #     ForeignKey("users.id"),
    #     nullable=True
    # )

    # @declared_attr
    # def deleted_by(cls):
    #     return relationship(
    #         "User",
    #         foreign_keys=lambda: [cls.deleted_by_id],
    #         viewonly=True,
    #         lazy="raise"
    #     )

    # --- Useful indexes for common filters ---
    __table_args__ = (
        # Common fetch path: active, not-deleted rows filtered by status
        sa.Index(
            "ix_%(table_name)s_status_not_deleted",
            "status",
            postgresql_where=sa.text("is_deleted = false"),
        ),
        # Housekeeping for deleted rows (partial index)
        sa.Index(
            "ix_%(table_name)s_deleted_only",
            "deleted_at",
            postgresql_where=sa.text("is_deleted = true"),
        ),
        # BRIN indexes for time-correlated scans on large tables
        sa.Index(
            "ix_%(table_name)s_created_at_brin",
            "created_at",
            postgresql_using="brin",
            postgresql_with={"pages_per_range": 16},
        ),
        sa.Index(
            "ix_%(table_name)s_last_updated_at_brin",
            "last_updated_at",
            postgresql_using="brin",
            postgresql_with={"pages_per_range": 16},
        ),
        # Composite index to speed status queries sorted by created_at; include id for covering
        sa.Index(
            "ix_%(table_name)s_status_created_at",
            "status",
            "created_at",
            postgresql_where=sa.text("is_deleted = false"),
            postgresql_include=["id"],
        ),
    )
