from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db import db

if TYPE_CHECKING:
    from models.location import Location
    from models.ml_model import MLModel


class Prediction(db.Model):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), index=True,
    )
    rain_probability: Mapped[Optional[float]] = mapped_column(db.Float, default=None)
    temperature_corrected: Mapped[Optional[float]] = mapped_column(db.Float, default=None)
    cloud_cover: Mapped[Optional[float]] = mapped_column(db.Float, default=None)
    storm_likelihood: Mapped[Optional[float]] = mapped_column(db.Float, default=None)
    confidence: Mapped[Optional[float]] = mapped_column(db.Float, default=None)
    data_json: Mapped[Optional[str]] = mapped_column(db.Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    location: Mapped[Location] = relationship("Location", back_populates="predictions")
    model_version: Mapped[MLModel] = relationship("MLModel", back_populates="predictions")

    def __init__(
        self,
        location_id: int = 0,
        model_version_id: int = 0,
        timestamp: Optional[datetime] = None,
        rain_probability: Optional[float] = None,
        temperature_corrected: Optional[float] = None,
        cloud_cover: Optional[float] = None,
        storm_likelihood: Optional[float] = None,
        confidence: Optional[float] = None,
        data_json: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            location_id=location_id, model_version_id=model_version_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            rain_probability=rain_probability,
            temperature_corrected=temperature_corrected,
            cloud_cover=cloud_cover, storm_likelihood=storm_likelihood,
            confidence=confidence, data_json=data_json, **kwargs,
        )
        super().__init__(**kw)
