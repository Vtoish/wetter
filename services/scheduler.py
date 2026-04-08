"""Background task scheduler.

Manages periodic jobs for data collection, alert evaluation,
model retraining, and federation sync. Uses APScheduler when
SCHEDULER_ENABLED is True.
"""

import logging

from flask import Flask

import config

logger: logging.Logger = logging.getLogger(__name__)


def init_scheduler(app: Flask) -> None:
    """Initialize the background scheduler with configured jobs.

    Only starts if config.SCHEDULER_ENABLED is True.
    Call this from create_app() after all extensions are initialized.
    """
    if not config.SCHEDULER_ENABLED:
        logger.info("Scheduler disabled (SCHEDULER_ENABLED=false)")
        return

    # TODO: initialize APScheduler, add jobs below
    logger.info("Scheduler initialized")


def job_fetch_forecasts() -> None:
    """Fetch and store forecast data for all active locations."""
    # TODO: iterate locations, call openmeteo/metno, store as Observations
    logger.info("Running scheduled forecast fetch")


def job_evaluate_alerts() -> None:
    """Evaluate all enabled alert rules against current data."""
    # TODO: call alerts.evaluate_alerts()
    logger.info("Running scheduled alert evaluation")


def job_sync_federation() -> None:
    """Sync shared records from all trusted federation peers."""
    # TODO: iterate trusted peers, call federation.sync_from_peer()
    if not config.FEDERATION_ENABLED:
        return
    logger.info("Running scheduled federation sync")


def job_retrain_models() -> None:
    """Retrain ML models for locations with sufficient data."""
    # TODO: iterate locations with enough history, call ml.train_model()
    logger.info("Running scheduled model retraining")
