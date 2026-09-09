"""Frozen operational collaborative-transaction filters for as-of replay.

These rules reproduce the five fixed BTCGraphConstruction mix detectors.  A
match is an operational detector result, never a CoinJoin ground-truth label.
"""

from __future__ import annotations

from dataclasses import dataclass

UPSTREAM_REVISION = "3becbc44a951abbe1e85d374a66340a639059d1c"
WASABI_2_DENOMINATIONS = (
    5000, 6561, 8192, 10000, 13122, 16384, 19683, 20000, 32768, 39366, 50000, 59049,
    65536, 100000, 118098, 131072, 177147, 200000, 262144, 354294, 500000, 524288,
    531441, 1000000, 1048576, 1062882, 1594323, 2000000, 2097152, 3188646, 4194304,
    4782969, 5000000, 8388608, 9565938, 10000000, 14348907, 16777216, 20000000,
    28697814, 33554432, 43046721, 50000000, 67108864, 86093442, 100000000, 129140163,
    134217728, 200000000, 258280326, 268435456, 387420489, 500000000, 536870912,
    774840978, 1000000000, 1073741824, 1162261467, 2000000000, 2147483648, 2324522934,
    3486784401, 4294967296, 5000000000, 6973568802, 8589934592, 10000000000,
    10460353203, 17179869184, 20000000000, 20920706406, 31381059609, 34359738368,
    50000000000, 62762119218, 68719476736, 94143178827, 100000000000, 137438953472,
)
_SAMOURAI_POOLS = {100000: 5000, 1000000: 50000, 5000000: 175000, 50000000: 1750000}


def _validate_side(name: str, script_ids: tuple[str, ...], values: tuple[int, ...]) -> None:
    if not isinstance(script_ids, tuple) or not isinstance(values, tuple):
        raise TypeError(f"{name} script IDs and values must be tuples")
    if len(script_ids) != len(values):
        raise ValueError(f"{name} script IDs and values must have equal length")
    if any(not isinstance(script_id, str) or not script_id for script_id in script_ids):
        raise ValueError(f"{name} script IDs must be non-empty strings")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
        raise ValueError(f"{name} values must be non-negative integer satoshis")


@dataclass(frozen=True)
class TransactionFeatures:
    """Paired script/value transaction inputs and outputs, including duplicates."""

    input_script_ids: tuple[str, ...]
    input_values: tuple[int, ...]
    output_script_ids: tuple[str, ...]
    output_values_raw: tuple[int, ...]

    def __post_init__(self) -> None:
        _validate_side("input", self.input_script_ids, self.input_values)
        _validate_side("output", self.output_script_ids, self.output_values_raw)

    @property
    def num_inputs(self) -> int:
        return len(self.input_script_ids)

    @property
    def num_outputs(self) -> int:
        return len(self.output_script_ids)

    @property
    def num_input_ids(self) -> int:
        return len(set(self.input_script_ids))

    @property
    def num_output_ids(self) -> int:
        return len(set(self.output_script_ids))

    @property
    def output_value_counts(self) -> tuple[tuple[int, int], ...]:
        """Value/count pairs: count descending, then value ascending on ties."""
        counts: dict[int, int] = {}
        for value in self.output_values_raw:
            counts[value] = counts.get(value, 0) + 1
        return tuple(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))

    @property
    def output_values(self) -> tuple[int, ...]:
        return tuple(value for value, _ in self.output_value_counts)

    @property
    def occ_output_values(self) -> tuple[int, ...]:
        return tuple(count for _, count in self.output_value_counts)

    @property
    def occ_most_represented_output_value(self) -> int | None:
        return self.occ_output_values[0] if self.occ_output_values else None


def is_coinjoin_joinmarket(features: TransactionFeatures, min_num_participants: int = 3) -> bool:
    anonymity_set = features.occ_most_represented_output_value
    if anonymity_set is None or anonymity_set < min_num_participants:
        return False
    if anonymity_set < features.num_outputs / 2 or anonymity_set > features.num_input_ids:
        return False
    return features.num_output_ids == features.num_outputs


def is_coinjoin_wasabi_1_0(
    features: TransactionFeatures, epsilon: int = 1_000_000,
    max_inputs_per_participants: int = 7, min_num_participants: int = 5,
) -> bool:
    anonymity_set = features.occ_most_represented_output_value
    if (
        anonymity_set is None
        or anonymity_set < min_num_participants
        or anonymity_set > features.num_input_ids
    ):
        return False
    if features.num_inputs > max_inputs_per_participants * anonymity_set:
        return False
    if (
        anonymity_set < (features.num_outputs - 1) / 2
        or features.num_output_ids < features.num_outputs
    ):
        return False
    denomination = min(
        (value for value, count in features.output_value_counts if count == anonymity_set),
        key=lambda value: abs(value - 10_000_000),
    )
    return 10_000_000 - epsilon <= denomination <= 10_000_000 + epsilon


def is_coinjoin_wasabi_1_1(
    features: TransactionFeatures, epsilon: int = 1_000_000,
    max_inputs_per_participants: int = 7, min_num_participants: int = 5,
    max_mixing_level: int = 12,
) -> bool:
    anonymity_set = features.occ_most_represented_output_value
    if (
        anonymity_set is None
        or anonymity_set < min_num_participants
        or anonymity_set > features.num_input_ids
    ):
        return False
    if (
        features.num_inputs > max_inputs_per_participants * anonymity_set
        or features.num_output_ids < features.num_outputs
    ):
        return False
    possible = [
        (value, count)
        for value, count in features.output_value_counts
        if count == anonymity_set
    ]
    denomination, count = min(possible, key=lambda pair: abs(pair[0] - 10_000_000))
    if not 10_000_000 - epsilon <= denomination <= 10_000_000 + epsilon:
        return False
    post_mix = count
    for level in range(1, max_mixing_level):
        lower, upper = 2**level * (10_000_000 - epsilon), 2**level * (10_000_000 + epsilon)
        post_mix += sum(
            count for value, count in features.output_value_counts if lower <= value <= upper
        )
    return post_mix >= features.num_outputs - anonymity_set - 1


def is_coinjoin_wasabi_2(
    features: TransactionFeatures, max_inputs_per_participants: int = 10,
    min_num_inputs: int = 50, min_input_value: int = 5000,
) -> bool:
    if features.num_inputs < min_num_inputs or not set(features.input_values):
        return False
    if (
        min(features.input_values) < min_input_value
        or features.num_output_ids < features.num_outputs
    ):
        return False
    post_mix = sum(
        count
        for value, count in features.output_value_counts
        if value in WASABI_2_DENOMINATIONS
    )
    return (
        post_mix >= (features.num_outputs - 1) / 2
        and post_mix >= features.num_inputs / max_inputs_per_participants
    )


def is_coinjoin_samourai(features: TransactionFeatures, epsilon_max: int = 20_000) -> bool:
    if (features.num_inputs != 5 or features.num_input_ids != 5 or features.num_outputs != 5
            or features.num_output_ids != 5 or len(features.output_values) > 1):
        return False
    denomination = features.output_values[0]
    if denomination not in _SAMOURAI_POOLS:
        return False
    found_post_mix = found_pre_mix = False
    for value in set(features.input_values):
        if value < denomination or value > denomination + epsilon_max:
            return False
        found_post_mix |= value == denomination
        found_pre_mix |= value != denomination
    return found_post_mix and found_pre_mix


def f_pub_matches(
    features: TransactionFeatures, *, samourai_epsilon_max: int = 20_000
) -> tuple[str, ...]:
    """Ordered matches for fixed-revision operational detectors; excludes Tx0."""
    checks = (
        ("joinmarket", is_coinjoin_joinmarket(features, min_num_participants=3)),
        (
            "wasabi_1_0",
            is_coinjoin_wasabi_1_0(
                features,
                epsilon=1_000_000,
                max_inputs_per_participants=7,
                min_num_participants=5,
            ),
        ),
        (
            "wasabi_1_1",
            is_coinjoin_wasabi_1_1(
                features,
                epsilon=1_000_000,
                max_inputs_per_participants=7,
                min_num_participants=5,
                max_mixing_level=12,
            ),
        ),
        (
            "wasabi_2",
            is_coinjoin_wasabi_2(
                features,
                max_inputs_per_participants=10,
                min_num_inputs=50,
                min_input_value=5000,
            ),
        ),
        ("whirlpool", is_coinjoin_samourai(features, epsilon_max=samourai_epsilon_max)),
    )
    return tuple(name for name, matched in checks if matched)


def exclude_f_pub(features: TransactionFeatures) -> bool:
    """Whether F_pub operationally excludes this transaction."""
    return bool(f_pub_matches(features))


def exclude_f_wide(features: TransactionFeatures) -> bool:
    """Whether F_wide operationally excludes this transaction."""
    return exclude_f_pub(features) or (
        features.num_inputs >= 2 and features.num_outputs >= 3
        and features.occ_most_represented_output_value is not None
        and features.occ_most_represented_output_value >= 3
    )


def d_wp100k_matches(features: TransactionFeatures) -> tuple[str, ...]:
    """D_wp100k diagnostic F_pub matches with only Whirlpool epsilon changed."""
    return f_pub_matches(features, samourai_epsilon_max=100_000)


def is_tx0_paper_diagnostic(
    features: TransactionFeatures, a_max: int = 70, eta1: float = 0.5,
    eta2: float = 3, epsilon_min: int = 100, epsilon_max: int = 100_000,
) -> bool:
    """Paper-parameter Tx0 necessary-condition candidate, not an exclusion or truth label."""
    candidate: tuple[int, int, int] | None = None
    for value, count in features.output_value_counts:
        for denomination in _SAMOURAI_POOLS:
            if (
                denomination + epsilon_min <= value <= denomination + epsilon_max
                and (
                    candidate is None
                    or count > candidate[1]
                    or (count == candidate[1] and value > candidate[0])
                )
            ):
                candidate = (value, count, denomination)
    if candidate is None:
        return False
    _, premix_count, denomination = candidate
    if premix_count < features.num_outputs - 3 or not 1 <= premix_count <= a_max:
        return False
    if sum(value == 0 for value in features.output_values_raw) != 1:
        return False
    fee = _SAMOURAI_POOLS[denomination]
    return sum(eta1 * fee <= value <= eta2 * fee for value in features.output_values_raw) == 1
