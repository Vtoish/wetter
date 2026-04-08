import pyotp
from flask import Flask
from flask.testing import FlaskClient

from models.user import User
from services.auth import is_safe_redirect, validate_password
from services.db import db


# --- Open redirect ---


def test_safe_redirect_relative_path() -> None:
    assert is_safe_redirect("/dashboard") is True


def test_safe_redirect_rejects_absolute_url() -> None:
    assert is_safe_redirect("http://evil.com") is False


def test_safe_redirect_rejects_protocol_relative() -> None:
    assert is_safe_redirect("//evil.com") is False


def test_safe_redirect_rejects_backslash() -> None:
    assert is_safe_redirect("\\evil.com") is False


def test_safe_redirect_rejects_empty() -> None:
    assert is_safe_redirect("") is False
    assert is_safe_redirect(None) is False


def test_login_ignores_external_next(client: FlaskClient, user: User) -> None:
    resp = client.post(
        "/auth/login?next=http://evil.com",
        data={"email": "test@example.com", "password": "SecurePass123!"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "evil.com" not in resp.headers["Location"]


def test_login_follows_safe_next(client: FlaskClient, user: User) -> None:
    resp = client.post(
        "/auth/login?next=/api/weather",
        data={"email": "test@example.com", "password": "SecurePass123!"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/api/weather" in resp.headers["Location"]


# --- MFA brute force ---


def test_mfa_lockout_after_max_attempts(client: FlaskClient, user: User, app: Flask) -> None:
    # Login
    client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
    })

    # Enable MFA
    client.get("/auth/mfa/setup")
    with app.app_context():
        u = db.session.get(User, user.id)
        assert u is not None
        assert u.totp_secret is not None
        token: str = pyotp.TOTP(u.totp_secret).now()
    client.post("/auth/mfa/setup", data={"token": token})

    # Logout and login again to trigger MFA flow
    client.post("/auth/logout")
    client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
    })

    # Submit 5 wrong TOTP codes
    for _ in range(5):
        client.post("/auth/mfa", data={"token": "000000"})

    # Account should now be locked
    with app.app_context():
        u = db.session.get(User, user.id)
        assert u is not None
        assert u.is_locked()
        assert u.failed_attempts == 5


# --- Admin self-deletion ---


def test_admin_cannot_delete_self(admin_client: FlaskClient, admin_user: User) -> None:
    resp = admin_client.post(f"/admin/users/{admin_user.id}/delete")
    assert resp.status_code == 302

    # Admin should still exist
    resp = admin_client.get("/admin/users")
    assert resp.status_code == 200
    assert b"admin@example.com" in resp.data


# --- Security headers ---


def test_hsts_header(authenticated_client: FlaskClient) -> None:
    resp = authenticated_client.get("/")
    assert "Strict-Transport-Security" in resp.headers
    assert "max-age=" in resp.headers["Strict-Transport-Security"]


def test_csp_header(authenticated_client: FlaskClient) -> None:
    resp = authenticated_client.get("/")
    csp: str = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_existing_security_headers(authenticated_client: FlaskClient) -> None:
    resp = authenticated_client.get("/")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
