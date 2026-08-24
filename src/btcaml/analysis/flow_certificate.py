"""Ledger-only source-flow certificates for the N1 Gate-2 pilot."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction

import networkx as nx

CERTIFIED_TRUE = "certified_true"
CERTIFIED_FALSE = "certified_false"
UNRESOLVED = "unresolved_under_ledger_only_provenance"


@dataclass(frozen=True)
class Transaction:
    txid: str
    inputs: tuple[tuple[str, int], ...]
    outputs: tuple[tuple[str, int], ...]
    fee_sats: int = 0


class FlowCertificate:
    """Exact integer min-cost-flow bounds for one fixed source set."""

    _SOURCE = "__source__"
    _SINK = "__sink__"

    def __init__(self, transactions: tuple[Transaction, ...], seeds: Mapping[str, int]):
        self.transactions = transactions
        self.seeds = dict(seeds)
        self._values, self._producer, spent = self._validate()
        self._graph, self._objective_edges = self._build_graph(spent)

    @staticmethod
    def _utxo(outpoint: str) -> str:
        return f"utxo:{outpoint}"

    @staticmethod
    def _tx(txid: str) -> str:
        return f"tx:{txid}"

    def _validate(self) -> tuple[dict[str, int], dict[str, tuple[int, str]], set[str]]:
        if not self.seeds:
            raise ValueError("at least one source seed is required")

        txids: set[str] = set()
        values: dict[str, int] = {}
        producer: dict[str, tuple[int, str]] = {}
        for index, tx in enumerate(self.transactions):
            if not tx.txid or tx.txid in txids:
                raise ValueError(f"invalid or duplicate txid: {tx.txid!r}")
            txids.add(tx.txid)
            if tx.fee_sats < 0:
                raise ValueError(f"negative fee in {tx.txid}")
            for outpoint, value in tx.outputs:
                self._check_value(outpoint, value)
                if outpoint in producer:
                    raise ValueError(f"duplicate output: {outpoint}")
                producer[outpoint] = (index, tx.txid)
                values[outpoint] = value

        spent: set[str] = set()
        for index, tx in enumerate(self.transactions):
            if not tx.inputs:
                raise ValueError(f"coinbase/empty-input transaction is outside the pilot: {tx.txid}")
            input_total = 0
            for outpoint, value in tx.inputs:
                self._check_value(outpoint, value)
                if outpoint in spent:
                    raise ValueError(f"double-spent input in pilot DAG: {outpoint}")
                spent.add(outpoint)
                input_total += value
                if outpoint in producer:
                    parent_index, _ = producer[outpoint]
                    if parent_index >= index:
                        raise ValueError(f"non-causal input edge: {outpoint} -> {tx.txid}")
                    if values[outpoint] != value:
                        raise ValueError(f"value mismatch for {outpoint}")
                else:
                    values.setdefault(outpoint, value)
                    if values[outpoint] != value:
                        raise ValueError(f"inconsistent external input value: {outpoint}")
            output_total = sum(value for _, value in tx.outputs)
            if input_total != output_total + tx.fee_sats:
                raise ValueError(f"value is not conserved in {tx.txid}")

        for outpoint, value in self.seeds.items():
            self._check_value(outpoint, value)
            if outpoint not in values or values[outpoint] != value:
                raise ValueError(f"unknown or mismatched source seed: {outpoint}")
            if outpoint in producer:
                raise ValueError(f"seed must be a boundary UTXO, not an included output: {outpoint}")
        return values, producer, spent

    @staticmethod
    def _check_value(outpoint: str, value: int) -> None:
        if not outpoint or isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"invalid positive-satoshi UTXO: {(outpoint, value)!r}")

    def _build_graph(
        self, spent: set[str]
    ) -> tuple[nx.DiGraph, dict[str, tuple[str, str]]]:
        graph = nx.DiGraph()
        total_source = sum(self.seeds.values())
        graph.add_node(self._SOURCE, demand=-total_source)
        graph.add_node(self._SINK, demand=total_source)
        objective_edges: dict[str, tuple[str, str]] = {}

        for outpoint, value in self.seeds.items():
            edge = (self._SOURCE, self._utxo(outpoint))
            graph.add_edge(*edge, capacity=value, weight=0)
            objective_edges[outpoint] = edge

        for tx in self.transactions:
            tx_node = self._tx(tx.txid)
            for outpoint, value in tx.inputs:
                graph.add_edge(self._utxo(outpoint), tx_node, capacity=value, weight=0)
            for outpoint, value in tx.outputs:
                edge = (tx_node, self._utxo(outpoint))
                graph.add_edge(*edge, capacity=value, weight=0)
                objective_edges[outpoint] = edge
            if tx.fee_sats:
                graph.add_edge(tx_node, self._SINK, capacity=tx.fee_sats, weight=0)

        terminal_outpoints = (set(self._producer) | set(self.seeds)) - spent
        for outpoint in terminal_outpoints:
            graph.add_edge(
                self._utxo(outpoint), self._SINK, capacity=self._values[outpoint], weight=0
            )
        return graph, objective_edges

    def linear_interval(self, coefficients: Mapping[str, int]) -> tuple[int, int]:
        clean = {outpoint: coefficient for outpoint, coefficient in coefficients.items() if coefficient}
        for outpoint, coefficient in clean.items():
            if outpoint not in self._objective_edges:
                raise KeyError(outpoint)
            if isinstance(coefficient, bool) or not isinstance(coefficient, int):
                raise TypeError("certificate coefficients must be integers")
        lower = self._optimize(clean, minimize=True)
        upper = self._optimize(clean, minimize=False)
        return lower, upper

    def interval(self, outpoint: str) -> tuple[int, int]:
        return self.linear_interval({outpoint: 1})

    def difference_interval(self, left: str, right: str) -> tuple[int, int]:
        if left == right:
            return 0, 0
        return self.linear_interval({left: 1, right: -1})

    def threshold_status(self, outpoint: str, threshold_sats: int) -> str:
        if threshold_sats < 0:
            raise ValueError("threshold must be non-negative")
        lower, upper = self.interval(outpoint)
        if lower >= threshold_sats:
            return CERTIFIED_TRUE
        if upper < threshold_sats:
            return CERTIFIED_FALSE
        return UNRESOLVED

    def strict_order_status(self, left: str, right: str) -> str:
        lower, upper = self.difference_interval(left, right)
        if lower > 0:
            return CERTIFIED_TRUE
        if upper < 0:
            return CERTIFIED_FALSE
        return UNRESOLVED

    def _optimize(self, coefficients: Mapping[str, int], minimize: bool) -> int:
        graph = self._graph.copy()
        direction = 1 if minimize else -1
        for outpoint, coefficient in coefficients.items():
            source, target = self._objective_edges[outpoint]
            graph[source][target]["weight"] = direction * coefficient
        _, flow = nx.network_simplex(graph)
        value = sum(
            coefficient * flow[source][target]
            for outpoint, coefficient in coefficients.items()
            for source, target in [self._objective_edges[outpoint]]
        )
        return int(value)

    def haircut_completion(self) -> dict[str, Fraction]:
        """Deterministic proportional point baseline, not a certificate."""
        source_mass = {outpoint: Fraction(value) for outpoint, value in self.seeds.items()}
        for tx in self.transactions:
            input_total = sum(value for _, value in tx.inputs)
            source_total = sum(source_mass.get(outpoint, Fraction()) for outpoint, _ in tx.inputs)
            for outpoint, value in tx.outputs:
                source_mass[outpoint] = source_total * value / input_total
        return source_mass
