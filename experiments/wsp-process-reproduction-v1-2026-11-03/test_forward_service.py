"""CPU tests of request validation and paired statistics (no model, no GPU)."""
import forward_service as FS

PROF = {"name": "t", "n_layers": 24, "hidden": 1024, "inter": 3584, "n_heads": 8, "full_attn": [3, 7, 11, 15, 19, 23]}
PRACTICE = {"a": {}, "b": {}}


def rejects(req):
    try:
        FS.validate(req, PROF, PRACTICE)
    except FS.RequestError:
        return True
    return False


def test_validation():
    ok = {"type": "generate", "model": "both", "problems": ["a", "b"], "n": 128}
    assert not rejects(ok)
    assert rejects(dict(ok, n=129))                      # 2 x 129 > 256 per model with both
    assert not rejects(dict(ok, model="edited", n=256))  # 512 single
    assert rejects(dict(ok, model="edited", n=257))
    assert rejects(dict(ok, problems=["zz"]))
    assert rejects(dict(ok, max_tokens=32769))
    assert rejects(dict(ok, activations={"layers": [25]}))
    assert not rejects(dict(ok, activations={"layers": [0, 24], "mlp": True}))
    tf = {"type": "teacher_forced", "model": "original", "texts": ["x"], "return": {"hidden_states": [0, 24], "topk": 50}}
    assert not rejects(tf)
    assert rejects(dict(tf, model="both"))
    assert rejects(dict(tf, return_={}, **{"return": {"topk": 51}}))
    assert rejects(dict(tf, **{"return": {"attn_layers": [4]}}))
    assert not rejects(dict(tf, **{"return": {"attn_layers": [3, 23]}}))
    assert rejects(dict(tf, **{"return": {"mlp_act": [24]}}))
    assert rejects(dict(tf, chats=[[]]))                 # both texts and chats


def test_paired():
    o = [{"key": "a", "sample": s, "correct": c, "text": t} for s, c, t in [(0, False, "x"), (1, True, "y")]] + \
        [{"key": "b", "sample": s, "correct": False, "text": "z"} for s in (0, 1)]
    e = [{"key": "a", "sample": s, "correct": c, "text": t} for s, c, t in [(0, True, "q"), (1, True, "y")]] + \
        [{"key": "b", "sample": s, "correct": False, "text": "z"} for s in (0, 1)]
    p = FS.paired(o, e)
    assert p["accuracy_difference"] == 0.25 and p["wrong_to_right"] == 1 and p["right_to_wrong"] == 0
    assert p["identical_texts"] == 3 and p["items"] == 2


def test_seed_and_batches():
    assert FS.item_seed("a") == FS.item_seed("a") != FS.item_seed("b")
    bs = FS.batches_by_tokens([10, 50, 30, 20], 60)
    assert sorted(i for b in bs for i in b) == [0, 1, 2, 3]
    assert all(len(b) * max([10, 50, 30, 20][i] for i in b) <= 60 or len(b) == 1 for b in bs)


if __name__ == "__main__":
    test_validation(); test_paired(); test_seed_and_batches()
    print("forward_service CPU tests passed")
