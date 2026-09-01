from pathlib import Path

from temperans import TrajectoryStore
from temperans.models import TemperansV1BehavioralPerception


db = Path("temperans_behavior_demo.db")

if db.exists():
    db.unlink()

model = TemperansV1BehavioralPerception()
store = TrajectoryStore(str(db))

trajectory = "deployment_project"


# --------------------------------------------------
# Conversation 1
# --------------------------------------------------

c1 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_1",
    behavior_model=model,
)

c1.human(
    "Production deployment is failing."
)

c1.agent(
    "Try restarting the service.",
    actor_id="agent_A",
)

event = c1.human(
    "It still isn't working."
)

print()
print("DETECTED HUMAN BEHAVIOR")
print(event.metadata.get("behavior"))

c1.agent(
    "I'll run deployment again.",
    actor_id="agent_A",
)

c1.tool(
    "deploy",
    status="failed",
    environment="production",
)


# --------------------------------------------------
# Conversation 2
# Agent B repeats failed action
# --------------------------------------------------

c2 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_2",
    behavior_model=model,
)

c2.agent(
    "I'll try deployment again.",
    actor_id="agent_B",
)

c2.tool(
    "deploy",
    status="failed",
    environment="production",
)


# --------------------------------------------------
# Conversation 3
# Agent C changes strategy and succeeds
# --------------------------------------------------

c3 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_3",
    behavior_model=model,
)

c3.agent(
    "I'll inspect the configuration instead.",
    actor_id="agent_C",
)

c3.tool(
    "inspect_config",
    status="success",
    environment="production",
)


# --------------------------------------------------
# Raw trajectory state
# --------------------------------------------------

print()
print("=" * 70)
print("FINAL TEMPERANS STATE")
print("=" * 70)

for key, value in c3.state().items():
    print(f"{key}: {value}")


# --------------------------------------------------
# Query layer
# --------------------------------------------------

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)

print(c3.summary())


print()
print("=" * 70)
print("REPAIRS")
print("=" * 70)

for event in c3.repairs():
    print(
        event.conversation_id,
        "->",
        event.text,
    )


print()
print("=" * 70)
print("FAILURES")
print("=" * 70)

for event in c3.failures():
    print(
        event.conversation_id,
        "->",
        event.tool_name,
        event.status,
    )


print()
print("=" * 70)
print("RESOLUTIONS")
print("=" * 70)

for result in c3.resolutions():

    agent = result["agent_event"]
    tool = result["tool_event"]

    print(
        "agent:",
        agent.actor_id if agent else None,
    )

    print(
        "answer:",
        agent.text if agent else None,
    )

    print(
        "tool:",
        tool.tool_name,
        tool.status,
    )


print()
print("=" * 70)
print("AGENTS")
print("=" * 70)

for agent_id, info in c3.agents().items():
    print(agent_id, "->", info)


print()
print("=" * 70)
print("TIMELINE")
print("=" * 70)

for item in c3.timeline():

    label = (
        item["actor_id"]
        or item["tool_name"]
        or item["actor_type"]
    )

    print(
        item["conversation_id"],
        item["actor_type"],
        label,
        item["status"] or "",
        item["text"][:60],
    )


store.close()
