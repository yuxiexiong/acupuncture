"""F1 structure probe (CPU only): configs, layer picks, mixer types, chat templates.

No weights are loaded.  Modules are instantiated on the meta device only to read
names.  Output: JSON to stdout.
"""
import json
import sys

import torch
from transformers import AutoConfig, AutoTokenizer

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import models as M  # noqa: E402


def main():
    out = {}
    probe_user = "Records:\nR1 | name: Talvin Osk | color: amber\n\nQuestion: What color is listed for Talvin Osk?"
    for key, spec in M.MODELS.items():
        cfg = AutoConfig.from_pretrained(spec["path"], local_files_only=True)
        tcfg = M.text_config(cfg)
        tok = AutoTokenizer.from_pretrained(spec["path"], local_files_only=True)
        n_layers = tcfg.num_hidden_layers
        picks = M.pick_layers(n_layers)
        layer_types = M.layer_types(key, tcfg)
        rendered = M.render(tok, key, probe_user)
        ids_template = M.template_ids(tok, key, probe_user)
        ids_text = tok(rendered, add_special_tokens=False)["input_ids"]
        with torch.device("meta"):
            model = M.build_from_config(key, cfg)
        layers = M.get_layers(model, key)
        block = layers[picks[0]]
        out[key] = {
            "path": spec["path"],
            "n_layers": n_layers,
            "hidden_size": tcfg.hidden_size,
            "picks": picks,
            "pick_mixers": {str(i): {"prev": layer_types[i - 1] if i > 0 else None,
                                     "this": layer_types[i],
                                     "next": layer_types[i + 1] if i + 1 < n_layers else None}
                            for i in picks},
            "layer_type_counts": {t: layer_types.count(t) for t in sorted(set(layer_types))},
            "block_children": [n for n, _ in block.named_children()],
            "mlp_children": [n for n, _ in M.get_mlp(block, key).named_children()],
            "intermediate_size": M.get_mlp(block, key).down_proj.weight.shape[1],
            "mlp_down_multiplier": M.down_multiplier(key, tcfg),
            "stop_ids": M.stop_ids(spec["path"], tok),
            "stop_tokens": [tok.convert_ids_to_tokens(t) for t in M.stop_ids(spec["path"], tok)],
            "rendered_tail_repr": repr(rendered[-120:]),
            "rendered_head_repr": repr(rendered[:160]),
            "template_ids_equal_retokenized_text": ids_template == ids_text,
            "n_tokens_probe": len(ids_template),
            "bos_token": tok.bos_token,
        }
    json.dump(out, sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
