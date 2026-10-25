"""CPU-only boundary checks; the runner must additionally validate real model batches."""
from model_engine import Engine, encode_pair, encode_text, finish_generation, mechanical_checks, token_hash

assert all(callable(getattr(Engine, name)) for name in ("calibrate", "score", "generate", "verify_unchanged"))
assert callable(mechanical_checks)


class Tokenizer:
    bos_token_id, eos_token_id = None, 99

    def __init__(self):
        self.calls = []

    def encode(self, text, **kwargs):
        self.calls.append((text, kwargs))
        return list(text.encode())

    def decode(self, token):
        return "<eos>"


tok = Tokenizer()
ctx, cont = encode_pair(tok, "Question: \n", " A")
assert bytes(ctx).decode() == "Question:"
assert bytes(cont).decode() == " \n A"
assert all(kwargs == {} for _, kwargs in tok.calls)
encode_text(tok, "<eos>already prefixed")
assert tok.calls[-1][1] == {"add_special_tokens": False}
assert token_hash([1, 2]) == token_hash([1, 2]) != token_hash([2, 1])


def decode(tokens, skip_special_tokens):
    words = {1: "answer", 2: "\n", 3: "\nextra", 4: "text", 9: "<eos>"}
    return "".join(words[t] for t in tokens if not (skip_special_tokens and t == 9))


r = finish_generation([1, 2, 3, 9, 9], [9], 9, 5, 3, ["\n\n"], decode)
assert r["token_ids"] == [1, 2, 3] and r["end_reason"] == "task_stop"
assert r["answer_text"] == "answer" and r["raw_text"] == "answer\n\nextra"
assert r["returned_padding_count"] == 2
r = finish_generation([1, 9, 9], [9], 9, 5, None, [], decode)
assert r["end_reason"] == "eos_token" and r["token_ids"] == [1, 9] and r["answer_text"] == "answer"
r = finish_generation([1, 4], [9], 9, 2, None, [], decode)
assert r["end_reason"] == "length_limit" and r["answer_text"] == "answertext"
try:
    finish_generation([1, 9, 4], [9], 9, 3, None, [], decode)
except AssertionError:
    pass
else:
    raise AssertionError("Nonpadding output after EOS must be rejected")
print("PASS: harness boundary encoding, tokenizer defaults, task stops, EOS/padding, and full budgets")
