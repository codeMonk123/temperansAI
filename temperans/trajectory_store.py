import json
from pathlib import Path

from temperans.workstate import TrajectoryState


class JsonTrajectoryStore:
    """
    Simple V0 persistent trajectory store.

    One JSON file contains all trajectory states.
    Suitable for demos/local pilots, not high-scale production.
    """

    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return {}

        data = json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )

        trajectories = {}

        for item in data.get(
            "trajectories",
            [],
        ):
            state = TrajectoryState(
                trajectory_id=item[
                    "trajectory_id"
                ],
                workspace_id=item[
                    "workspace_id"
                ],
                person_id=item[
                    "person_id"
                ],
                durable_goal=item.get(
                    "durable_goal",
                    "",
                ),
                current_state=item.get(
                    "current_state",
                    "",
                ),
                lifecycle=item.get(
                    "lifecycle",
                    "active",
                ),
                entities=item.get(
                    "entities",
                    [],
                ),
                artifacts=item.get(
                    "artifacts",
                    [],
                ),
                anchors=[],
                open_questions=item.get(
                    "open_questions",
                    [],
                ),
                resolved_questions=item.get(
                    "resolved_questions",
                    [],
                ),
                decisions=item.get(
                    "decisions",
                    [],
                ),
                attempts=item.get(
                    "attempts",
                    [],
                ),
                failures=item.get(
                    "failures",
                    [],
                ),
                outcomes=item.get(
                    "outcomes",
                    [],
                ),
                surfaces=item.get(
                    "surfaces",
                    [],
                ),
                conversation_ids=item.get(
                    "conversation_ids",
                    [],
                ),
                recent_context=item.get(
                    "recent_context",
                    [],
                ),
            )

            trajectories[
                state.trajectory_id
            ] = state

        return trajectories

    def save(self, trajectories):
        payload = {
            "trajectories": [
                {
                    key: value
                    for key, value
                    in state.to_dict().items()
                    if key != "anchors"
                }
                for state
                in trajectories.values()
            ]
        }

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        temporary.replace(self.path)
