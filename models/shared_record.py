# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db import db

if TYPE_CHECKING:
    from models.peer import Peer


class SharedRecord(db.Model):
    __tablename__ = "shared_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    peer_id: Mapped[int] = mapped_column(ForeignKey("peers.id"), index=True)
    origin_instance: Mapped[str] = mapped_column(db.String(255))
    origin_id: Mapped[str] = mapped_column(db.String(128))
    record_type: Mapped[str] = mapped_column(db.String(32))  # observation, prediction, aggregate
    data_json: Mapped[str] = mapped_column(db.Text)
    recorded_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True))
    imported_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    peer: Mapped[Peer] = relationship("Peer", back_populates="shared_records")

    def __init__(
        self,
        peer_id: int = 0,
        origin_instance: str = "",
        origin_id: str = "",
        record_type: str = "",
        data_json: str = "{}",
        recorded_at: Optional[datetime] = None,
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            peer_id=peer_id, origin_instance=origin_instance,
            origin_id=origin_id, record_type=record_type,
            data_json=data_json,
            recorded_at=recorded_at or datetime.now(timezone.utc),
            **kwargs,
        )
        super().__init__(**kw)
