from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db import db

if TYPE_CHECKING:
    from models.alert_rule import AlertRule
    from models.observation import Observation
    from models.prediction import Prediction
    from models.sensor import Sensor
    from models.user import User


class Location(db.Model):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(db.String(255))
    latitude: Mapped[float] = mapped_column(db.Float)
    longitude: Mapped[float] = mapped_column(db.Float)
    timezone: Mapped[str] = mapped_column(db.String(64), default="UTC")
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="locations")
    sensors: Mapped[list[Sensor]] = relationship(
        "Sensor", back_populates="location", cascade="all, delete-orphan",
    )
    observations: Mapped[list[Observation]] = relationship(
        "Observation", back_populates="location", cascade="all, delete-orphan",
    )
    predictions: Mapped[list[Prediction]] = relationship(
        "Prediction", back_populates="location", cascade="all, delete-orphan",
    )
    alert_rules: Mapped[list[AlertRule]] = relationship(
        "AlertRule", back_populates="location", cascade="all, delete-orphan",
    )

    def __init__(
        self,
        user_id: int = 0,
        name: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
        timezone: str = "UTC",
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            user_id=user_id, name=name, latitude=latitude,
            longitude=longitude, timezone=timezone, **kwargs,
        )
        super().__init__(**kw)
