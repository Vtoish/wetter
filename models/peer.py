from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db import db

if TYPE_CHECKING:
    from models.shared_record import SharedRecord


class Peer(db.Model):
    __tablename__ = "peers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255))
    url: Mapped[str] = mapped_column(db.String(512))
    api_key_hash: Mapped[str] = mapped_column(db.String(255))
    shared_data_types_json: Mapped[Optional[str]] = mapped_column(db.Text, default=None)
    trusted: Mapped[bool] = mapped_column(default=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime(timezone=True), default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    shared_records: Mapped[list[SharedRecord]] = relationship(
        "SharedRecord", back_populates="peer", cascade="all, delete-orphan",
    )

    def __init__(
        self,
        name: str = "",
        url: str = "",
        api_key_hash: str = "",
        shared_data_types_json: Optional[str] = None,
        trusted: bool = False,
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            name=name, url=url, api_key_hash=api_key_hash,
            shared_data_types_json=shared_data_types_json,
            trusted=trusted, **kwargs,
        )
        super().__init__(**kw)
