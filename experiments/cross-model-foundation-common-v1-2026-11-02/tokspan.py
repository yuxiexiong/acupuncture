"""Tokenization helpers shared by engine, validation and tests (CPU only)."""
import models as M


def encode_item(tok, key, item):
    """Render one panel item with the model's chat template and locate spans.

    Returns ids (full prompt), record token positions (tokens whose char span lies
    fully inside the record block; boundary-crossing tokens are excluded and
    counted), and q = last prompt position.
    """
    rendered = M.render(tok, key, item["user"])
    ids_t = M.template_ids(tok, key, item["user"])
    enc = tok(rendered, add_special_tokens=False, return_offsets_mapping=True)
    ids = list(enc["input_ids"])
    assert ids == ids_t, "retokenized rendered text differs from template ids"
    off = rendered.find(item["user"])
    assert off >= 0 and rendered.count(item["user"]) == 1
    rs, re_ = off + item["record_char_span"][0], off + item["record_char_span"][1]
    inside, crossing = [], 0
    for i, (a, b) in enumerate(enc["offset_mapping"]):
        if a >= rs and b <= re_ and b > a:
            inside.append(i)
        elif a < re_ and b > rs:
            crossing += 1
    assert inside, "empty record span"
    assert inside == list(range(inside[0], inside[-1] + 1)), "record span not contiguous"
    q = len(ids) - 1
    assert inside[-1] < q
    return {"ids": ids, "record_positions": inside, "record_boundary_excluded": crossing,
            "q": q, "n_tokens": len(ids)}


def continuation_ids(tok, key, item, text):
    """Exact continuation tokens of `text` after the rendered prompt (no leading space)."""
    rendered = M.render(tok, key, item["user"])
    base = tok(rendered, add_special_tokens=False)["input_ids"]
    full = tok(rendered + text, add_special_tokens=False)["input_ids"]
    if full[:len(base)] != base:
        return None
    return full[len(base):]
