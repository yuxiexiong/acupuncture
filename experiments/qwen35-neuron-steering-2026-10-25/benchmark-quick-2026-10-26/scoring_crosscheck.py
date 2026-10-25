"""Post-hoc explicit-answer diagnostic; never changes the preregistered strict score."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from benchmark_quick import parse_answer as strict_parse

NUMBER = r"[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d*)?|\.\d+)"
VALUE = r"(?:[$£€¥₹₩₽]\s*)?(" + NUMBER + r")"
PREFIX = r"(?<!\w)(?:the\s+)?(?:(?:correct|final)\s+)?answer\s*(?:is\b\s*:?\s*|:\s*)"
MCQ = re.compile(PREFIX + r"(?:option\s+|choice\s+)?\(?([A-D])\)?(?=[ \t]*(?:[.!:;,]|\n|$|because\b|since\b))", re.I)
MATH = re.compile(r"(?:####\s*|" + PREFIX + r")" + VALUE + r"(?![\w,/+*^\-]|\.(?!\s|$))", re.I)
BOXED = re.compile(r"\\boxed\s*\{\s*" + VALUE + r"\s*\}")
AUTHOR_GSM = re.compile(r"#### (\-?[0-9\.\,]+)")
RULES = {
    "status": "post_hoc",
    "version": 2,
    "change_reason": "Restore omitted optional currency formatting symmetrically for both arms; all other extraction and scoring rules are unchanged. Preserve the v1 report and its hash.",
    "purpose": "Symmetric diagnostic of explicit answers despite extra prose; does not replace strict_generated_accuracy.",
    "mcq": "First nonempty line must contain only A-D (optional parentheses/Markdown/terminal punctuation), or an explicit [the] [correct/final] answer is/: [option/choice] A-D marker. A marked letter must end or have punctuation/newline/because/since after it. Arbitrary prose letters and option mentions are ignored.",
    "gsm8k": "Entirely numeric response, explicit #### number, boxed{number}, or [the] [correct/final] answer is/: number. Allow an optional $/£/€/¥/₹/₩/₽ currency symbol and whitespace before each explicit number. Signed decimal numbers and properly grouped thousands only; normalize using Decimal; no arbitrary last-number extraction.",
    "conflicts": "All recognized explicit candidates must agree after normalization; otherwise invalid. No target-aware selection. Unrecognized/malformed claims may be missed: this is a syntactic diagnostic, not semantic adjudication.",
    "markdown": "Ignore paired bold/italic/backtick delimiters around tokens; no changes to the underlying answers.",
    "denominator": "All 100 fixed items per benchmark, both arms, including invalid and truncated answers; all 300 pairs must be completed before this script writes a report.",
    "truncation": "An explicit answer before truncation can count in this diagnostic; truncation is separately retained and reported.",
    "author_gsm8k_reference": "Separate reference: first match of #### (\\-?[0-9\\.\\,]+), strip whitespace and commas, then string equality. No Decimal normalization, no conflict rejection. The target comes from the original GSM8K source answer.",
    "author_source": "https://github.com/openai/grade-school-math/blob/2909d34ef28520753df82a2234c357259d254aa8/grade_school_math/dataset.py",
}


def normalized_number(value):
    number = Decimal(value.replace(",", "").replace("−", "-"))
    return "0" if number == 0 else format(number.normalize(), "f")


def explicit_answer(text, benchmark):
    # Parse before seeing a target. Remove formatting delimiters, not prose.
    text = text.strip().replace("−", "-")
    text = re.sub(r"(\*\*|__|`|\*)(.+?)\1", r"\2", text)
    candidates = []
    if benchmark == "gsm8k":
        entire = re.fullmatch(VALUE, text)
        if entire:
            candidates.append({"value": normalized_number(entire.group(1)), "marker": "entire_numeric", "excerpt": text})
        for pattern, marker in ((MATH, "explicit_numeric"), (BOXED, "boxed")):
            for match in pattern.finditer(text):
                # A following arithmetic operator/alternative means this is not a final scalar.
                if re.match(r"\s*(?:[-/+*^=]|or\b|and\b)", text[match.end():], re.I):
                    return {"parsed": None, "reason": "ambiguous_numeric_expression", "candidates": candidates}
                candidates.append({"value": normalized_number(match.group(1)), "marker": marker, "excerpt": match.group(0)})
    else:
        if re.search(PREFIX + r"(?:option\s+|choice\s+)?\(?[A-D]\)?\s*(?:,\s*(?:(?:or|and)\s+)?|(?:or|and)\b\s*|/)\(?[A-D]\)?\b", text, re.I):
            return {"parsed": None, "reason": "ambiguous_multiple_choices", "candidates": []}
        first = text.splitlines()[0].strip() if text else ""
        match = re.fullmatch(r"\(?([A-D])\)?[.!]?", first, re.I)
        if match:
            candidates.append({"value": match.group(1).upper(), "marker": "standalone_first_line", "excerpt": first})
        for match in MCQ.finditer(text):
            candidates.append({"value": match.group(1).upper(), "marker": "explicit_choice", "excerpt": match.group(0)})
    values = {c["value"] for c in candidates}
    return {"parsed": next(iter(values)) if len(values) == 1 else None,
            "reason": "explicit_agreement" if len(values) == 1 else "conflicting_explicit_answers" if values else "no_explicit_answer",
            "candidates": candidates}


def author_gsm_answer(text):
    match = AUTHOR_GSM.search(text)
    return match.group(1).strip().replace(",", "") if match else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.root.resolve()
    print(json.dumps(RULES, ensure_ascii=False, indent=2))
    items = json.loads((root / "items.json").read_text())
    expected = {item["id"]: item for item in items}
    assert len(expected) == 300 and Counter(item["benchmark"] for item in items) == {"race": 100, "gsm8k": 100, "logiqa2": 100}
    rows, sources = {}, {}
    for directory in (root / "results-reading-logic", root / "results-math"):
        receipt = json.loads((directory / "receipt.json").read_text())
        assert receipt["status"] == "completed", f"Incomplete run: {directory}"
        for path in sorted(directory.glob("[0-9][0-9][0-9][0-9].json")):
            row = json.loads(path.read_text())
            assert row["id"] not in rows and row["status"] == "completed"
            assert all(row["outputs"][arm]["status"] == "completed" for arm in ("baseline", "evo"))
            assert row["target"] == expected[row["id"]]["target"] and row["prompt"] == expected[row["id"]]["prompt"]
            rows[row["id"]] = row
            sources[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert set(rows) == set(expected), "All 300 fixed paired items must be present"
    gsm_source = [json.loads(line) for line in (root / "sources/gsm8k_test.jsonl").read_text().splitlines() if line.strip()]
    records, differences = [], []
    for item in items:
        row = rows[item["id"]]
        result = {"id": row["id"], "benchmark": row["benchmark"], "outputs": {}}
        for arm in ("baseline", "evo"):
            output = row["outputs"][arm]
            text = output["answer_text"]
            extracted = explicit_answer(text, row["benchmark"])
            strict = strict_parse(text, row["benchmark"])
            assert strict == output["parsed_answer"]
            target = normalized_number(row["target"]) if row["benchmark"] == "gsm8k" else row["target"]
            scored = {**extracted, "correct": extracted["parsed"] is not None and extracted["parsed"] == target,
                      "strict_parsed": strict, "strict_correct": output["correct"], "end_reason": output["end_reason"]}
            assert output["correct"] == (strict is not None and strict == strict_parse(row["target"], row["benchmark"]))
            if row["benchmark"] == "gsm8k":
                source = gsm_source[int(row["source_id"].rsplit("line", 1)[1]) - 1]
                author_target = author_gsm_answer(source["answer"])
                assert author_target is not None and normalized_number(author_target) == target
                author = author_gsm_answer(text)
                scored["author_regex_reference"] = {"parsed": author, "target": author_target, "correct": author is not None and author == author_target}
            result["outputs"][arm] = scored
            if extracted["parsed"] != strict or scored["correct"] != scored["strict_correct"]:
                differences.append({"id": row["id"], "benchmark": row["benchmark"], "arm": arm, "target": target,
                                    "answer_excerpt": text[:1200], "excerpt_truncated": len(text) > 1200,
                                    "raw_text_excerpt": output["raw_text"][:1200], **scored})
        records.append(result)
    summary = {}
    for benchmark in ("race", "gsm8k", "logiqa2"):
        selected = [row for row in records if row["benchmark"] == benchmark]
        entry = {"n": len(selected), "denominator": 100}
        assert len(selected) == 100
        for arm in ("baseline", "evo"):
            outputs = [row["outputs"][arm] for row in selected]
            entry[arm] = {"strict_correct": sum(o["strict_correct"] for o in outputs),
                          "strict_invalid": sum(o["strict_parsed"] is None for o in outputs),
                          "post_hoc_correct": sum(o["correct"] for o in outputs),
                          "post_hoc_explicit_answer_count": sum(o["parsed"] is not None for o in outputs),
                          "post_hoc_invalid": sum(o["parsed"] is None for o in outputs),
                          "truncated": sum(o["end_reason"] == "length_limit" for o in outputs),
                          "post_hoc_correct_but_truncated": sum(o["correct"] and o["end_reason"] == "length_limit" for o in outputs)}
            if benchmark == "gsm8k":
                entry[arm]["author_regex_reference_correct"] = sum(o["author_regex_reference"]["correct"] for o in outputs)
                entry[arm]["author_regex_reference_invalid"] = sum(o["author_regex_reference"]["parsed"] is None for o in outputs)
        entry["post_hoc_evo_minus_baseline_percentage_points"] = entry["evo"]["post_hoc_correct"] - entry["baseline"]["post_hoc_correct"]
        summary[benchmark] = entry
    report = {"status": "completed", "analysis_type": "post_hoc_diagnostic", "created_utc": datetime.now(timezone.utc).isoformat(),
              "analysis_version": 2, "previous_report": "scoring_crosscheck-v1.json",
              "previous_report_sha256": hashlib.sha256((root / "scoring_crosscheck-v1.json").read_bytes()).hexdigest(),
              "rules": RULES, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "input_sha256": sources, "summary": summary, "differences": differences, "records": records}
    path = root / "scoring_crosscheck.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved {path}; {len(differences)} arm/item parsing or scoring differences")


if __name__ == "__main__":
    main()
