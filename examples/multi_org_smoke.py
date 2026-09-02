import shutil
from pathlib import Path

from temperans.platform import (
    TemperansPlatform,
)


root = Path(
    ".temperans/multi-org-smoke"
)

if root.exists():
    shutil.rmtree(root)

platform = TemperansPlatform(
    root
)

boardy = (
    platform.create_organization(
        organization_id="org_boardy",
        name="Boardy",
        allowed_surfaces=[
            "boardy_chat",
            "boardy_product",
        ],
    )
)

partner = (
    platform.create_organization(
        organization_id="org_partner_b",
        name="Partner B",
        allowed_surfaces=[
            "support_bot",
        ],
    )
)

boardy_key = boardy[
    "api_key"
]

partner_key = partner[
    "api_key"
]

# Boardy: goal is optional.
a = platform.observe_with_key(
    api_key=boardy_key,
    payload={
        "workspace_id":
            "boardy_prod",
        "surface":
            "boardy_chat",
        "external_user_id":
            "user_17",
        "conversation_id":
            "call_1",
        "message":
            "I want introductions "
            "to fintech investors.",
    },
)

b = platform.observe_with_key(
    api_key=boardy_key,
    payload={
        "workspace_id":
            "boardy_prod",
        "surface":
            "boardy_chat",
        "external_user_id":
            "user_17",
        "conversation_id":
            "call_2",
        "message":
            "Can we continue with "
            "those investor introductions?",
    },
)

# Partner B uses identical external user ID.
# It MUST remain isolated.
c = platform.observe_with_key(
    api_key=partner_key,
    payload={
        "workspace_id":
            "production",
        "surface":
            "support_bot",
        "external_user_id":
            "user_17",
        "conversation_id":
            "support_1",
        "message":
            "Production deployment "
            "is failing.",
    },
)

assert (
    a["organization_id"]
    == "org_boardy"
)

assert (
    c["organization_id"]
    == "org_partner_b"
)

assert (
    a["person_id"]
    != c["person_id"]
)

assert (
    a["trajectory_id"]
    != c["trajectory_id"]
)

assert (
    b["trajectory_id"]
    == a["trajectory_id"]
)

# API key must not authenticate as another org.
assert (
    platform.authenticate(
        boardy_key
    ).organization_id
    == "org_boardy"
)

print(
    "MULTI-ORG ISOLATION: PASS"
)

print(
    "Boardy trajectory:",
    a["trajectory_id"],
)

print(
    "Partner B trajectory:",
    c["trajectory_id"],
)

print(
    "Boardy person:",
    a["person_id"],
)

print(
    "Partner B person:",
    c["person_id"],
)
