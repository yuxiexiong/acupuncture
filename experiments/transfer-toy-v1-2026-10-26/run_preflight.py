"""Bounded GPU hook/state checks; no experimental answers or new condition selection."""
import argparse
from pathlib import Path
import time
import traceback
from run_io import utc, write, sha
from transfer_engine import TransferEngine, encode_text


def main(args):
    import torch
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    receipt = dict(status='running', started_utc=utc(), arguments=vars(args),
                   code_sha256={p.name: sha(p) for p in Path(__file__).parent.glob('*.py')})
    write(out / 'receipt.json', receipt)
    try:
        engine = TransferEngine(args.model)
        text = 'A library has three shelves with ten books each. Five are borrowed. How many books remain?'
        cal = engine.calibrate([text])
        inputs = engine._inputs([encode_text(engine.tokenizer, text)])
        values = {}
        with torch.inference_mode():
            for label in ['T_0', 'zero_channel', 'zero_vector', 'T_0_restored']:
                arm = 'T_0' if label.endswith('_restored') else label
                with engine._intervention(arm, cal, inputs['attention_mask']):
                    values[label] = engine.model(**inputs, use_cache=False, logits_to_keep=1).logits.detach().cpu()
        comparisons = {label: torch.equal(values['T_0'], value) for label, value in values.items()}
        assert all(comparisons.values()), comparisons
        generator = torch.Generator().manual_seed(20261026)
        w = torch.randn(7, 13, generator=generator)
        a = torch.randn(2, 5, 13, generator=generator)
        altered = a.clone(); altered[..., 3] += 0.75
        error = (altered @ w.T - (a @ w.T + .75 * w[:, 3])).abs().max().item()
        assert error < 1e-5
        receipt.update(status='completed', engine=engine.metadata, calibration=cal,
                       zero_hook_exact=comparisons, synthetic_fp32_max_abs_error=error,
                       tokenizer_sha256={name: sha(Path(args.model)/name) for name in
                           ['tokenizer.json', 'tokenizer_config.json', 'chat_template.jinja'] if (Path(args.model)/name).exists()},
                       **engine.verify_unchanged())
    except Exception as exc:
        receipt.update(status='failed', error=str(exc), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), elapsed_seconds=time.monotonic()-start)
        write(out/'receipt.json', receipt)
        print({k:receipt[k] for k in ['status', 'ended_utc', 'elapsed_seconds']}, flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--model', required=True); p.add_argument('--output', required=True)
    main(p.parse_args())
