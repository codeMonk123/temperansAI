import json
import sys
import urllib.request
import os

MODEL = "qwen2.5:14b"

CLASSES = {
    "continue": "The actor continues, accepts, elaborates, or naturally advances the existing interaction direction.",
    "new_topic": "The actor introduces a materially different topic or goal without opposing the prior direction.",
    "clarify": "The actor requests or supplies clarification needed to understand the existing interaction.",
    "repair": "The actor indicates that the prior attempt failed, was incorrect, did not work, or did not satisfy the underlying need, and requests or initiates another attempt to fix or replace it.",
    "correct": "The actor supplies information that corrects a factual, technical, interpretive, or contextual error in the prior interaction.",
    "disagree": "The actor explicitly disputes a claim, judgment, interpretation, or position without necessarily refusing the broader direction.",
    "resist": "The actor declines, refuses, rejects, pushes back against, or deliberately circumvents the direction established by the prior interaction.",
    "refine": "The actor requests modification, expansion, simplification, restyling, or improvement of the existing output without necessarily indicating that the prior attempt failed.",
}

RULES = [
    "Classify the observable behavioral relationship, not sentiment.",
    "Use prior trajectory context when it is provided.",
    "Do not use future events.",
    "A failed attempt followed by a request for another solution is repair, not automatically resist.",
    "A factual or technical correction is correct, not automatically resist.",
    "A topic switch without opposition is new_topic.",
    "Explicit refusal, rejection, decline, or deliberate circumvention of a prior boundary is resist.",
    "Choose the dominant behavioral transition when more than one is plausible.",
    "A request such as 'make it longer', 'simplify it', or 'use a different tone' is refine unless failure or inadequacy of the prior attempt is expressed.",
    "A statement such as 'that did not work', 'the error remains', or 'try another solution' is repair when it responds to failure of the prior attempt.",
    "Refinement changes an otherwise usable output; repair responds to an unsuccessful or inadequate attempt.",
]

LABELS = list(CLASSES.keys())


def ollama(prompt):
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0
        }
    }).encode()

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=900) as r:
        result = json.loads(r.read())

    return result["response"].strip()


def base_prompt():
    definitions = "\n".join(
        f"- {label}: {definition}"
        for label, definition in CLASSES.items()
    )

    rules = "\n".join(
        f"- {rule}"
        for rule in RULES
    )

    return f"""You are classifying the behavioral primitive of the CURRENT human event.

ONTOLOGY:
{definitions}

RULES:
{rules}

Return exactly ONE label from:
{", ".join(LABELS)}

Do not explain your answer.
"""


def classify_current(target):
    prompt = base_prompt() + f"""
IMPORTANT: For this classification you have ONLY the current event.
Do not assume or invent any previous interaction.

CURRENT HUMAN EVENT:
{target}

LABEL:
"""
    return ollama(prompt)


def classify_history(previous, target):
    prompt = base_prompt() + f"""
PREVIOUS EVENT:
{previous}

CURRENT HUMAN EVENT:
{target}

Classify the CURRENT event conditioned on the previous event.

LABEL:
"""
    return ollama(prompt)


def normalize(label):
    """
    Normalize harmless formatting variations from Qwen.

    Accepted examples:
        new_topic
        "new_topic"
        `new_topic`
        label: new_topic
        LABEL: new_topic
        Label: new_topic
        new_topic.
    """

    cleaned = label.strip().lower()

    # Remove common "label:" prefix.
    if cleaned.startswith("label:"):
        cleaned = cleaned.split(":", 1)[1].strip()

    # Remove harmless surrounding formatting.
    cleaned = cleaned.strip("`'\". ")

    if cleaned in LABELS:
        return cleaned

    raise ValueError(
        f"Invalid model label: {label!r} -> normalized={cleaned!r}"
    )


def load_rows(path):
    with open(path) as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def get_completed_rows(out):
    if not os.path.exists(out):
        return []

    return load_rows(out)


def main():
    if len(sys.argv) != 3:
        print(
            "usage: python label_history_dependence_v2.py "
            "INPUT.jsonl OUTPUT.jsonl"
        )
        sys.exit(1)

    inp, out = sys.argv[1], sys.argv[2]

    rows = load_rows(inp)
    completed = get_completed_rows(out)

    done = len(completed)

    if done > len(rows):
        raise RuntimeError(
            f"Output contains {done} records but input contains "
            f"only {len(rows)}."
        )

    # Verify that existing output corresponds exactly to the
    # beginning of the requested input. This prevents accidentally
    # resuming against the wrong dataset.
    for i, existing in enumerate(completed):
        expected = rows[i]

        if (
            existing.get("probe_id") != expected.get("probe_id")
            or existing.get("trajectory_id") != expected.get("trajectory_id")
            or existing.get("target_event_index")
            != expected.get("target_event_index")
        ):
            raise RuntimeError(
                f"Resume validation failed at record {i + 1}. "
                "Existing output does not match input."
            )

    print(f"INPUT CASES: {len(rows)}")
    print(f"RESUMING: {done}/{len(rows)} already completed")

    if done == len(rows):
        print("Nothing to do. Output is already complete.")
        return

    with open(out, "a") as f:

        for index in range(done, len(rows)):
            x = rows[index]

            current = normalize(
                classify_current(x["target_text"])
            )

            history = normalize(
                classify_history(
                    x["previous_text"],
                    x["target_text"]
                )
            )

            y = dict(x)

            y["ontology"] = "behavioral_primitives_v2"
            y["current_only"] = current
            y["history_aware"] = history
            y["changed"] = current != history

            f.write(
                json.dumps(
                    y,
                    ensure_ascii=False
                ) + "\n"
            )

            # Immediately persist each completed case so a crash
            # never forces us to redo earlier inference.
            f.flush()
            os.fsync(f.fileno())

            marker = (
                " CHANGED"
                if current != history
                else ""
            )

            print(
                f"{index + 1:02d}/{len(rows)} "
                f"current={current:<10} "
                f"history={history:<10}"
                f"{marker}",
                flush=True,
            )

    print()
    print("COMPLETE")
    print(f"OUTPUT: {out}")


if __name__ == "__main__":
    main()
