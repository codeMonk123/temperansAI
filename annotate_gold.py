import json

PATH = "data/annotation/resistance_gold_blind_12.jsonl"

with open(PATH) as f:
    rows = [json.loads(x) for x in f]

for r in rows:
    if r["human_annotation"]["score"] is not None:
        continue

    p = r["previous"]
    t = r["target"]

    print("\n" + "=" * 70)
    print("BENCHMARK:", r["benchmark_id"])
    print("=" * 70)

    print("\nPREVIOUS:")
    print(" ".join(p["text"].split())[-1000:])

    print("\nTARGET:")
    print(" ".join(t["text"].split())[:1000])

    print("\n0.00 none")
    print("0.25 weak/indirect reluctance")
    print("0.50 clear disagreement/rejection")
    print("0.75 strong/repeated rejection")
    print("1.00 forceful/sustained refusal")
    print("\nq = stop")

    raw = input("\nscore: ").strip()

    if raw.lower() == "q":
        break

    r["human_annotation"]["score"] = float(raw)
    r["human_annotation"]["confidence"] = float(
        input("confidence: ").strip()
    )
    r["human_annotation"]["rationale"] = input(
        "rationale: "
    ).strip()

    with open(PATH, "w") as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")

    print("SAVED")

print("\nEnded.")
