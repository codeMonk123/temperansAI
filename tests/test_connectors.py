from types import SimpleNamespace

from temperans import TrajectoryStore
from temperans.openai import OpenAIConnector
from temperans.anthropic import AnthropicConnector


class FakeOpenAIResponses:
    def create(self, model, input, **kwargs):
        return SimpleNamespace(
            id="openai_1",
            output_text="Inspect runtime logs.",
        )


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeOpenAIResponses()


class FakeAnthropicMessages:
    def create(
        self,
        model,
        max_tokens,
        messages,
        **kwargs,
    ):
        return SimpleNamespace(
            id="anthropic_1",
            content=[
                SimpleNamespace(
                    text="Inspect production configuration."
                )
            ],
        )


class FakeAnthropicClient:
    def __init__(self):
        self.messages = FakeAnthropicMessages()


def test_cross_provider_trajectory(tmp_path):
    db = tmp_path / "providers.db"

    store = TrajectoryStore(str(db))

    trajectory_id = "deployment"
    thread_id = "deployment_debugging"

    trace = store.trace(
        user_id="user",
        trajectory_id=trajectory_id,
        conversation_id="chat_openai",
        thread_id=thread_id,
    )

    OpenAIConnector(
        trace=trace,
        client=FakeOpenAIClient(),
        model="fake-openai",
    ).generate(
        "Deployment is failing."
    )

    trace = store.trace(
        user_id="user",
        trajectory_id=trajectory_id,
        conversation_id="chat_anthropic",
        thread_id=thread_id,
    )

    AnthropicConnector(
        trace=trace,
        client=FakeAnthropicClient(),
        model="fake-anthropic",
    ).generate(
        "Build works but startup fails."
    )

    trace = store.trace(
        user_id="user",
        trajectory_id=trajectory_id,
        conversation_id="analysis",
    )

    analysis = trace.analyze_trajectory(
        thread_id
    )

    assert analysis.conversation_count == 2
    assert analysis.providers == [
        "openai",
        "anthropic",
    ]
    assert analysis.agent_ids == [
        "openai",
        "anthropic",
    ]
    assert analysis.human_turns == 2
    assert analysis.agent_turns == 2
    assert analysis.revisited is True
    assert analysis.state == "evolving"

    store.close()
