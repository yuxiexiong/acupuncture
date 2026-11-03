"""CPU-only audit of frozen tokenizer profiles and already dispatched inputs."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['HF_HUB_OFFLINE'] = '1'
import transformers
from transformers import AutoTokenizer

ROOT = Path('/workspace/acupuncture/external/wsp')
CASES = ["2 + 3 = 5", "1234567 3.14159", "We're solving x² + 2x = 0.\n\\boxed{3}",
         "中文数学：三加二", "e\u0301 A\u0308 café", "def f(x):\n    return x + 1\n", "<think>\n</think>"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def backend(tok):
    return json.loads(tok.backend_tokenizer.to_str())


results = []
for name, text, raw, turn in [
    ('0p8b', ROOT/'text-Qwen3.5-0.8B', ROOT/'raw-Qwen3.5-0.8B', 'turn-002'),
    ('4b', ROOT/'text-Qwen3.5-4B-r2', Path('/data/models/Qwen3.5-4B-851bf6e'), 'turn-003'),
]:
    current = AutoTokenizer.from_pretrained(text, local_files_only=True)
    original = AutoTokenizer.from_pretrained(raw, local_files_only=True)
    # 0.8B intentionally follows the author's frozen Qwen2 profile, not raw AutoTokenizer.
    with tempfile.TemporaryDirectory(prefix='wsp-author-tokenizer-') as directory:
        if name == '0p8b':
            author = ROOT/'observer-upstream/exp8_math/base_model/Qwen3.5-0.8B-text'
            for file in ['config.json', 'tokenizer_config.json', 'chat_template.jinja']:
                (Path(directory)/file).symlink_to(author/file)
            (Path(directory)/'tokenizer.json').symlink_to(raw/'tokenizer.json')
            reference = AutoTokenizer.from_pretrained(directory, local_files_only=True)
        else:
            reference = original
    explicit_false = AutoTokenizer.from_pretrained(text, local_files_only=True, fix_mistral_regex=False)
    config = json.loads((text/'config.json').read_text())
    action = ROOT/'fleet-v1'/('math-'+name)/'actions'/turn
    items = json.loads((action/'gen_1_original.raw.jsonl.items.json').read_text())
    mismatches = []
    for item in items:
        messages = [{'role': 'user', 'content': item['user']}]
        outputs = []
        for tok in [current, reference]:
            rendered = tok.apply_chat_template(messages, tokenize=False, enable_thinking=True, add_generation_prompt=True)
            outputs.append(tok(rendered, add_special_tokens=False)['input_ids'])
        if outputs[0] != item['prompt_ids'] or outputs[1] != item['prompt_ids']:
            mismatches.append(item['key'])
    raw_out = action/'gen_1_original.raw.jsonl'
    decode_count = 0
    decode_mismatches = []
    if raw_out.exists():
        for line in raw_out.open():
            record = json.loads(line)
            a = current.decode(record['token_ids'], skip_special_tokens=True)
            b = reference.decode(record['token_ids'], skip_special_tokens=True)
            decode_count += 1
            if a != b or a != record['text']:
                decode_mismatches.append(record['key'])
    current_backend, reference_backend, raw_backend, false_backend = map(backend, [current, reference, original, explicit_false])
    result = dict(profile=name, model_type=config.get('model_type'),
                  config_transformers_version=config.get('transformers_version'),
                  runtime_class=type(current).__name__, raw_class=type(original).__name__,
                  reference_class=type(reference).__name__,
                  tokenizer_file_sha256=sha(text/'tokenizer.json'),
                  raw_tokenizer_file_sha256=sha(raw/'tokenizer.json'),
                  reference_backend_equal=current_backend==reference_backend,
                  raw_auto_backend_equal=current_backend==raw_backend,
                  explicit_false_backend_equal=current_backend==false_backend,
                  reference_backend_diff_keys=[k for k in current_backend if current_backend[k]!=reference_backend[k]],
                  raw_auto_backend_diff_keys=[k for k in current_backend if current_backend[k]!=raw_backend[k]],
                  explicit_false_backend_diff_keys=[k for k in current_backend if current_backend[k]!=false_backend[k]],
                  chat_template_equal=current.chat_template==reference.chat_template,
                  dispatched_inputs=len(items), input_mismatches=mismatches,
                  saved_outputs_checked=decode_count, decode_mismatches=decode_mismatches,
                  fixture_mismatches=[s for s in CASES if current.encode(s)!=reference.encode(s)])
    results.append(result)
passed = all(r['reference_backend_equal'] and r['explicit_false_backend_equal'] and r['chat_template_equal']
             and not r['input_mismatches'] and not r['decode_mismatches'] and not r['fixture_mismatches'] for r in results)
print(json.dumps(dict(status='passed' if passed else 'requires_review', transformers_version=transformers.__version__,
                     scope='CPU tokenization only; no model forward or runtime changes', results=results), indent=2))
