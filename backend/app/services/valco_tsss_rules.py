"""
ValCo TSSS business rules.

Scope:
- Land type conversion standard.
- Total adjustment ratio guard.
- No double-counting land type adjustment.

This module is deterministic and must not invent missing data.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any

ADJUSTMENT_RATIO_LIMIT = 0.40

LAND_CONVERSION_FACTORS: dict[str, float] = {
    # Residential / land for housing
    "RESIDENTIAL": 1.00,
    "DAT_O": 1.00,
    "DATO": 1.00,
    "DAT O": 1.00,
    "ODT": 1.00,
    "ONT": 1.00,
    # Commercial / service land
    "TMDV": 0.85,
    "COMMERCIAL_SERVICE": 0.85,
    "COMMERCIAL": 0.85,
    "SERVICE": 0.85,
    "DAT_TMDV": 0.85,
    # Non-agricultural production/business land
    "SKC": 0.75,
    "NON_AGRICULTURAL_PRODUCTION_BUSINESS": 0.75,
    "PRODUCTION_BUSINESS": 0.75,
    "DAT_SKC": 0.75,
    # Perennial crop land
    "CLN": 0.60,
    "PERENNIAL_CROP": 0.60,
    "DAT_CLN": 0.60,
}


@dataclass(frozen=True)
class AdjustmentAssessment:
    total_adjustment_ratio: float
    size_adjustment_ratio: float
    land_type_adjustment_ratio: float
    is_within_limit: bool
    warnings: list[str]


def _remove_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_land_type(value: Any) -> str | None:
    """Normalize land type text without inventing missing values."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    text = _remove_accents(text)
    text = text.upper()
    text = text.replace("-", "_").replace("/", "_")
    text = re_sub_spaces(text)
    return text


def re_sub_spaces(value: str) -> str:
    import re

    collapsed = re.sub(r"\s+", " ", value).strip()
    return collapsed


def land_conversion_factor(value: Any) -> float | None:
    """Return ValCo standard factor or None if land type is unknown/missing."""
    key = normalize_land_type(value)
    if key is None:
        return None

    direct = LAND_CONVERSION_FACTORS.get(key)
    if direct is not None:
        return direct

    compact = key.replace(" ", "_")
    return LAND_CONVERSION_FACTORS.get(compact)


def estimate_size_adjustment_ratio(candidate_size: Any, subject_size: Any) -> float:
    """
    Estimate area-scale adjustment ratio.

    Missing or invalid values return 0.0 to avoid inventing business data.
    A separate warning is generated in assess_adjustment_ratio().
    """
    try:
        c_size = float(candidate_size)
        s_size = float(subject_size)
    except (TypeError, ValueError):
        return 0.0

    if c_size <= 0 or s_size <= 0:
        return 0.0

    return abs(c_size - s_size) / s_size


def estimate_land_type_adjustment_ratio(candidate_land_type: Any, subject_land_type: Any) -> float:
    """
    Estimate land type conversion difference.

    If either factor is missing/unknown, return 0.0 and let warnings flag missing basis.
    """
    c_factor = land_conversion_factor(candidate_land_type)
    s_factor = land_conversion_factor(subject_land_type)

    if c_factor is None or s_factor is None or s_factor == 0:
        return 0.0

    return abs(c_factor - s_factor) / s_factor


def assess_adjustment_ratio(
    *,
    candidate_size: Any,
    subject_size: Any,
    candidate_land_type: Any,
    subject_land_type: Any,
    land_type_already_adjusted: bool = False,
) -> AdjustmentAssessment:
    """
    Assess total adjustment ratio using ValCo internal guardrail.

    No double-counting rule:
    - If land_type_already_adjusted=True, land type adjustment component is forced to 0.
    - A warning is returned to make this traceable.
    """
    warnings: list[str] = []

    size_ratio = estimate_size_adjustment_ratio(candidate_size, subject_size)

    if candidate_size is None or subject_size is None:
        warnings.append("missing_size_basis")

    if land_type_already_adjusted:
        land_ratio = 0.0
        warnings.append("land_type_adjustment_skipped_to_avoid_double_counting")
    else:
        land_ratio = estimate_land_type_adjustment_ratio(candidate_land_type, subject_land_type)
        if (
            land_conversion_factor(candidate_land_type) is None
            or land_conversion_factor(subject_land_type) is None
        ):
            warnings.append("missing_or_unknown_land_type_conversion_factor")

    total_ratio = size_ratio + land_ratio
    is_within = total_ratio < ADJUSTMENT_RATIO_LIMIT

    if not is_within:
        warnings.append("total_adjustment_ratio_exceeds_or_equals_40_percent")

    return AdjustmentAssessment(
        total_adjustment_ratio=total_ratio,
        size_adjustment_ratio=size_ratio,
        land_type_adjustment_ratio=land_ratio,
        is_within_limit=is_within,
        warnings=warnings,
    )
