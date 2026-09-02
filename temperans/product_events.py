from dataclasses import dataclass


@dataclass
class ProductEventResult:
    trajectory_id: str
    lifecycle: str
    outcome: str


class ProductEventProcessor:
    """
    Applies trusted product/business outcomes to an
    already-resolved Temperans trajectory.

    V0 deliberately requires trajectory identity to
    already be known. We do not semantically guess which
    trajectory a product event belongs to.
    """

    def apply(
        self,
        trajectory,
        *,
        event_name,
        status,
        description="",
    ):
        outcome = (
            description.strip()
            or f"{event_name}={status}"
        )

        if outcome not in trajectory.outcomes:
            trajectory.outcomes.append(outcome)

        # V0 resolution policy.
        if (
            event_name == "deployment_validation"
            and status == "success"
        ):
            trajectory.lifecycle = "resolved"

            trajectory.current_state = (
                "deployment validated successfully"
            )

            if (
                "deployment validated successfully"
                not in trajectory.recent_context
            ):
                trajectory.recent_context.append(
                    "deployment validated successfully"
                )

        return ProductEventResult(
            trajectory_id=trajectory.trajectory_id,
            lifecycle=trajectory.lifecycle,
            outcome=outcome,
        )
