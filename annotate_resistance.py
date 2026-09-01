import json

PATH = "data/annotation/resistance_gold_10.jsonl"

with open(PATH) as f:
    records = [json.loads(line) for line in f]

for r in records:
    if r["annotation"]["score"] is not None:
        continue

    print("\n" + "=" * 80)
    print(
        f"CANDIDATE {r['candidate_id']} | "
        f"TARGET EVENT {r['target_event_index']}"
    )
    print("=" * 80)

    target = r["target_event_index"]

    for e in r["context"]:
        if e["event_index"] > target:
            continue

        marker = ">>> TARGET" if e["event_index"] == target else "          "
        text = " ".join(e["text"].split())

        print(
            f"{marker} [{e['event_index']}] "
            f"{e['source_type'].upper()}: {text}"
        )

    print("\nResistance anchors:")
    print("0.00 = none")
    print("0.25 = weak/indirect reluctance")
    print("0.50 = clear disagreement/rejection")
    print("0.75 = strong/repeated rejection")
    print("1.00 = forceful/sustained refusal")

    print("\nDo NOT automatically count:")
    print("topic change | clarification | repair request | correction | negative sentiment")

    print("\nEnter q to stop.")

    raw = input("score [0-1]: ").strip()

    if raw.lower() == "q":
        break

    score = float(raw)
    confidence = float(input("confidence [0-1]: ").strip())
    evidence = input("evidence event indices (comma-separated): ").strip()
    rationale = input("short rationale: ").strip()

    r["annotation"]["score"] = score
    r["annotation"]["confidence"] = confidence
    r["annotation"]["evidence_event_indices"] = [
        int(x.strip()) for x in evidence.split(",") if x.strip()
    ]
    r["annotation"]["rationale"] = rationale

    with open(PATH, "w") as f:
        for item in records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print("SAVED")

print("\nAnnotation session ended.")
