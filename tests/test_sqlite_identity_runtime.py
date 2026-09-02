from temperans.platform import TemperansPlatform


def make_org(platform, oid):
    return platform.create_organization(
        organization_id=oid,
        name=oid,
    )


def test_runtime_identity_is_written_to_shared_sqlite(tmp_path):
    root = tmp_path / "platform"
    p = TemperansPlatform(root)
    make_org(p, "a")
    r = p.runtime("a")

    person = r.identities.resolve(
        "workspace",
        "slack",
        "U1",
        True,
    )

    assert person.startswith("person_")
    assert r.sqlite.resolve_identity(
        organization_id="a",
        workspace_id="workspace",
        surface="slack",
        external_user_id="U1",
    ) == person

    assert not (
        r.root / "identities.json"
    ).exists()


def test_identical_external_identity_is_tenant_scoped(tmp_path):
    root = tmp_path / "platform"
    p = TemperansPlatform(root)
    make_org(p, "a")
    make_org(p, "b")

    a = p.runtime("a")
    b = p.runtime("b")

    a.link_identity(
        workspace_id="w",
        surface="slack",
        external_user_id="U1",
        person_id="person_a",
    )

    b.link_identity(
        workspace_id="w",
        surface="slack",
        external_user_id="U1",
        person_id="person_b",
    )

    assert a.identities.resolve(
        "w", "slack", "U1", False
    ) == "person_a"

    assert b.identities.resolve(
        "w", "slack", "U1", False
    ) == "person_b"


def test_identity_survives_platform_restart(tmp_path):
    root = tmp_path / "platform"

    p1 = TemperansPlatform(root)
    created = make_org(p1, "a")
    key = created["api_key"]

    r1 = p1.runtime("a")
    r1.link_identity(
        workspace_id="w",
        surface="slack",
        external_user_id="U1",
        person_id="person_fixed",
    )

    p2 = TemperansPlatform(root)
    assert (
        p2.authenticate(key)
        .organization_id
        == "a"
    )

    r2 = p2.runtime("a")

    assert r2.identities.resolve(
        "w",
        "slack",
        "U1",
        False,
    ) == "person_fixed"


def test_observe_uses_sqlite_identity(tmp_path):
    root = tmp_path / "platform"
    p = TemperansPlatform(root)
    created = make_org(p, "a")

    result = p.observe_with_key(
        api_key=created["api_key"],
        payload={
            "event_id": "evt1",
            "workspace_id": "w",
            "external_user_id": "U1",
            "surface": "generic_chatbot",
            "conversation_id": "c1",
            "message": "Investigate PROD-218",
        },
    )

    r = p.runtime("a")
    person = r.identities.resolve(
        "w",
        "generic_chatbot",
        "U1",
        False,
    )

    assert person is not None
    assert result["person_id"] == person
    assert not (
        r.root / "identities.json"
    ).exists()
