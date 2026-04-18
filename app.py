import logging
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, jsonify, render_template, request, Response
from flask_login import LoginManager, login_required
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect  # type: ignore[import-untyped]

import config
from services.db import db
from services.limiter import limiter

logger: logging.Logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=2)
cache = Cache()


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app: Flask = Flask(__name__)
    app.secret_key = config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
    app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
    app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE
    app.config["PERMANENT_SESSION_LIFETIME"] = config.PERMANENT_SESSION_LIFETIME

    if test_config:
        app.config.update(test_config)

    # Extensions
    db.init_app(app)
    CSRFProtect(app)
    limiter.init_app(app)
    cache.init_app(app, config={
        "CACHE_TYPE": "simple",
        "CACHE_DEFAULT_TIMEOUT": 600
    })

    login_manager: LoginManager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "error"

    from models.user import User

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))

    # Blueprints
    from services.admin import admin_bp
    from services.alerts import alerts_bp
    from services.analytics import analytics_bp
    from services.api import api_bp
    from services.auth import auth_bp
    from services.federation import federation_bp
    from services.locations import locations_bp
    from services.station import station_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(station_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(federation_bp)
    app.register_blueprint(api_bp)

    # Security headers
    @app.after_request
    def set_security_headers(response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://unpkg.com; "
            "img-src 'self' data: https://*.openstreetmap.org "
            "https://*.opentopomap.org https://*.cartocdn.com "
            "https://*.rainviewer.com; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "frame-ancestors 'none'"
        )
        return response

    # --- Routes ---
    from services import openmeteo, metno, rainviewer

    @app.route("/")
    @login_required
    def index() -> str:
        return render_template("index.html")

    @app.route("/api/weather")
    @login_required
    @cache.cached(timeout=600)
    def api_weather() -> Response | tuple[Response, int]:
        lat: float | None = request.args.get("lat", type=float)
        lon: float | None = request.args.get("lon", type=float)
        if lat is None or lon is None:
            return jsonify({"error": "lat and lon parameters are required"}), 400

        futures = [
            executor.submit(openmeteo.fetch_weather, lat, lon),
            executor.submit(metno.fetch_weather, lat, lon)
        ]

        results: list[dict[str, Any]] = []
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

        if not results:
            return jsonify({
                "error": "All weather sources unavailable",
                "source": None,
                "current": None,
                "daily": [],
            }), 503

        if len(results) == 2:
            primary_res: dict[str, Any] | None = None
            secondary_res: dict[str, Any] | None = None

            for r in results:
                if r.get("source") == "openmeteo":
                    primary_res = r
                elif r.get("source") == "metno":
                    secondary_res = r

            if primary_res and secondary_res:
                result = primary_res.copy()
                result["secondary"] = secondary_res
                return jsonify(result)
            elif primary_res:
                return jsonify(primary_res)
            else:
                return jsonify(secondary_res)

        return jsonify(results[0])


    @app.route("/api/radar")
    @login_required
    def api_radar() -> Response | tuple[Response, int]:
        data: dict[str, Any] | None = rainviewer.fetch_radar_metadata()
        if data is None:
            return jsonify({"error": "Radar data unavailable"}), 503
        return jsonify(data)

    @app.route("/api/search")
    @login_required
    @cache.cached(timeout=600)
    def api_search() -> Response:
        q: str = request.args.get("q", "").strip()
        if not q:
            return jsonify([])
        return jsonify(openmeteo.search_location(q))

    # Background scheduler
    from services.scheduler import init_scheduler
    init_scheduler(app)

    # DB init, data dirs, and admin seeding
    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.ML_MODEL_DIR, exist_ok=True)

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin() -> None:
    """Create initial admin user from env vars if no users exist."""
    from models.user import User
    if User.query.first() is not None:
        return
    if not config.ADMIN_EMAIL or not config.ADMIN_PASSWORD:
        logger.warning(
            "No users exist. Set ADMIN_EMAIL and ADMIN_PASSWORD env vars to create an admin."
        )
        return

    admin: User = User(email=config.ADMIN_EMAIL.lower(), role="admin")
    admin.set_password(config.ADMIN_PASSWORD)
    db.session.add(admin)
    db.session.commit()
    logger.info("Admin user created: %s", config.ADMIN_EMAIL)


if __name__ == "__main__":
    app: Flask = create_app()
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
