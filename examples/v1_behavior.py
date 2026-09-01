from temperans.models import (
    TemperansV1BehavioralPerception,
)

model = TemperansV1BehavioralPerception()

cases = [
    (
        "Try restarting the service.",
        "It still isn't working.",
    ),
    (
        "Here are three possible names.",
        "Give me five more options.",
    ),
    (
        "Paris is the capital of Germany.",
        "Actually, Berlin is the capital of Germany.",
    ),
]

for previous, current in cases:

    result = model.perceive(
        previous,
        current,
    )

    print()
    print("PREVIOUS:", previous)
    print("CURRENT:", current)
    print("PRIMITIVE:", result.primitive)
    print(
        "CONFIDENCE:",
        round(result.confidence, 3),
    )
    print(
        "HISTORY MATCH:",
        round(result.history_match, 3),
    )
    print(
        "MODEL:",
        result.model_version,
    )
