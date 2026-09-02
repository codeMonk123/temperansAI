from pathlib import Path

from temperans import TrajectoryStore
from temperans.router import TrajectoryRouter
from temperans.goal import GeminiGoalStateExtractor
from google import genai


DB = Path(
    "/Users/bhushanjain/Desktop/temperans-model/"
    "temperans_router_test.db"
)

if DB.exists():
    DB.unlink()

store = TrajectoryStore(str(DB))

goal_extractor = GeminiGoalStateExtractor(
    client=genai.Client(),
    model="gemini-3.6-flash",
)

router = TrajectoryRouter(
    attach_threshold=0.30,
    suggest_threshold=0.15,
    margin_threshold=0.08,
    extractor=goal_extractor,
)

trajectory_id = "user_workspace"


def conversation(
    conversation_id,
    provider,
    human_text,
    agent_text,
):
    trace = store.trace(
        user_id="user_1",
        trajectory_id=trajectory_id,
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

    routing = human.metadata.get(
        "thread_resolution",
        {},
    )

    print()
    print("=" * 72)
    print(conversation_id, "|", provider)
    print("=" * 72)

    print("THREAD:", human.thread_id)
    print("DECISION:", routing.get("decision"))
    print("SCORE:", routing.get("score"))
    print("MARGIN:", routing.get("margin"))

    print("EVIDENCE:")
    for item in routing.get("evidence", []):
        print(" -", item)

    return human.thread_id


deployment_1 = conversation(
    "chat_01",
    "gemini",
    "My production deployment keeps failing after the latest release.",
    "Inspect the deployment logs and determine whether "
    "the failure occurs during build or runtime.",
)

deployment_2 = conversation(
    "chat_02",
    "openai",
    "The build succeeds now, but the service dies during startup.",
    "Inspect production configuration and environment variables.",
)

robotics = conversation(
    "chat_03",
    "anthropic",
    "Which robotics master's programs let me start in January "
    "and finish autonomous systems training in about one year?",
    "Compare spring-start robotics and autonomous-systems programs.",
)

deployment_3 = conversation(
    "chat_04",
    "gemini",
    "We found that a required production environment variable "
    "was missing. What should we do next?",
    "Add the missing production configuration and redeploy safely.",
)


trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="analysis",
)

print()
print("=" * 72)
print("ROUTER RESULT")
print("=" * 72)

print("DEPLOYMENT 1:", deployment_1)
print("DEPLOYMENT 2:", deployment_2)
print("DEPLOYMENT 3:", deployment_3)
print("ROBOTICS:", robotics)

print()
print(
    "DEPLOYMENT SAME:",
    deployment_1 == deployment_2 == deployment_3,
)

print(
    "ROBOTICS SEPARATE:",
    robotics != deployment_1,
)

print()
print("=" * 72)
print("TRAJECTORIES")
print("=" * 72)

for thread_id, analysis in trace.analyze_trajectories().items():
    print()
    print("THREAD:", thread_id)
    print("STATE:", analysis.state)
    print("CONVERSATIONS:", analysis.conversation_count)
    print("PROVIDERS:", analysis.providers)

store.close()
