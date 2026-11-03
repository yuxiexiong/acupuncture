"""Verify text export preserves raw-model text-only chat tokenization."""
import argparse
import hashlib
import json
from pathlib import Path
from transformers import AutoTokenizer


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--text", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args()
    raw, text = [AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
                 for path in (args.raw, args.text)]
    backend_before, backend_after = raw.backend_tokenizer.to_str(), text.backend_tokenizer.to_str()
    assert backend_before == backend_after, "Backend differs; short fixtures cannot certify identity"
    assert raw.chat_template == text.chat_template
    cases = []
    for problem in ("What is 2 + 3?", r"Solve for x: 3x + 4 = 19."):
        messages = [{"role": "user", "content": problem + "\nPlease reason step by step, and put your final answer within \\boxed{}."}]
        a, b = [t.apply_chat_template(messages, tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=True)
                for t in (raw, text)]
        assert a == b
        rendered = text.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=True)
        assert rendered.endswith("<think>\n")
        cases.append({"messages": messages, "token_ids": a, "rendered": rendered,
                      "sha256": hashlib.sha256(json.dumps(a).encode()).hexdigest()})
    receipt = {"status": "passed", "raw": str(args.raw), "text": str(args.text),
               "backend_sha256": hashlib.sha256(backend_before.encode()).hexdigest(),
               "scope": "text-only thinking chat fixtures, no model forward", "cases": cases}
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "passed", "cases": len(cases)}))


if __name__ == "__main__":
    main()
