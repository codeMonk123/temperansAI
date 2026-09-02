from temperans.product_events import ProductEventProcessor
from temperans.runtime_v2 import TemperansRuntimeV2
from temperans.workstate import ConversationState


def scorer(t, c):
    left = (t.durable_goal + " " + t.current_state).lower()
    right = (c.goal + " " + c.current_problem).lower()

    groups = [
        {"production","deployment","service","startup","configuration","environment","variable","validation"},
        {"robotics","master","program","autonomous","january"},
    ]

    for terms in groups:
        if sum(x in left for x in terms) >= 2 and sum(x in right for x in terms) >= 2:
            return .82
    return .05


def state(surface, cid, goal, problem, **kwargs):
    return ConversationState(
        workspace_id="startup_x",
        person_id="person_001",
        conversation_id=cid,
        surface=surface,
        goal=goal,
        current_problem=problem,
        **kwargs,
    )


runtime = TemperansRuntimeV2(semantic_scorer=scorer, candidate_floor=.12)

r1 = runtime.process(state(
    "gemini","gemini_1",
    "restore stable production deployment",
    "production deployment is failing",
))

r2 = runtime.process(state(
    "openai","openai_1",
    "restore stable production deployment",
    "the build succeeds but the service dies during startup configuration",
))

r3 = runtime.process(state(
    "anthropic","claude_1",
    "find a one-year robotics masters program",
    "compare robotics programs that allow a January start",
))

r4 = runtime.process(state(
    "slack","slack_1",
    "restore stable production deployment",
    "we found that PROD_DATABASE_URL was missing from production",
    artifacts=["PROD_DATABASE_URL"],
))

r5 = runtime.process(state(
    "acme_chatbot","acme_1",
    "restore stable production deployment",
    "the production service is healthy now; prevent this configuration failure from recurring",
    artifacts=["PROD_DATABASE_URL"],
    decisions=["add deployment-time configuration validation"],
    outcomes=["production service restored"],
    unresolved=["prevent configuration regression"],
))

deploy_id = r1.trajectory_id
deploy = runtime.trajectories[deploy_id]

product = ProductEventProcessor().apply(
    deploy,
    event_name="deployment_validation",
    status="success",
    description="corrected production deployment validated successfully",
)

checks = {
    "Gemini/OpenAI same": r1.trajectory_id == r2.trajectory_id,
    "Slack same": r4.trajectory_id == deploy_id,
    "Acme same": r5.trajectory_id == deploy_id,
    "Robotics separate": r3.trajectory_id != deploy_id,
    "Two trajectories": len(runtime.trajectories) == 2,
    "Deployment resolved": product.lifecycle == "resolved",
}

print("=" * 72)
print("TEMPERANS E2E")
print("=" * 72)

for name, result in [
    ("GEMINI", r1),
    ("OPENAI", r2),
    ("CLAUDE", r3),
    ("SLACK", r4),
    ("ACME", r5),
]:
    print(f"{name:8} {result.decision:8} {result.trajectory_id} {result.source}")

print()
for name, ok in checks.items():
    print(f"{name:24} {'PASS' if ok else 'FAIL'}")

print()
print("FINAL DEPLOYMENT CONTEXT")
print(runtime.context.build(deploy).to_prompt())

if not all(checks.values()):
    raise SystemExit("TEMPERANS E2E FAILED")

print()
print("TEMPERANS E2E PASSED")
