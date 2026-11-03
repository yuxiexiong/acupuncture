"""Synthetic counterexamples to natural-mechanism attribution; no model/GPU."""
import json
import math

# A one-dimensional native trajectory family: alpha=.8, k=1, v=1,
# beta in [.2, .4], and a common preceding state of 1.
def step(beta, value):
    return .8 * (1-beta) + beta*value

native_range = [step(.2, 1.), step(.4, 1.)]
compensated_value = (.2*1.)/.4
compensated_state = step(.4, compensated_value)
assert math.isclose(.4*compensated_value, .2)
assert compensated_state < min(native_range)

# Two distinct reader functions give identical four cells and agree on s=o.
def joint_limiter(s, o):
    return min(s, o)

def content_with_match_gate(s, o):
    return o*max(0., 1.-abs(s-o))

grid = [(0., 0.), (1., 0.), (0., 1.), (1., 1.)]
a = [joint_limiter(*x) for x in grid]
b = [content_with_match_gate(*x) for x in grid]
assert a == b == [0., 0., 0., 1.]
assert all(joint_limiter(x, x) == content_with_match_gate(x, x)
           for x in [0., .25, .5, .75, 1.])
assert joint_limiter(.75, .25) != content_with_match_gate(.75, .25)

print(json.dumps({
    'status': 'counterexamples_verified_synthetic_only',
    'compensation': {'native_state_range': native_range,
                     'compensated_value': compensated_value,
                     'compensated_state': compensated_state,
                     'write_product_preserved': True},
    'four_cells': {'order': ['00', '10', '01', '11'],
                   'joint_limiter': a, 'content_with_match_gate': b,
                   'same_on_diagonal': True},
    'interpretation': 'Algebraic validity does not certify source-trajectory support; four cells do not uniquely distinguish joint computation from matching response.',
    'limits': 'Not evidence that actual Qwen states are out of distribution, nor a reproduction or model experiment.'
}, ensure_ascii=False, indent=2))
