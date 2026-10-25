"""Mechanical checks only: paired extension and failure preservation, with no model."""
from copy import deepcopy

from collect_raw import end_reason, pair_attempts


def main():
    calls, snapshots = [], []

    def generate(arm, budget):
        calls.append((arm, budget))
        return {"status": "completed", "token_ids": [budget], "raw_text": f"{arm}:{budget}",
                "end_reason": "length_limit" if (arm, budget) == ("modified", 512) else "eos_token"}

    attempts = pair_attempts(generate, lambda value: snapshots.append(deepcopy(value)))
    assert calls == [("baseline", 512), ("modified", 512), ("baseline", 1024), ("modified", 1024)]
    assert attempts[0]["baseline"]["raw_text"] == "baseline:512"
    assert len(attempts) == 2 and snapshots[-1] == attempts
    snapshots.clear()
    no_extension = pair_attempts(lambda arm, budget: {"status": "completed", "end_reason": "eos_token"}, lambda value: None)
    assert len(no_extension) == 1

    def fail(arm, budget):
        if arm == "modified":
            raise RuntimeError("technical test error")
        return {"status": "completed", "raw_text": "keep this raw answer", "end_reason": "eos_token"}

    try:
        pair_attempts(fail, lambda value: snapshots.append(deepcopy(value)))
        raise AssertionError("Failure was swallowed")
    except RuntimeError:
        pass
    assert snapshots[-1][0]["baseline"]["raw_text"] == "keep this raw answer"
    assert snapshots[-1][0]["modified"]["status"] == "failed"
    assert end_reason([1, 2], 2, [2]) == "eos_token"
    assert end_reason([1, 3], 2, [2]) == "length_limit"
    assert end_reason([1], 2, [2]) == "other_stop"
    print("PASS: paired extension, retained first attempts, incremental failure preservation, EOS/length classification")


if __name__ == "__main__":
    main()
