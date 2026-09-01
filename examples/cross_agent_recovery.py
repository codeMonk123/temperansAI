from pathlib import Path
from temperans import TrajectoryStore

db = Path("temperans_recovery_demo.db")

if db.exists():
    db.unlink()

store = TrajectoryStore(str(db))

trajectory = "deployment_project"


# Conversation 1 — Agent A fails
c1 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_1",
)

c1.human("Production deployment is failing.")
c1.agent(
    "I'll try deployment.",
    actor_id="agent_A",
)
c1.tool(
    "deploy",
    status="failed",
    environment="production",
)


# Conversation 2 — Agent B repeats same failure
c2 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_2",
)

c2.human("It still isn't working.")
c2.agent(
    "I'll try deployment again.",
    actor_id="agent_B",
)
c2.tool(
    "deploy",
    status="failed",
    environment="production",
)


# Conversation 3 — Agent C changes strategy and succeeds
c3 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_3",
)

c3.human(
    "We've already tried deployment twice."
)

c3.agent(
    "I'll inspect the configuration first.",
    actor_id="agent_C",
)

c3.tool(
    "inspect_config",
    status="success",
    environment="production",
)

print("FINAL TRAJECTORY STATE")
print()

for key, value in c3.state().items():
    print(f"{key}: {value}")

store.close()
