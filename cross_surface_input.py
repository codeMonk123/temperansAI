import json
from datetime import datetime


# ---------------------------------------------------------
# LOAD EVENTS
# ---------------------------------------------------------

events = []

with open("temperans_events.jsonl", "r") as file:

    for line in file:

        if line.strip():

            event = json.loads(line)

            events.append(event)


# ---------------------------------------------------------
# SORT BY TIME
# ---------------------------------------------------------

events.sort(
    key=lambda event: datetime.fromisoformat(
        event["timestamp"].replace("Z", "+00:00")
    )
)


# ---------------------------------------------------------
# CURRENT EVENT
# ---------------------------------------------------------

current_event = events[-1]


# ---------------------------------------------------------
# GLOBAL HISTORY
# ---------------------------------------------------------

trajectory_history = [
    event
    for event in events
    if (
        event["trajectory_id"]
        == current_event["trajectory_id"]
        and event["timestamp"]
        < current_event["timestamp"]
    )
]


# ---------------------------------------------------------
# FORMAT ONE EVENT
# ---------------------------------------------------------

def format_event(event):

    surface = event["surface"].upper()

    source_type = event["source"]["type"].upper()
    source_id = event["source"]["id"]

    target_type = event["target"]["type"].upper()
    target_id = event["target"]["id"]

    text = event["text"]

    return (
        "[" + surface + "] "
        + source_type
        + "(" + source_id + ")"
        + " -> "
        + target_type
        + "(" + target_id + ")"
        + ": "
        + text
    )


# ---------------------------------------------------------
# BUILD TRAJECTORY TEXT
# ---------------------------------------------------------

history_parts = []

for event in trajectory_history:

    history_parts.append(
        format_event(event)
    )


history_text = "\n".join(
    history_parts
)


current_text = format_event(
    current_event
)


model_input = (
    "TRAJECTORY HISTORY:\n"
    + history_text
    + "\n\nCURRENT EVENT:\n"
    + current_text
)


# ---------------------------------------------------------
# PRINT
# ---------------------------------------------------------

print("TEMPERANS MODEL INPUT")
print("=====================")

print(model_input)
