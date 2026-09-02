from dataclasses import dataclass

from temperans import TrajectoryStore
from temperans.router import TrajectoryRouter


@dataclass
class FakeGoalState:
    text: str
    intent: str = "other"

    @property
    def summary(self):
        return self.text

    def routing_text(self):
        return self.text


class FakeSemanticGoalExtractor:
    """
    Deterministic semantic normalizer for CI.

    It simulates provider-independent GoalState extraction
    without making external API calls.
    """

    def extract(self, text):
        lower = text.lower()

        if any(
            term in lower
            for term in [
                "deployment",
                "startup",
                "production",
                "environment variable",
                "runtime",
                "configuration",
            ]
        ):
            return FakeGoalState(
                "software deployment restore production service "
                "debug runtime startup configuration"
            )

        if any(
            term in lower
            for term in [
                "robotics",
                "autonomous systems",
                "master",
                "graduate",
            ]
        ):
            return FakeGoalState(
                "robotics education find graduate robotics "
                "program research autonomous systems"
            )

        return FakeGoalState(lower)


def add_conversation(
    store,
    router,
    conversation_id,
    provider,
    human_text,
    agent_text,
):
    trace = store.trace(
        user_id="test_user",
        trajectory_id="workspace",
        conversation_id=conversation_id,
        trajectory_router=router,
    )

    human = trace.human(
        human_text,
        provider=provider,
    )

    trace.agent(
        agent_text,
        actor_id=provider,
        thread_id=human.thread_id,
        provider=provider,
    )

    return human


def test_cross_provider_automatic_routing(tmp_path):
    store = TrajectoryStore(
        str(tmp_path / "router.db")
    )

    router = TrajectoryRouter(
        attach_threshold=0.30,
        suggest_threshold=0.15,
        margin_threshold=0.08,
        extractor=FakeSemanticGoalExtractor(),
    )

    first = add_conversation(
        store,
        router,
        "chat_01",
        "gemini",
        "My production deployment keeps failing.",
        "Inspect whether the failure occurs during build or runtime.",
    )

    second = add_conversation(
        store,
        router,
        "chat_02",
        "openai",
        "The build succeeds but the service dies during startup.",
        "Inspect production configuration.",
    )

    robotics = add_conversation(
        store,
        router,
        "chat_03",
        "anthropic",
        "Which robotics master's programs start in January?",
        "Compare robotics and autonomous systems programs.",
    )

    third = add_conversation(
        store,
        router,
        "chat_04",
        "gemini",
        "A required production environment variable was missing.",
        "Correct the configuration and redeploy.",
    )

    # Same work across different providers.
    assert first.thread_id == second.thread_id
    assert first.thread_id == third.thread_id

    # Different goal remains separate.
    assert robotics.thread_id != first.thread_id

    trace = store.trace(
        user_id="test_user",
        trajectory_id="workspace",
        conversation_id="analysis",
    )

    analyses = trace.analyze_trajectories()

    assert len(analyses) == 2

    deployment = analyses[first.thread_id]
    robotics_analysis = analyses[robotics.thread_id]

    assert deployment.conversation_count == 3
    assert deployment.providers == [
        "gemini",
        "openai",
    ]

    assert robotics_analysis.conversation_count == 1
    assert robotics_analysis.providers == [
        "anthropic",
    ]

    store.close()


def test_unrelated_conversation_does_not_merge(tmp_path):
    store = TrajectoryStore(
        str(tmp_path / "separate.db")
    )

    router = TrajectoryRouter(
        extractor=FakeSemanticGoalExtractor(),
    )

    deployment = add_conversation(
        store,
        router,
        "deployment",
        "gemini",
        "Production deployment is failing.",
        "Inspect runtime configuration.",
    )

    robotics = add_conversation(
        store,
        router,
        "robotics",
        "anthropic",
        "Compare robotics master's programs.",
        "Let's compare graduate programs.",
    )

    assert deployment.thread_id != robotics.thread_id

    store.close()
