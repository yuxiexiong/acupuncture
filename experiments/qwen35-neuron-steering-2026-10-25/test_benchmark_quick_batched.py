"""No model loading: check row EOS trimming and preservation of real generated padding."""
from benchmark_quick_batched import trim_generated


assert trim_generated([5, 9, 0, 0], [9], 0, 4) == ([5, 9], 2, "eos_token")
assert trim_generated([0, 5, 9, 0], [9], 0, 4) == ([0, 5, 9], 1, "eos_token")
assert trim_generated([1, 2, 3, 4], [9], 0, 4) == ([1, 2, 3, 4], 0, "length_limit")
assert trim_generated([9, 0, 0, 0], [9], 0, 4) == ([9], 3, "eos_token")
for bad in ([5, 9, 6, 0], [1, 2]):
    try:
        trim_generated(bad, [9], 0, 4)
    except AssertionError:
        pass
    else:
        raise AssertionError("Malformed batched return was silently accepted")
print("PASS: first-EOS row trimming, generated pad preservation, unfinished budget and post-EOS validation")
