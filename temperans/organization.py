from dataclasses import dataclass, asdict, field
import hashlib
import json
from pathlib import Path
import secrets


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
    File-backed V1 control plane.

    Production replacement can be Postgres without changing the
    organization/runtime contracts.
    """

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "organizations.json"
        self.data = {"organizations": {}, "api_keys": {}}
        self._load()

    def _load(self):
        if self.path.exists():
            self.data = json.loads(
                self.path.read_text(encoding="utf-8")
            )

    def _save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(self.path)

    @staticmethod
    def _hash_key(key):
        return hashlib.sha256(
            key.encode("utf-8")
        ).hexdigest()

    def create(self, config):
        if config.organization_id in self.data["organizations"]:
            raise ValueError("organization already exists")

        self.data["organizations"][
            config.organization_id
        ] = config.to_dict()

        api_key = "tmp_live_" + secrets.token_urlsafe(24)

        self.data["api_keys"][
            self._hash_key(api_key)
        ] = config.organization_id

        self._save()

        return {
            "organization": config.to_dict(),
            "api_key": api_key,
        }

    def get(self, organization_id):
        raw = self.data["organizations"].get(
            organization_id
        )
        return (
            OrganizationConfig(**raw)
            if raw else None
        )

    def authenticate(self, api_key):
        if not api_key:
            return None

        organization_id = self.data[
            "api_keys"
        ].get(self._hash_key(api_key))

        return (
            self.get(organization_id)
            if organization_id
            else None
        )
