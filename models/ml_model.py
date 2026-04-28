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
    from models.prediction import Prediction


class MLModel(db.Model):
    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    version: Mapped[str] = mapped_column(db.String(64))
    trained_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True))
    metrics_json: Mapped[Optional[str]] = mapped_column(db.Text, default=None)
    artifact_path: Mapped[Optional[str]] = mapped_column(db.String(512), default=None)
    active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    location: Mapped[Location] = relationship("Location")
    predictions: Mapped[list[Prediction]] = relationship(
        "Prediction", back_populates="model_version", cascade="all, delete-orphan",
    )

    def __init__(
        self,
        location_id: int = 0,
        version: str = "",
        trained_at: Optional[datetime] = None,
        metrics_json: Optional[str] = None,
        artifact_path: Optional[str] = None,
        active: bool = False,
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            location_id=location_id, version=version,
            trained_at=trained_at or datetime.now(timezone.utc),
            metrics_json=metrics_json, artifact_path=artifact_path,
            active=active, **kwargs,
        )
        super().__init__(**kw)
