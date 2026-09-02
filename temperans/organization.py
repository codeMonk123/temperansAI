from dataclasses import dataclass, asdict, field
from pathlib import Path

from temperans.sqlite_store import SQLiteStore


@dataclass
class OrganizationConfig:
    organization_id: str
    name: str
    policy_id: str = "default_v0_1"
    retention_days: int = 30
    redact_pii: bool = True
    clarification_enabled: bool = True
    semantic_provider: str = "default"
    allowed_surfaces: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class OrganizationRegistry:
    """
    SQLite-backed organization control plane.

    Public contract intentionally matches the former file-backed registry:
      create(config) -> {"organization": ..., "api_key": ...}
      get(organization_id) -> OrganizationConfig | None
      authenticate(api_key) -> OrganizationConfig | None
    """

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "control.db"
        self.store = SQLiteStore(self.db_path)

    def create(self, config):
        if self.get(config.organization_id) is not None:
            raise ValueError("organization already exists")

        result = self.store.create_organization(
            organization_id=config.organization_id,
            name=config.name,
            config=config.to_dict(),
        )

        return {
            "organization": config.to_dict(),
            "api_key": result["api_key"],
        }

    def get(self, organization_id):
        row = self.store.get_organization(organization_id)
        if row is None:
            return None

        raw = dict(row["config"])
        # Database columns are authoritative for these identity fields.
        raw["organization_id"] = row["organization_id"]
        raw["name"] = row["name"]
        return OrganizationConfig(**raw)

    def authenticate(self, api_key):
        row = self.store.authenticate(api_key)
        if row is None:
            return None

        raw = dict(row["config"])
        raw["organization_id"] = row["organization_id"]
        raw["name"] = row["name"]
        return OrganizationConfig(**raw)

    def close(self):
        self.store.close()
