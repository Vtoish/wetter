# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

"""Location management blueprint.

Users can create, view, and delete locations. Each location
serves as the primary unit for weather data, predictions,
analytics, and alerts.
"""

import logging
from typing import Any, cast

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from models.location import Location
from models.user import User
from services.db import db

logger: logging.Logger = logging.getLogger(__name__)

locations_bp: Blueprint = Blueprint("locations", __name__, url_prefix="/locations")


@locations_bp.route("/")
@login_required
def index() -> str:
    """List all locations for the current user."""
    user = cast(User, current_user)
    user_locations: list[Location] = cast(
        list[Location],
        Location.query.filter_by(user_id=user.id).order_by(
            Location.created_at.desc()
        ).all(),
    )
    return render_template("locations/index.html", locations=user_locations)


@locations_bp.route("/", methods=["POST"])
@login_required
def create() -> Response:
    """Create a new location for the current user."""
    user = cast(User, current_user)
    name: str = request.form.get("name", "").strip()
    lat_str: str = request.form.get("latitude", "")
    lon_str: str = request.form.get("longitude", "")
    tz: str = request.form.get("timezone", "UTC").strip()

    if not name or not lat_str or not lon_str:
        flash("Name, latitude, and longitude are required.", "error")
        return redirect(url_for("locations.index"))

    try:
        lat: float = float(lat_str)
        lon: float = float(lon_str)
    except ValueError:
        flash("Invalid latitude or longitude.", "error")
        return redirect(url_for("locations.index"))

    location: Location = Location(
        user_id=user.id,
        name=name,
        latitude=lat,
        longitude=lon,
        timezone=tz,
    )
    db.session.add(location)
    db.session.commit()
    flash(f"Location '{name}' created.", "success")
    return redirect(url_for("locations.index"))


@locations_bp.route("/<int:location_id>")
@login_required
def detail(location_id: int) -> str | tuple[str, int]:
    """Show detail view for a single location."""
    user = cast(User, current_user)
    location: Location | None = db.session.get(Location, location_id)
    if not location or location.user_id != user.id:
        flash("Location not found.", "error")
        return render_template("locations/index.html", locations=[]), 404
    return render_template("locations/detail.html", location=location)


@locations_bp.route("/<int:location_id>/delete", methods=["POST"])
@login_required
def delete(location_id: int) -> Response:
    """Delete a location owned by the current user."""
    user = cast(User, current_user)
    location: Location | None = db.session.get(Location, location_id)
    if not location or location.user_id != user.id:
        flash("Location not found.", "error")
        return redirect(url_for("locations.index"))

    db.session.delete(location)
    db.session.commit()
    flash(f"Location '{location.name}' deleted.", "success")
    return redirect(url_for("locations.index"))
