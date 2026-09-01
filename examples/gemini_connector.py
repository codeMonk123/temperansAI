from pathlib import Path

from google import genai

from temperans import TrajectoryStore
from temperans.gemini import GeminiConnector


DB = Path(
    "/Users/bhushanjain/Desktop/temperans-model/"
    "temperans_gemini_connector.db"
)

if DB.exists():
    DB.unlink()

store = TrajectoryStore(str(DB))
client = genai.Client()

trajectory_id = "gemini_connector_test"
thread_id = "deployment_debugging"


def run(conversation_id, prompt):
    trace = store.trace(
        user_id="user_1",
        trajectory_id=trajectory_id,
        conversation_id=conversation_id,
        thread_id=thread_id,
    )

    connector = GeminiConnector(
        trace=trace,
        client=client,
        model="gemini-3.6-flash",
    )

    response = connector.generate(prompt)

    print()
    print(conversation_id)
    print("GEMINI:", (response.text or "")[:300])


run(
    "chat_1",
    "A production service fails immediately after deployment. "
    "What should I investigate first?",
)

run(
    "chat_2",
    "The container starts but the application crashes while "
    "loading production configuration. What does that suggest?",
)

run(
    "chat_3",
    "We discovered a required environment variable was missing. "
    "What should we do next?",
)


trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="analysis",
)

analysis = trace.analyze_trajectory(thread_id)

print()
print("=" * 72)
print("GEMINI CONNECTOR RESULT")
print("=" * 72)

print("STATE:", analysis.state)
print("CONVERSATIONS:", analysis.conversation_count)
print("PROVIDERS:", analysis.providers)
print("AGENTS:", analysis.agent_ids)
print("HUMAN TURNS:", analysis.human_turns)
print("AGENT TURNS:", analysis.agent_turns)

print()
print("EVIDENCE:")

for item in analysis.evidence:
    print("-", item)

print()
print("EVENTS:")

for event in trace.timeline(thread_id=thread_id):
    print(
        event["conversation_id"],
        event["actor_type"],
        "->",
        (event["text"] or event["tool_name"])[:150],
    )

store.close()
