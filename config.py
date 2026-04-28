# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

DEBUG: bool = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")

APP_NAME: str = os.getenv("WETTER_APP_NAME", "Wetter")
APP_CONTACT: str = os.getenv("WETTER_APP_CONTACT", "wetter@example.com")
METNO_USER_AGENT: str = f"{APP_NAME}/1.0 {APP_CONTACT}"

REQUEST_TIMEOUT: int = int(os.getenv("WETTER_REQUEST_TIMEOUT", "10"))

# Database
SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URI", "sqlite:///wetter.db")

# Session security
SESSION_COOKIE_HTTPONLY: bool = True
SESSION_COOKIE_SAMESITE: str = "Lax"
SESSION_COOKIE_SECURE: bool = not DEBUG
PERMANENT_SESSION_LIFETIME: timedelta = timedelta(minutes=30)

# Password policy
PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "12"))

# Account lockout
MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION: int = int(os.getenv("LOCKOUT_DURATION", "900"))  # seconds

# Initial admin (first-run seeding)
ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")

# Data directories
DATA_DIR: str = os.getenv("DATA_DIR", "data")
ML_MODEL_DIR: str = os.getenv("ML_MODEL_DIR", os.path.join(DATA_DIR, "models"))

# Ecowitt / weather station
ECOWITT_API_KEY: str = os.getenv("ECOWITT_API_KEY", "")
ECOWITT_PASSKEY: str = os.getenv("ECOWITT_PASSKEY", "")

# Machine learning
ML_RETRAIN_INTERVAL_HOURS: int = int(os.getenv("ML_RETRAIN_INTERVAL_HOURS", "24"))

# Alerts
ALERT_CHECK_INTERVAL_MINUTES: int = int(os.getenv("ALERT_CHECK_INTERVAL_MINUTES", "5"))
ALERT_EMAIL_ENABLED: bool = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() in ("1", "true", "yes")

# Email (SMTP)
SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

# Federation
FEDERATION_ENABLED: bool = os.getenv("FEDERATION_ENABLED", "false").lower() in ("1", "true", "yes")
FEDERATION_API_KEY: str = os.getenv("FEDERATION_API_KEY", "")
FEDERATION_SYNC_INTERVAL_MINUTES: int = int(os.getenv("FEDERATION_SYNC_INTERVAL_MINUTES", "60"))

# Background scheduler
SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "false").lower() in ("1", "true", "yes")
