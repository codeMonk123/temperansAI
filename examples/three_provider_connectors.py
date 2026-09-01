from pathlib import Path
from types import SimpleNamespace

from google import genai

from temperans import TrajectoryStore
from temperans.openai import OpenAIConnector
from temperans.anthropic import AnthropicConnector
from temperans.gemini import GeminiConnector


DB = Path(
    "/Users/bhushanjain/Desktop/temperans-model/"
    "temperans_three_provider.db"
)

if DB.exists():
    DB.unlink()


# --------------------------------------------------
# Fake OpenAI client
# Same surface used by OpenAIConnector:
# client.responses.create(...)
# --------------------------------------------------

class FakeOpenAIResponses:
    def create(self, model, input, **kwargs):
        return SimpleNamespace(
            id="openai_response_001",
            output_text=(
                "Inspect the deployment logs and determine "
                "whether the failure happens during build "
                "or runtime startup."
            ),
        )


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeOpenAIResponses()


# --------------------------------------------------
# Fake Anthropic client
# Same surface used by AnthropicConnector:
# client.messages.create(...)
# --------------------------------------------------

class FakeAnthropicMessages:
    def create(
        self,
        model,
        max_tokens,
        messages,
        **kwargs,
    ):
        return SimpleNamespace(
            id="anthropic_message_001",
            content=[
                SimpleNamespace(
                    text=(
                        "Since the build succeeds but the "
                        "service dies at startup, inspect "
                        "production configuration and "
                        "environment variables."
                    )
                )
            ],
        )


class FakeAnthropicClient:
    def __init__(self):
        self.messages = FakeAnthropicMessages()


store = TrajectoryStore(str(DB))

trajectory_id = "deployment_project"
thread_id = "deployment_debugging"


# --------------------------------------------------
# CHAT 1 — OpenAI
# --------------------------------------------------

trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="chat_openai",
    thread_id=thread_id,
)

openai = OpenAIConnector(
    trace=trace,
    client=FakeOpenAIClient(),
    model="fake-openai-model",
)

openai.generate(
    "My production deployment keeps failing."
)


# --------------------------------------------------
# CHAT 2 — Anthropic
# --------------------------------------------------

trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="chat_anthropic",
    thread_id=thread_id,
)

anthropic = AnthropicConnector(
    trace=trace,
    client=FakeAnthropicClient(),
    model="fake-anthropic-model",
)

anthropic.generate(
    "The build succeeds, but the service dies "
    "during startup."
)


# --------------------------------------------------
# CHAT 3 — REAL Gemini
# --------------------------------------------------

trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="chat_gemini",
    thread_id=thread_id,
)

gemini = GeminiConnector(
    trace=trace,
    client=genai.Client(),
    model="gemini-3.6-flash",
)

gemini.generate(
    "We discovered a required production environment "
    "variable was missing. Give the next remediation step "
    "in one short paragraph."
)


# --------------------------------------------------
# ANALYZE
# --------------------------------------------------

trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="analysis",
)

analysis = trace.analyze_trajectory(
    thread_id
)

print()
print("=" * 72)
print("THREE-PROVIDER TEMPERANS TRAJECTORY")
print("=" * 72)

print("STATE:", analysis.state)
print("CONVERSATIONS:", analysis.conversation_count)
print("PROVIDERS:", analysis.providers)
print("AGENTS:", analysis.agent_ids)
print("HUMAN TURNS:", analysis.human_turns)
print("AGENT TURNS:", analysis.agent_turns)

print()
print("EVIDENCE")

for item in analysis.evidence:
    print("-", item)

print()
print("TIMELINE")

for event in trace.timeline(
    thread_id=thread_id
):
    print(
        event["conversation_id"],
        event["actor_type"],
        "->",
        (event["text"] or event["tool_name"])[:180],
    )

store.close()
