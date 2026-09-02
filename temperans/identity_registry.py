import uuid


class IdentityRegistry:
    """
    Identity registry backed by a shared SQLiteStore when supplied.

    Compatibility:
    - legacy callers may still pass a JSON path only; they should migrate.
    - OrganizationRuntime should pass store=... and organization_id=....

    Tenant identity key:
      (organization_id, workspace_id, surface, external_user_id)
    """

    def __init__(self, path=None, organization_id="default", store=None):
        self.path = path
        self.organization_id = organization_id
        self.store = store

        if self.store is None:
            raise ValueError(
                "IdentityRegistry now requires SQLiteStore via store="
            )

    def link(self, workspace_id, surface, external_user_id, person_id):
        self.store.link_identity(
            organization_id=self.organization_id,
            workspace_id=str(workspace_id),
            surface=str(surface),
            external_user_id=str(external_user_id),
            person_id=str(person_id),
        )
        return {
            "organization_id": self.organization_id,
            "workspace_id": workspace_id,
            "surface": surface,
            "external_user_id": external_user_id,
            "person_id": person_id,
        }

    def resolve(self, workspace_id, surface, external_user_id, create=True):
        existing = self.store.resolve_identity(
            organization_id=self.organization_id,
            workspace_id=str(workspace_id),
            surface=str(surface),
            external_user_id=str(external_user_id),
        )
        if existing is not None:
            return existing

        if not create:
            return None

        person_id = "person_" + uuid.uuid4().hex[:16]
        self.store.link_identity(
            organization_id=self.organization_id,
            workspace_id=str(workspace_id),
            surface=str(surface),
            external_user_id=str(external_user_id),
            person_id=person_id,
        )
        return person_id
