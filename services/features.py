# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

"""Feature engineering for ML models.

Computes derived features from raw observations and forecast data
for use in training and real-time prediction.
"""

import logging
from typing import Any

logger: logging.Logger = logging.getLogger(__name__)


def compute_derived_features(location_id: int) -> dict[str, Any]:
    """Compute derived features for a location from recent observations.

    Includes pressure trends, humidity changes, forecast differences,
    and radar-based indicators.

    Returns a dict of feature name -> value pairs.
    """
    # TODO: query recent observations, compute deltas and trends
    logger.info("Computing derived features for location %d", location_id)
    return {
        "pressure_trend_3h": 0.0,
        "humidity_delta_1h": 0.0,
        "forecast_temp_diff": 0.0,
        "radar_intensity_max": 0.0,
    }


def build_training_features(
    location_id: int, days: int = 30
) -> list[dict[str, Any]]:
    """Build historical feature vectors for model training.

    Fetches observations for the past N days, computes derived features
    for each timestep, and returns a list of feature dicts.

    Args:
        location_id: The location to build features for.
        days: Number of days of history to include.

    Returns:
        List of feature dicts, one per timestep.
    """
    # TODO: query observation history, build aligned feature vectors
    logger.info(
        "Building training features for location %d (%d days)",
        location_id, days,
    )
    return []
