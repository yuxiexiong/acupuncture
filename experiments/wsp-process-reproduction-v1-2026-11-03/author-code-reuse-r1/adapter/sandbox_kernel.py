"""Persistent CPU kernel. Run only inside the whitelisted bubblewrap mounts."""
import ast
import contextlib
import io
import json
import resource
import signal
import sys
import traceback
from pathlib import Path

import numpy as np
import torch
from safetensors import safe_open
from tokenizers import Tokenizer

torch.set_grad_enabled(False)
torch.set_num_threads(8)
resource.setrlimit(resource.RLIMIT_AS, (96 * 1024**3, 96 * 1024**3))
MODEL = Path("/model")
WORK = Path("/work")
EDITS = WORK / "edited"
EDITS.mkdir(exist_ok=True)
with safe_open(str(MODEL / "model.safetensors"), framework="pt", device="cpu") as f:
    NAMES = sorted(f.keys())
FROZEN = {"model.language_model.norm.weight", "model.language_model.embed_tokens.weight", "lm_head.weight"}
tok = Tokenizer.from_file(str(MODEL / "tokenizer.json"))


def load_original(name):
    if name not in NAMES:
        raise KeyError(name)
    with safe_open(str(MODEL / "model.safetensors"), framework="pt", device="cpu") as f:
        return f.get_tensor(name).float().clone()


def load(name):
    if name not in NAMES:
        raise KeyError(name)
    p = EDITS / (name + ".npy")
    return torch.from_numpy(np.load(p, allow_pickle=False)).float().clone() if p.exists() else load_original(name)


def save_edit(name, tensor):
    if name in FROZEN:
        raise ValueError("This tensor is frozen by the task contract")
    original = load_original(name)
    candidate = torch.as_tensor(tensor).detach().cpu().float()
    if candidate.shape != original.shape or not torch.isfinite(candidate).all():
        raise ValueError("Tensor shape must match and values must be finite")
    # The unpublished author's validator has no published numeric tolerance.
    # This reconstruction explicitly records its tolerance; forward must revalidate files.
    norm2 = torch.sum(original.double() ** 2)
    alpha = torch.sum(candidate.double() * original.double()) / norm2 if norm2 else 0.0
    if torch.allclose(candidate, original * float(alpha), rtol=1e-5, atol=1e-7):
        raise ValueError("Whole-tensor scaling is out of scope")
    destination = EDITS / (name + ".npy")
    temporary = EDITS / (name + ".pending")
    with temporary.open("wb") as f:
        np.save(f, candidate.numpy(), allow_pickle=False)
    temporary.replace(destination)
    return {"name": name, "relative_change": float((candidate - original).norm() / original.norm())}


def drop_edit(name):
    if name not in NAMES:
        raise KeyError(name)
    (EDITS / (name + ".npy")).unlink(missing_ok=True)


def edited():
    return sorted(p.name[:-4] for p in EDITS.glob("*.npy"))


def timeout_handler(*_):
    raise TimeoutError("Python execution exceeded 900 seconds; restart kernel")


namespace = {name: globals()[name] for name in ("NAMES", "load", "load_original", "save_edit", "drop_edit", "edited", "tok")}
signal.signal(signal.SIGALRM, timeout_handler)
print(json.dumps({"ready": True, "tensor_count": len(NAMES)}), flush=True)
for line in sys.stdin:
    request = json.loads(line)
    stream = io.StringIO()
    failed = False
    signal.alarm(900)
    try:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            tree = ast.parse(request["code"])
            last = tree.body.pop() if tree.body and isinstance(tree.body[-1], ast.Expr) else None
            exec(compile(tree, "<wsp-python>", "exec"), namespace)
            if last is not None:
                result = eval(compile(ast.Expression(last.value), "<wsp-python>", "eval"), namespace)
                if result is not None:
                    print(repr(result))
    except BaseException:
        failed = True
        traceback.print_exc(file=stream)
    finally:
        signal.alarm(0)
    output = stream.getvalue()
    # Full tool output is preserved by the observer; the editor sees the original cap.
    print(json.dumps({"id": request["id"], "failed": failed, "full_output": output,
                      "editor_output": output[:10000].encode("ascii", "replace").decode(),
                      "truncated": len(output) > 10000}), flush=True)
