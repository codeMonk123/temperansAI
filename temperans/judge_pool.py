from dataclasses import dataclass, asdict


@dataclass
class JudgeAttempt:
    provider: str
    success: bool
    error: str = ""

    def to_dict(self):
        return asdict(self)


class FrontierJudgePool:
    """
    Sequential fallback across semantic judges.

    Temperans owns the routing policy.
    Frontier providers are replaceable semantic brains.
    """

    def __init__(self, judges=None):
        self.judges = judges or []

    def add(self, provider, judge):
        self.judges.append((provider, judge))

    def judge(
        self,
        trajectory,
        conversation,
        structural_evidence=None,
    ):
        attempts = []

        for provider, judge in self.judges:
            try:
                result = judge.judge(
                    trajectory=trajectory,
                    conversation=conversation,
                    structural_evidence=structural_evidence,
                )

                attempts.append(
                    JudgeAttempt(
                        provider=provider,
                        success=True,
                    )
                )

                return result, provider, attempts

            except Exception as exc:
                attempts.append(
                    JudgeAttempt(
                        provider=provider,
                        success=False,
                        error=(
                            f"{type(exc).__name__}: "
                            f"{str(exc)[:240]}"
                        ),
                    )
                )

        return None, None, attempts
