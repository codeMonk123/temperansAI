"""
P0 adversarial regression tests for Temperans multi-organization runtime.

Current P0 invariants:

1. Invalid API credentials cannot ingest events.
2. Organizations receive distinct credentials.
3. Organization runtime/storage is tenant isolated.
4. Same external event_id is legal across organizations.
5. Same event_id + same payload is idempotent within an organization.
6. Same event_id + different payload conflicts within an organization.
7. Duplicate ingestion does not create duplicate event/decision records.
8. Idempotency survives platform restart.
9. Partner API uses authenticated TemperansPlatform routing.
10. Partner API does not depend on legacy pilot_api.

NOTE:
The current GenericChatbotAdapter expects raw input field "message".
The future CanonicalEvent content={"text": ...} migration is a later block.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from temperans.idempotency import (
    IdempotencyConflict,
    IdempotencyStore,
)
from temperans.platform import TemperansPlatform


def _create_org(
    platform: TemperansPlatform,
    organization_id: str,
    name: str,
):
    result = platform.create_organization(
        organization_id=organization_id,
        name=name,
    )

    if isinstance(result, tuple):
        assert len(result) >= 2
        config = result[0]
        api_key = result[1]

    elif isinstance(result, dict):
        config = (
            result.get("organization")
            or result.get("config")
            or result
        )
        api_key = result.get("api_key")

    else:
        config = result
        api_key = getattr(result, "api_key", None)

    if isinstance(config, dict):
        actual_org_id = config.get("organization_id")
    else:
        actual_org_id = getattr(
            config,
            "organization_id",
            None,
        )

    if api_key is None:
        if isinstance(config, dict):
            api_key = config.get("api_key")
        else:
            api_key = getattr(
                config,
                "api_key",
                None,
            )

    assert actual_org_id == organization_id
    assert api_key

    return actual_org_id, api_key


def _event(
    event_id: str,
    *,
    user: str = "user_17",
    message: str = "hello",
    conversation_id: str = "conv_1",
    surface: str = "generic_chatbot",
):
    """
    Raw CURRENT GenericChatbotAdapter payload.

    Do not change this to content={"text": ...} during P0.
    That belongs to the CanonicalEvent/shared-observe milestone.
    """
    return {
        "event_id": event_id,
        "workspace_id": "production",
        "external_user_id": user,
        "surface": surface,
        "conversation_id": conversation_id,
        "message": message,
    }


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0

    text = path.read_text().strip()

    if not text:
        return 0

    return len(text.splitlines())


def test_unknown_api_key_is_rejected(
    tmp_path: Path,
):
    platform = TemperansPlatform(
        tmp_path / "platform"
    )

    assert (
        platform.authenticate(
            "definitely-not-a-valid-key"
        )
        is None
    )

    with pytest.raises(PermissionError):
        platform.observe_with_key(
            api_key="definitely-not-a-valid-key",
            payload=_event(
                "evt_bad_auth"
            ),
        )


def test_organizations_receive_distinct_credentials(
    tmp_path: Path,
):
    platform = TemperansPlatform(
        tmp_path / "platform"
    )

    org_a, key_a = _create_org(
        platform,
        "xyzabc321",
        "XYZABC321 Inc.",
    )

    org_b, key_b = _create_org(
        platform,
        "xyzabc322",
        "XYZABC322 Inc.",
    )

    assert org_a != org_b
    assert key_a != key_b

    auth_a = platform.authenticate(key_a)
    auth_b = platform.authenticate(key_b)

    assert auth_a is not None
    assert auth_b is not None

    assert auth_a.organization_id == org_a
    assert auth_b.organization_id == org_b


def test_runtime_storage_is_physically_tenant_scoped(
    tmp_path: Path,
):
    root = tmp_path / "platform"

    platform = TemperansPlatform(root)

    _create_org(
        platform,
        "xyzabc321",
        "XYZABC321 Inc.",
    )

    _create_org(
        platform,
        "xyzabc322",
        "XYZABC322 Inc.",
    )

    runtime_a = platform.runtime(
        "xyzabc321"
    )

    runtime_b = platform.runtime(
        "xyzabc322"
    )

    assert runtime_a.root == (
        root
        / "organizations"
        / "xyzabc321"
    )

    assert runtime_b.root == (
        root
        / "organizations"
        / "xyzabc322"
    )

    assert runtime_a.root != runtime_b.root

    assert (
        runtime_a.idempotency.path
        != runtime_b.idempotency.path
    )

    # Identity persistence is now shared SQLite. Tenant isolation is enforced
    # by organization_id in the identity primary key, not separate files.
    assert runtime_a.identities.store.path == runtime_b.identities.store.path
    assert runtime_a.identities.organization_id == "xyzabc321"
    assert runtime_b.identities.organization_id == "xyzabc322"


def test_same_event_id_is_legal_in_two_organizations(
    tmp_path: Path,
):
    """
    Current file-backed equivalent of future SQLite:

        UNIQUE (organization_id, event_id)
    """

    platform = TemperansPlatform(
        tmp_path / "platform"
    )

    org_a, key_a = _create_org(
        platform,
        "xyzabc321",
        "XYZABC321 Inc.",
    )

    org_b, key_b = _create_org(
        platform,
        "xyzabc322",
        "XYZABC322 Inc.",
    )

    payload_a = _event(
        "evt_shared_001",
        user="same_external_user",
        message=(
            "Investigate PROD-218 "
            "for organization A"
        ),
    )

    payload_b = _event(
        "evt_shared_001",
        user="same_external_user",
        message=(
            "Prepare pricing analysis "
            "for organization B"
        ),
    )

    result_a = platform.observe_with_key(
        api_key=key_a,
        payload=payload_a,
    )

    result_b = platform.observe_with_key(
        api_key=key_b,
        payload=payload_b,
    )

    assert result_a["organization_id"] == org_a
    assert result_b["organization_id"] == org_b

    assert (
        result_a["event_id"]
        == "evt_shared_001"
    )

    assert (
        result_b["event_id"]
        == "evt_shared_001"
    )

    runtime_a = platform.runtime(org_a)
    runtime_b = platform.runtime(org_b)

    cached_a = (
        runtime_a.idempotency.lookup(
            "evt_shared_001",
            payload_a,
        )
    )

    cached_b = (
        runtime_b.idempotency.lookup(
            "evt_shared_001",
            payload_b,
        )
    )

    assert cached_a == result_a
    assert cached_b == result_b

    # A's payload must not exist in B's idempotency domain.
    with pytest.raises(
        IdempotencyConflict
    ):
        runtime_b.idempotency.lookup(
            "evt_shared_001",
            payload_a,
        )

    # B's payload must not exist in A's idempotency domain.
    with pytest.raises(
        IdempotencyConflict
    ):
        runtime_a.idempotency.lookup(
            "evt_shared_001",
            payload_b,
        )


def test_duplicate_observe_does_not_mutate_twice(
    tmp_path: Path,
):
    """
    Critical A2 regression.

    First observation may mutate trajectory/event/decision state.

    Repeating the exact event must return the cached result BEFORE
    PilotService.observe() is called again.
    """

    platform = TemperansPlatform(
        tmp_path / "platform"
    )

    org_id, api_key = _create_org(
        platform,
        "xyzabc321",
        "XYZABC321 Inc.",
    )

    payload = _event(
        "evt_duplicate_001",
        user="user_17",
        message=(
            "Help me investigate PROD-218"
        ),
    )

    first = platform.observe_with_key(
        api_key=api_key,
        payload=payload,
    )

    runtime = platform.runtime(org_id)

    events_path = (
        runtime.root
        / "events.jsonl"
    )

    decisions_path = (
        runtime.root
        / "decisions.jsonl"
    )

    events_before = _line_count(
        events_path
    )

    decisions_before = _line_count(
        decisions_path
    )

    trajectories_before = {
        trajectory_id:
            trajectory.to_dict()
        for trajectory_id, trajectory
        in runtime.service.runtime.trajectories.items()
    }

    second = platform.observe_with_key(
        api_key=api_key,
        payload=payload,
    )

    events_after = _line_count(
        events_path
    )

    decisions_after = _line_count(
        decisions_path
    )

    trajectories_after = {
        trajectory_id:
            trajectory.to_dict()
        for trajectory_id, trajectory
        in runtime.service.runtime.trajectories.items()
    }

    assert second == first

    assert events_after == events_before
    assert decisions_after == decisions_before

    assert (
        trajectories_after
        == trajectories_before
    )


def test_duplicate_event_different_payload_conflicts_at_runtime(
    tmp_path: Path,
):
    platform = TemperansPlatform(
        tmp_path / "platform"
    )

    _org_id, api_key = _create_org(
        platform,
        "xyzabc321",
        "XYZABC321 Inc.",
    )

    first = _event(
        "evt_conflict_001",
        message="original payload",
    )

    conflicting = _event(
        "evt_conflict_001",
        message="different payload",
    )

    platform.observe_with_key(
        api_key=api_key,
        payload=first,
    )

    with pytest.raises(
        IdempotencyConflict
    ):
        platform.observe_with_key(
            api_key=api_key,
            payload=conflicting,
        )


def test_idempotency_store_same_payload_returns_original(
    tmp_path: Path,
):
    store = IdempotencyStore(
        tmp_path / "idempotency.json"
    )

    payload = _event(
        "evt_001",
        message="same payload",
    )

    first_result = {
        "decision_id": "dec_1",
        "trajectory_id": "traj_1",
    }

    committed = store.commit(
        "evt_001",
        payload,
        first_result,
    )

    assert committed == first_result

    second_result = {
        "decision_id":
            "dec_SHOULD_NOT_REPLACE",
        "trajectory_id":
            "traj_SHOULD_NOT_REPLACE",
    }

    duplicate = store.commit(
        "evt_001",
        payload,
        second_result,
    )

    assert duplicate == first_result


def test_idempotency_store_different_payload_conflicts(
    tmp_path: Path,
):
    store = IdempotencyStore(
        tmp_path / "idempotency.json"
    )

    first = _event(
        "evt_001",
        message="original",
    )

    conflicting = _event(
        "evt_001",
        message="different",
    )

    store.commit(
        "evt_001",
        first,
        {"ok": True},
    )

    with pytest.raises(
        IdempotencyConflict
    ):
        store.lookup(
            "evt_001",
            conflicting,
        )


def test_idempotency_survives_platform_restart(
    tmp_path: Path,
):
    root = tmp_path / "platform"

    first_platform = TemperansPlatform(
        root
    )

    org_id, api_key = _create_org(
        first_platform,
        "xyzabc321",
        "XYZABC321 Inc.",
    )

    payload = _event(
        "evt_restart_001",
        message="persist this event",
    )

    first_result = (
        first_platform.observe_with_key(
            api_key=api_key,
            payload=payload,
        )
    )

    second_platform = TemperansPlatform(
        root
    )

    authenticated = (
        second_platform.authenticate(
            api_key
        )
    )

    assert authenticated is not None

    assert (
        authenticated.organization_id
        == org_id
    )

    second_result = (
        second_platform.observe_with_key(
            api_key=api_key,
            payload=payload,
        )
    )

    assert second_result == first_result


def test_partner_api_uses_platform_authentication():
    import temperans.partner_api as partner_api

    source = inspect.getsource(
        partner_api
    )

    assert "TemperansPlatform" in source
    assert ".authenticate(" in source

    forbidden = (
        (
            "from temperans.pilot_service "
            "import PilotService"
        ),
        "import PilotService",
    )

    for token in forbidden:
        assert token not in source


def test_partner_api_does_not_import_legacy_pilot_api():
    import temperans.partner_api as partner_api

    source = inspect.getsource(
        partner_api
    )

    assert "pilot_api" not in source


def test_idempotency_file_is_valid_json(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "idempotency.json"
    )

    store = IdempotencyStore(path)

    payload = _event("evt_json")

    store.commit(
        "evt_json",
        payload,
        {"ok": True},
    )

    import json

    data = json.loads(
        path.read_text()
    )

    assert "evt_json" in data

    assert (
        data["evt_json"]["result"]
        == {"ok": True}
    )


def test_legacy_pilot_api_is_decommissioned():
    """
    A1 regression guard.

    The legacy unauthenticated server may remain as a migration tombstone,
    but it must be impossible to start as a working HTTP API.
    """
    import temperans.pilot_api as pilot_api

    assert pilot_api.DECOMMISSIONED is True

    with pytest.raises(
        RuntimeError,
        match="decommissioned",
    ):
        pilot_api.main()
