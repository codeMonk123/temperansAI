"""Frozen ingestion-equivalence contract for Temperans Phase 1.

This module does not implement historical import or replay. It defines the
comparison surface those implementations must satisfy.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from temperans.state_normalization import (
    NORMALIZATION_VERSION,
    compare_normalized,
    normalized_trajectory_set,
)

EQUIVALENCE_CONTRACT_VERSION = "ingestion-equivalence-v1"
REQUIRED_PATHS = ("live", "import", "replay")


@dataclass(frozen=True)
class IngestionState:
    path: str
    trajectories: object
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.path not in REQUIRED_PATHS:
            raise ValueError(
                f"unsupported ingestion path: {self.path}"
            )

    def normalized(self):
        return normalized_trajectory_set(
            self.trajectories
        )


@dataclass(frozen=True)
class EquivalenceReport:
    equivalent: bool
    contract_version: str
    normalization_version: str
    pair_reports: dict
    path_metadata: dict

    def to_dict(self):
        return {
            "equivalent": self.equivalent,
            "contract_version": self.contract_version,
            "normalization_version": self.normalization_version,
            "pair_reports": self.pair_reports,
            "path_metadata": self.path_metadata,
        }


def compare_ingestion_states(*, live, imported, replayed):
    states = {
        "live": live,
        "import": imported,
        "replay": replayed,
    }

    for expected, state in states.items():
        if not isinstance(state, IngestionState):
            raise TypeError(
                f"{expected} must be IngestionState"
            )
        if state.path != expected:
            raise ValueError(
                f"expected path {expected}, got {state.path}"
            )

    pairs = {
        "live_vs_import": compare_normalized(
            live.trajectories,
            imported.trajectories,
        ),
        "live_vs_replay": compare_normalized(
            live.trajectories,
            replayed.trajectories,
        ),
        "import_vs_replay": compare_normalized(
            imported.trajectories,
            replayed.trajectories,
        ),
    }

    return EquivalenceReport(
        equivalent=all(
            report["equivalent"]
            for report in pairs.values()
        ),
        contract_version=EQUIVALENCE_CONTRACT_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        pair_reports=pairs,
        path_metadata={
            name: dict(state.metadata)
            for name, state in states.items()
        },
    )


def assert_ingestion_equivalent(*, live, imported, replayed):
    report = compare_ingestion_states(
        live=live,
        imported=imported,
        replayed=replayed,
    )

    if not report.equivalent:
        differences = {
            pair: value["differences"]
            for pair, value
            in report.pair_reports.items()
            if not value["equivalent"]
        }
        raise AssertionError(
            "ingestion paths are not equivalent: "
            + repr(differences)
        )

    return report
