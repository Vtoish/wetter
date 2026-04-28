# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

"""REST API blueprint (v1).

Provides authenticated JSON API access to locations, current conditions,
predictions, historical data, and alerts. All endpoints are scoped to
the authenticated user and their permitted locations.
"""

import logging
from typing import Any, cast

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user, login_required
from models.location import Location
from models.user import User
from services import ml
from services.db import db

logger: logging.Logger = logging.getLogger(__name__)

api_bp: Blueprint = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_bp.route("/locations")
@login_required
def list_locations() -> Response:
    """Return the authenticated user's locations with pagination."""
    user = cast(User, current_user)
    page = request.args.get("page", 1, type=int)
    per_page = 50
    pagination = Location.query.filter_by(user_id=user.id).paginate(page=page, per_app=per_page, error_out=False)

    result: list[dict[str, Any]] = [
        {
            "id": loc.id,
            "name": loc.name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "timezone": loc.timezone,
        }
        for loc in pagination.items
    ]
    return jsonify({
        "items": result,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page
    })


@api_bp.route("/locations/<int:location_id>/current")
@login_required
def location_current(location_id: int) -> Response | tuple[Response, int]:
    """Return current and latest prediction for a location."""
    user = cast(User, current_user)
    location: Location | None = db.session.get(Location, location_id)
    if not location or location.user_id != user.id:
        return jsonify({"error": "Location not found"}), 404

    prediction: dict[str, Any] | None = ml.get_latest_prediction(location_id)

    return jsonify({
        "location": {
            "id": location.id,
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        },
        "prediction": prediction,
        # TODO: include latest observation data
        "observations": None,
    })


@api_bp.route("/locations/<int:location_id>/history")
@login_required
def location_history(location_id: int) -> Response | tuple[Response, int]:
    """Return historical observation data for a location."""
    user = cast(User, current_user)
    location: Location | None = db.session.get(Location, location_id)
    if not location or location.user_id != user.id:
        return jsonify({"error": "Location not found"}), 404

    days: int = request.args.get("days", 7, type=int)

    # TODO: query Observation records for this location
    history: list[dict[str, Any]] = []
    return jsonify({"location_id": location_id, "days": days, "data": history})


@api_bp.route("/alerts")
@login_required
def list_alerts() -> Response:
    """Return the authenticated user's recent alerts."""
    from models.alert import Alert
    from models.alert_rule import AlertRule
    user = cast(User, current_user)

    alerts: list[Alert] = cast(
        list[Alert],
        Alert.query.join(AlertRule).filter(
            AlertRule.user_id == user.id
        ).order_by(Alert.triggered_at.desc()).limit(50).all(),
    )

    result: list[dict[str, Any]] = [
        {
            "id": a.id,
            "rule_id": a.rule_id,
            "message": a.message,
            "triggered_at": a.triggered_at.isoformat(),
            "acknowledged": a.acknowledged,
        }
        for a in alerts
    ]
    return jsonify(result)


@api_bp.route("/predictions/<int:location_id>")
@login_required
def get_predictions(location_id: int) -> Response | tuple[Response, int]:
    """Return the latest prediction for a location."""
    user = cast(User, current_user)
    location: Location | None = db.session.get(Location, location_id)
    if not location or location.user_id != user.id:
        return jsonify({"error": "Location not found"}), 404

    prediction: dict[str, Any] | None = ml.get_latest_prediction(location_id)
    if prediction is None:
        return jsonify({"error": "No predictions available"}), 404

    return jsonify(prediction)
