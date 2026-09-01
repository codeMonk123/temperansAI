from pathlib import Path

from temperans import TrajectoryStore
from temperans.adapters import (
    OpenAIAdapter,
    AnthropicAdapter,
    GeminiAdapter,
)


DB = Path("temperans_cross_provider.db")

if DB.exists():
    DB.unlink()

store = TrajectoryStore(str(DB))

trajectory_id = "production_debugging"
thread_id = "deployment_debugging"


# --------------------------------------------------
# Conversation 1 — OpenAI
# --------------------------------------------------

trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="chat_openai",
    thread_id=thread_id,
)

openai = OpenAIAdapter(
    trace,
    model="gpt",
)

openai.human(
    "My production deployment keeps failing."
)

openai.agent(
    "Let's inspect the deployment logs first.",
    actor_id="openai_agent",
)


# --------------------------------------------------
# Conversation 2 — Anthropic
# --------------------------------------------------

trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="chat_anthropic",
    thread_id=thread_id,
)

anthropic = AnthropicAdapter(
    trace,
    model="claude",
)

anthropic.human(
    "The build succeeds now, but the service dies at startup."
)

anthropic.agent(
    "Inspect production configuration and secret loading.",
    actor_id="anthropic_agent",
)

anthropic.tool(
    "inspect_config",
    status="failed",
)


# --------------------------------------------------
# Conversation 3 — Gemini
# --------------------------------------------------

trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="chat_gemini",
    thread_id=thread_id,
)

gemini = GeminiAdapter(
    trace,
    model="gemini",
)

gemini.human(
    "We found that a required production configuration value is missing."
)

gemini.agent(
    "Add the missing value and validate the deployment again.",
    actor_id="gemini_agent",
)

gemini.tool(
    "validate_deployment",
    status="success",
)


# --------------------------------------------------
# Reconstruct + analyze
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
print("CROSS-PROVIDER TEMPERANS TRAJECTORY")
print("=" * 72)

print("THREAD:", analysis.thread_id)
print("STATE:", analysis.state)
print("CONVERSATIONS:", analysis.conversation_count)
print("PROVIDERS:", analysis.providers)
print("AGENTS:", analysis.agent_ids)
print("HUMAN TURNS:", analysis.human_turns)
print("AGENT TURNS:", analysis.agent_turns)
print("TOOL CALLS:", analysis.tool_calls)
print("CONTINUITY:", analysis.continuity)
print("EVOLUTION:", analysis.evolution)
print("FAILURES:", analysis.failures)
print("SUCCESSES:", analysis.successes)
print("RECOVERIES:", analysis.recoveries)

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
        event["text"] or event["tool_name"],
    )

store.close()
