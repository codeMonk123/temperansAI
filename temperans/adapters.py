from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ProviderContext:
    provider: str
    model: Optional[str] = None
    external_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TemperansAdapter:
    """
    Base adapter for converting provider interactions into
    canonical Temperans events.
    """

    provider = "unknown"

    def __init__(
        self,
        trace,
        model=None,
    ):
        self.trace = trace
        self.model = model

    def _metadata(
        self,
        external_id=None,
        **metadata,
    ):
        result = {
            "provider": self.provider,
        }

        if self.model:
            result["model"] = self.model

        if external_id:
            result["external_id"] = external_id

        result.update(metadata)

        return result

    def human(
        self,
        text,
        external_id=None,
        thread_id=None,
        **metadata,
    ):
        return self.trace.human(
            text,
            thread_id=thread_id,
            **self._metadata(
                external_id=external_id,
                **metadata,
            ),
        )

    def agent(
        self,
        text,
        actor_id=None,
        external_id=None,
        thread_id=None,
        **metadata,
    ):
        return self.trace.agent(
            text,
            actor_id=actor_id or self.provider,
            thread_id=thread_id,
            **self._metadata(
                external_id=external_id,
                **metadata,
            ),
        )

    def tool(
        self,
        name,
        status="success",
        external_id=None,
        thread_id=None,
        **metadata,
    ):
        return self.trace.tool(
            name,
            status=status,
            thread_id=thread_id,
            **self._metadata(
                external_id=external_id,
                **metadata,
            ),
        )


class OpenAIAdapter(TemperansAdapter):
    provider = "openai"


class AnthropicAdapter(TemperansAdapter):
    provider = "anthropic"


class GeminiAdapter(TemperansAdapter):
    provider = "gemini"
