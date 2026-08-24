from fractions import Fraction

import pytest

from btcaml.analysis.flow_certificate import (
    CERTIFIED_FALSE,
    CERTIFIED_TRUE,
    UNRESOLVED,
    FlowCertificate,
    Transaction,
)


def test_sharp_single_transaction_bounds_and_thresholds():
    ledger = FlowCertificate(
        (
            Transaction(
                "mix",
                inputs=(("S", 6), ("N", 4)),
                outputs=(("X", 7), ("Y", 2)),
                fee_sats=1,
            ),
        ),
        {"S": 6},
    )

    assert ledger.interval("X") == (3, 6)
    assert ledger.interval("Y") == (0, 2)
    assert ledger.threshold_status("X", 3) == CERTIFIED_TRUE
    assert ledger.threshold_status("X", 7) == CERTIFIED_FALSE
    assert ledger.threshold_status("X", 6) == UNRESOLVED
    assert ledger.haircut_completion()["X"] == Fraction(21, 5)


def test_joint_dag_bound_preserves_conservation_coupling():
    ledger = FlowCertificate(
        (
            Transaction("split", (("A", 1), ("B", 1)), (("P", 1), ("Q", 1))),
            Transaction("left", (("P", 1),), (("D", 1),)),
            Transaction("right", (("Q", 1),), (("E", 1),)),
        ),
        {"A": 1},
    )

    assert ledger.interval("D") == (0, 1)
    assert ledger.interval("E") == (0, 1)
    assert ledger.linear_interval({"D": 1, "E": 1}) == (1, 1)
    assert ledger.difference_interval("D", "E") == (-1, 1)
    assert ledger.strict_order_status("D", "E") == UNRESOLVED


def test_deterministic_single_input_and_invalid_ledger():
    ledger = FlowCertificate(
        (Transaction("pay", (("S", 10),), (("X", 9),), fee_sats=1),), {"S": 10}
    )
    assert ledger.interval("X") == (9, 9)
    assert ledger.threshold_status("X", 9) == CERTIFIED_TRUE

    with pytest.raises(ValueError, match="not conserved"):
        FlowCertificate(
            (Transaction("broken", (("S", 10),), (("X", 8),), fee_sats=1),), {"S": 10}
        )


def test_single_transaction_bounds_match_integer_brute_force():
    capacities = {"X": 2, "Y": 3, "fee": 1}
    for source in range(1, 6):
        ledger = FlowCertificate(
            (
                Transaction(
                    "mix",
                    (("S", source), ("N", 6 - source)),
                    (("X", 2), ("Y", 3)),
                    fee_sats=1,
                ),
            ),
            {"S": source},
        )
        completions = [
            (x, y)
            for x in range(capacities["X"] + 1)
            for y in range(capacities["Y"] + 1)
            if 0 <= source - x - y <= capacities["fee"]
        ]

        assert ledger.interval("X") == (
            min(x for x, _ in completions),
            max(x for x, _ in completions),
        )
        assert ledger.interval("Y") == (
            min(y for _, y in completions),
            max(y for _, y in completions),
        )
