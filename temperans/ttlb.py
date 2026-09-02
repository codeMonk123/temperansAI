from dataclasses import dataclass, asdict
from typing import Optional
import json


ATTACH = "attach"
BRANCH = "branch"
NEW = "new"


@dataclass
class TTLBCase:
    case_id: str
    category: str
    new_text: str
    candidate_text: str
    label: str
    difficulty: str = "medium"
    notes: str = ""

    # Observable candidate-trajectory state.
    # These fields are INPUTS to the linker, never derived
    # from the ground-truth linkage label.
    candidate_lifecycle: str = "active"
    candidate_unresolved: bool = False

    def to_dict(self):
        return asdict(self)


def build_v0_cases():
    """
    Small deterministic seed benchmark.

    This is intentionally hand-readable.
    Later generators will scale TTLB to thousands
    of cases from real/synthetic trajectories.
    """

    cases = [
        # ------------------------------------------------
        # Different wording, same evolving goal
        # ------------------------------------------------
        TTLBCase(
            case_id="attach_deploy_001",
            category="different_words_same_goal",
            candidate_text=(
                "Production deployment is failing after release. "
                "We need to restore the service."
            ),
            new_text=(
                "The build works now but the container dies "
                "while loading runtime configuration."
            ),
            label=ATTACH,
            difficulty="hard",
            candidate_unresolved=True,
        ),

        TTLBCase(
            case_id="attach_deploy_002",
            category="different_words_same_goal",
            candidate_text=(
                "Service crashes during startup. "
                "Investigate production configuration."
            ),
            new_text=(
                "We found the missing production environment "
                "variable that caused the incident."
            ),
            label=ATTACH,
            difficulty="hard",
            candidate_unresolved=True,
        ),

        # ------------------------------------------------
        # Same broad project, different work
        # ------------------------------------------------
        TTLBCase(
            case_id="new_temperans_001",
            category="same_project_different_goal",
            candidate_text=(
                "Package Temperans and publish the Python SDK."
            ),
            new_text=(
                "Prepare the Temperans investor pitch and "
                "fundraising strategy."
            ),
            label=NEW,
            difficulty="hard",
        ),

        TTLBCase(
            case_id="new_repo_001",
            category="same_repo_different_bug",
            candidate_text=(
                "Fix trajectory routing in temperans/router.py."
            ),
            new_text=(
                "Repair the PyPI packaging metadata in "
                "the Temperans repository."
            ),
            label=NEW,
            difficulty="hard",
        ),

        # ------------------------------------------------
        # Completely unrelated
        # ------------------------------------------------
        TTLBCase(
            case_id="new_unrelated_001",
            category="unrelated",
            candidate_text=(
                "Debug the production deployment failure."
            ),
            new_text=(
                "Compare one-year robotics master's programs "
                "with January admission."
            ),
            label=NEW,
            difficulty="easy",
        ),

        # ------------------------------------------------
        # Branch
        # ------------------------------------------------
        TTLBCase(
            case_id="branch_001",
            category="branch",
            candidate_text=(
                "Resolve the production deployment incident."
            ),
            new_text=(
                "This incident showed that our monitoring is "
                "weak. Let's redesign production observability."
            ),
            label=BRANCH,
            difficulty="hard",
        ),

        TTLBCase(
            case_id="branch_002",
            category="branch",
            candidate_text=(
                "Build the Temperans Slack connector."
            ),
            new_text=(
                "Now design enterprise privacy controls for "
                "Slack data captured by Temperans."
            ),
            label=BRANCH,
            difficulty="hard",
        ),

        # ------------------------------------------------
        # Reopen maps to ATTACH in routing V1
        # ------------------------------------------------
        TTLBCase(
            case_id="attach_reopen_001",
            category="reopen",
            candidate_text=(
                "The checkout login crash was fixed and "
                "the incident was resolved."
            ),
            new_text=(
                "The same checkout crash after login is back."
            ),
            label=ATTACH,
            difficulty="hard",
        ),

        # ------------------------------------------------
        # Same topic, different entity
        # ------------------------------------------------
        TTLBCase(
            case_id="new_customer_001",
            category="same_topic_different_entity",
            candidate_text=(
                "Customer A cannot activate enterprise SSO."
            ),
            new_text=(
                "Customer B cannot activate enterprise SSO."
            ),
            label=NEW,
            difficulty="hard",
        ),

        # ------------------------------------------------
        # Vague continuation
        # ------------------------------------------------
        TTLBCase(
            case_id="attach_vague_001",
            category="vague_continuation",
            candidate_text=(
                "Investigate why the deployment fails while "
                "loading production configuration."
            ),
            new_text=(
                "Still doesn't work after that change."
            ),
            label=ATTACH,
            difficulty="hard",
            notes=(
                "Requires prior trajectory state; raw text "
                "similarity should struggle."
            ),
            candidate_unresolved=True,
        ),
    ]

    return cases


def save_jsonl(path, cases=None):
    cases = cases or build_v0_cases()

    with open(path, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(
                json.dumps(
                    case.to_dict(),
                    ensure_ascii=False,
                )
                + "\n"
            )


def summary(cases=None):
    cases = cases or build_v0_cases()

    counts = {}

    for case in cases:
        key = (
            case.label,
            case.difficulty,
        )

        counts[key] = counts.get(key, 0) + 1

    return {
        "cases": len(cases),
        "distribution": counts,
    }
