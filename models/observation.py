from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db import db

if TYPE_CHECKING:
    from models.location import Location
    from models.sensor import Sensor


class Observation(db.Model):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    sensor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sensors.id"), index=True, default=None,
    )
    source: Mapped[str] = mapped_column(db.String(32))  # ecowitt, openmeteo, metno, rainviewer
    timestamp: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), index=True,
    )
    data_json: Mapped[str] = mapped_column(db.Text)  # flexible JSON blob
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    location: Mapped[Location] = relationship("Location", back_populates="observations")
    sensor: Mapped[Optional[Sensor]] = relationship("Sensor", back_populates="observations")

    def __init__(
        self,
        location_id: int = 0,
        source: str = "",
        timestamp: Optional[datetime] = None,
        data_json: str = "{}",
        sensor_id: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            location_id=location_id, source=source,
            timestamp=timestamp or datetime.now(timezone.utc),
            data_json=data_json, sensor_id=sensor_id, **kwargs,
        )
        super().__init__(**kw)
