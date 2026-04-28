# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

import pyotp
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from services.db import db

if TYPE_CHECKING:
    from models.location import Location


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(db.String(255))
    role: Mapped[str] = mapped_column(db.String(20), default="user")  # viewer, user, analyst, admin
    totp_secret: Mapped[Optional[str]] = mapped_column(db.String(32), default=None)
    mfa_enabled: Mapped[bool] = mapped_column(default=False)
    failed_attempts: Mapped[int] = mapped_column(default=0)
    mfa_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    locations: Mapped[list[Location]] = relationship(
        "Location", back_populates="user", cascade="all, delete-orphan",
    )

    def __init__(
        self,
        email: str = "",
        role: str = "user",
        password_hash: str = "",
        totp_secret: Optional[str] = None,
        mfa_enabled: bool = False,
        failed_attempts: int = 0,
        mfa_attempts: int = 0,
        locked_until: Optional[datetime] = None,
        **kwargs: Any,
    ) -> None:
        kw: dict[str, Any] = dict(
            email=email, role=role, password_hash=password_hash,
            totp_secret=totp_secret, mfa_enabled=mfa_enabled,
            failed_attempts=failed_attempts, mfa_attempts=mfa_attempts,
            locked_until=locked_until,
            **kwargs,
        )
        super().__init__(**kw)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        locked = self.locked_until
        if locked.tzinfo is None:
            locked = locked.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < locked

    def generate_totp_secret(self) -> None:
        self.totp_secret = pyotp.random_base32()

    def get_totp_uri(self) -> Optional[str]:
        if not self.totp_secret:
            return None
        return pyotp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email, issuer_name="Wetter"
        )

    def verify_totp(self, token: str) -> bool:
        if not self.totp_secret:
            return False
        return pyotp.TOTP(self.totp_secret).verify(token, valid_window=1)
