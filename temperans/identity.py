from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib


@dataclass(frozen=True)
class SurfaceIdentity:
    """
    Identity supplied by an external surface.

    Examples:
        slack:U012ABC
        startup_chatbot:user_872
        internal_app:customer_194

    Temperans should not infer that two surface identities
    are the same human without reliable mapping evidence.
    """

    surface: str
    surface_user_id: str
    workspace_id: str

    def key(self) -> str:
        return (
            f"{self.workspace_id}:"
            f"{self.surface}:"
            f"{self.surface_user_id}"
        )


@dataclass
class CanonicalIdentity:
    """
    Temperans-internal identity.

    One canonical identity may have multiple explicitly
    linked surface identities.
    """

    person_id: str
    workspace_id: str
    identities: list[SurfaceIdentity] = field(
        default_factory=list
    )

    def add_identity(
        self,
        identity: SurfaceIdentity,
    ):
        if identity not in self.identities:
            self.identities.append(identity)

    def to_dict(self):
        return {
            "person_id": self.person_id,
            "workspace_id": self.workspace_id,
            "identities": [
                asdict(identity)
                for identity in self.identities
            ],
        }


@dataclass
class EventIdentity:
    """
    Identity envelope attached to a canonical event.
    """

    workspace_id: str
    person_id: Optional[str]
    surface: str
    surface_user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class IdentityResolver:
    """
    V0 deterministic identity resolver.

    IMPORTANT:
    This does NOT guess identity from conversation text.

    Surface identities remain separate unless an explicit
    mapping is registered.
    """

    def __init__(self):
        self._surface_to_person = {}
        self._people = {}

    def register_person(
        self,
        person_id: str,
        workspace_id: str,
    ) -> CanonicalIdentity:
        person = self._people.get(person_id)

        if person is None:
            person = CanonicalIdentity(
                person_id=person_id,
                workspace_id=workspace_id,
            )
            self._people[person_id] = person

        return person

    def link(
        self,
        person_id: str,
        workspace_id: str,
        surface: str,
        surface_user_id: str,
    ) -> CanonicalIdentity:
        person = self.register_person(
            person_id=person_id,
            workspace_id=workspace_id,
        )

        identity = SurfaceIdentity(
            surface=surface,
            surface_user_id=surface_user_id,
            workspace_id=workspace_id,
        )

        person.add_identity(identity)

        self._surface_to_person[
            identity.key()
        ] = person_id

        return person

    def resolve(
        self,
        workspace_id: str,
        surface: str,
        surface_user_id: str,
    ) -> Optional[str]:
        identity = SurfaceIdentity(
            surface=surface,
            surface_user_id=surface_user_id,
            workspace_id=workspace_id,
        )

        return self._surface_to_person.get(
            identity.key()
        )

    def anonymous_person_id(
        self,
        workspace_id: str,
        surface: str,
        surface_user_id: str,
    ) -> str:
        """
        Stable pseudonymous ID for an unlinked identity.

        This does NOT imply equivalence with identities on
        any other surface.
        """

        raw = (
            f"{workspace_id}:"
            f"{surface}:"
            f"{surface_user_id}"
        )

        digest = hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:16]

        return f"surface_{digest}"

    def people(self):
        return {
            person_id: person.to_dict()
            for person_id, person
            in self._people.items()
        }
