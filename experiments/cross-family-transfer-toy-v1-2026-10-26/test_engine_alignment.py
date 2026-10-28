"""CPU-only synthetic checks; no torch, weights, downloads or model execution."""
from types import SimpleNamespace

from collect import aligned_tokens, plain_text, token_boundaries
from engine import LlamaTokenizer, encode_pair, encode_text, stop_tokens


class FakeTokenizer:
    bos_token_id, eos_token_id, pad_token_id = 1000, 1001, None

    def __init__(self, width=1):
        self.width, self.pieces = width, {}

    def __call__(self, text, **kwargs):
        assert kwargs["add_special_tokens"] is False
        offsets = [(i, min(i + self.width, len(text))) for i in range(0, len(text), self.width)]
        ids = []
        for left, right in offsets:
            piece = text[left:right]
            identifier = next((i for i, value in self.pieces.items() if value == piece), len(self.pieces) + 10)
            self.pieces[identifier] = piece
            ids.append(identifier)
        return {"input_ids": ids, "offset_mapping": offsets}

    def encode(self, text, add_special_tokens=True, **kwargs):
        if text.startswith("<bos>"):
            return [self.bos_token_id, *self.encode(text[5:], False)]
        ids = self(text, add_special_tokens=False)["input_ids"]
        return [self.bos_token_id, *ids] if add_special_tokens else ids

    def decode(self, ids, **kwargs):
        ids = [ids] if isinstance(ids, int) else ids
        return "".join("<bos>" if i == self.bos_token_id else self.pieces[i] for i in ids)

    def get_vocab(self):
        return {"<|eot_id|>": 1002}

    def apply_chat_template(self, messages, **kwargs):
        return kwargs["date_string"]


def main():
    source, target = FakeTokenizer(1), LlamaTokenizer(FakeTokenizer(2))
    row = {"id": "unicode", "kind": "plain", "text": "a中😀bcd"}
    text, source_ids, target_ids, paired = aligned_tokens(source, target, row, limit=5)
    assert paired["char_end"] == [2, 4]
    assert paired["source_positions"] == [1, 3] and paired["target_positions"] == [1, 2]
    assert source_ids != target_ids and len(source_ids) <= 5 and len(target_ids) <= 5
    for end, si, ti in zip(paired["char_end"], paired["source_positions"], paired["target_positions"]):
        assert source.decode(source_ids[:si + 1]) == target.decode(target_ids[1:ti + 1]) == text[:end]
    assert paired == aligned_tokens(source, target, row, limit=5)[-1]
    assert plain_text({"kind": "dialogue", "messages": [{"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"}]}) == "user:\nHi\n\nassistant:\nHello"
    long = {"id": "long", "kind": "plain", "text": "a" * 2000}
    _, a, b, alignment = aligned_tokens(source, target, long)
    assert len(alignment["char_end"]) == 128 and max(len(a), len(b)) <= 512

    class ByteTokenizer(FakeTokenizer):
        def __call__(self, text, **kwargs):
            return {"input_ids": [1, 2, 3], "offset_mapping": [(0, 1), (0, 1), (1, 2)]}

        def decode(self, ids, **kwargs):
            return {(): "", (1,): "�", (1, 2): "中", (1, 2, 3): "中a"}[tuple(ids)]

    _, boundaries = token_boundaries(ByteTokenizer(), "中a")
    assert boundaries == {1: 1, 2: 2}
    try:
        token_boundaries(ByteTokenizer(), "中a", limit=1)
    except AssertionError:
        pass
    else:
        raise AssertionError("Truncated duplicate Unicode offset accepted")
    assert encode_text(target, "abcd")[0] == target.bos_token_id
    assert encode_text(target, "<bos>abcd").count(target.bos_token_id) == 1
    assert target.apply_chat_template([]) == "26 Oct 2026"
    context, continuation = encode_pair(target, "ab ", "cd")
    assert context[0] == target.bos_token_id and target.bos_token_id not in continuation
    generation = SimpleNamespace(eos_token_id=[1001, 1002, 1003])
    config = SimpleNamespace(eos_token_id=1001, vocab_size=2000)
    assert stop_tokens(target, generation, config) == ([1001, 1002, 1003], 1001)
    try:
        stop_tokens(target, SimpleNamespace(eos_token_id=[1001]), config)
    except AssertionError:
        pass
    else:
        raise AssertionError("Missing chat EOS was silently accepted")
    print("PASS: text boundaries, Unicode overlap, token caps, BOS and complete EOS controls")


if __name__ == "__main__":
    main()
