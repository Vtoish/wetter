from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db import db

if TYPE_CHECKING:
    from models.alert_rule import AlertRule


class Alert(db.Model):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id"), index=True)
    triggered_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True))
    message: Mapped[str] = mapped_column(db.Text)
    acknowledged: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    rule: Mapped[AlertRule] = relationship("AlertRule", back_populates="alerts")

    def __init__(
        self,
        rule_id: int = 0,
        triggered_at: Optional[datetime] = None,
        message: str = "",
        acknowledged: bool = False,
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            rule_id=rule_id,
            triggered_at=triggered_at or datetime.now(timezone.utc),
            message=message, acknowledged=acknowledged, **kwargs,
        )
        super().__init__(**kw)
