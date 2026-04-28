# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

import base64
import io
import re
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, cast
from urllib.parse import ParseResult, urlparse

import qrcode
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.wrappers import Response

import config
from models.user import User
from services.db import db
from services.limiter import limiter

auth_bp: Blueprint = Blueprint("auth", __name__, url_prefix="/auth")


def validate_password(password: str) -> list[str]:
    """Return list of error messages. Empty list means valid."""
    errors: list[str] = []
    if len(password) < config.PASSWORD_MIN_LENGTH:
        errors.append(f"Must be at least {config.PASSWORD_MIN_LENGTH} characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Must contain at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Must contain at least one special character.")
    return errors


def is_safe_redirect(target: str | None) -> bool:
    """Reject redirects to external hosts or scheme-relative URLs."""
    if not target:
        return False
    if "\\" in target:
        return False
    parsed: ParseResult = urlparse(target)
    return not parsed.netloc and not parsed.scheme


def role_required(*roles: str) -> Callable[..., Any]:
    """Decorator that requires login and one of the specified roles."""
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        @login_required
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if not current_user:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def signup() -> str | Response | tuple[str, int]:
    user_auth: User = cast(User, current_user)
    if user_auth.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email: str = request.form.get("email", "").strip().lower()
        password: str = request.form.get("password", "")
        confirm: str = request.form.get("confirm", "")

        if not email:
            flash("Email is required.", "error")
            return render_template("auth/signup.html"), 400

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth/signup.html"), 400

        pw_errors: list[str] = validate_password(password)
        if pw_errors:
            for err in pw_errors:
                flash(err, "error")
            return render_template("auth/signup.html"), 400

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return render_template("auth/signup.html"), 409

        user: User = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login() -> str | Response | tuple[str, int]:
    user = cast(User, current_user)
    if user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email: str = request.form.get("email", "").strip().lower()
        password: str = request.form.get("password", "")

        user: User | None = cast("User | None", User.query.filter_by(email=email).first())

        if user and user.is_locked():
            flash("Account is temporarily locked. Try again later.", "error")
            return render_template("auth/login.html"), 429

        if user is None or not user.check_password(password):
            if user:
                user.failed_attempts += 1
                if user.failed_attempts >= config.MAX_LOGIN_ATTEMPTS:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(
                        seconds=config.LOCKOUT_DURATION
                    )
                    flash("Account locked due to too many failed attempts.", "error")
                else:
                    flash("Invalid email or password.", "error")
                db.session.commit()
            else:
                flash("Invalid email or password.", "error")
            return render_template("auth/login.html"), 401

        # Password correct — check MFA
        if user.mfa_enabled:
            session["mfa_pending_user_id"] = user.id
            return redirect(url_for("auth.mfa_verify"))

        # No MFA — complete login
        user.failed_attempts = 0
        user.locked_until = None
        db.session.commit()
        login_user(user)
        session.permanent = True
        next_page: str | None = request.args.get("next")
        if not is_safe_redirect(next_page):
            next_page = None
        return redirect(next_page or url_for("index"))

    return render_template("auth/login.html")


@auth_bp.route("/mfa", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def mfa_verify() -> str | Response | tuple[str, int]:
    user_id: int | None = session.get("mfa_pending_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    user: User | None = db.session.get(User, user_id)
    if not user:
        session.pop("mfa_pending_user_id", None)
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        token: str = request.form.get("token", "").strip()

        if user.verify_totp(token):
            session.pop("mfa_pending_user_id", None)
            user.failed_attempts = 0
            user.mfa_attempts = 0
            user.locked_until = None
            db.session.commit()
            login_user(user)
            session.permanent = True
            return redirect(url_for("index"))

        user.mfa_attempts += 1
        if user.mfa_attempts >= config.MAX_LOGIN_ATTEMPTS:
            session.pop("mfa_pending_user_id", None)
            user.failed_attempts = config.MAX_LOGIN_ATTEMPTS
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                seconds=config.LOCKOUT_DURATION
            )
            db.session.commit()
            flash("Account locked due to too many failed attempts.", "error")
            return redirect(url_for("auth.login"))

        flash("Invalid code. Please try again.", "error")
        db.session.commit()
        return render_template("auth/mfa.html"), 401

    return render_template("auth/mfa.html")


@auth_bp.route("/mfa/setup", methods=["GET", "POST"])
@login_required
def mfa_setup() -> str | Response:
    user: User = cast(User, current_user)
    if not user.totp_secret:
        user.generate_totp_secret()
        db.session.commit()

    if request.method == "POST":
        token: str = request.form.get("token", "").strip()

        if user.verify_totp(token):
            user.mfa_enabled = True
            db.session.commit()
            flash("MFA enabled successfully.", "success")
            return redirect(url_for("index"))

        flash("Invalid code. Please try again.", "error")

    # Generate QR code as base64 data URI
    uri: str = user.get_totp_uri() or ""
    img: Any = qrcode.make(uri)
    buf: io.BytesIO = io.BytesIO()
    img.save(buf, format="PNG")  # type: ignore[call-arg]
    buf.seek(0)
    qr_data: str = base64.b64encode(buf.getvalue()).decode()

    return render_template(
        "auth/mfa_setup.html",
        qr_data=qr_data,
        secret=user.totp_secret,
    )


@auth_bp.route("/mfa/disable", methods=["POST"])
@login_required
def mfa_disable() -> Response:
    token: str = request.form.get("token", "").strip()

    user = cast(User, current_user)
    if not user.mfa_enabled:
        flash("MFA is not enabled.", "error")
        return redirect(url_for("auth.mfa_setup"))

    if user.verify_totp(token):
        user.mfa_enabled = False
        user.totp_secret = None
        db.session.commit()
        flash("MFA disabled.", "success")
        return redirect(url_for("index"))

    flash("Invalid code.", "error")
    return redirect(url_for("auth.mfa_setup"))


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout() -> Response:
    logout_user()
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login"))
