from dataclasses import dataclass, asdict
from enum import Enum
import re


class AnchorStrength(str, Enum):
    BOUNDARY = "boundary"
    STRONG = "strong"
    MEDIUM = "medium"
    SCOPE = "scope"


ANCHOR_SEMANTICS = {
    # Identity boundaries.
    "customer": AnchorStrength.BOUNDARY,
    "tenant": AnchorStrength.BOUNDARY,
    "account": AnchorStrength.BOUNDARY,

    # Strong trajectory identifiers.
    "ticket": AnchorStrength.STRONG,
    "incident": AnchorStrength.STRONG,
    "pr": AnchorStrength.STRONG,
    "slack_thread": AnchorStrength.STRONG,
    "email_thread": AnchorStrength.STRONG,
    "trace_id": AnchorStrength.STRONG,

    # Supporting evidence.
    "error_sig": AnchorStrength.MEDIUM,
    "file": AnchorStrength.MEDIUM,
    "env_var": AnchorStrength.MEDIUM,
    "git_sha": AnchorStrength.MEDIUM,
    "url": AnchorStrength.MEDIUM,

    # Candidate scope only.
    "repo": AnchorStrength.SCOPE,
    "project": AnchorStrength.SCOPE,
}


@dataclass(frozen=True)
class Anchor:
    type: str
    value: str
    strength: AnchorStrength

    def key(self):
        return (
            self.type,
            self.value.lower(),
        )

    def to_dict(self):
        result = asdict(self)
        result["strength"] = self.strength.value
        return result


class AnchorExtractor:
    """
    Deterministic V0 anchor extraction.

    No model calls.
    Same text -> same anchors on every replay.
    """

    TICKET = re.compile(
        r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b"
    )

    PR = re.compile(
        r"\b(?:PR|pull request|pull)\s*#?\s*(\d+)\b",
        re.IGNORECASE,
    )

    INCIDENT = re.compile(
        r"\b(?:INC|INCIDENT)[-_ ]?(\d+)\b",
        re.IGNORECASE,
    )

    UUID = re.compile(
        r"\b[0-9a-fA-F]{8}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{12}\b"
    )

    GIT_SHA = re.compile(
        r"\b[0-9a-fA-F]{7,40}\b"
    )

    FILE = re.compile(
        r"\b[\w./-]+\."
        r"(?:py|ts|tsx|js|jsx|go|rs|java|"
        r"yaml|yml|json|toml|sql|sh)\b",
        re.IGNORECASE,
    )

    ENV_VAR = re.compile(
        r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b"
    )

    URL = re.compile(
        r"https?://[^\s<>\"]+",
        re.IGNORECASE,
    )

    CUSTOMER = re.compile(
        r"\bcustomer[_\s:-]+([A-Za-z0-9_-]+)\b",
        re.IGNORECASE,
    )

    TENANT = re.compile(
        r"\btenant[_\s:-]+([A-Za-z0-9_-]+)\b",
        re.IGNORECASE,
    )

    ACCOUNT = re.compile(
        r"\baccount[_\s:-]+([A-Za-z0-9_-]+)\b",
        re.IGNORECASE,
    )

    REPO = re.compile(
        r"\b(?:repo|repository)"
        r"[_\s:=]+([A-Za-z0-9_.-]+)\b",
        re.IGNORECASE,
    )

    PROJECT = re.compile(
        r"\bproject"
        r"[_\s:=]+([A-Za-z0-9_.-]+)\b",
        re.IGNORECASE,
    )

    def _anchor(self, type_, value):
        return Anchor(
            type=type_,
            value=str(value).strip(),
            strength=ANCHOR_SEMANTICS[type_],
        )

    def extract(self, text):
        text = text or ""
        anchors = []

        uuid_matches = list(
            self.UUID.finditer(text)
        )

        incident_matches = list(
            self.INCIDENT.finditer(text)
        )

        protected_spans = [
            match.span()
            for match in (
                uuid_matches
                + incident_matches
            )
        ]

        def protected(start, end):
            return any(
                start < protected_end
                and end > protected_start
                for (
                    protected_start,
                    protected_end,
                ) in protected_spans
            )

        for match in self.TICKET.finditer(text):
            if protected(
                match.start(),
                match.end(),
            ):
                continue

            anchors.append(
                self._anchor(
                    "ticket",
                    match.group(1).upper(),
                )
            )

        for value in self.PR.findall(text):
            anchors.append(
                self._anchor("pr", value)
            )

        for match in incident_matches:
            anchors.append(
                self._anchor(
                    "incident",
                    match.group(1),
                )
            )

        for match in uuid_matches:
            anchors.append(
                self._anchor(
                    "trace_id",
                    match.group(0).lower(),
                )
            )

        for value in self.FILE.findall(text):
            # FILE has a capture group for extension,
            # so use finditer to recover full match below.
            pass

        for match in self.FILE.finditer(text):
            anchors.append(
                self._anchor(
                    "file",
                    match.group(0),
                )
            )

        for value in self.ENV_VAR.findall(text):
            anchors.append(
                self._anchor("env_var", value)
            )

        for value in self.URL.findall(text):
            anchors.append(
                self._anchor("url", value)
            )

        for value in self.CUSTOMER.findall(text):
            anchors.append(
                self._anchor(
                    "customer",
                    value.lower(),
                )
            )

        for value in self.TENANT.findall(text):
            anchors.append(
                self._anchor(
                    "tenant",
                    value.lower(),
                )
            )

        for value in self.ACCOUNT.findall(text):
            anchors.append(
                self._anchor(
                    "account",
                    value.lower(),
                )
            )

        for value in self.REPO.findall(text):
            anchors.append(
                self._anchor(
                    "repo",
                    value.lower(),
                )
            )

        for value in self.PROJECT.findall(text):
            anchors.append(
                self._anchor(
                    "project",
                    value.lower(),
                )
            )

        # SHA last because many structured identifiers
        # can otherwise look hex-like.
        for match in self.GIT_SHA.finditer(text):
            if protected(
                match.start(),
                match.end(),
            ):
                continue

            anchors.append(
                self._anchor(
                    "git_sha",
                    match.group(0).lower(),
                )
            )

        # Stable deterministic de-duplication.
        unique = {}

        for anchor in anchors:
            unique[anchor.key()] = anchor

        return sorted(
            unique.values(),
            key=lambda x: (
                x.type,
                x.value.lower(),
            ),
        )
