# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db import db

if TYPE_CHECKING:
    from models.alert import Alert
    from models.location import Location
    from models.user import User


class AlertRule(db.Model):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    name: Mapped[str] = mapped_column(db.String(255))
    condition_json: Mapped[str] = mapped_column(db.Text)  # {"field": ..., "operator": ..., "threshold": ...}
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped[User] = relationship("User")
    location: Mapped[Location] = relationship("Location", back_populates="alert_rules")
    alerts: Mapped[list[Alert]] = relationship(
        "Alert", back_populates="rule", cascade="all, delete-orphan",
    )

    def __init__(
        self,
        user_id: int = 0,
        location_id: int = 0,
        name: str = "",
        condition_json: str = "{}",
        enabled: bool = True,
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            user_id=user_id, location_id=location_id, name=name,
            condition_json=condition_json, enabled=enabled, **kwargs,
        )
        super().__init__(**kw)
