# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

"""Analytics blueprint.

Provides historical charts, forecast accuracy comparisons,
trend analysis, and model performance views. Access is gated
by role — analysts and admins can view all analytics.
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, render_template, request
from flask_login import login_required

from services.auth import role_required

logger: logging.Logger = logging.getLogger(__name__)

analytics_bp: Blueprint = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("/")
@role_required("analyst", "admin")
def index() -> str:
    """Analytics dashboard with historical charts and trends."""
    return render_template("analytics/index.html")


@analytics_bp.route("/api/history")
@login_required
def api_history() -> Response | tuple[Response, int]:
    """Return historical observations for a location as JSON.

    Query params: location_id, days (default 7).
    """
    location_id: int | None = request.args.get("location_id", type=int)
    days: int = request.args.get("days", 7, type=int)

    if location_id is None:
        return jsonify({"error": "location_id is required"}), 400

    # TODO: query Observation records, aggregate by time
    observations: list[dict[str, Any]] = []
    return jsonify({"location_id": location_id, "days": days, "data": observations})


@analytics_bp.route("/api/accuracy")
@role_required("analyst", "admin")
def api_accuracy() -> Response | tuple[Response, int]:
    """Return forecast vs actual comparison data as JSON.

    Query params: location_id, days (default 30).
    """
    location_id: int | None = request.args.get("location_id", type=int)
    days: int = request.args.get("days", 30, type=int)

    if location_id is None:
        return jsonify({"error": "location_id is required"}), 400

    # TODO: compare stored forecasts against actual observations
    accuracy: list[dict[str, Any]] = []
    return jsonify({"location_id": location_id, "days": days, "data": accuracy})


@analytics_bp.route("/api/trends")
@role_required("analyst", "admin")
def api_trends() -> Response | tuple[Response, int]:
    """Return trend data over time as JSON.

    Query params: location_id, metric (temperature, humidity, etc.), days.
    """
    location_id: int | None = request.args.get("location_id", type=int)
    metric: str = request.args.get("metric", "temperature")
    days: int = request.args.get("days", 30, type=int)

    if location_id is None:
        return jsonify({"error": "location_id is required"}), 400

    # TODO: compute rolling averages, min/max envelopes, etc.
    trends: list[dict[str, Any]] = []
    return jsonify({
        "location_id": location_id,
        "metric": metric,
        "days": days,
        "data": trends,
    })
