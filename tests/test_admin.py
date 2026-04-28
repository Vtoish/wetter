# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from datetime import datetime, timedelta, timezone

from flask import Flask
from flask.testing import FlaskClient

from models.user import User
from services.db import db


def test_admin_can_list_users(admin_client: FlaskClient) -> None:
    resp = admin_client.get("/admin/users")
    assert resp.status_code == 200
    assert b"admin@example.com" in resp.data


def test_non_admin_gets_403(authenticated_client: FlaskClient) -> None:
    resp = authenticated_client.get("/admin/users")
    assert resp.status_code == 403


def test_unauthenticated_gets_redirect(client: FlaskClient, app: Flask) -> None:
    resp = client.get("/admin/users")
    assert resp.status_code == 302


def test_change_role(admin_client: FlaskClient, user: User, app: Flask) -> None:
    resp = admin_client.post(f"/admin/users/{user.id}/role", data={"role": "admin"})
    assert resp.status_code == 302

    with app.app_context():
        u = db.session.get(User, user.id)
        assert u is not None
        assert u.role == "admin"


def test_change_role_invalid(admin_client: FlaskClient, user: User) -> None:
    resp = admin_client.post(f"/admin/users/{user.id}/role", data={"role": "superuser"})
    assert resp.status_code == 302  # redirects with flash error


def test_unlock_user(admin_client: FlaskClient, app: Flask) -> None:
    # Create a locked user within the app context
    with app.app_context():
        u: User = User(email="locked@example.com", role="user")
        u.set_password("LockedPass123!")
        u.failed_attempts = 5
        u.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.add(u)
        db.session.commit()
        user_id: int = u.id

    resp = admin_client.post(f"/admin/users/{user_id}/unlock")
    assert resp.status_code == 302

    with app.app_context():
        u2 = db.session.get(User, user_id)
        assert u2 is not None
        assert u2.failed_attempts == 0
        assert u2.locked_until is None


def test_delete_user(admin_client: FlaskClient, app: Flask) -> None:
    # Create a user to delete
    with app.app_context():
        u: User = User(email="todelete@example.com", role="user")
        u.set_password("DeleteMe123!")
        db.session.add(u)
        db.session.commit()
        user_id: int = u.id

    resp = admin_client.post(f"/admin/users/{user_id}/delete")
    assert resp.status_code == 302

    with app.app_context():
        assert db.session.get(User, user_id) is None
