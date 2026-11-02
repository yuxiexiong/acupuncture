"""Validate the panel against all four real tokenizers (CPU).  Writes panel-validation-r01.json."""
import json
import statistics
import sys

from transformers import AutoTokenizer

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import models as M  # noqa: E402
import panel as P  # noqa: E402
import tokspan as T  # noqa: E402


def main():
    report = {"panel_sha256": P.panel_sha256(), "models": {}}
    ok_all = True
    for key, spec in M.MODELS.items():
        tok = AutoTokenizer.from_pretrained(spec["path"], local_files_only=True)
        lens, excl, bad_cand, cand_lens, rec_lens = {"A": [], "B": []}, 0, [], [], []
        for task in ("A", "B"):
            for it in P.items(task):
                e = T.encode_item(tok, key, it)
                lens[task].append(e["n_tokens"])
                excl += e["record_boundary_excluded"]
                rec_lens.append(len(e["record_positions"]))
                if task == "A":
                    for c in it["candidates_in_order"]:
                        ci = T.continuation_ids(tok, key, it, c)
                        if ci is None or not ci:
                            bad_cand.append((it["item_id"], c))
                        else:
                            cand_lens.append(len(ci))
        # B: the canonical answer "<id>: <value>" must have a token prefix ending exactly at the colon.
        no_boundary = []
        for it in P.items("B"):
            for form in (f"{it['target_row_id']}: {it['correct']}", f"<{it['target_row_id']}>: {it['correct']}"):
                ci = T.continuation_ids(tok, key, it, form)
                ok = ci is not None and any(P.at_boundary(it, tok.decode(ci[:j])) for j in range(1, len(ci)))
                if not ok:
                    no_boundary.append((it["item_id"], form))
        r = {
            "B_canonical_answer_without_colon_boundary": no_boundary,
            "A_tokens": {"min": min(lens["A"]), "median": statistics.median(lens["A"]), "max": max(lens["A"])},
            "B_tokens": {"min": min(lens["B"]), "median": statistics.median(lens["B"]), "max": max(lens["B"])},
            "record_tokens": {"min": min(rec_lens), "max": max(rec_lens)},
            "record_boundary_tokens_excluded_total": excl,
            "candidate_token_lengths": sorted(set(cand_lens)),
            "candidate_split_failures": bad_cand,
            "within_128_256": all(128 <= n <= 256 for n in lens["A"] + lens["B"]),
        }
        ok_all &= r["within_128_256"] and not bad_cand and not no_boundary
        report["models"][key] = r
    report["passed"] = ok_all
    json.dump(report, open("panel-validation-r01.json", "w"), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
