"""Synthetic timings verify denominators and scheduling, without model execution."""
import json
from pathlib import Path
import tempfile
import unittest

import estimate_eta as eta


def profile(speed=1.):
    rows = []
    for role in ("full", "prefill", "decode", "prompt_last", "prompt_except_last",
                 "branch_continue", "branch_withdraw", "branch_rebuild", "patch"):
        for kind in ("clean", "native", "direction"):
            for family in eta.FAMILIES + ("open",):
                for n in (0, 1):
                    rows.append({"kind": kind, "family": family, "window": "early", "sign": 1,
                        "dose": .5, "role": role, "benchmark": role == "full" and kind != "clean",
                        "base_id": f"{family}{n}", "tokens": 10, "generation_seconds": 2. * speed,
                        "candidate_seconds": 6. * speed, "candidate_count": 2,
                        "other_seconds": speed, "save_seconds": .5 * speed,
                        "generation_bytes": 1000, "candidate_bytes": 500, "envelope_bytes": 200,
                        "bytes": 1700})
    return {"samples": rows, "load_seconds": 3. * speed, "calibration_seconds_per_base": .2 * speed,
            "save_seconds_per_record": .5 * speed, "donor_seconds_at_preflight_step": .3 * speed,
            "donor_prediction_step_observed": 0, "donor_save_seconds": .1 * speed,
            "donor_archive_bytes": 100, "unattributed_preflight_seconds": 4. * speed,
            "unknown_overheads": []}


class EstimateTests(unittest.TestCase):
    def test_exact_counts_and_extra_replays_do_not_join_scientific_denominator(self):
        self.assertEqual(sum(eta.SCIENTIFIC_COUNTS.values()), 12144)
        for stage, expected in eta.SCIENTIFIC_COUNTS.items():
            jobs = [job for gpu in (0, 1) for job in eta.requests(stage, gpu)]
            self.assertEqual(sum(j["count"] for j in jobs if j["scientific"]), expected)
        dev = [j for g in (0, 1) for j in eta.requests("mechanism_development", g)]
        self.assertEqual(sum(j["count"] for j in dev if j["technical"] == "continue_replay"), 384)
        patch = [j for g in (0, 1) for j in eta.requests("patch_development", g)]
        self.assertEqual(sum(j["count"] for j in patch if j["technical"] == "patch_source_replay"), 128)

    def test_parallel_workers_take_max_not_sum_and_completed_are_excluded(self):
        completed = set(eta.STAGES) - {"development"}
        result = eta.estimate([profile(), profile(2)], completed_stages=completed)
        scenario = result["scenarios"]["observed_preflight_lengths"]
        stage = scenario["stages"]["development"]
        times = [w["known_wall_seconds"] for w in stage["workers"]]
        self.assertEqual(stage["known_wall_seconds"], max(times))
        self.assertNotEqual(stage["known_wall_seconds"], sum(times))
        self.assertEqual(scenario["known_compute_setup_and_measured_io_seconds"], max(times))
        self.assertEqual(stage["workers"][0]["scientific_generations"], 2316)
        self.assertAlmostEqual(times[0], 2316 * 9.5 + 3 + 6 * .2)
        self.assertTrue(all(scenario["stages"][name]["known_wall_seconds"] == 0 for name in completed))

    def test_all128_scales_generation_not_candidate_or_loading(self):
        jobs = [{"dimensions": {"kind": "native", "family": "reading"}, "role": "full",
                 "count": 2, "candidates": True, "scientific": True, "technical": None}]
        observed = eta.estimate_worker(profile(), jobs, donor_count=6)
        long = eta.estimate_worker(profile(), jobs, donor_count=6, all_128=True)
        self.assertAlmostEqual(long["generation_seconds"], observed["generation_seconds"] * 12.8)
        self.assertEqual(long["candidate_seconds"], observed["candidate_seconds"])
        self.assertEqual(long["load_and_identity_seconds"], observed["load_and_identity_seconds"])
        self.assertAlmostEqual(long["donor_seconds"], 6 * (.3 + 127 * (2. - .3) / 9))
        self.assertFalse(long["donor_timing_evidence"]["measured_long_donor"])

    def test_long_donor_prefill_is_paid_once_not_128_times(self):
        measured = profile()
        measured["donor_seconds_at_preflight_step"] = 10.
        for row in measured["samples"]:
            row["tokens"], row["generation_seconds"] = 128, 11.
        seconds, evidence = eta.donor_timing(measured, 6, True)
        self.assertAlmostEqual(seconds, 66.)
        self.assertLess(seconds, 6 * 10 * 128)
        self.assertEqual(evidence["mode"], "one_measured_prefill_plus_127_estimated_increments")
        self.assertTrue(all(p["prefill_seconds"] == 10. for p in evidence["pools"]))

    def test_patch_recipient_mix_uses_clean_patch_not_ordinary_clean(self):
        measured = profile()
        for row in measured["samples"]:
            if row["kind"] == "clean":
                row["generation_seconds"] = 11. if row["role"] == "patch" else 5.
            elif row["kind"] == "native" and row["role"] == "patch":
                row["generation_seconds"] = 3.
        jobs = [j for j in eta.requests("patch_development", 0)
                if j["role"] == "patch" and j["dimensions"]["family"] == "reading"]
        self.assertEqual({j["dimensions"]["kind"]: j["count"] for j in jobs},
                         {"native": 64, "clean": 32})
        result = eta.estimate_worker(measured, jobs)
        self.assertEqual(result["scientific_generations"], 96)
        self.assertEqual(result["generation_seconds"], 64 * 3. + 32 * 11.)
        clean_pool, evidence = eta.pool(measured["samples"], {"kind": "clean", "family": "reading"}, "patch")
        self.assertTrue(all(row["role"] == "patch" and row["kind"] == "clean" for row in clean_pool))
        self.assertEqual(evidence["role"], "patch")

    def test_storage_capacities_are_separate_and_absent_not_zero(self):
        result = eta.estimate([profile(), profile()], completed_stages=set(eta.STAGES)-{"development"},
                              server_free_gib=0., local_free_gib=None)
        value = result["scenarios"]["observed_preflight_lengths"]
        self.assertFalse(value["server_raw_space_sufficient_under_scenario"])
        self.assertIsNone(value["local_raw_archive_sufficient_under_scenario"])
        self.assertFalse(value["optional_eight_anchor_clean_if_not_reused"]["included_in_total"])

    def test_loads_measured_io_and_calibration_field_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            records, saves = {}, {}
            row = {"item": {"base_id": "RD01", "family": "reading"},
                "condition": {"kind": "native", "layer": 0, "dose": .5}, "mode": "full",
                "output": {"status": "completed", "seconds": 2., "generated_token_count": 10},
                "choices": [{"seconds": .2}, {"seconds": .3}], "wall_seconds": 2.6}
            for i in range(60):
                name = f"benchmark-{i:03d}"
                relative = f"records/{name}.json"
                (root / relative).write_text(json.dumps(row))
                records[relative], saves[name] = "unused_by_pure_loader", .01
            (root / "receipt.json").write_text(json.dumps({"record_hashes": records, "asset_hashes": {},
                "load_and_identity_seconds": 4., "wall_seconds": 180.}))
            (root / "preflight.json").write_text(json.dumps({"benchmark_records": list(records),
                "save_seconds_by_record": saves, "calibration_seconds_by_base": {"RD01": .7},
                "donor_replay_seconds": [.3, .4]}))
            loaded = eta.load_worker(root)
            self.assertEqual(loaded["samples"][0]["save_seconds"], .01)
            self.assertEqual(loaded["calibration_seconds_per_base"], .7)
            self.assertEqual(loaded["calibration_seconds_by_family"]["reading"], [.7])
            self.assertEqual(loaded["samples"][0]["candidate_seconds"], .5)

    def test_unverified_controller_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, value in (("controller.json", {"status": "running"}),
                                ("verification.json", {"status": "passed"}), ("execution.json", {})):
                (root / name).write_text(json.dumps(value))
            with self.assertRaises(AssertionError):
                eta.verified_profiles(root)


if __name__ == "__main__":
    unittest.main()
