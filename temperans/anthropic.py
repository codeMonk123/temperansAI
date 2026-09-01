from typing import Optional

from .adapters import AnthropicAdapter


class AnthropicConnector:
    provider = "anthropic"

    def __init__(
        self,
        trace,
        client,
        model="claude-sonnet-4-20250514",
        actor_id="anthropic",
    ):
        self.trace = trace
        self.client = client
        self.model = model
        self.actor_id = actor_id

        self.adapter = AnthropicAdapter(
            trace=trace,
            model=model,
        )

    def generate(
        self,
        prompt: str,
        thread_id: Optional[str] = None,
        max_tokens=1024,
        **kwargs,
    ):
        human_event = self.adapter.human(
            prompt,
            thread_id=thread_id,
        )

        resolved_thread_id = (
            human_event.thread_id
            or thread_id
            or self.trace.thread_id
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            **kwargs,
        )

        text_parts = []

        for block in getattr(
            response,
            "content",
            [],
        ):
            text = getattr(
                block,
                "text",
                None,
            )

            if text:
                text_parts.append(text)

        text = "\n".join(text_parts)

        external_id = getattr(
            response,
            "id",
            None,
        )

        self.adapter.agent(
            text,
            actor_id=self.actor_id,
            external_id=external_id,
            thread_id=resolved_thread_id,
        )

        return response
