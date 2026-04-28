# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db import db

if TYPE_CHECKING:
    from models.location import Location
    from models.observation import Observation


class Sensor(db.Model):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    kind: Mapped[str] = mapped_column(db.String(32))  # ecowitt, addon
    name: Mapped[str] = mapped_column(db.String(255))
    hardware_id: Mapped[str] = mapped_column(db.String(128), unique=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(db.Text, default=None)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    location: Mapped[Location] = relationship("Location", back_populates="sensors")
    observations: Mapped[list[Observation]] = relationship(
        "Observation", back_populates="sensor", cascade="all, delete-orphan",
    )

    def __init__(
        self,
        location_id: int = 0,
        kind: str = "ecowitt",
        name: str = "",
        hardware_id: str = "",
        metadata_json: Optional[str] = None,
        active: bool = True,
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            location_id=location_id, kind=kind, name=name,
            hardware_id=hardware_id, metadata_json=metadata_json,
            active=active, **kwargs,
        )
        super().__init__(**kw)
