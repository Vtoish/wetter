"""Federation blueprint for multi-instance data sharing.

Supports a local-first, decentralized architecture where independent
Wetter instances can optionally share weather data with trusted peers.
Federation uses a pull-based model: each instance exposes a read-only
API, and peers periodically fetch new records.
"""

import logging
from typing import Any

from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required  # type: ignore[import-untyped]
from werkzeug.wrappers import Response as WerkzeugResponse

import config
from models.peer import Peer
from models.shared_record import SharedRecord
from services.auth import role_required
from services.db import db

logger: logging.Logger = logging.getLogger(__name__)

federation_bp: Blueprint = Blueprint("federation", __name__, url_prefix="/federation")


@federation_bp.route("/peers")
@role_required("admin")
def peers() -> str:
    """List all configured federation peers."""
    all_peers: list[Peer] = Peer.query.order_by(Peer.created_at.desc()).all()  # type: ignore[assignment]
    return render_template("federation/peers.html", peers=all_peers)


@federation_bp.route("/peers", methods=["POST"])
@role_required("admin")
def add_peer() -> WerkzeugResponse:
    """Add a new federation peer."""
    name: str = request.form.get("name", "").strip()
    url: str = request.form.get("url", "").strip()
    api_key: str = request.form.get("api_key", "").strip()

    if not name or not url or not api_key:
        flash("Name, URL, and API key are required.", "error")
        return redirect(url_for("federation.peers"))

    from werkzeug.security import generate_password_hash
    peer: Peer = Peer(
        name=name,
        url=url,
        api_key_hash=generate_password_hash(api_key),
        trusted=True,
    )
    db.session.add(peer)
    db.session.commit()
    flash(f"Peer '{name}' added.", "success")
    return redirect(url_for("federation.peers"))


@federation_bp.route("/peers/<int:peer_id>/delete", methods=["POST"])
@role_required("admin")
def delete_peer(peer_id: int) -> WerkzeugResponse:
    """Remove a federation peer and its imported records."""
    peer: Peer | None = db.session.get(Peer, peer_id)
    if not peer:
        flash("Peer not found.", "error")
        return redirect(url_for("federation.peers"))

    db.session.delete(peer)
    db.session.commit()
    flash(f"Peer '{peer.name}' removed.", "success")
    return redirect(url_for("federation.peers"))


@federation_bp.route("/api/records")
def api_records() -> Response | tuple[Response, int]:
    """Read-only API endpoint for peers to pull shared data.

    Authenticated by API key in the Authorization header.
    Query params: since (ISO timestamp), record_type, limit.
    """
    if not config.FEDERATION_ENABLED:
        return jsonify({"error": "Federation is disabled"}), 503

    auth_header: str | None = request.headers.get("Authorization")
    if not auth_header or not _validate_federation_key(auth_header):
        return jsonify({"error": "Invalid API key"}), 403

    # TODO: query local observations/predictions, filter by shared types
    records: list[dict[str, Any]] = []
    return jsonify({"records": records})


def sync_from_peer(peer_id: int) -> int:
    """Pull new shared records from a trusted peer.

    Fetches records from the peer's federation API that are newer
    than our last sync timestamp. Stores them as SharedRecord entries
    with read-only status and origin metadata.

    Returns:
        Number of new records imported.
    """
    # TODO: HTTP GET peer.url/federation/api/records?since=last_sync_at
    logger.info("Syncing from peer %d", peer_id)
    return 0


def _validate_federation_key(auth_header: str) -> bool:
    """Validate an incoming federation API key."""
    if not config.FEDERATION_API_KEY:
        return False
    # Expected format: "Bearer <key>"
    parts: list[str] = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer":
        return False
    return parts[1] == config.FEDERATION_API_KEY
