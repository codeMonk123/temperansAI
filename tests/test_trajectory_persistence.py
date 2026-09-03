from temperans.trajectory_persistence import (
    structural_delta,
)


def test_structural_delta_only_records_changed_fields():
    before = {
        "t": {
            "durable_goal": "g",
            "current_state": "old",
            "lifecycle": "active",
            "surfaces": ["slack"],
        }
    }

    after = {
        "t": {
            "durable_goal": "g",
            "current_state": "new",
            "lifecycle": "active",
            "surfaces": [
                "slack",
                "chat",
            ],
        }
    }

    delta = structural_delta(
        before,
        after,
        "t",
    )

    assert set(
        delta["fields"]
    ) == {
        "current_state",
        "surfaces",
    }

    assert delta["fields"]["current_state"] == {
        "from": "old",
        "to": "new",
    }


def test_new_trajectory_is_explicit():
    after = {
        "t": {
            "durable_goal": "goal",
            "current_state": "problem",
            "lifecycle": "active",
            "surfaces": ["slack"],
        }
    }

    delta = structural_delta(
        {},
        after,
        "t",
    )

    assert (
        delta["trajectory_created"]
        is True
    )

    assert (
        delta["fields"]["durable_goal"]["to"]
        == "goal"
    )
