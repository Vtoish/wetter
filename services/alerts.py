"""Alert system blueprint and evaluation engine.

Users create alert rules with conditions (e.g., rain probability > 80%,
temperature < 0). The system evaluates these rules against current data
and generates Alert records with in-app notifications and optional email.
"""

import logging
from typing import Any, cast

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required  # type: ignore[import-untyped]
from werkzeug.wrappers import Response

from models.alert import Alert
from models.alert_rule import AlertRule
from services.db import db

logger: logging.Logger = logging.getLogger(__name__)

alerts_bp: Blueprint = Blueprint("alerts", __name__, url_prefix="/alerts")


@alerts_bp.route("/")
@login_required
def index() -> str:
    """List the current user's alert rules and recent triggered alerts."""
    rules: list[AlertRule] = cast(
        list[AlertRule],
        AlertRule.query.filter_by(user_id=current_user.id).order_by(  # type: ignore[attr-defined]
            AlertRule.created_at.desc()
        ).all(),
    )
    recent_alerts: list[Alert] = cast(
        list[Alert],
        Alert.query.join(AlertRule).filter(
            AlertRule.user_id == current_user.id  # type: ignore[attr-defined]
        ).order_by(Alert.triggered_at.desc()).limit(50).all(),
    )
    return render_template(
        "alerts/index.html", rules=rules, alerts=recent_alerts,
    )


@alerts_bp.route("/rules", methods=["POST"])
@login_required
def create_rule() -> Response:
    """Create a new alert rule."""
    name: str = request.form.get("name", "").strip()
    location_id_str: str = request.form.get("location_id", "")
    field: str = request.form.get("field", "").strip()
    operator: str = request.form.get("operator", "").strip()
    threshold_str: str = request.form.get("threshold", "")

    if not all([name, location_id_str, field, operator, threshold_str]):
        flash("All fields are required.", "error")
        return redirect(url_for("alerts.index"))

    import json
    condition: dict[str, Any] = {
        "field": field,
        "operator": operator,
        "threshold": float(threshold_str),
    }

    rule: AlertRule = AlertRule(
        user_id=current_user.id,  # type: ignore[attr-defined]
        location_id=int(location_id_str),
        name=name,
        condition_json=json.dumps(condition),
    )
    db.session.add(rule)
    db.session.commit()
    flash(f"Alert rule '{name}' created.", "success")
    return redirect(url_for("alerts.index"))


@alerts_bp.route("/rules/<int:rule_id>/delete", methods=["POST"])
@login_required
def delete_rule(rule_id: int) -> Response:
    """Delete an alert rule owned by the current user."""
    rule: AlertRule | None = db.session.get(AlertRule, rule_id)
    if not rule or rule.user_id != current_user.id:  # type: ignore[attr-defined]
        flash("Rule not found.", "error")
        return redirect(url_for("alerts.index"))

    db.session.delete(rule)
    db.session.commit()
    flash("Alert rule deleted.", "success")
    return redirect(url_for("alerts.index"))


@alerts_bp.route("/<int:alert_id>/acknowledge", methods=["POST"])
@login_required
def acknowledge(alert_id: int) -> Response:
    """Acknowledge a triggered alert."""
    alert: Alert | None = db.session.get(Alert, alert_id)
    if not alert:
        flash("Alert not found.", "error")
        return redirect(url_for("alerts.index"))

    alert.acknowledged = True
    db.session.commit()
    flash("Alert acknowledged.", "success")
    return redirect(url_for("alerts.index"))


def evaluate_alerts() -> int:
    """Evaluate all enabled alert rules against current data.

    Checks each rule's condition against the latest observations or
    predictions for its location. Creates Alert records for triggered
    rules and optionally sends notifications.

    Returns:
        Number of alerts triggered.
    """
    # TODO: query all enabled rules, check conditions, create Alerts
    logger.info("Evaluating alert rules")
    return 0


def send_notification(alert: Alert) -> None:
    """Send a notification for a triggered alert.

    Delivers in-app notification and, if ALERT_EMAIL_ENABLED,
    sends an email to the rule owner.
    """
    # TODO: implement in-app + email notification
    logger.info("Sending notification for alert %d", alert.id)
