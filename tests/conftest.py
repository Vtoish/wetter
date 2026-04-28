# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from app import create_app
from models.user import User
from services.db import db as _db


@pytest.fixture
def app() -> Generator[Flask]:
    application: Flask = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
        "SERVER_NAME": "localhost",
    })

    with application.app_context():
        _db.drop_all()
        _db.create_all()
        yield application
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def db(app: Flask) -> SQLAlchemy:
    return _db


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def user(app: Flask, db: SQLAlchemy) -> User:
    """Create a regular test user."""
    u: User = User(email="test@example.com", role="user")
    u.set_password("SecurePass123!")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def admin_user(app: Flask, db: SQLAlchemy) -> User:
    """Create an admin test user."""
    u: User = User(email="admin@example.com", role="admin")
    u.set_password("AdminPass123!")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def authenticated_client(client: FlaskClient, user: User) -> FlaskClient:
    """Client logged in as regular user."""
    client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "SecurePass123!",
    })
    return client


@pytest.fixture
def admin_client(client: FlaskClient, admin_user: User) -> FlaskClient:
    """Client logged in as admin."""
    client.post("/auth/login", data={
        "email": "admin@example.com",
        "password": "AdminPass123!",
    })
    return client
