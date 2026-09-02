from pathlib import Path

from temperans import TrajectoryStore
from temperans.router import TrajectoryRouter
from temperans.goal import LocalGoalStateExtractor
from temperans.slack import SlackAdapter


DB = Path(
    "/Users/bhushanjain/Desktop/temperans-model/"
    "temperans_slack_test.db"
)

if DB.exists():
    DB.unlink()

store = TrajectoryStore(str(DB))

router = TrajectoryRouter(
    attach_threshold=0.30,
    suggest_threshold=0.15,
    margin_threshold=0.08,
    extractor=LocalGoalStateExtractor(),
)

trajectory_id = "cross_surface_workspace"


def ai_conversation(
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
    print(provider.upper(), conversation_id)
    print("THREAD:", human.thread_id)
    print("DECISION:", routing.get("decision"))
    print("SCORE:", routing.get("score"))

    return human.thread_id


# 1 — Gemini starts deployment work

deployment_1 = ai_conversation(
    "gemini_chat",
    "gemini",
    "My production deployment keeps failing.",
    "Inspect whether the failure occurs during build or runtime.",
)


# 2 — OpenAI continues deployment work

deployment_2 = ai_conversation(
    "openai_chat",
    "openai",
    "The build succeeds but the service dies during startup.",
    "Inspect production configuration and environment variables.",
)


# 3 — Slack human continues SAME work

trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="slack_thread_1",
    trajectory_router=router,
)

slack = SlackAdapter(trace)

slack_event = slack.message(
    "We found the required production environment variable "
    "was missing. I added it and the service is starting now.",
    actor_id="slack_user_42",
    channel_id="engineering",
    slack_thread_ts="1720000000.001",
    external_id="slack_message_001",
)

slack_routing = slack_event.metadata.get(
    "thread_resolution",
    {},
)

deployment_3 = slack_event.thread_id

print()
print("SLACK slack_thread_1")
print("THREAD:", deployment_3)
print("DECISION:", slack_routing.get("decision"))
print("SCORE:", slack_routing.get("score"))


# 4 — Anthropic discusses unrelated robotics work

robotics = ai_conversation(
    "claude_chat",
    "anthropic",
    "Which one-year robotics master's programs "
    "let me start in January?",
    "Compare spring-start robotics and autonomous systems programs.",
)


# Analyze

trace = store.trace(
    user_id="user_1",
    trajectory_id=trajectory_id,
    conversation_id="analysis",
)

print()
print("=" * 72)
print("CROSS-SURFACE RESULT")
print("=" * 72)

print(
    "DEPLOYMENT SAME:",
    deployment_1 == deployment_2 == deployment_3,
)

print(
    "ROBOTICS SEPARATE:",
    robotics != deployment_1,
)

print()

for thread_id, analysis in (
    trace.analyze_trajectories().items()
):
    print("THREAD:", thread_id)
    print(
        "CONVERSATIONS:",
        analysis.conversation_count,
    )
    print(
        "PROVIDERS:",
        analysis.providers,
    )
    print(
        "STATE:",
        analysis.state,
    )
    print()

store.close()
