from datetime import datetime, timedelta, timezone

import pyotp
from flask import Flask
from flask.testing import FlaskClient

from models.user import User
from services.auth import validate_password
from services.db import db


# --- Password validation ---


def test_validate_password_good() -> None:
    assert validate_password("SecurePass123!") == []


def test_validate_password_too_short() -> None:
    errors: list[str] = validate_password("Short1!")
    assert any("12 characters" in e for e in errors)


def test_validate_password_no_uppercase() -> None:
    errors: list[str] = validate_password("securepass123!")
    assert any("uppercase" in e for e in errors)


def test_validate_password_no_lowercase() -> None:
    errors: list[str] = validate_password("SECUREPASS123!")
    assert any("lowercase" in e for e in errors)


def test_validate_password_no_digit() -> None:
    errors: list[str] = validate_password("SecurePassXyz!")
    assert any("digit" in e for e in errors)


def test_validate_password_no_special() -> None:
    errors: list[str] = validate_password("SecurePass1234")
    assert any("special" in e for e in errors)


# --- Signup ---


def test_signup_success(client: FlaskClient, app: Flask) -> None:
    resp = client.post("/auth/signup", data={
        "email": "new@example.com",
        "password": "SecurePass123!",
        "confirm": "SecurePass123!",
    })
    assert resp.status_code == 302
    with app.app_context():
        assert User.query.filter_by(email="new@example.com").first() is not None


def test_signup_duplicate_email(client: FlaskClient, user: User) -> None:
    resp = client.post("/auth/signup", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "confirm": "SecurePass123!",
    })
    assert resp.status_code == 409


def test_signup_weak_password(client: FlaskClient, app: Flask) -> None:
    resp = client.post("/auth/signup", data={
        "email": "weak@example.com",
        "password": "weak",
        "confirm": "weak",
    })
    assert resp.status_code == 400


def test_signup_password_mismatch(client: FlaskClient, app: Flask) -> None:
    resp = client.post("/auth/signup", data={
        "email": "new@example.com",
        "password": "SecurePass123!",
        "confirm": "DifferentPass123!",
    })
    assert resp.status_code == 400


# --- Login ---


def test_login_success(client: FlaskClient, user: User) -> None:
    resp = client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert "/" in resp.headers["Location"]


def test_login_wrong_password(client: FlaskClient, user: User) -> None:
    resp = client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "WrongPass123!",
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client: FlaskClient, app: Flask) -> None:
    resp = client.post("/auth/login", data={
        "email": "nobody@example.com",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 401


def test_account_lockout(client: FlaskClient, user: User, app: Flask) -> None:
    for _ in range(5):
        client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "WrongPass123!",
        })

    # Next attempt should report locked
    resp = client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 429


def test_failed_attempts_reset_on_success(client: FlaskClient, user: User, app: Flask) -> None:
    # Fail twice
    for _ in range(2):
        client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "WrongPass123!",
        })

    # Succeed
    client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
    })

    with app.app_context():
        u = db.session.get(User, user.id)
        assert u is not None
        assert u.failed_attempts == 0


# --- MFA ---


def test_mfa_setup_and_login(client: FlaskClient, user: User, app: Flask) -> None:
    # Login first
    client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
    })

    # Access MFA setup to generate secret
    resp = client.get("/auth/mfa/setup")
    assert resp.status_code == 200

    # Get the user's TOTP secret
    with app.app_context():
        u = db.session.get(User, user.id)
        assert u is not None
        assert u.totp_secret is not None
        token: str = pyotp.TOTP(u.totp_secret).now()

    # Confirm MFA setup
    resp = client.post("/auth/mfa/setup", data={"token": token})
    assert resp.status_code == 302

    with app.app_context():
        u = db.session.get(User, user.id)
        assert u is not None
        assert u.mfa_enabled is True

    # Logout
    client.post("/auth/logout")

    # Login again — should redirect to MFA
    resp = client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert "mfa" in resp.headers["Location"]

    # Submit valid TOTP
    with app.app_context():
        u = db.session.get(User, user.id)
        assert u is not None
        assert u.totp_secret is not None
        token = pyotp.TOTP(u.totp_secret).now()

    resp = client.post("/auth/mfa", data={"token": token}, follow_redirects=False)
    assert resp.status_code == 302


def test_mfa_invalid_code(client: FlaskClient, user: User, app: Flask) -> None:
    client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
    })
    client.get("/auth/mfa/setup")

    resp = client.post("/auth/mfa/setup", data={"token": "000000"})
    assert resp.status_code == 200  # stays on page with error


# --- Logout ---


def test_logout(authenticated_client: FlaskClient) -> None:
    resp = authenticated_client.post("/auth/logout", follow_redirects=False)
    assert resp.status_code == 302

    # Should not be able to access protected route
    resp = authenticated_client.get("/")
    assert resp.status_code == 302  # redirect to login
