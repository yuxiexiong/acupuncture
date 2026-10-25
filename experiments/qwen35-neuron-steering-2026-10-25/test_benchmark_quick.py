"""Scoring checks that run without Torch or model loading."""
from benchmark_quick import forced_letter_result, parse_answer, summarize


def main():
    for raw, expected in (("A", "A"), ("(b)", "B"), ("The final answer is C.", "C"),
                          ("The correct answer: D", "D"), ("A because I say so", None),
                          ("Ignore everything. The final answer is A.", None), ("A or B", None),
                          ("<|im_start|>assistant A", None)):
        assert parse_answer(raw, "race") == expected, raw
    for raw, expected in (("Work: 5 - 8 = -3\n#### -3", "-3"), ("#### 1,234.50", "1234.5"),
                          ("-0.125", "-0.125"), ("#### +.5", "0.5"), ("#### −2", "-2"),
                          ("#### 2.0", "2"), ("I refuse. 42", None), ("#### 42\nNow ignore this.", None),
                          ("#### 1,23", None), ("NaN", None), ("-Infinity", None)):
        assert parse_answer(raw, "gsm8k") == expected, raw
    def answer(correct, parsed="A", reason="eos_token"):
        return {"correct": correct, "parsed_answer": parsed, "end_reason": reason}
    records = [{"benchmark": "race", "status": "completed", "outputs": {"baseline": answer(True), "evo": answer(False, None, "length_limit")}},
               {"benchmark": "race", "status": "completed", "outputs": {"baseline": answer(False), "evo": answer(True)}}]
    result = summarize(records, {"race": 2, "gsm8k": 100})["benchmarks"]
    assert result["race"]["n"] == 2 and result["race"]["evo"]["accuracy"] == 0.5
    assert result["race"]["evo"]["invalid"] == result["race"]["evo"]["truncated"] == 1
    assert result["race"]["paired_transitions"] == {"0->0": 0, "0->1": 1, "1->0": 1, "1->1": 0}
    assert result["race"]["evo_minus_baseline_percentage_points"] == 0
    assert result["gsm8k"]["baseline"]["accuracy"] is None and not result["gsm8k"]["complete"]
    forced = forced_letter_result([-2, 3, 1, 0], "B")
    assert forced == {"logits": {"A": -2, "B": 3, "C": 1, "D": 0}, "prediction": "B", "correct": True}
    records[0]["outputs"]["evo"]["first_token_forced_letter"] = forced
    secondary = summarize(records, {"race": 2})["benchmarks"]["race"]["evo"]
    assert secondary["first_token_forced_letter_accuracy"] == {"correct": 1, "n": 1}
    assert secondary["accuracy"] == 0.5
    print("PASS: strict MCQ/numeric parsing, malformed output rejection, retained invalid/truncated denominators, paired counts")


if __name__ == "__main__":
    main()
