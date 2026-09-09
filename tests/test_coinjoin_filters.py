import pytest

from btcaml.data.coinjoin_filters import (
    UPSTREAM_REVISION,
    TransactionFeatures,
    d_wp100k_matches,
    exclude_f_pub,
    exclude_f_wide,
    f_pub_matches,
    is_coinjoin_joinmarket,
    is_coinjoin_samourai,
    is_coinjoin_wasabi_1_0,
    is_coinjoin_wasabi_1_1,
    is_coinjoin_wasabi_2,
    is_tx0_paper_diagnostic,
)


def tx(inputs, outputs):
    return TransactionFeatures(
        tuple(script for script, _ in inputs), tuple(value for _, value in inputs),
        tuple(script for script, _ in outputs), tuple(value for _, value in outputs),
    )


def ids(prefix, values):
    return [(f"{prefix}{index}", value) for index, value in enumerate(values)]


def test_feature_validation_and_stable_value_order():
    assert UPSTREAM_REVISION == "3becbc44a951abbe1e85d374a66340a639059d1c"
    with pytest.raises(ValueError, match="equal length"):
        TransactionFeatures(("in",), (), (), ())
    with pytest.raises(TypeError, match="tuples"):
        TransactionFeatures(["in"], (1,), (), ())  # type: ignore[arg-type]
    feature = tx(ids("i", [1, 2]), ids("o", [9, 9, 7, 7]))
    assert feature.output_value_counts == ((7, 2), (9, 2))


def test_joinmarket_boundary_and_duplicate_output_id():
    positive = tx(ids("i", [1, 2, 3]), ids("o", [8, 8, 8]))
    assert is_coinjoin_joinmarket(positive)
    assert not is_coinjoin_joinmarket(tx(ids("i", [1, 2]), ids("o", [8, 8])))
    duplicate_output = TransactionFeatures(
        ("i0", "i1", "i2"), (1, 2, 3), ("o", "o", "o"), (8, 8, 8)
    )
    assert not is_coinjoin_joinmarket(duplicate_output)


def test_wasabi_1_detectors_keep_inclusive_denomination_boundary():
    boundary = tx(ids("i", range(5)), ids("o", [11_000_000] * 5))
    assert is_coinjoin_wasabi_1_0(boundary)
    assert is_coinjoin_wasabi_1_1(boundary)
    outside = tx(ids("i", range(5)), ids("o", [11_000_001] * 5))
    assert not is_coinjoin_wasabi_1_0(outside)
    assert not is_coinjoin_wasabi_1_1(outside)


def test_wasabi_2_input_boundaries_and_distinct_output_ids():
    positive = tx(ids("i", [5000] * 50), ids("o", [5000] * 5))
    assert is_coinjoin_wasabi_2(positive)
    low_input = tx(ids("i", [4999] + [5000] * 49), ids("o", [5000] * 5))
    assert not is_coinjoin_wasabi_2(low_input)
    assert not is_coinjoin_wasabi_2(tx(ids("i", [5000] * 49), ids("o", [5000] * 5)))


def test_whirlpool_default_and_paper_epsilon_differ():
    feature = tx(
        ids("i", [100_000, 150_000, 150_001, 150_002, 150_003]),
        ids("o", [100_000] * 5),
    )
    assert not is_coinjoin_samourai(feature)
    assert is_coinjoin_samourai(feature, epsilon_max=100_000)
    assert f_pub_matches(feature) == ("joinmarket",)
    assert d_wp100k_matches(feature) == ("joinmarket", "whirlpool")


def test_f_pub_returns_all_operational_matches_in_fixed_order():
    feature = tx(ids("i", [5000] * 50), ids("o", [5000] * 5))
    assert f_pub_matches(feature) == ("joinmarket", "wasabi_2")


def test_f_pub_is_ordered_operational_detector_not_a_label_or_tx0_filter():
    tx0_only = tx(ids("i", [1, 2]), ids("o", [100_100, 100_100, 0, 5000]))
    assert is_tx0_paper_diagnostic(tx0_only)
    assert f_pub_matches(tx0_only) == ()
    assert not exclude_f_pub(tx0_only)
    assert not exclude_f_wide(tx0_only)
    assert exclude_f_pub(tx(ids("i", [1, 2, 3]), ids("o", [8, 8, 8])))
    with pytest.raises(TypeError, match="label"):
        TransactionFeatures((), (), (), (), label="illicit")  # type: ignore[call-arg]


def test_f_wide_requires_three_equal_outputs():
    wide_only = tx(ids("i", [1, 2]), ids("o", [4, 4, 4]))
    assert exclude_f_wide(wide_only)
    assert not exclude_f_pub(wide_only)


def test_tx0_paper_zero_fee_and_parameter_boundaries():
    candidate = tx(ids("i", [1]), ids("o", [100_100] * 70 + [0, 5000]))
    assert is_tx0_paper_diagnostic(candidate)
    too_many = tx(ids("i", [1]), ids("o", [100_100] * 71 + [0, 5000]))
    assert not is_tx0_paper_diagnostic(too_many)
    no_zero = tx(ids("i", [1]), ids("o", [100_100, 100_100, 1, 5000]))
    two_fees = tx(ids("i", [1]), ids("o", [100_100, 100_100, 0, 5000, 5000]))
    assert not is_tx0_paper_diagnostic(no_zero)
    assert not is_tx0_paper_diagnostic(two_fees)
