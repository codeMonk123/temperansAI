from temperans.organization import OrganizationConfig, OrganizationRegistry
from temperans.platform import TemperansPlatform


def test_registry_uses_sqlite(tmp_path):
    root = tmp_path / "control"
    registry = OrganizationRegistry(root)
    assert registry.db_path == root / "control.db"
    assert registry.db_path.exists()
    registry.close()


def test_registry_contract_create_get_authenticate(tmp_path):
    registry = OrganizationRegistry(tmp_path / "control")
    cfg = OrganizationConfig(
        organization_id="xyzabc321",
        name="XYZABC321 Inc.",
        allowed_surfaces=["slack", "chat"],
    )
    created = registry.create(cfg)
    assert created["organization"]["organization_id"] == "xyzabc321"
    assert created["api_key"].startswith("tmp_live_")

    loaded = registry.get("xyzabc321")
    assert loaded == cfg

    authenticated = registry.authenticate(created["api_key"])
    assert authenticated == cfg
    registry.close()


def test_registry_persists_across_restart(tmp_path):
    root = tmp_path / "control"
    first = OrganizationRegistry(root)
    cfg = OrganizationConfig(organization_id="xyzabc321", name="XYZABC321 Inc.")
    created = first.create(cfg)
    key = created["api_key"]
    first.close()

    second = OrganizationRegistry(root)
    assert second.get("xyzabc321") == cfg
    assert second.authenticate(key) == cfg
    second.close()


def test_registry_rejects_duplicate_org(tmp_path):
    registry = OrganizationRegistry(tmp_path / "control")
    cfg = OrganizationConfig(organization_id="xyzabc321", name="XYZABC321 Inc.")
    registry.create(cfg)

    try:
        registry.create(cfg)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "already exists" in str(exc)
    finally:
        registry.close()


def test_platform_public_contract_survives_sqlite_control_plane(tmp_path):
    root = tmp_path / "platform"

    first = TemperansPlatform(root)
    created = first.create_organization(
        organization_id="xyzabc321",
        name="XYZABC321 Inc.",
        allowed_surfaces=["generic_chatbot"],
    )
    key = created["api_key"]

    auth = first.authenticate(key)
    assert auth.organization_id == "xyzabc321"
    assert auth.name == "XYZABC321 Inc."
    assert auth.allowed_surfaces == ["generic_chatbot"]

    # New platform instance = process restart. Authentication must survive.
    second = TemperansPlatform(root)
    auth2 = second.authenticate(key)
    assert auth2.organization_id == "xyzabc321"
    assert second.runtime("xyzabc321").config.organization_id == "xyzabc321"


def test_two_orgs_remain_distinct_through_platform(tmp_path):
    platform = TemperansPlatform(tmp_path / "platform")
    a = platform.create_organization(
        organization_id="xyzabc321",
        name="XYZABC321 Inc.",
    )
    b = platform.create_organization(
        organization_id="xyzabc322",
        name="XYZABC322 Inc.",
    )

    assert a["api_key"] != b["api_key"]
    assert platform.authenticate(a["api_key"]).organization_id == "xyzabc321"
    assert platform.authenticate(b["api_key"]).organization_id == "xyzabc322"
