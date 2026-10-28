"""Single-channel survey; reuse the existing immutable model and decoding path."""
from contextlib import contextmanager
import importlib.util
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("survey_transfer_engine", BASE / "transfer-toy-v1-2026-10-26/transfer_engine.py")
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


class SurveyEngine(transfer.TransferEngine):
    def __init__(self, model_path, model_spec, device):
        super().__init__(model_path, device=device, batch_size=1, threads=4)
        assert len(self.layers) == model_spec["layers"]
        assert self.metadata["hidden_size"] == model_spec["hidden_size"]
        assert self.metadata["intermediate_size"] == model_spec["intermediate_size"]
        self.modules = {i: block.mlp.down_proj for i, block in enumerate(self.layers)}
        assert all(m.bias is None for m in self.modules.values())
        self.column_norms = {str(i): m.weight.float().norm(dim=0).cpu() for i, m in self.modules.items()}
        self.weight_hashes = self._weight_hashes()
        self.metadata.update(layers=list(self.modules), target_weight_sha256_before=self.weight_hashes,
                             model_id=model_spec["id"], revision=model_spec["revision"],
                             chat_template_applied=True, enable_thinking=False)
        self.last_hook = None

    def calibrate(self, contexts):
        results = []
        for text in contexts:
            tokens = transfer.encode_text(self.tokenizer, text)
            assert len(tokens) >= 2
            inputs = self._inputs([tokens])
            row = {"context_sha256": transfer.text_hash(text), "input_token_sha256": transfer.token_hash(tokens),
                   "input_token_count": len(tokens), "residual_scales": {}}
            handles = []
            try:
                for i, block in enumerate(self.layers):
                    def capture(_module, _args, output, i=i):
                        residual = output[0] if isinstance(output, tuple) else output
                        value = self.torch.quantile(residual[0, 1:].float().norm(dim=-1), 0.5).item()
                        assert math.isfinite(value) and value > 0
                        row["residual_scales"][str(i)] = value
                    handles.append(block.register_forward_hook(capture))
                with self.torch.inference_mode():
                    self.model(**inputs, use_cache=False, logits_to_keep=1)
            finally:
                for handle in handles:
                    handle.remove()
            results.append(row)
        return results

    @contextmanager
    def _intervention(self, arm, calibrations, input_mask):
        assert all(not m._forward_pre_hooks for m in self.modules.values())
        self.last_hook = None
        if arm == "baseline":
            yield
            return
        layer, channel, dose = arm
        assert len(calibrations) == 1 and input_mask.shape[0] == 1
        assert layer in self.modules and 0 <= channel < self.modules[layer].weight.shape[1]
        assert dose in (0.0, 1.0)
        module = self.modules[layer]
        norm = float(self.column_norms[str(layer)][channel])
        assert math.isfinite(norm) and norm > 0
        scale = calibrations[0]["residual_scales"][str(layer)]
        requested = dose * scale / norm
        amount = module.weight.new_tensor(requested)
        audit = {"layer": layer, "channel": channel, "dose": dose, "column_norm": norm,
                 "clean_residual_scale": scale, "requested_offset": requested,
                 "bf16_offset": float(amount), "calls": 0, "positions": 0}
        self.last_hook = audit
        def add_one(_module, args):
            original = args[0]
            changed = original.clone()
            width = original.shape[1]
            mask = input_mask.to(original.dtype) if width == input_mask.shape[1] else 1.0
            assert width == input_mask.shape[1] or width == 1
            changed[..., channel] += amount * mask
            audit["calls"] += 1
            audit["positions"] += width
            if audit["calls"] == 1:
                # One prefill sample establishes the actual BF16 local change; no content judgment.
                audit["prefill_first_original"] = float(original[0, 0, channel])
                audit["prefill_first_changed"] = float(changed[0, 0, channel])
            return (changed, *args[1:])
        handle = module.register_forward_pre_hook(add_one)
        try:
            yield
        finally:
            handle.remove()

    def verify_unchanged(self):
        assert all(not m._forward_pre_hooks for m in self.modules.values())
        assert all(not block._forward_hooks for block in self.layers)
        hashes = self._weight_hashes()
        assert hashes == self.weight_hashes
        return {"target_weight_sha256_after": hashes, "hooks_removed": True}
