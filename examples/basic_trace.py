from temperans import Trace

trace = Trace(
    user_id="user_123",
    trajectory_id="deployment_debugging",
    conversation_id="conversation_1",
)

trace.human(
    "My deployment keeps failing."
)

trace.agent(
    "I'll try the deployment tool.",
    actor_id="deployment_agent",
)

trace.tool(
    "deploy",
    status="failed",
    environment="production",
)

trace.agent(
    "I'll retry."
)

trace.tool(
    "deploy",
    status="failed",
    environment="production",
)

trace.human(
    "I already told you this isn't working."
)

print("Trajectory:", trace.trajectory_id)
print()
print("State:")

for key, value in trace.state().items():
    print(f"  {key}: {value}")
