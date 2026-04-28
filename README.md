# Wetter

A multi-user weather intelligence platform that combines local sensor data, global forecasts, radar imagery, and machine learning to produce accurate, personalized weather predictions. Features multi-location management, an alert system, analytics, role-based access control with MFA, federated multi-instance data sharing, and Docker deployment.

## Features

### Implemented

- **Multi-source weather data** -- Open-Meteo (primary) and Met.no (fallback) provide current conditions and 7-day forecasts
- **Live radar** -- Animated precipitation radar powered by RainViewer on a Leaflet map with configurable base layers, color schemes, and opacity
- **Location search** -- City search via Open-Meteo geocoding API with persistent selection (localStorage)
- **Authentication** -- Signup, login, logout with strong password policy (length, complexity)
- **TOTP-based MFA** -- Two-factor authentication with QR code setup, enable/disable flow
- **Account lockout** -- Automatic lockout after repeated failed login or MFA attempts
- **Role-based access control** -- Four roles (viewer, user, analyst, admin) with a `role_required` decorator
- **Admin panel** -- User management with role changes, account unlock, deletion (with self-deletion protection)
- **Security hardening** -- CSRF, rate limiting, secure cookies, HSTS, CSP, security headers

### Scaffolded (structure in place, implementation in progress)

- **Multi-location management** -- Users create and manage multiple locations; each location is the primary unit for data, predictions, and alerts
- **Ecowitt sensor ingestion** -- Receives data from Ecowitt Wittboy GW2001 and add-on sensors via HTTP webhook with passkey auth
- **Data pipeline** -- Observations model for timestamped readings from sensors and forecast snapshots; feature engineering for derived metrics (pressure trends, humidity deltas, forecast diffs)
- **Machine learning** -- Per-location model training, versioning, and real-time predictions (rain probability, corrected temperature, cloud cover, storm likelihood)
- **Alert system** -- User-defined rules with conditions on weather metrics; continuous evaluation with in-app notifications and optional email
- **Analytics** -- Historical charts, forecast accuracy comparison, trend analysis, model performance views (analyst/admin only)
- **Federation** -- Local-first architecture with pull-based data sharing between trusted peer instances; read-only imported records with origin metadata
- **Background scheduler** -- Periodic forecast fetching, alert evaluation, federation sync, and model retraining
- **REST API (v1)** -- Authenticated JSON API for locations, current data, predictions, history, and alerts
- **Docker deployment** -- Dockerfile and docker-compose.yml for web + background worker services

## Architecture

```
app.py                      Application factory, core routes, blueprint registration
config.py                   All settings via environment variables (.env supported)

models/
    user.py                 User -- auth, password hashing, TOTP, lockout, roles
    location.py             Location -- user's named lat/lon points
    sensor.py               Sensor -- hardware devices attached to locations
    observation.py          Observation -- timestamped readings (sensor or forecast)
    prediction.py           Prediction -- ML model outputs per location
    ml_model.py             MLModel -- trained model versions with metrics
    alert_rule.py           AlertRule -- user-defined alert conditions
    alert.py                Alert -- triggered alert instances
    peer.py                 Peer -- federation peer instances
    shared_record.py        SharedRecord -- imported federated data

services/
    db.py                   Flask-SQLAlchemy instance
    limiter.py              Flask-Limiter instance
    auth.py                 Auth blueprint (/auth) -- signup, login, logout, MFA
    admin.py                Admin blueprint (/admin) -- user management
    locations.py            Locations blueprint (/locations) -- CRUD
    station.py              Station blueprint (/station) -- Ecowitt ingestion
    alerts.py               Alerts blueprint (/alerts) -- rules and notifications
    analytics.py            Analytics blueprint (/analytics) -- charts and trends
    federation.py           Federation blueprint (/federation) -- peer management and sync
    api.py                  REST API blueprint (/api/v1) -- JSON endpoints
    openmeteo.py            Open-Meteo weather + geocoding client
    metno.py                Met.no weather client
    rainviewer.py           RainViewer radar client
    features.py             Feature engineering for ML
    ml.py                   Model training and prediction
    scheduler.py            Background task scheduling

templates/
    base.html               Layout with nav, flash messages
    index.html              Main dashboard -- weather, forecast, radar
    auth/                   Login, signup, MFA verify, MFA setup
    admin/                  User management
    locations/              Location list and detail
    alerts/                 Alert rules and history
    analytics/              Analytics dashboard
    federation/             Peer management

static/style.css            Application styles with dark mode support
tests/                      Pytest suite (63 tests)
data/                       ML model artifacts and exports
```

### Data Flow

```
Ecowitt sensor  ──POST──>  /station/ingest  ──>  Observation
Open-Meteo API  ──fetch──>  openmeteo.py    ──>  Observation (forecast snapshot)
Met.no API      ──fetch──>  metno.py        ──>  Observation (forecast snapshot)
RainViewer API  ──fetch──>  rainviewer.py   ──>  radar tile metadata

Observations  ──>  features.py  ──>  ml.py  ──>  Prediction
Predictions + Rules  ──>  alerts.py  ──>  Alert + notification

Federation peer  ──pull──>  /federation/api/records  ──>  SharedRecord
```

### Roles

| Role | Permissions |
|------|-------------|
| `viewer` | Read-only dashboard access |
| `user` | Manage own locations, sensors, alerts |
| `analyst` | User permissions + analytics + model inspection |
| `admin` | Full access: user management, federation, system config |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

All settings load from environment variables. A `.env` file is supported via python-dotenv.

| Variable | Description | Default |
|---|---|---|
| **Core** | | |
| `SECRET_KEY` | Flask session secret | `dev-secret-change-me` |
| `DATABASE_URI` | SQLAlchemy database URI | `sqlite:///wetter.db` |
| `FLASK_DEBUG` | Enable debug mode | `true` |
| **Auth** | | |
| `ADMIN_EMAIL` | Initial admin email (first-run seeding) | -- |
| `ADMIN_PASSWORD` | Initial admin password (first-run seeding) | -- |
| `PASSWORD_MIN_LENGTH` | Minimum password length | `12` |
| `MAX_LOGIN_ATTEMPTS` | Failed attempts before lockout | `5` |
| `LOCKOUT_DURATION` | Lockout duration (seconds) | `900` |
| **Weather APIs** | | |
| `WETTER_APP_NAME` | App name for Met.no User-Agent | `Wetter` |
| `WETTER_APP_CONTACT` | Contact email for Met.no User-Agent | `wetter@example.com` |
| `WETTER_REQUEST_TIMEOUT` | HTTP timeout (seconds) | `10` |
| **Ecowitt** | | |
| `ECOWITT_API_KEY` | Station API key | -- |
| `ECOWITT_PASSKEY` | Device passkey for ingest auth | -- |
| **Machine Learning** | | |
| `DATA_DIR` | Base data directory | `data` |
| `ML_MODEL_DIR` | Model artifact storage | `data/models` |
| `ML_RETRAIN_INTERVAL_HOURS` | Retraining schedule | `24` |
| **Alerts** | | |
| `ALERT_CHECK_INTERVAL_MINUTES` | Alert evaluation frequency | `5` |
| `ALERT_EMAIL_ENABLED` | Enable email notifications | `false` |
| `SMTP_HOST` | SMTP server host | -- |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | -- |
| `SMTP_PASSWORD` | SMTP password | -- |
| **Federation** | | |
| `FEDERATION_ENABLED` | Enable federation | `false` |
| `FEDERATION_API_KEY` | API key for peer auth | -- |
| `FEDERATION_SYNC_INTERVAL_MINUTES` | Sync frequency | `60` |
| **Scheduler** | | |
| `SCHEDULER_ENABLED` | Enable background scheduler | `false` |

## Running

### Development

```bash
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD='SecurePass123!' python app.py
```

The admin account is seeded on first run when the database is empty. The app runs on `http://localhost:5000`.

### Docker

```bash
# Copy and edit environment file
cp .env.example .env

# Build and start
docker compose up -d

# View logs
docker compose logs -f web
```

The `web` service runs gunicorn on port 5000. The `worker` service runs the background scheduler for data collection, alert evaluation, federation sync, and model retraining.

## Testing

```bash
pytest -v                                     # full suite (63 tests)
pytest tests/test_auth.py                     # single file
pytest tests/test_auth.py::test_login_success # single test
```

## Security

- **Password policy** -- Minimum 12 characters with uppercase, lowercase, digit, and special character
- **TOTP MFA** -- Time-based one-time passwords via authenticator apps, with brute-force lockout
- **Account lockout** -- 5 failed login or MFA attempts triggers 15-minute lockout
- **CSRF** -- All forms protected via Flask-WTF
- **Rate limiting** -- Auth endpoints rate-limited (login: 10/min, signup: 5/min, MFA: 10/min)
- **Session security** -- HttpOnly, SameSite=Lax, Secure (in production), 30-minute lifetime
- **Open redirect protection** -- Login `next` parameter validated against external redirects
- **Security headers** -- X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, Content-Security-Policy
- **Station ingest auth** -- Ecowitt webhook requires valid passkey
- **Federation auth** -- Peer API access requires Bearer token; imported records are read-only

## Data Sources

- [Open-Meteo](https://open-meteo.com/) -- Weather forecasts and geocoding (no API key required)
- [Met.no](https://api.met.no/) -- Norwegian Meteorological Institute weather API (no API key required)
- [RainViewer](https://www.rainviewer.com/api.html) -- Global precipitation radar tiles (no API key required)
- [Ecowitt](https://www.ecowitt.com/) -- Local weather station data (Wittboy GW2001 + add-on sensors)

## License

AGPL-3.0-only — see [LICENSE](LICENSE) for the full text.

Copyright (C) 2026 Vtoish
