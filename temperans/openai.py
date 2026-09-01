from typing import Optional

from .adapters import OpenAIAdapter


class OpenAIConnector:
    provider = "openai"

    def __init__(
        self,
        trace,
        client,
        model="gpt-5-mini",
        actor_id="openai",
    ):
        self.trace = trace
        self.client = client
        self.model = model
        self.actor_id = actor_id

        self.adapter = OpenAIAdapter(
            trace=trace,
            model=model,
        )

    def generate(
        self,
        prompt: str,
        thread_id: Optional[str] = None,
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

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            **kwargs,
        )

        text = getattr(
            response,
            "output_text",
            "",
        ) or ""

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
