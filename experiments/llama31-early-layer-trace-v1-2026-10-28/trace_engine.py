"""Keep Llama's frozen generation path; reuse the existing trace measurements."""
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


llama = load("llama_trace_source_engine", BASE / "llama31-single-point-dose-survey-v1-2026-10-28/engine.py")
shared = load("llama_shared_trace_engine", BASE / "early-layer-mechanism-v1-2026-10-28/trace_engine.py")
record_arm, token_hash, text_hash = shared.record_arm, shared.token_hash, shared.text_hash


class TraceEngine(llama.Engine):
    # Explicit method reuse leaves loader, calibration, generation and signed
    # intervention resolution entirely on the original Llama inheritance path.
    _sites = shared.TraceEngine._sites
    _observe = shared.TraceEngine._observe
    _logit_hashes = shared.TraceEngine._logit_hashes
    _forced_clean = shared.TraceEngine._forced_clean
    _component_summaries = shared.TraceEngine._component_summaries
    _logit_summaries = shared.TraceEngine._logit_summaries
    collect = shared.TraceEngine.collect

    def verify_unchanged(self):
        result = super().verify_unchanged()
        assert not self.model._forward_hooks
        assert all(not module._forward_hooks for _, module in self._sites())
        return result
