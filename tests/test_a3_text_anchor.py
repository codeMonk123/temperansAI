import inspect

from temperans.platform import TemperansPlatform
from temperans.workstate_extractor_v1 import WorkStateExtractor


def test_text_only_ticket_becomes_workstate_anchor():
    work = WorkStateExtractor().extract(
        text="Investigate ticket PROD-218 after restart"
    )
    pairs = {(a.type, a.value) for a in work.anchors}
    assert ("ticket", "PROD-218") in pairs


def test_extractor_cannot_receive_trajectory_context():
    signature = inspect.signature(WorkStateExtractor.extract)
    assert "trajectory_context" not in signature.parameters


def test_a3_text_only_anchor_attaches_through_real_partner_path(tmp_path):
    platform = TemperansPlatform(tmp_path / "platform")
    created = platform.create_organization(
        organization_id="xyzabc321",
        name="XYZABC321 Inc.",
    )
    key = created["api_key"]

    first = platform.observe_with_key(
        api_key=key,
        payload={
            "event_id": "a3_1",
            "workspace_id": "production",
            "external_user_id": "user_17",
            "surface": "generic_chatbot",
            "conversation_id": "conv_1",
            "message": "Ticket PROD-218 deployment is failing during startup",
        },
    )

    second = platform.observe_with_key(
        api_key=key,
        payload={
            "event_id": "a3_2",
            "workspace_id": "production",
            "external_user_id": "user_17",
            "surface": "generic_chatbot",
            "conversation_id": "conv_2",
            "message": "PROD-218 now shows a certificate mismatch after restart",
        },
    )

    assert second["source"] not in {"no_candidates", "candidate_retrieval"}
    assert second["trajectory_id"] == first["trajectory_id"]
    assert second["decision"] == "attach"

    trajectory = platform.runtime("xyzabc321").service.trajectory(
        first["trajectory_id"]
    )
    anchors = {(a["type"], a["value"]) for a in trajectory["anchors"]}
    assert ("ticket", "PROD-218") in anchors
