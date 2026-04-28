# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

"""Machine learning model training and prediction.

Trains per-location models on historical data and generates
real-time predictions: rain probability, corrected temperature,
cloud cover estimates, and storm likelihood.
"""

import logging
from typing import Any

import config

logger: logging.Logger = logging.getLogger(__name__)


def train_model(location_id: int) -> dict[str, Any]:
    """Train a new model version for a location.

    Builds training features, fits a model, saves the artifact,
    and creates an MLModel record.

    Returns:
        Dict with model version info and metrics.
    """
    # TODO: build features, train sklearn model, save to ML_MODEL_DIR
    logger.info("Training model for location %d", location_id)
    return {
        "location_id": location_id,
        "version": "v0.0.0",
        "metrics": {},
        "artifact_path": None,
    }


def predict(location_id: int) -> dict[str, Any] | None:
    """Run the active model for a location and return predictions.

    Computes current derived features and feeds them through the
    active model version. Stores the result as a Prediction record.

    Returns:
        Dict with prediction values, or None if no active model.
    """
    # TODO: load active model, compute features, run inference
    logger.info("Generating prediction for location %d", location_id)
    return None


def get_latest_prediction(location_id: int) -> dict[str, Any] | None:
    """Fetch the most recent prediction for a location.

    Returns:
        Dict with prediction values, or None if no predictions exist.
    """
    # TODO: query Prediction model ordered by timestamp desc
    return None
