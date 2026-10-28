"""CPU acceptance for Llama-specific runner checks and preflight gates."""
import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import trace_run as run
import source_prepare


def output(tokens, reason="eos_token"):
    return dict(token_ids=tokens, token_sha256=run.source_checks.token_hash(tokens),
        generated_token_count=len(tokens), max_new_tokens=128, returned_padding_count=0,
        batch_size=1, end_reason=reason)


class RunnerTests(unittest.TestCase):
    def test_native_eos_and_length_checks_reject_qwen_or_early_stop(self):
        for eos in (128001, 128008, 128009):
            run.check_output(output([7, eos]))
        run.check_output(output([7] * 128, "length_limit"))
        for value in (output([248046]), output([128009, 7, 128009]),
                      output([7], "length_limit"), output([True, 128009])):
            with self.assertRaises(AssertionError):
                run.check_output(value)

    def test_metadata_allows_only_device_difference(self):
        source = dict(device="cuda:0", model_id=run.MODEL, revision="fixed",
                      effective_stop_tokens={"128009": "<|eot_id|>"})
        run.compatible_metadata(dict(source, device="cuda:1"), source)
        for field, value in (("revision", "changed"), ("effective_stop_tokens", {"248046": "wrong"})):
            with self.assertRaises(AssertionError):
                run.compatible_metadata(dict(source, **{field: value}), source)

    def test_adapted_runner_uses_new_root_model_sources_and_native_checks(self):
        runner = run.adapted_runner()
        self.assertEqual((runner.ROOT, runner.MODELS, runner.EXPECTED),
                         (run.ROOT, (run.MODEL,), {run.MODEL: 920}))
        self.assertIs(runner.validate_authorization, run.validate_authorization)
        native = runner.load_module("trace_source_checks", Path("unused"))
        self.assertIs(native.check_model_assets, run.source_checks.check_model_assets)
        self.assertIs(native.check_output, run.check_output)
        rows = source_prepare.build_source_inventory()
        with patch.object(runner, "load_sources", return_value=rows):
            self.assertEqual([len(runner.cases_for("survey", run.MODEL, s)) for s in (0, 1)], [464, 456])
            self.assertEqual([len(runner.cases_for("preflight", run.MODEL, s)) for s in (0, 1)], [7, 7])

    def test_authorization_budget_cpu_and_freeze_tampering_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "queue_run.py").write_text("fixed")
            run.write(root / "contract.json", {"queue": {"predecessor_freeze_sha256": "parent"}})
            cpu = dict(status="passed", failures=0, errors=0, skipped=0, freeze_sha256="frozen")
            run.write(root / "cpu.json", cpu)
            auth = dict(status="authorized", purpose="llama_early_trace_queue", experiment=root.name,
                user_instruction="Trace six layers after the predecessor", freeze_sha256="frozen",
                models=[run.MODEL], maximum_records={"preflight": 14, "survey": 920},
                maximum_generations={"preflight": 38, "survey": 1840},
                queue_sha256=run.sha(root / "queue_run.py"), predecessor={"freeze_sha256": "parent"},
                cpu_test_receipt={"path": "cpu.json", "sha256": run.sha(root / "cpu.json")})
            path = root / "auth.json"
            with patch.object(run, "ROOT", root), patch.object(run, "validate_freeze", return_value="frozen"):
                run.write(path, auth)
                self.assertEqual(run.validate_authorization(path), auth)
                for key, value in (("maximum_records", {"preflight": 14, "survey": 921}),
                                   ("maximum_generations", {"preflight": 38, "survey": 1841}),
                                   ("models", ["4b"]), ("freeze_sha256", "changed")):
                    run.write(path, dict(auth, **{key: value}))
                    with self.assertRaises(AssertionError):
                        run.validate_authorization(path)
                run.write(root / "cpu.json", dict(cpu, skipped=1))
                auth["cpu_test_receipt"]["sha256"] = run.sha(root / "cpu.json")
                run.write(path, auth)
                with self.assertRaises(AssertionError):
                    run.validate_authorization(path)
            run.write(root / "freeze.json", {"experiment": root.name, "files": {"queue_run.py": run.sha(root / "queue_run.py")}})
            with patch.object(run, "ROOT", root), patch.object(run, "REPO", root):
                run.validate_freeze()
                (root / "queue_run.py").write_text("changed")
                with self.assertRaisesRegex(AssertionError, "Frozen file changed"):
                    run.validate_freeze()

    def test_all_96_sites_and_same_prefix_are_required(self):
        item = {"model": run.MODEL, "record": {"output": {"token_ids": [128009]},
                "calibration": {"input_token_count": 1, "input_token_sha256": "prompt"}}}
        trace = dict(generated_token_ids=[128009], source_token_ids_match=True,
            input_token_sha256="prompt", input_token_ids=[128000], observed_input_token_ids=[128000],
            observed_position_count=1, prompt_token_count=1, forward_steps=[{}],
            clean_shadow=dict(fresh_cache=True, token_ids=[128009], prefixes_verified=1),
            sites=[dict(layer=l, component=c, clean_norm=[1.0], steer_norm=[1.0], delta_norm=[0.0],
                        relative_delta=[0.0], cosine=[1.0])
                   for l in range(32) for c in ("attention", "mlp", "residual")],
            logits={"steps": [dict(step=0, generated_token_id=128009, candidates=[dict(
                clean_logit=1.0, steer_logit=1.0, clean_logprob=-1.0, steer_logprob=-1.0)])]})
        runner = run.adapted_runner()
        self.assertTrue(runner.check_trace(trace, item, "baseline"))
        for kind in ("missing", "changed", "history"):
            bad = copy.deepcopy(trace)
            if kind == "missing":
                bad["sites"].pop()
            elif kind == "changed":
                bad["sites"][0]["delta_norm"][0] = 0.5
            else:
                bad["clean_shadow"]["token_ids"] = [7]
            with self.assertRaises(AssertionError):
                runner.check_trace(bad, item, "baseline")

    def test_preflight_requires_both_llama_workers_and_bound_receipts(self):
        runner = run.adapted_runner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workers = {}
            for shard in (0, 1):
                key = f"{run.MODEL}-shard-{shard}"
                path = root / "preflight" / key / "receipt.json"
                run.write(path, {"status": "completed"})
                workers[key] = dict(status="completed", exit_code=0, receipt_sha256=run.sha(path))
            accepted = dict(status="passed", freeze_sha256="frozen", workers=workers)
            path = root / "preflight-accepted.json"
            target = root / "survey" / f"{run.MODEL}-shard-0"
            with patch.object(runner, "verify_worker", return_value={}) as verify:
                run.write(path, accepted)
                runner.require_preflight_acceptance(target, {"freeze_sha256": "frozen"})
                self.assertEqual(verify.call_count, 2)
                for kind in ("missing", "failed", "changed_receipt"):
                    bad = copy.deepcopy(accepted)
                    key = f"{run.MODEL}-shard-1"
                    if kind == "missing":
                        del bad["workers"][key]
                    elif kind == "failed":
                        bad["workers"][key]["exit_code"] = 1
                    else:
                        bad["workers"][key]["receipt_sha256"] = "changed"
                    run.write(path, bad)
                    with self.assertRaises(AssertionError):
                        runner.require_preflight_acceptance(target, {"freeze_sha256": "frozen"})


if __name__ == "__main__":
    unittest.main()
