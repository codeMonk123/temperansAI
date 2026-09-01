from temperans.threading import SemanticThreadResolver


resolver = SemanticThreadResolver(
    threshold=0.15
)

threads = {
    "temperans_benchmark": [
        "How should we benchmark trajectory understanding?",
        "Compare correct history with shuffled history.",
        "Freeze the benchmark before evaluating the model.",
    ],

    "temperans_sdk": [
        "How should pip install temperans expose traces?",
        "Add persistent cross-agent trajectories.",
        "The Trace API should observe human agent and tool events.",
    ],
}


tests = [
    "The shuffled-history benchmark needs more examples.",

    "How should the Temperans Trace API expose agent events?",

    "Tell me a joke about penguins.",
]


for text in tests:

    result = resolver.resolve(
        text=text,
        existing_threads=threads,
    )

    print()
    print("TEXT:", text)
    print("THREAD:", result.thread_id)
    print(
        "CONFIDENCE:",
        round(result.confidence, 3),
    )
    print("NEW:", result.is_new)
    print("METHOD:", result.method)
