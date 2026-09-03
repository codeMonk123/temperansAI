import pytest

from temperans.ingestion_equivalence import (
    EQUIVALENCE_CONTRACT_VERSION,
    IngestionState,
    assert_ingestion_equivalent,
    compare_ingestion_states,
)
from temperans.state_normalization import (
    NORMALIZATION_VERSION,
)


def trajectory(
    *,
    trajectory_id,
    current_state="certificate mismatch",
    version=1,
):
    return {
        "trajectory_id": trajectory_id,
        "workspace_id": "production",
        "person_id": "person_1",
        "durable_goal": "restore production",
        "current_state": current_state,
        "lifecycle": "active",
        "entities": ["service"],
        "artifacts": [],
        "anchors": [
            {
                "type": "ticket",
                "value": "PROD-218",
                "strength": "strong",
            }
        ],
        "open_questions": [],
        "resolved_questions": [],
        "decisions": [],
        "attempts": [],
        "failures": [],
        "outcomes": [],
        "surfaces": ["chat", "slack"],
        "conversation_ids": ["c1", "c2"],
        "recent_context": [
            "deployment failed",
            "certificate mismatch",
        ],
        "trajectory_version": version,
        "updated_at": "incidental timestamp",
    }


def state(path, item, **metadata):
    return IngestionState(
        path=path,
        trajectories=[item],
        metadata=metadata,
    )


def test_equivalence_contract_ignores_generated_identity_and_version():
    live = state(
        "live",
        trajectory(
            trajectory_id="traj_live",
            version=9,
        ),
    )

    imported = state(
        "import",
        trajectory(
            trajectory_id="traj_import",
            version=1,
        ),
    )

    replayed = state(
        "replay",
        trajectory(
            trajectory_id="traj_replay",
            version=42,
        ),
    )

    report = assert_ingestion_equivalent(
        live=live,
        imported=imported,
        replayed=replayed,
    )

    assert report.equivalent is True
    assert (
        report.contract_version
        == EQUIVALENCE_CONTRACT_VERSION
    )
    assert (
        report.normalization_version
        == NORMALIZATION_VERSION
    )


def test_equivalence_contract_detects_meaningful_state_difference():
    live = state(
        "live",
        trajectory(
            trajectory_id="traj_live",
        ),
    )

    imported = state(
        "import",
        trajectory(
            trajectory_id="traj_import",
            current_state="healthy",
        ),
    )

    replayed = state(
        "replay",
        trajectory(
            trajectory_id="traj_replay",
        ),
    )

    report = compare_ingestion_states(
        live=live,
        imported=imported,
        replayed=replayed,
    )

    assert report.equivalent is False

    fields = {
        difference["field"]
        for difference
        in report.pair_reports[
            "live_vs_import"
        ]["differences"]
    }

    assert "current_state" in fields

    with pytest.raises(AssertionError):
        assert_ingestion_equivalent(
            live=live,
            imported=imported,
            replayed=replayed,
        )


def test_path_labels_are_part_of_contract():
    with pytest.raises(ValueError):
        IngestionState(
            path="historical_magic_path",
            trajectories=[],
        )


def test_compare_rejects_swapped_path_objects():
    item = trajectory(
        trajectory_id="t",
    )

    with pytest.raises(ValueError):
        compare_ingestion_states(
            live=state("import", item),
            imported=state("live", item),
            replayed=state("replay", item),
        )


def test_equivalence_metadata_is_preserved_but_not_compared():
    item = trajectory(
        trajectory_id="t",
    )

    report = assert_ingestion_equivalent(
        live=state(
            "live",
            item,
            run_id="live-123",
        ),
        imported=state(
            "import",
            item,
            run_id="import-456",
        ),
        replayed=state(
            "replay",
            item,
            run_id="replay-789",
        ),
    )

    assert report.equivalent is True
    assert (
        report.path_metadata["live"]["run_id"]
        == "live-123"
    )
