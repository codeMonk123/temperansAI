from dataclasses import dataclass


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str


class TrajectoryPolicy:
    """
    Workspace/organization policy seam.

    V1 deliberately preserves frozen linker-v0.1 behavior.
    Later, corrections can calibrate policy per organization
    without forking the Temperans engine.
    """

    policy_id = "default_v0_1"

    def allow_surface(self, config, surface):
        allowed = config.allowed_surfaces

        if allowed and surface not in allowed:
            return PolicyDecision(
                False,
                "surface is not enabled for organization",
            )

        return PolicyDecision(
            True,
            "surface allowed",
        )

    def clarification_enabled(self, config):
        return bool(
            config.clarification_enabled
        )


class PolicyRegistry:
    def __init__(self):
        self.policies = {
            "default_v0_1":
                TrajectoryPolicy()
        }

    def get(self, policy_id):
        if policy_id not in self.policies:
            raise KeyError(
                f"unknown policy: {policy_id}"
            )
        return self.policies[policy_id]
