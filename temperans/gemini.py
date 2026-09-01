from typing import Optional

from .adapters import GeminiAdapter


class GeminiConnector:
    """
    Live Gemini -> Temperans connector.

    A generate() call:
      1. records the human prompt
      2. calls Gemini
      3. records Gemini's response
      4. returns the native Gemini response
    """

    provider = "gemini"

    def __init__(
        self,
        trace,
        client,
        model="gemini-3.6-flash",
        actor_id="gemini",
    ):
        self.trace = trace
        self.client = client
        self.model = model
        self.actor_id = actor_id

        self.adapter = GeminiAdapter(
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

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            **kwargs,
        )

        text = response.text or ""

        external_id = getattr(
            response,
            "response_id",
            None,
        )

        self.adapter.agent(
            text,
            actor_id=self.actor_id,
            external_id=external_id,
            thread_id=resolved_thread_id,
        )

        return response
