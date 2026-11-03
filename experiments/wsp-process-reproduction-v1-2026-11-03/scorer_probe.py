"""Check original mathematical grading independently of unpublished loop diagnostics."""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.read_text()
    tree = ast.parse(source)
    excluded = [node for node in tree.body if isinstance(node, ast.Try)
                and any(isinstance(x, ast.ImportFrom) and x.module == "weightenv.lmo.tasks.mcqa" for x in node.body)]
    assert len(excluded) == 1
    tree.body.remove(excluded[0])
    namespace = {"__file__": str(args.source), "__name__": "wsp_original_mathqa_probe"}
    # Only this import is excluded. score/extract/is_correct and math-verify are unmodified.
    # Unavailable mcqa_loop_signals stays undefined: invoking it fails, never fabricates a result.
    exec(compile(tree, str(args.source), "exec"), namespace)
    cases = [(r"\boxed{2}", "2", True), (r"\boxed{2}", "3", False),
             (r"\boxed{\frac{1}{2}}", "0.5", True), ("No final answer", "2", False),
             (r"\boxed{1} then \boxed{2}", "2", True)]
    records = []
    for text, gold, expected in cases:
        actual = namespace["score"]({"gold": gold}, text)
        records.append({"text": text, "gold": gold, "expected": expected, "actual": actual})
    status = "passed" if all(r["actual"]["correct"] == r["expected"] for r in records) else "failed"
    receipt = {"status": status, "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
               "scope": "Original score/extract/math-verify only; missing mcqa loop diagnostics not accepted", "cases": records}
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": status, "cases": len(records)}))
    if status != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
