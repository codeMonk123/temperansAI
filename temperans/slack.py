from .adapters import TemperansAdapter


class SlackAdapter(TemperansAdapter):
    provider = "slack"

    def message(
        self,
        text,
        actor_id,
        thread_id=None,
        channel_id=None,
        slack_thread_ts=None,
        external_id=None,
        **metadata,
    ):
        return self.trace.human(
            text,
            actor_id=actor_id,
            thread_id=thread_id,
            **self._metadata(
                external_id=external_id,
                channel_id=channel_id,
                slack_thread_ts=slack_thread_ts,
                **metadata,
            ),
        )
