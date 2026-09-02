from dataclasses import dataclass, asdict, field
import re


@dataclass
class LinkageEvidence:
    positive: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    branch_signals: list[str] = field(default_factory=list)
    continuation_signals: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    @property
    def has_contradiction(self):
        return bool(self.contradictions)

    @property
    def has_branch_signal(self):
        return bool(self.branch_signals)

    @property
    def has_continuation_signal(self):
        return bool(self.continuation_signals)


class LinkageEvidenceExtractor:
    """
    V0 deterministic evidence layer.

    This is NOT the final trajectory linker.

    Its purpose is to extract evidence that generic
    semantic similarity misses:
      - identity contradictions
      - continuation language
      - branching language
      - exact artifact/entity anchors
    """

    CONTINUATION_PATTERNS = [
        r"\bstill\b",
        r"\bagain\b",
        r"\bafter that\b",
        r"\bafter the change\b",
        r"\bnow\b.*\bbut\b",
        r"\bwe found\b",
        r"\bturns out\b",
        r"\bthe same\b.*\bis back\b",
    ]

    BRANCH_PATTERNS = [
        r"\bthis showed\b",
        r"\bthis incident showed\b",
        r"\bthis revealed\b",
        r"\bbecause of this\b",
        r"\bnow design\b",
        r"\bnow let's\b",
        r"\blet's redesign\b",
    ]

    CUSTOMER_PATTERN = re.compile(
        r"\bcustomer\s+([a-z0-9_-]+)\b",
        re.IGNORECASE,
    )

    REPO_PATTERN = re.compile(
        r"\b(?:repo|repository)\s*[:=#]?\s*"
        r"([a-zA-Z0-9_.-]+)",
        re.IGNORECASE,
    )

    PR_PATTERN = re.compile(
        r"\bPR\s*#?\s*(\d+)\b",
        re.IGNORECASE,
    )

    TICKET_PATTERN = re.compile(
        r"\b([A-Z][A-Z0-9]+-\d+)\b",
    )

    def _matches(self, patterns, text):
        lower = text.lower()

        return [
            pattern
            for pattern in patterns
            if re.search(
                pattern,
                lower,
                flags=re.IGNORECASE,
            )
        ]

    def _single(self, pattern, text):
        match = pattern.search(text)

        if not match:
            return None

        return match.group(1).lower()

    def _compare_anchor(
        self,
        name,
        left,
        right,
        evidence,
    ):
        if not left or not right:
            return

        if left == right:
            evidence.positive.append(
                f"same {name}: {left}"
            )
        else:
            evidence.contradictions.append(
                f"different {name}: "
                f"{left} vs {right}"
            )

    def extract(
        self,
        candidate_text,
        new_text,
    ):
        evidence = LinkageEvidence()

        # -----------------------------------------
        # Continuation language
        # -----------------------------------------

        continuation = self._matches(
            self.CONTINUATION_PATTERNS,
            new_text,
        )

        for pattern in continuation:
            evidence.continuation_signals.append(
                f"continuation language: {pattern}"
            )

        # -----------------------------------------
        # Branch language
        # -----------------------------------------

        branch = self._matches(
            self.BRANCH_PATTERNS,
            new_text,
        )

        for pattern in branch:
            evidence.branch_signals.append(
                f"branch language: {pattern}"
            )

        # -----------------------------------------
        # Exact identity anchors
        # -----------------------------------------

        candidate_customer = self._single(
            self.CUSTOMER_PATTERN,
            candidate_text,
        )

        new_customer = self._single(
            self.CUSTOMER_PATTERN,
            new_text,
        )

        self._compare_anchor(
            "customer",
            candidate_customer,
            new_customer,
            evidence,
        )

        candidate_repo = self._single(
            self.REPO_PATTERN,
            candidate_text,
        )

        new_repo = self._single(
            self.REPO_PATTERN,
            new_text,
        )

        self._compare_anchor(
            "repository",
            candidate_repo,
            new_repo,
            evidence,
        )

        candidate_pr = self._single(
            self.PR_PATTERN,
            candidate_text,
        )

        new_pr = self._single(
            self.PR_PATTERN,
            new_text,
        )

        self._compare_anchor(
            "PR",
            candidate_pr,
            new_pr,
            evidence,
        )

        candidate_ticket = self._single(
            self.TICKET_PATTERN,
            candidate_text,
        )

        new_ticket = self._single(
            self.TICKET_PATTERN,
            new_text,
        )

        self._compare_anchor(
            "ticket",
            candidate_ticket,
            new_ticket,
            evidence,
        )

        return evidence
