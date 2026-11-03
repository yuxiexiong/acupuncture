"""CPU-only synthetic design checks; no model, tensor library, or GPU."""
import itertools
import json
import math
import random

rng = random.Random(20261031)
errors = []


def close(x, y):
    error = max(abs(a - b) for row_x, row_y in zip(x, y)
                for a, b in zip(row_x, row_y))
    errors.append(error)
    assert error < 1e-11, error


def operator(alpha, beta, key):
    return [[alpha * ((i == j) - beta * key[i] * key[j])
             for j in range(2)] for i in range(2)]


def write(key, p):
    return [[key[i] * p[j] for j in range(2)] for i in range(2)]


def affine(state, alpha, beta, key, p):
    a, b = operator(alpha, beta, key), write(key, p)
    return [[sum(a[i][k] * state[k][j] for k in range(2)) + b[i][j]
             for j in range(2)] for i in range(2)]


def native(state, alpha, beta, key, value):
    decayed = [[alpha * x for x in row] for row in state]
    residual = [value[j] - sum(key[i] * decayed[i][j] for i in range(2))
                for j in range(2)]
    return [[decayed[i][j] + key[i] * beta * residual[j]
             for j in range(2)] for i in range(2)]


def compensate(beta, p):
    if beta == 0 and all(x == 0 for x in p):
        return [0. for x in p]
    if beta <= 0:
        raise ValueError('Cannot implement this write through a zero beta.')
    return [x / beta for x in p]


def source_step():
    angle = rng.uniform(-math.pi, math.pi)
    alpha, beta = rng.uniform(.2, .95), rng.uniform(.15, .85)
    value = [rng.uniform(-2, 2) for _ in range(2)]
    return alpha, beta, [math.cos(angle), math.sin(angle)], [beta*x for x in value]


for _ in range(32):
    sources = [[source_step() for _ in range(5)] for _ in range(2)]
    for w, r, k in itertools.product(range(2), repeat=3):
        s = [[0., 0.], [0., 0.]]
        online = [[0., 0.], [0., 0.]]
        for t in range(5):
            alpha, beta = sources[r][t][:2]
            key, p = sources[k][t][2], sources[w][t][3]
            value = compensate(beta, p)
            close(write(key, p), write(key, [beta*x for x in value]))
            s = affine(s, alpha, beta, key, p)
            online = native(online, alpha, beta, key, value)
            close(s, online)
            # W holds A fixed; R holds B fixed even when beta changes.
            other_p = sources[1-w][t][3]
            zero = [[0., 0.], [0., 0.]]
            old_parts = []
            for write_p in (p, other_p):
                full = native(online, alpha, beta, key, compensate(beta, write_p))
                new_only = native(zero, alpha, beta, key, compensate(beta, write_p))
                old_parts.append([[full[i][j]-new_only[i][j] for j in range(2)] for i in range(2)])
            close(*old_parts)
            other_beta = sources[1-r][t][1]
            other_alpha = sources[1-r][t][0]
            close(native(zero, alpha, beta, key, value),
                  native(zero, other_alpha, other_beta, key, compensate(other_beta, p)))
            # A changed write gives exactly the expected one-step difference.
            sw = affine(online, alpha, beta, key, other_p)
            sb = affine(online, alpha, beta, key, p)
            close([[sw[i][j]-sb[i][j] for j in range(2)] for i in range(2)],
                  write(key, [other_p[j]-p[j] for j in range(2)]))

try:
    compensate(0., [1., 0.])
    raise AssertionError('Zero beta was silently accepted.')
except ValueError:
    pass
assert compensate(0., [0., 0.]) == [0., 0.]

# Same total effect, different cut-channel mechanisms: the crossed cells distinguish them.
functions = {'state_only': lambda s, o: s, 'other_only': lambda s, o: o,
             'joint_only': lambda s, o: s*o, 'cancellation': lambda s, o: s-o}
cells = {}
for name, f in functions.items():
    y00, y10, y01, y11 = f(0, 0), f(1, 0), f(0, 1), f(1, 1)
    interaction = y11-y10-y01+y00
    assert y11-y00 == (y10-y00)+(y01-y00)+interaction
    cells[name] = dict(y00=y00, y10=y10, y01=y01, y11=y11,
                       state_effect=y10-y00, other_effect=y01-y00, interaction=interaction)
assert len({tuple(cells[n].values()) for n in ('state_only', 'other_only', 'joint_only')}) == 3

print(json.dumps({'status': 'passed_synthetic_only', 'seed': 20261031,
                  'cases': 32, 'factor_cells_per_case': 8, 'steps_per_case': 5,
                  'max_abs_error': max(errors), 'zero_beta_rejected': True,
                  'cut_counterexamples': cells,
                  'limits': 'No real-model run, BF16 validation, distribution-validity test, or scientific mechanism finding.'},
                 ensure_ascii=False, indent=2))
