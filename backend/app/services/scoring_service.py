from app.config import settings


def classify_adjustment(adjustment_ratio: float) -> str:
    if adjustment_ratio > settings.max_main_adjustment_ratio:
        return "REJECT"
    return "ELIGIBLE"


def rank_top10(items: list[dict]) -> list[dict]:
    ranked = sorted(
        items,
        key=lambda x: x.get("total_score", 0),
        reverse=True,
    )[: settings.top_recommended_count]
    for item in ranked:
        item["candidate_class"] = "RECOMMENDED_TOP_10"
    return ranked


def score_market_area(candidate_market_area: str | None, subject_market_area: str) -> float:
    return 1.0 if candidate_market_area == subject_market_area else 0.0


def score_land_type(
    candidate_land_type: str | None,
    candidate_planning_segment: str | None,
    subject_land_type: str,
    subject_planning_segment: str | None,
    land_type_adjusted: dict,  # To track if land type adjustment has been applied
) -> float:
    LAND_CONVERSION_RATES = {
        "residential": 1.0,
        "ONT": 1.0,
        "ODT": 1.0,
        "dat_o": 1.0,
        "dat o": 1.0,
        "TMDV": 0.85,
        "commercial_service": 0.85,
        "SKC": 0.75,
        "non_agricultural_production_business": 0.75,
        "CLN": 0.60,
        "perennial_crop": 0.60,
    }

    if candidate_land_type == subject_land_type:
        if subject_planning_segment and candidate_planning_segment != subject_planning_segment:
            return 0.5
        return 1.0
    else:
        # Apply land conversion standards
        candidate_rate = LAND_CONVERSION_RATES.get(candidate_land_type, 0.0)
        subject_rate = LAND_CONVERSION_RATES.get(subject_land_type, 0.0)

        if candidate_rate > 0 and subject_rate > 0:
            land_type_adjusted["status"] = True  # Mark as adjusted
            return candidate_rate / subject_rate
        return 0.0


def score_size(candidate_size_sqm: float | None, subject_size_sqm: float) -> float:
    if not candidate_size_sqm or not subject_size_sqm:
        return 0.0
    deviation = abs(candidate_size_sqm - subject_size_sqm) / subject_size_sqm
    return max(0.0, 1.0 - deviation)


def score_unit_price(candidate_unit_price: float | None) -> float:
    return 1.0 if candidate_unit_price and candidate_unit_price > 0 else 0.0


def score_source_link(candidate_source_url: str | None) -> float:
    return 1.0 if candidate_source_url else 0.0


def score_adjustment_ratio(adjustment_ratio: float) -> float:
    return max(0.0, 1.0 - min(adjustment_ratio, 1.0))


def build_scoring_tuple(candidate, subject, adjustment_ratio: float) -> tuple[float, ...]:
    land_type_adjusted = {"status": False}
    return (
        score_market_area(candidate.market_area, subject.market_area),
        score_land_type(
            candidate.land_type,
            candidate.planning_segment,
            subject.land_type,
            subject.planning_segment,
            land_type_adjusted,
        ),
        score_size(candidate.size_sqm, subject.size_sqm),
        score_unit_price(candidate.unit_price),
        score_source_link(candidate.source_url),
        score_adjustment_ratio(adjustment_ratio),
    )


def rank_eligible_candidates(scored_items: list[dict], limit: int | None = None) -> list[dict]:
    top_n = limit if limit is not None else settings.top_recommended_count
    ranked = sorted(scored_items, key=lambda item: item["score_tuple"], reverse=True)
    result = ranked[:top_n]
    for item in result:
        item["candidate_class"] = "RECOMMENDED_TOP_10"
    return result


def insufficient_data_status(eligible_count: int) -> str:
    if eligible_count >= 10:
        return "FULL_TOP_10"
    if eligible_count >= 6:
        return "PARTIAL_ELIGIBLE_SHOWN"
    if eligible_count >= 3:
        return "PROVISIONAL_FINAL_3_ONLY"
    return "INSUFFICIENT_EXPAND_OR_ANALYST_DECISION"


# VALCO_NO_DOUBLE_COUNT_LAND_TYPE_NOTE:
# Land type conversion must not be applied twice.
# Use assess_adjustment_ratio(..., land_type_already_adjusted=True)
# when upstream conversion has already been applied.
