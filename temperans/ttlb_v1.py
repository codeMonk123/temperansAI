from dataclasses import dataclass, asdict
import json
import random


ATTACH = "attach"
BRANCH = "branch"
NEW = "new"


@dataclass
class TTLBV1Case:
    case_id: str
    label: str
    category: str
    difficulty: str

    candidate_goal: str
    candidate_state: str
    candidate_lifecycle: str
    candidate_unresolved: bool

    candidate_entities: list
    candidate_artifacts: list

    new_text: str

    def candidate_text(self):
        parts = [
            self.candidate_goal,
            self.candidate_state,
            " ".join(self.candidate_entities),
            " ".join(self.candidate_artifacts),
        ]

        return " ".join(
            x for x in parts if x
        )

    def to_dict(self):
        return asdict(self)


def build_v1(seed=42):
    rng = random.Random(seed)
    cases = []

    # --------------------------------------------------
    # 1. HARD ATTACH — evolving incidents
    # --------------------------------------------------

    systems = [
        "checkout service",
        "authentication service",
        "payment API",
        "search service",
        "notification worker",
        "analytics pipeline",
        "recommendation service",
        "mobile backend",
        "billing service",
        "deployment controller",
    ]

    transitions = [
        (
            "production deployment is failing",
            "The build works now but the process dies during startup.",
        ),
        (
            "service crashes during startup",
            "We traced the failure to configuration loading.",
        ),
        (
            "runtime configuration is failing",
            "The required production secret appears to be missing.",
        ),
        (
            "requests are timing out",
            "The database connection pool is exhausted.",
        ),
        (
            "authentication requests fail",
            "The token validation key is not loading correctly.",
        ),
    ]

    n = 0

    for system in systems:
        for state, new_text in transitions:
            n += 1

            cases.append(
                TTLBV1Case(
                    case_id=f"attach_evolve_{n:03d}",
                    label=ATTACH,
                    category="evolving_goal",
                    difficulty="hard",
                    candidate_goal=f"restore {system}",
                    candidate_state=state,
                    candidate_lifecycle="active",
                    candidate_unresolved=True,
                    candidate_entities=[system],
                    candidate_artifacts=[],
                    new_text=new_text,
                )
            )

    # --------------------------------------------------
    # 2. VAGUE ATTACH
    # --------------------------------------------------

    vague = [
        "Still doesn't work after that change.",
        "That didn't fix it either.",
        "Same failure again.",
        "We're still blocked.",
        "It broke again after the restart.",
        "No luck. The issue is still happening.",
        "That improved things but didn't resolve it.",
        "We're seeing the same problem after the update.",
        "The previous fix didn't hold.",
        "It is still failing in production.",
    ]

    for i, text in enumerate(vague, 1):
        system = rng.choice(systems)

        cases.append(
            TTLBV1Case(
                case_id=f"attach_vague_{i:03d}",
                label=ATTACH,
                category="vague_continuation",
                difficulty="hard",
                candidate_goal=f"restore {system}",
                candidate_state=(
                    "active unresolved production failure"
                ),
                candidate_lifecycle="active",
                candidate_unresolved=True,
                candidate_entities=[system],
                candidate_artifacts=[],
                new_text=text,
            )
        )

    # --------------------------------------------------
    # 3. REOPEN
    # --------------------------------------------------

    for i, system in enumerate(systems, 1):
        cases.append(
            TTLBV1Case(
                case_id=f"attach_reopen_{i:03d}",
                label=ATTACH,
                category="reopen",
                difficulty="hard",
                candidate_goal=f"resolve failure in {system}",
                candidate_state="incident resolved",
                candidate_lifecycle="resolved",
                candidate_unresolved=False,
                candidate_entities=[system],
                candidate_artifacts=[],
                new_text=(
                    f"The same {system} failure is back "
                    "after being fixed."
                ),
            )
        )

    # --------------------------------------------------
    # 4. SAME PROJECT, DIFFERENT GOAL
    # --------------------------------------------------

    projects = [
        "Temperans",
        "Atlas",
        "Mercury",
        "Phoenix",
        "Nova",
        "Orion",
        "Helios",
        "Vector",
        "Nimbus",
        "Aster",
    ]

    project_goals = [
        (
            "publish the Python SDK",
            "Prepare the investor fundraising deck.",
        ),
        (
            "debug production deployment",
            "Design the pricing strategy.",
        ),
        (
            "build the Slack connector",
            "Prepare accelerator application materials.",
        ),
        (
            "improve trajectory routing",
            "Redesign the marketing website.",
        ),
        (
            "build evaluation benchmark",
            "Negotiate enterprise partnership terms.",
        ),
    ]

    n = 0

    for project in projects:
        for goal, new_text in project_goals:
            n += 1

            cases.append(
                TTLBV1Case(
                    case_id=f"new_project_{n:03d}",
                    label=NEW,
                    category="same_project_different_goal",
                    difficulty="hard",
                    candidate_goal=f"{goal} for {project}",
                    candidate_state="work in progress",
                    candidate_lifecycle="active",
                    candidate_unresolved=True,
                    candidate_entities=[project],
                    candidate_artifacts=[],
                    new_text=f"{project}: {new_text}",
                )
            )

    # --------------------------------------------------
    # 5. SAME REPOSITORY, DIFFERENT BUG
    # --------------------------------------------------

    repos = [
        "temperansAI",
        "checkout-api",
        "mobile-app",
        "agent-platform",
        "billing-service",
        "identity-service",
        "search-api",
        "analytics-core",
        "support-bot",
        "workflow-engine",
    ]

    for i, repo in enumerate(repos, 1):
        cases.append(
            TTLBV1Case(
                case_id=f"new_repo_{i:03d}",
                label=NEW,
                category="same_repo_different_bug",
                difficulty="hard",
                candidate_goal="fix trajectory routing failure",
                candidate_state="router produces incorrect thread assignment",
                candidate_lifecycle="active",
                candidate_unresolved=True,
                candidate_entities=[],
                candidate_artifacts=[repo],
                new_text=(
                    f"In repository {repo}, fix the broken "
                    "package metadata used for publishing."
                ),
            )
        )

    # --------------------------------------------------
    # 6. SAME PROBLEM TYPE, DIFFERENT CUSTOMER
    # --------------------------------------------------

    for i in range(1, 31):
        a = f"customer_{i:03d}"
        b = f"customer_{i + 100:03d}"

        cases.append(
            TTLBV1Case(
                case_id=f"new_customer_{i:03d}",
                label=NEW,
                category="different_entity",
                difficulty="hard",
                candidate_goal="restore enterprise SSO activation",
                candidate_state="SSO activation failing",
                candidate_lifecycle="active",
                candidate_unresolved=True,
                candidate_entities=[a],
                candidate_artifacts=[],
                new_text=(
                    f"{b} cannot activate enterprise SSO."
                ),
            )
        )

    # --------------------------------------------------
    # 7. BRANCH
    # --------------------------------------------------

    branch_templates = [
        (
            "resolve production deployment incident",
            "This incident showed our monitoring is weak. "
            "Let's redesign observability.",
        ),
        (
            "fix authentication outage",
            "This revealed gaps in our incident process. "
            "Let's create a new response playbook.",
        ),
        (
            "repair data pipeline failure",
            "Because of this incident, let's redesign "
            "pipeline health monitoring.",
        ),
        (
            "fix agent tool failures",
            "This showed the tool architecture is brittle. "
            "Let's redesign the tool interface.",
        ),
        (
            "resolve customer escalation",
            "This exposed a support-process gap. "
            "Let's redesign escalation handling.",
        ),
    ]

    for i in range(40):
        goal, new_text = rng.choice(
            branch_templates
        )

        cases.append(
            TTLBV1Case(
                case_id=f"branch_{i + 1:03d}",
                label=BRANCH,
                category="branch",
                difficulty="hard",
                candidate_goal=goal,
                candidate_state="under investigation",
                candidate_lifecycle="active",
                candidate_unresolved=True,
                candidate_entities=[],
                candidate_artifacts=[],
                new_text=new_text,
            )
        )

    # --------------------------------------------------
    # 8. EASY NEGATIVE CONTROLS
    # --------------------------------------------------

    easy_pairs = [
        (
            "debug production deployment",
            "Compare robotics master's programs.",
        ),
        (
            "research graduate scholarships",
            "Fix the checkout API timeout.",
        ),
        (
            "prepare investor pitch",
            "How long should I boil an egg?",
        ),
        (
            "debug authentication",
            "Plan a vacation to Japan.",
        ),
        (
            "evaluate AI benchmark",
            "Compare mortgage refinance options.",
        ),
    ]

    for i in range(30):
        goal, new_text = rng.choice(easy_pairs)

        cases.append(
            TTLBV1Case(
                case_id=f"new_easy_{i + 1:03d}",
                label=NEW,
                category="unrelated",
                difficulty="easy",
                candidate_goal=goal,
                candidate_state="active",
                candidate_lifecycle="active",
                candidate_unresolved=True,
                candidate_entities=[],
                candidate_artifacts=[],
                new_text=new_text,
            )
        )

    rng.shuffle(cases)

    return cases


def save(path="ttlb_v1.jsonl"):
    cases = build_v1()

    with open(path, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(
                json.dumps(
                    case.to_dict(),
                    ensure_ascii=False,
                )
                + "\n"
            )

    return cases


if __name__ == "__main__":
    cases = save()

    counts = {}

    for case in cases:
        key = (
            case.label,
            case.category,
        )
        counts[key] = counts.get(key, 0) + 1

    print("TTLB V1")
    print("=" * 70)
    print("CASES:", len(cases))

    for key, count in sorted(counts.items()):
        print(
            f"{key[0]:7} "
            f"{key[1]:32} "
            f"{count}"
        )

    print()
    print("SAVED: ttlb_v1.jsonl")
