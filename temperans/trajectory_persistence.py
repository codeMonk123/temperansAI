"""Trajectory serialization and structural state-delta utilities."""

from copy import deepcopy

from temperans.anchors import Anchor, AnchorStrength
from temperans.workstate import TrajectoryState


STRUCTURAL_FIELDS = (
    "durable_goal",
    "current_state",
    "lifecycle",
    "entities",
    "artifacts",
    "anchors",
    "open_questions",
    "resolved_questions",
    "decisions",
    "attempts",
    "failures",
    "outcomes",
    "surfaces",
    "conversation_ids",
    "recent_context",
)


def serialize_trajectory(t):
    x = t.to_dict()
    x["anchors"] = [
        a.to_dict() if hasattr(a, "to_dict") else a
        for a in t.anchors
    ]
    return x


def deserialize_trajectory(x):
    anchors = []

    for a in x.get("anchors", []):
        if isinstance(a, Anchor):
            anchors.append(a)
        else:
            anchors.append(
                Anchor(
                    type=a["type"],
                    value=a["value"],
                    strength=AnchorStrength(a["strength"]),
                )
            )

    return TrajectoryState(
        trajectory_id=x["trajectory_id"],
        workspace_id=x["workspace_id"],
        person_id=x["person_id"],
        durable_goal=x.get("durable_goal", ""),
        current_state=x.get("current_state", ""),
        lifecycle=x.get("lifecycle", "active"),
        entities=x.get("entities", []),
        artifacts=x.get("artifacts", []),
        anchors=anchors,
        open_questions=x.get("open_questions", []),
        resolved_questions=x.get("resolved_questions", []),
        decisions=x.get("decisions", []),
        attempts=x.get("attempts", []),
        failures=x.get("failures", []),
        outcomes=x.get("outcomes", []),
        surfaces=x.get("surfaces", []),
        conversation_ids=x.get("conversation_ids", []),
        recent_context=x.get("recent_context", []),
    )


def snapshot(trajectories):
    return {
        trajectory_id: deepcopy(
            serialize_trajectory(trajectory)
        )
        for trajectory_id, trajectory
        in trajectories.items()
    }


def structural_delta(
    before,
    after,
    trajectory_id,
):
    previous = before.get(trajectory_id)
    current = after.get(trajectory_id)

    if current is None:
        return {}

    if previous is None:
        fields = {
            field: {
                "from": None,
                "to": deepcopy(current.get(field)),
            }
            for field in STRUCTURAL_FIELDS
            if current.get(field) not in (
                None,
                "",
                [],
                {},
            )
        }

        return {
            "trajectory_created": True,
            "fields": fields,
        }

    fields = {}

    for field in STRUCTURAL_FIELDS:
        if previous.get(field) != current.get(field):
            fields[field] = {
                "from": deepcopy(
                    previous.get(field)
                ),
                "to": deepcopy(
                    current.get(field)
                ),
            }

    if not fields:
        return {}

    return {
        "fields": fields,
    }
