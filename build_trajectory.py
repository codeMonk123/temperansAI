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
# SORT EVENTS BY TIME
# ---------------------------------------------------------

events.sort(
    key=lambda event: datetime.fromisoformat(
        event["timestamp"].replace("Z", "+00:00")
    )
)


print("Total events:", len(events))


# ---------------------------------------------------------
# CHOOSE CURRENT EVENT
# ---------------------------------------------------------

current_event = events[-1]


print("\nCURRENT EVENT")
print("-------------")

print("Event:", current_event["event_id"])
print("Surface:", current_event["surface"])
print("Interaction:", current_event["interaction_id"])
print("Text:", current_event["text"])


# ---------------------------------------------------------
# FIND EVERYTHING BEFORE CURRENT EVENT
# ---------------------------------------------------------

previous_events = [
    event
    for event in events
    if event["timestamp"] < current_event["timestamp"]
]


# ---------------------------------------------------------
# LOCAL HISTORY
#
# Same interaction_id only
# ---------------------------------------------------------

local_history = [
    event
    for event in previous_events
    if event["interaction_id"]
    == current_event["interaction_id"]
]


# ---------------------------------------------------------
# GLOBAL TRAJECTORY HISTORY
#
# Same trajectory_id across ALL surfaces/interactions
# ---------------------------------------------------------

trajectory_history = [
    event
    for event in previous_events
    if event["trajectory_id"]
    == current_event["trajectory_id"]
]


# ---------------------------------------------------------
# PRINT LOCAL HISTORY
# ---------------------------------------------------------

print("\nLOCAL HISTORY")
print("-------------")

for event in local_history:

    print(
        event["timestamp"],
        "|",
        event["surface"],
        "|",
        event["source"]["id"],
        "->",
        event["target"]["id"],
        "|",
        event["text"]
    )


# ---------------------------------------------------------
# PRINT GLOBAL TRAJECTORY HISTORY
# ---------------------------------------------------------

print("\nGLOBAL TRAJECTORY HISTORY")
print("-------------------------")

for event in trajectory_history:

    print(
        event["timestamp"],
        "|",
        event["surface"],
        "|",
        event["source"]["id"],
        "->",
        event["target"]["id"],
        "|",
        event["text"]
    )
