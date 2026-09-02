from dataclasses import dataclass, field, asdict
import re


@dataclass
class LifecycleEvidence:
    reopen_signal: bool = False
    recurrence_terms: list[str] = field(
        default_factory=list
    )
    reasons: list[str] = field(
        default_factory=list
    )

    def to_dict(self):
        return asdict(self)


class LifecycleEvidenceEngine:
    """
    Deterministic lifecycle evidence.

    This does NOT independently prove trajectory identity.

    It answers:
        Does the incoming interaction linguistically
        indicate recurrence/reopening?

    Candidate identity is still handled elsewhere.
    """

    REOPEN_PATTERNS = [
        r"\bthe same\b.*\bis back\b",
        r"\bis back\b",
        r"\brecurr(?:ed|ing|ence)\b",
        r"\bhappening again\b",
        r"\bfailing again\b",
        r"\bbroke again\b",
        r"\breturned\b",
        r"\breappeared\b",
    ]

    def extract(
        self,
        *,
        lifecycle,
        incoming_text,
    ):
        evidence = LifecycleEvidence()

        if lifecycle != "resolved":
            return evidence

        text = incoming_text or ""

        for pattern in self.REOPEN_PATTERNS:
            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                evidence.recurrence_terms.append(
                    pattern
                )

        if evidence.recurrence_terms:
            evidence.reopen_signal = True
            evidence.reasons.append(
                "resolved trajectory has explicit "
                "recurrence language"
            )

        return evidence
