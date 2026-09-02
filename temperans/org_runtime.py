from pathlib import Path

from temperans.event_adapter import (
    GenericChatbotAdapter,
)
from temperans.identity_registry import (
    IdentityRegistry,
)
from temperans.pilot_service import (
    PilotService,
)
from temperans.policy import PolicyRegistry
from temperans.workstate_extractor_v1 import (
    WorkStateExtractor,
)


class OrganizationRuntime:
    """
    One reusable runtime contract for every organization.

    Organization-specific state is isolated under:
        <root>/organizations/<organization_id>/
    """

    def __init__(
        self,
        *,
        root,
        config,
        adapter=None,
        extractor=None,
        policies=None,
    ):
        self.root = (
            Path(root)
            / "organizations"
            / config.organization_id
        )

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.config = config

        self.adapter = (
            adapter
            or GenericChatbotAdapter()
        )

        self.extractor = (
            extractor
            or WorkStateExtractor()
        )

        self.policies = (
            policies
            or PolicyRegistry()
        )

        self.policy = (
            self.policies.get(
                config.policy_id
            )
        )

        self.service = PilotService(
            self.root
        )

        self.identities = (
            IdentityRegistry(
                self.root
                / "identities.json"
            )
        )

    def observe(self, payload):
        event = self.adapter.normalize(
            organization_id=
                self.config.organization_id,
            payload=payload,
        )

        surface_policy = (
            self.policy.allow_surface(
                self.config,
                event.surface,
            )
        )

        if not surface_policy.allowed:
            raise PermissionError(
                surface_policy.reason
            )

        person_id = (
            self.identities.resolve(
                event.workspace_id,
                event.surface,
                event.external_user_id,
                True,
            )
        )

        candidates = (
            self.service.trajectories(
                event.workspace_id,
                person_id,
            )
        )

        work = self.extractor.extract(
            text=event.text,
            supplied_goal=event.goal,
            entities=event.entities,
            artifacts=event.artifacts,
            trajectory_context=candidates,
        )

        result = self.service.observe({
            "workspace_id":
                event.workspace_id,
            "person_id":
                person_id,
            "external_user_id":
                event.external_user_id,
            "conversation_id":
                event.conversation_id,
            "surface":
                event.surface,
            "goal":
                work.goal,
            "current_problem":
                work.current_problem,
            "entities":
                work.entities,
            "artifacts":
                work.artifacts,
            "properties":
                event.properties,
        })

        result[
            "organization_id"
        ] = self.config.organization_id

        result[
            "person_id"
        ] = person_id

        return result

    def link_identity(
        self,
        *,
        workspace_id,
        surface,
        external_user_id,
        person_id,
    ):
        return self.identities.link(
            workspace_id,
            surface,
            external_user_id,
            person_id,
        )
