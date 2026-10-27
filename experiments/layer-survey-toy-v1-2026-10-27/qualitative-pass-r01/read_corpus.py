"""Display complete answers from the frozen survey; no semantic scoring."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=["2b", "4b", "9b"])
    parser.add_argument("--layers", nargs=2, type=int, metavar=("FIRST", "LAST"))
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent / "delivery-r01"
    filename = "original.raw.jsonl" if args.baseline else "modified.raw.jsonl"
    rows = [json.loads(line) for line in (root / filename).read_text().splitlines()]
    rows = [r for r in rows if r["model_id"] == args.model]
    if args.layers and not args.baseline:
        rows = [r for r in rows if args.layers[0] <= r["layer"] <= args.layers[1]]
    rows.sort(key=lambda r: (r["layer"] or 0, r["channel"] or 0, r["question_id"]))
    assert len({(r['condition_id'], r['question_id']) for r in rows}) == len(rows)
    prompts = {r["question_id"]: r["prompt"] for r in rows}
    print(json.dumps({"model": args.model, "questions": prompts}, ensure_ascii=False))
    for r in rows:
        print(json.dumps({"id": r["condition_id"] + "/" + r["question_id"],
                          "end": r["output"]["end_reason"],
                          "raw": r["output"]["raw_text"]}, ensure_ascii=False))
    print(json.dumps({"displayed_complete_records": len(rows)}))


if __name__ == "__main__":
    main()
