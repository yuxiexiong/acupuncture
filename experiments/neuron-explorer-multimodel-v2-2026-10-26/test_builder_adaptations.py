"""CPU-only checks: grid identity/coverage and exact half-open shard boundaries."""
import importlib.util
from pathlib import Path

import numpy as np


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


layout = load("build_layout", "upstream/explorer/build_layout.py")
steer = load("steer_lens", "upstream/sweep/steer_lens.py")
rng = np.random.default_rng(0)
for n in (1, 5, 6144, 9216, 12288):
    xy = rng.normal(size=(n, 2))
    actual = layout.snap_to_grid(xy)
    assert actual.dtype == np.int16
    assert np.array_equal(np.sort(actual), np.arange(n)), n
    if n == 9216:
        expected = np.zeros(n, np.int16)
        by_y = np.argsort(xy[:, 1], kind="stable")
        for row in range(96):
            band = by_y[row * 96:(row + 1) * 96]
            band = band[np.argsort(xy[band, 0], kind="stable")]
            expected[band] = row * 96 + np.arange(96)
        assert np.array_equal(actual, expected), "4B grid behavior changed"

for n in (6144, 9216, 12288):
    assert steer.neuron_bounds(None, n) == (0, n)
    spans = [steer.neuron_bounds(f"{start}:{min(start + 1000, n)}", n) for start in range(0, n, 1000)]
    assert [i for start, stop in spans for i in range(start, stop)] == list(range(n))
    assert steer.neuron_bounds(f"{n - 1}:{n}", n) == (n - 1, n)
    for spec in ("0:0", "1:0", "-1:2", f"0:{n + 1}", "0-1", "0:1:2"):
        try:
            steer.neuron_bounds(spec, n)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid shard accepted: {spec}")
assert steer.CHAT == ["Who are you?", "Write whatever you like."]
assert steer.PLAIN == ["I think the most important thing to remember is", "Today we are going to talk about"]
print("PASS: non-square grids, unchanged 4B layout snapping, complete/nonoverlapping shards and unchanged contexts")
