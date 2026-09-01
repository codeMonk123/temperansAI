from pathlib import Path

from google import genai

from temperans import TrajectoryStore
from temperans.adapters import GeminiAdapter


DB = Path(
    "/Users/bhushanjain/Desktop/temperans-model/"
    "temperans_live_gemini.db"
)

if DB.exists():
    DB.unlink()

client = genai.Client()
store = TrajectoryStore(str(DB))

trajectory_id = "live_gemini_debugging"
thread_id = "deployment_debugging"


def run_chat(conversation_id, prompt):
    trace = store.trace(
        user_id="user_1",
        trajectory_id=trajectory_id,
        conversation_id=conversation_id,
        thread_id=thread_id,
    )

    adapter = GeminiAdapter(
        trace,
        model="gemini-3.6-flash",
    )

    adapter.human(prompt)

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    text = response.text or ""

    adapter.agent(
        text,
        actor_id="gemini",
    )

    print()
    print(conversation_id)
    print("HUMAN:", prompt)
    print("GEMINI:", text[:500])


run_chat(
    "gemini_chat_1",
    "A production service fails immediately after deployment. "
    "What should I investigate first?"
)

run_chat(
    "gemini_chat_2",
    "The build succeeds and the container starts, but the "
    "application dies while loading production configuration. "
    "What does that suggest?"
)

run_chat(
    "gemini_chat_3",
    "We discovered a required production environment variable "
    "was missing. What should we do next?"
)


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
print("REAL GEMINI TEMPERANS TRAJECTORY")
print("=" * 72)

print("STATE:", analysis.state)
print("CONVERSATIONS:", analysis.conversation_count)
print("PROVIDERS:", analysis.providers)
print("AGENTS:", analysis.agent_ids)
print("HUMAN TURNS:", analysis.human_turns)
print("AGENT TURNS:", analysis.agent_turns)
print("CONTINUITY:", analysis.continuity)
print("EVOLUTION:", analysis.evolution)

print()
print("EVIDENCE")

for item in analysis.evidence:
    print("-", item)

print()
print("TIMELINE")

for event in trace.timeline(
    thread_id=thread_id
):
    provider = event.get("behavior")

    print(
        event["conversation_id"],
        event["actor_type"],
        "->",
        (event["text"] or event["tool_name"])[:250],
    )

store.close()
