from pathlib import Path

from temperans.organization import (
    OrganizationConfig,
    OrganizationRegistry,
)
from temperans.org_runtime import (
    OrganizationRuntime,
)


class TemperansPlatform:
    """
    Multi-organization control plane.

    Same code path for Boardy, Partner B, Partner C, etc.
    """

    def __init__(
        self,
        root=".temperans/platform",
    ):
        self.root = Path(root)
        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.organizations = (
            OrganizationRegistry(
                self.root / "control"
            )
        )

        self._runtimes = {}

    def create_organization(
        self,
        *,
        organization_id,
        name,
        allowed_surfaces=None,
        retention_days=30,
    ):
        config = OrganizationConfig(
            organization_id=
                organization_id,
            name=name,
            retention_days=
                retention_days,
            allowed_surfaces=
                allowed_surfaces or [],
        )

        return self.organizations.create(
            config
        )

    def authenticate(
        self,
        api_key,
    ):
        return (
            self.organizations
            .authenticate(api_key)
        )

    def runtime(
        self,
        organization_id,
    ):
        if (
            organization_id
            in self._runtimes
        ):
            return self._runtimes[
                organization_id
            ]

        config = (
            self.organizations.get(
                organization_id
            )
        )

        if config is None:
            raise KeyError(
                "organization not found"
            )

        runtime = OrganizationRuntime(
            root=self.root,
            config=config,
        )

        self._runtimes[
            organization_id
        ] = runtime

        return runtime

    def observe_with_key(
        self,
        *,
        api_key,
        payload,
    ):
        config = self.authenticate(
            api_key
        )

        if config is None:
            raise PermissionError(
                "invalid API key"
            )

        return self.runtime(
            config.organization_id
        ).observe(payload)
