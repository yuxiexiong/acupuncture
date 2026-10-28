"""Standard-library preparation checks; optional tiny synthetic torch CPU checks."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock

import capture_differences as capture

HAS_TORCH = importlib.util.find_spec("torch") is not None
INPUT = {"text": "ab", "dose": 1.0,
         "channels": [{"layer": 13, "index": 7956}, {"layer": 14, "index": 8949}],
         "vectors": [{"site": "L15.residual", "positions": [0, 1]}]}


class PreparationTests(unittest.TestCase):
    def test_ratios_and_zero_denominator(self):
        self.assertEqual(capture.ratios([0., 3., 1.], [2., 2., 0.]), [0., 1.5, None])
        for values in ([float("nan")], [float("inf")], [-1.]):
            with self.assertRaises(AssertionError):
                capture.ratios(values, [1.])

    def test_token_identity_not_just_length(self):
        capture.matched_tokens([1, 2], [1, 2])
        with self.assertRaises(AssertionError):
            capture.matched_tokens([1, 3], [1, 2])

    def test_bounded_input(self):
        capture.validate_input(INPUT)
        for bad in ({**INPUT, "dose": .1}, {**INPUT, "channels": [{"layer": 32, "index": 0}]},
                    {**INPUT, "vectors": [{"site": "L1.residual", "positions": list(range(9))}]}):
            with self.assertRaises(AssertionError):
                capture.validate_input(bad)

    def test_preparation_never_constructs_model_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "request.json"
            source.write_text(json.dumps(INPUT))
            args = SimpleNamespace(input=source, output=root / "prepared", execute=False,
                authorization=None, model_path=root / "absent-model", device="cpu")
            factory = Mock(side_effect=AssertionError("Must not load a model"))
            result = capture.run(args, factory)
            self.assertEqual(result["status"], "prepared")
            self.assertFalse(result["model_loaded"])
            factory.assert_not_called()
            self.assertFalse((args.output / "trace.json").exists())
            with self.assertRaises(FileExistsError):
                capture.run(args, factory)
            args.execute, args.output = True, root / "unauthorized"
            with self.assertRaises(AssertionError):
                capture.run(args, factory)
            self.assertFalse(args.output.exists())
            factory.assert_not_called()


def tiny_engine():
    """Reuse the frozen project's synthetic network, never RootEngine.__init__."""
    path = capture.ROOT_ENGINE.with_name("test_root_engine.py")
    spec = importlib.util.spec_from_file_location("trace_tiny_fixture", path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    engine = module.tiny_engine()
    engine.torch.set_num_threads(1)
    engine.metadata = {"synthetic_cpu_test": True, "hidden_size": 4}
    return engine


@unittest.skipUnless(HAS_TORCH, "torch unavailable locally; run on existing remote CPU environment")
class SyntheticCaptureTests(unittest.TestCase):
    def assert_no_hooks(self, engine):
        self.assertTrue(all(not m._forward_hooks and not m._forward_pre_hooks for m in engine.model.modules()))

    def test_capture_preserves_outputs_in_each_condition(self):
        engine = tiny_engine()
        tokens = capture.load_root_module()._transfer.encode_text(engine.tokenizer, INPUT["text"])
        calibration = engine.calibrate([INPUT["text"]])[0]
        for condition in capture.ORDER:
            arm = engine.make_condition(condition)
            with engine.torch.no_grad():
                expected = engine._forward(tokens, arm, calibration, 1)
            _, selected, actual, _ = capture.capture_forward(engine, tokens, arm, calibration, INPUT["channels"])
            self.assertTrue(engine.torch.equal(expected.cpu(), actual))
            self.assertEqual(len(selected), 2)
            self.assert_no_hooks(engine)

    def test_trace_alignment_zero_difference_and_shared_scales(self):
        engine = tiny_engine()
        trace = capture.collect_trace(engine, INPUT, {"test_only": True})
        capture.validate_trace(trace)
        self.assertEqual(len(trace["sites"]), 96)
        self.assertEqual(set(trace["conditions"]["A"]["source_write_audit"]), {"14"})
        self.assertEqual(set(trace["conditions"]["B"]["source_write_audit"]), {"13"})
        self.assertEqual(set(trace["conditions"]["AB"]["source_write_audit"]), {"13", "14"})
        for site in trace["sites"]:
            self.assertEqual(site["series"]["clean"]["delta_norm"], [0., 0.])
        saved = trace["details"]["vectors"][0]["values"]
        tensors = {key: engine.torch.tensor(value) for key, value in saved.items()}
        algebra = tensors["clean"] - tensors["A"] - tensors["B"] + tensors["AB"]
        expected = algebra.double().norm(dim=-1).tolist()
        site = next(row for row in trace["sites"] if row["id"] == "L15.residual")
        self.assertEqual(site["interaction"]["norm"], expected)
        calls = engine.model.calls
        self.assertEqual(len(calls), 5)  # one calibration plus four matched-input forwards
        self.assertTrue(all(engine.torch.equal(ids, calls[0][0]) for ids, _ in calls))
        self.assert_no_hooks(engine)
        broken = json.loads(json.dumps(trace))
        broken["conditions"]["B"]["input_token_sha256"] = "wrong"
        with self.assertRaises(AssertionError):
            capture.validate_trace(broken)
        broken = json.loads(json.dumps(trace))
        broken["conditions"]["B"]["calibration"]["residual_scales"]["13"] *= 2
        with self.assertRaises(AssertionError):
            capture.validate_trace(broken)

    def test_forward_failure_and_nonfinite_values_remove_hooks(self):
        for nonfinite in (False, True):
            engine = tiny_engine()
            tokens = [1, 2]
            calibration = {"residual_scales": {"13": 1., "14": 1.}}
            module = engine.layers[16].linear_attn
            original = module.forward
            def fail(value):
                if nonfinite:
                    return value * float("nan")
                raise RuntimeError("synthetic forward failure")
            module.forward = fail
            with self.assertRaises((RuntimeError, AssertionError)):
                capture.capture_forward(engine, tokens, engine.make_condition("AB"), calibration, INPUT["channels"])
            module.forward = original
            self.assert_no_hooks(engine)


if __name__ == "__main__":
    unittest.main()
