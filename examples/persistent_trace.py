from pathlib import Path

from temperans import TrajectoryStore

db = Path("temperans_demo.db")

if db.exists():
    db.unlink()

store = TrajectoryStore(str(db))

# Conversation 1, Agent A
chat1 = store.trace(
    user_id="user_123",
    trajectory_id="deployment_project",
    conversation_id="chat_1",
)

chat1.human(
    "Production deployment is failing."
)

chat1.agent(
    "I'll try the deployment tool.",
    actor_id="agent_A",
)

chat1.tool(
    "deploy",
    status="failed",
    environment="production",
)

print("AFTER CHAT 1")
print(chat1.state())


# Same trajectory, NEW conversation, NEW agent.
chat2 = store.trace(
    user_id="user_123",
    trajectory_id="deployment_project",
    conversation_id="chat_2",
)

print()
print("START OF CHAT 2")
print(chat2.state())

chat2.human(
    "It still isn't working."
)

chat2.agent(
    "I'll try deployment again.",
    actor_id="agent_B",
)

chat2.tool(
    "deploy",
    status="failed",
    environment="production",
)

print()
print("AFTER CHAT 2")
print(chat2.state())

print()
print("EVENTS:", len(chat2.events))

for event in chat2.events:
    print(
        event.conversation_id,
        event.actor_type,
        event.actor_id or event.tool_name,
        event.status or "",
        event.text[:50],
    )

store.close()
