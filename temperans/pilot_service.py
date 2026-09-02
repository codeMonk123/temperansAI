import json
from pathlib import Path

from temperans.pilot_store import PilotStore
from temperans.redaction import Redactor
from temperans.runtime_v2 import TemperansRuntimeV2
from temperans.pilot_snapshot import TrajectorySnapshotStore
from temperans.workstate import ConversationState


class PilotService:
    def __init__(self, root=".temperans/pilot"):
        self.root = Path(root)
        self.store = PilotStore(self.root)
        self.redactor = Redactor()
        self.runtime = TemperansRuntimeV2(
            semantic_scorer=self.score,
            candidate_floor=.12,
        )
        self.snapshots = TrajectorySnapshotStore(
            self.root / "trajectories.json"
        )
        self.runtime.trajectories.update(
            self.snapshots.load()
        )

    @staticmethod
    def score(t, c):
        a = set(
            (
                t.durable_goal
                + " "
                + t.current_state
            ).lower().split()
        )
        b = set(
            (
                c.goal
                + " "
                + c.current_problem
            ).lower().split()
        )
        return (
            len(a & b) / len(a | b)
            if a and b
            else 0.0
        )

    def observe(self, data):
        r = self.redactor.redact(
            data["current_problem"]
        )

        person_id = data.get("person_id")
        if not person_id:
            raise ValueError(
                "person_id is required; identity resolution "
                "belongs to OrganizationRuntime"
            )

        state = ConversationState(
            workspace_id=data["workspace_id"],
            person_id=person_id,
            conversation_id=data["conversation_id"],
            surface=data["surface"],
            goal=data.get("goal", ""),
            current_problem=r.text,
            entities=data.get("entities", []),
            artifacts=data.get("artifacts", []),
            decisions=data.get("decisions", []),
            outcomes=data.get("outcomes", []),
            unresolved=data.get("unresolved", []),
        )

        ev = self.store.event({
            **data,
            "current_problem": r.text,
            "redacted": r.redacted,
            "redaction_categories": r.categories,
        })

        result = self.runtime.process(state)
        self.snapshots.save(
            self.runtime.trajectories
        )

        dr = self.store.decision({
            "event_record_id": ev["record_id"],
            **result.to_dict(),
        })

        options = []
        if result.decision == "clarify":
            options = [
                {
                    "action": "attach",
                    "trajectory_id": t.trajectory_id,
                    "label":
                        t.durable_goal
                        or t.current_state,
                }
                for t in self.runtime.trajectories.values()
                if (
                    t.workspace_id
                    == state.workspace_id
                    and t.person_id
                    == state.person_id
                )
            ][:5]

            options += [
                {
                    "action": "new",
                    "trajectory_id": None,
                    "label": "Start new work",
                },
                {
                    "action": "branch",
                    "trajectory_id":
                        result.trajectory_id,
                    "label":
                        "Related, but separate branch",
                },
            ]

        return {
            **result.to_dict(),
            "decision_record_id":
                dr["record_id"],
            "clarification_options":
                options,
        }

    def link_identity(self, data):
        raise RuntimeError(
            "identity linking moved to OrganizationRuntime"
        )

    def correct(self, data):
        allowed = {
            "confirm",
            "attach",
            "new",
            "branch",
            "split",
            "merge",
        }
        if data["action"] not in allowed:
            raise ValueError(
                "unsupported correction"
            )
        return self.store.correction(data)

    def corrections(self):
        return self.store.read(
            "corrections.jsonl"
        )

    def trajectory(self, trajectory_id):
        t = self.runtime.trajectories.get(
            trajectory_id
        )
        if t is None:
            return None

        x = t.to_dict()
        x["anchors"] = [
            a.to_dict()
            for a in t.anchors
        ]
        x["context_pack"] = (
            self.runtime.context
            .build(t)
            .to_dict()
        )
        return x

    def trajectories(
        self,
        workspace_id,
        person_id,
    ):
        return [
            {
                "trajectory_id":
                    t.trajectory_id,
                "goal":
                    t.durable_goal,
                "current_state":
                    t.current_state,
                "lifecycle":
                    t.lifecycle,
                "surfaces":
                    t.surfaces,
                "conversation_ids":
                    t.conversation_ids,
            }
            for t
            in self.runtime.trajectories.values()
            if (
                t.workspace_id
                == workspace_id
                and t.person_id
                == person_id
            )
        ]
