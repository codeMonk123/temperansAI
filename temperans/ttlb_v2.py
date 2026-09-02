from dataclasses import dataclass, asdict, field
import json
import random


ATTACH = "attach"
BRANCH = "branch"
NEW = "new"


@dataclass
class Candidate:
    candidate_id: str
    goal: str
    state: str
    lifecycle: str = "active"
    text: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class TTLBV2Case:
    case_id: str
    category: str
    difficulty: str

    incoming_text: str

    candidates: list[Candidate]

    expected_decision: str
    expected_candidate_id: str | None = None

    notes: str = ""

    def to_dict(self):
        result = asdict(self)
        result["candidates"] = [
            candidate.to_dict()
            for candidate in self.candidates
        ]
        return result


def distractors():
    return [
        Candidate(
            candidate_id="robotics",
            goal="find one-year robotics masters program",
            state="compare January-start robotics programs",
            text=(
                "Research robotics and autonomous systems "
                "graduate programs."
            ),
        ),
        Candidate(
            candidate_id="fundraising",
            goal="prepare startup fundraising",
            state="build investor materials",
            text=(
                "Prepare investor deck and fundraising strategy."
            ),
        ),
        Candidate(
            candidate_id="sdk",
            goal="publish Python SDK",
            state="prepare package release",
            text=(
                "Publish the Python SDK and validate packaging."
            ),
        ),
    ]


def build_v2(seed=20260901):
    rng = random.Random(seed)
    cases = []

    # ==================================================
    # 1. STRONG TICKET MATCH
    # ==================================================

    for i in range(1, 41):
        ticket = f"PROD-{1000 + i}"

        target = Candidate(
            candidate_id=f"deploy_{i}",
            goal="restore production service",
            state="production incident under investigation",
            text=(
                f"Investigating ticket {ticket}. "
                "Production service is failing."
            ),
        )

        candidates = [
            target,
            *rng.sample(distractors(), 2),
        ]

        rng.shuffle(candidates)

        cases.append(
            TTLBV2Case(
                case_id=f"strong_ticket_{i:03d}",
                category="strong_anchor_attach",
                difficulty="medium",
                incoming_text=(
                    f"Update on {ticket}: the service "
                    "now starts but configuration still fails."
                ),
                candidates=candidates,
                expected_decision=ATTACH,
                expected_candidate_id=target.candidate_id,
            )
        )

    # ==================================================
    # 2. BOUNDARY MISMATCH
    # ==================================================

    for i in range(1, 41):
        old_customer = f"customer_{i:03d}"
        new_customer = f"customer_{100 + i:03d}"

        target = Candidate(
            candidate_id=f"sso_{i}",
            goal="restore enterprise SSO activation",
            state="SSO activation failing",
            text=(
                f"Customer {old_customer} cannot "
                "activate enterprise SSO."
            ),
        )

        candidates = [
            target,
            *rng.sample(distractors(), 2),
        ]

        rng.shuffle(candidates)

        cases.append(
            TTLBV2Case(
                case_id=f"boundary_{i:03d}",
                category="boundary_new",
                difficulty="hard",
                incoming_text=(
                    f"Customer {new_customer} cannot "
                    "activate enterprise SSO."
                ),
                candidates=candidates,
                expected_decision=NEW,
            )
        )

    # ==================================================
    # 3. SAME REPO / DIFFERENT WORK
    # ==================================================

    for i in range(1, 41):
        repo = f"service-{i}"

        target = Candidate(
            candidate_id=f"router_{i}",
            goal="fix trajectory routing",
            state="router assigns incorrect threads",
            text=(
                f"repository {repo}: fix trajectory "
                "routing failure."
            ),
        )

        candidates = [
            target,
            *rng.sample(distractors(), 2),
        ]

        rng.shuffle(candidates)

        cases.append(
            TTLBV2Case(
                case_id=f"scope_repo_{i:03d}",
                category="scope_hard_negative",
                difficulty="hard",
                incoming_text=(
                    f"repository {repo}: repair Python "
                    "package metadata for release."
                ),
                candidates=candidates,
                expected_decision=NEW,
            )
        )

    # ==================================================
    # 4. SEMANTIC EVOLUTION — NO STRONG ID
    # ==================================================

    systems = [
        "checkout",
        "billing",
        "authentication",
        "search",
        "notifications",
        "analytics",
        "recommendation",
        "identity",
        "payments",
        "deployment",
    ]

    evolutions = [
        (
            "production deployment is failing",
            "The build succeeds now but the process "
            "dies during startup."
        ),
        (
            "service crashes during startup",
            "The failure appears while loading "
            "production configuration."
        ),
        (
            "production configuration fails",
            "We discovered the required secret "
            "is not present at runtime."
        ),
        (
            "requests are timing out",
            "The database connection pool appears "
            "to be exhausted."
        ),
    ]

    n = 0

    for system in systems:
        for state, incoming in evolutions:
            n += 1

            target = Candidate(
                candidate_id=f"evolve_{n}",
                goal=f"restore {system} service",
                state=state,
                text=(
                    f"Goal: restore {system} service. "
                    f"Current state: {state}."
                ),
            )

            candidates = [
                target,
                *rng.sample(distractors(), 2),
            ]

            rng.shuffle(candidates)

            cases.append(
                TTLBV2Case(
                    case_id=f"evolve_{n:03d}",
                    category="semantic_evolution",
                    difficulty="hard",
                    incoming_text=incoming,
                    candidates=candidates,
                    expected_decision=ATTACH,
                    expected_candidate_id=target.candidate_id,
                )
            )

    # ==================================================
    # 5. REOPEN
    # ==================================================

    for i, system in enumerate(systems, 1):
        target = Candidate(
            candidate_id=f"reopen_{i}",
            goal=f"resolve {system} production failure",
            state="incident resolved",
            lifecycle="resolved",
            text=(
                f"The {system} production failure "
                "was fixed and resolved."
            ),
        )

        candidates = [
            target,
            *rng.sample(distractors(), 2),
        ]

        rng.shuffle(candidates)

        cases.append(
            TTLBV2Case(
                case_id=f"reopen_{i:03d}",
                category="reopen",
                difficulty="hard",
                incoming_text=(
                    f"The same {system} production "
                    "failure is back."
                ),
                candidates=candidates,
                expected_decision=ATTACH,
                expected_candidate_id=target.candidate_id,
            )
        )

    # ==================================================
    # 6. BRANCH
    # ==================================================

    branch_pairs = [
        (
            "resolve production deployment incident",
            "production incident under investigation",
            "This incident exposed weak monitoring. "
            "Let's redesign production observability.",
        ),
        (
            "fix authentication outage",
            "authentication outage under investigation",
            "This outage exposed gaps in our incident "
            "process. Let's build a response playbook.",
        ),
        (
            "repair agent tool failures",
            "tool failures under investigation",
            "This showed the tool architecture is brittle. "
            "Let's redesign the tool interface.",
        ),
    ]

    for i in range(1, 41):
        goal, state, incoming = rng.choice(
            branch_pairs
        )

        target = Candidate(
            candidate_id=f"branch_parent_{i}",
            goal=goal,
            state=state,
            text=f"{goal}. {state}.",
        )

        candidates = [
            target,
            *rng.sample(distractors(), 2),
        ]

        rng.shuffle(candidates)

        cases.append(
            TTLBV2Case(
                case_id=f"branch_{i:03d}",
                category="branch",
                difficulty="hard",
                incoming_text=incoming,
                candidates=candidates,
                expected_decision=BRANCH,
                expected_candidate_id=target.candidate_id,
            )
        )

    # ==================================================
    # 7. NO MATCH
    # ==================================================

    no_match = [
        "Compare mortgage refinance rates.",
        "Plan a seven-day trip to Japan.",
        "Which one-year finance masters programs start in January?",
        "Create a vegetarian meal plan for next week.",
        "Explain options pricing using a simple example.",
    ]

    for i in range(1, 41):
        candidates = rng.sample(
            distractors(),
            3,
        )

        cases.append(
            TTLBV2Case(
                case_id=f"no_match_{i:03d}",
                category="no_match",
                difficulty="medium",
                incoming_text=rng.choice(no_match),
                candidates=candidates,
                expected_decision=NEW,
            )
        )

    rng.shuffle(cases)

    return cases


def save(
    path="ttlb_v2_holdout.jsonl",
):
    cases = build_v2()

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:
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
        counts[case.category] = (
            counts.get(case.category, 0)
            + 1
        )

    print("TTLB V2 HOLDOUT")
    print("=" * 72)
    print("TOTAL:", len(cases))

    for category, count in sorted(
        counts.items()
    ):
        print(
            f"{category:28} {count}"
        )

    print()
    print(
        "SAVED: ttlb_v2_holdout.jsonl"
    )
    print(
        "IMPORTANT: freeze this dataset before "
        "running/tuning the linker."
    )
