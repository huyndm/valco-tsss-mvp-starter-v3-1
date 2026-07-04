from app.services.valco_tsss_rules import (
    ADJUSTMENT_RATIO_LIMIT,
    assess_adjustment_ratio,
    land_conversion_factor,
)


def test_land_conversion_standards():
    assert land_conversion_factor("ONT") == 1.00
    assert land_conversion_factor("ODT") == 1.00
    assert land_conversion_factor("dat o") == 1.00
    assert land_conversion_factor("TMDV") == 0.85
    assert land_conversion_factor("SKC") == 0.75
    assert land_conversion_factor("CLN") == 0.60


def test_total_adjustment_ratio_under_40_percent_passes():
    assessment = assess_adjustment_ratio(
        candidate_size=110,
        subject_size=100,
        candidate_land_type="ONT",
        subject_land_type="ONT",
    )
    assert assessment.total_adjustment_ratio == 0.10
    assert assessment.total_adjustment_ratio < ADJUSTMENT_RATIO_LIMIT
    assert assessment.is_within_limit is True


def test_total_adjustment_ratio_equal_or_above_40_percent_is_flagged():
    assessment = assess_adjustment_ratio(
        candidate_size=150,
        subject_size=100,
        candidate_land_type="ONT",
        subject_land_type="ONT",
    )
    assert assessment.total_adjustment_ratio >= ADJUSTMENT_RATIO_LIMIT
    assert assessment.is_within_limit is False
    assert "total_adjustment_ratio_exceeds_or_equals_40_percent" in assessment.warnings


def test_land_type_conversion_difference_is_counted_once():
    once = assess_adjustment_ratio(
        candidate_size=100,
        subject_size=100,
        candidate_land_type="SKC",
        subject_land_type="ONT",
        land_type_already_adjusted=False,
    )
    skipped = assess_adjustment_ratio(
        candidate_size=100,
        subject_size=100,
        candidate_land_type="SKC",
        subject_land_type="ONT",
        land_type_already_adjusted=True,
    )

    assert once.land_type_adjustment_ratio == 0.25
    assert skipped.land_type_adjustment_ratio == 0.0
    assert "land_type_adjustment_skipped_to_avoid_double_counting" in skipped.warnings


def test_missing_unknown_land_type_does_not_invent_factor():
    assessment = assess_adjustment_ratio(
        candidate_size=100,
        subject_size=100,
        candidate_land_type="UNKNOWN",
        subject_land_type="ONT",
    )
    assert assessment.land_type_adjustment_ratio == 0.0
    assert "missing_or_unknown_land_type_conversion_factor" in assessment.warnings
