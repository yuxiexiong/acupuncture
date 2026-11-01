"""CPU tests for CFM-CONV-FACTOR v1 (no weights, no CUDA).

CUDA_VISIBLE_DEVICES= python test_conv_factor.py [RECEIPT_JSON]
"""
import json
import os
import sys
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cf_core as K  # noqa: E402
import cf_analysis as A  # noqa: E402
import torch  # noqa: E402


def rnd(*shape, seed=0):
    return torch.randn(*shape, generator=torch.Generator().manual_seed(seed), dtype=torch.float64)


class ConvSlots(unittest.TestCase):
    def test_real_update_reads_slots_1_to_3(self):
        import transformers.models.qwen3_5.modeling_qwen3_5 as qm
        fn = getattr(qm.causal_conv1d_update, '__wrapped__', qm.causal_conv1d_update)
        C = 16
        w = torch.nn.Parameter(rnd(C, 4, seed=1).float())
        b = torch.nn.Parameter(rnd(C, seed=2).float())
        x = rnd(1, C, 1, seed=3).float()
        st = rnd(1, C, 4, seed=4).float()

        def run(state):
            s = state.clone()
            return fn(x.clone(), s, w, b, 'silu'), s
        base, s_after = run(st)
        self.assertTrue(torch.equal(s_after[..., :3], st[..., 1:]))        # in-place shift: oldest slot leaves
        alt = st.clone()
        alt[..., 0] += 5
        self.assertTrue(torch.equal(run(alt)[0], base))                     # slot 0 not consumed
        for k in K.CONSUMED:
            alt = st.clone()
            alt[..., k] += 5
            self.assertFalse(torch.equal(run(alt)[0], base), k)


class Segments(unittest.TestCase):
    def test_assemble_and_views(self):
        fq = rnd(1, 8192, 4, seed=1).to(torch.bfloat16)
        fv = rnd(1, 8192, 4, seed=2).to(torch.bfloat16)
        a = K.assemble(fq, fv)
        self.assertTrue(torch.equal(a[:, :4096], fq[:, :4096]))
        self.assertTrue(torch.equal(a[:, 4096:], fv[:, 4096:]))
        self.assertTrue(torch.equal(K.assemble(fq, fq), fq))
        for seg in ('q', 'k', 'v'):
            v = K.seg_view(fq, seg)
            self.assertEqual(tuple(v.shape), (4, K.HEADS[seg], 128))
            self.assertTrue(torch.equal(K.seg_put(fq, seg, v), fq))
        # slot / head layout: channel h*128+d of segment at slot s
        self.assertEqual(float(K.seg_view(fq, 'v')[2, 3, 5]), float(fq[0, 4096 + 3 * 128 + 5, 2].double()))


class RandomRefs(unittest.TestCase):
    def test_xi(self):
        diffs = {i: rnd(4, 32, 128, seed=i) for i in (13, 14)}
        diffs[14][1, 7] = 0
        xa = K.random_xi('X', 0, 'v', [14, 13], diffs)
        xb = K.random_xi('X', 0, 'v', [13, 14], diffs)
        self.assertTrue(all(torch.equal(xa[i], xb[i]) for i in xa))
        self.assertFalse(torch.equal(K.random_xi('X', 1, 'v', [13, 14], diffs)[13], xa[13]))
        for i in xa:
            self.assertTrue(torch.allclose(xa[i].norm(dim=-1), diffs[i].norm(dim=-1), rtol=1e-12, atol=1e-15))
        self.assertEqual(float(xa[14][1, 7].abs().max()), 0.0)
        self.assertEqual(K.seed_of('X', 1, 'q'), 20261101 + 1000 + zlib.crc32(b'X|q'))

    def test_displacement_gate_pass_and_fail(self):
        f_t = (rnd(1, 8192, 4, seed=5) * 0.3).to(torch.bfloat16)
        diff = K.seg_view((rnd(1, 8192, 4, seed=6) * 0.1).to(torch.bfloat16), 'v') - K.seg_view(f_t, 'v')
        xi = K.random_xi('Y', 0, 'v', [13], {13: diff})[13]
        new = K.seg_put(f_t, 'v', K.seg_view(f_t, 'v') + xi)
        self.assertTrue(K.displacement_check(f_t, new, 'v', xi)['ok'])
        tiny = xi * 1e-4
        new = K.seg_put(f_t, 'v', K.seg_view(f_t, 'v') + tiny)
        self.assertFalse(K.displacement_check(f_t, new, 'v', tiny)['ok'])
        z = torch.zeros_like(xi)
        self.assertTrue(K.displacement_check(f_t, K.seg_put(f_t, 'v', K.seg_view(f_t, 'v') + z), 'v', z)['ok'])


class Recon(unittest.TestCase):
    def test_recon_gate_pass_and_fail(self):
        o = rnd(32, 128, seed=9) * 0.01
        self.assertTrue(K.recon_check(o, o.to(torch.bfloat16))['ok'])                 # correct path: residual = rounding
        self.assertFalse(K.recon_check(o, (o * 1.01).to(torch.bfloat16))['ok'])      # 1% source error: ratio >> 1
        self.assertFalse(K.recon_check(o, (o + 0.02 * rnd(32, 128, seed=10) * 0.01).to(torch.bfloat16))['ok'])


class Readout(unittest.TestCase):
    def test_readout(self):
        z = torch.zeros(248320)
        z[5], z[K.STOP_MAIN], z[K.THINK] = 4.0, 2.0, 1.0
        ro = K.readout(z, 5)
        mu = float(z.double().mean())
        self.assertAlmostEqual(ro['primary']['cz_a'], 4.0 - mu)
        self.assertAlmostEqual(ro['derived']['s46_minus_a'], -2.0)
        self.assertAlmostEqual(ro['D'], -2.0)
        self.assertFalse(ro['eos'])


def eff(G, AV, RV, AQ, RQ):
    return {'G': G, 'A_V': AV, 'R_V': RV, 'A_Q': AQ, 'R_Q': RQ, 'I': RV - AV}


S6 = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']


class Rules(unittest.TestCase):
    def test_factorial_identities(self):
        Z = {K.m_cell('T', q, v): x for (q, v), x in zip([('C', 'C'), ('C', 'T'), ('T', 'C'), ('T', 'T')], [1.0, 4.0, 2.0, 7.0])}
        f = K.factorial(Z, 'M_T')
        self.assertAlmostEqual(f['G'], f['A_V'] + f['R_Q'])
        self.assertAlmostEqual(f['G'], f['A_Q'] + f['R_V'])
        self.assertAlmostEqual(f['I'], f['R_V'] - f['A_V'])

    def test_dominance_pass_fail_undecidable(self):
        e = {s: eff(-10, -9, -9.5, -0.5, -1.0) for s in S6}
        self.assertEqual(K.material_dominance(e, 'V')['label'], 'supported')
        self.assertEqual(K.material_dominance(e, 'Q')['label'], 'not_supported')
        e2 = dict(e, S1=eff(-10, -9, -6, -4, -1), S2=eff(-10, -9, -6, -4, -1))      # removal 0.6 and other 0.4 -> fail
        self.assertEqual(K.material_dominance(e2, 'V')['label'], 'not_supported')
        e3 = dict(e, S1=eff(0.5, 0.4, 0.4, 0.1, 0.1))
        self.assertEqual(K.material_dominance(e3, 'V')['scenarios']['S1'], 'undecidable')

    def test_additivity_and_transfer(self):
        self.assertEqual(K.additivity({s: eff(-10, -9, -9.5, -0.5, -1.0) for s in S6})['label'], 'supported')
        self.assertEqual(K.additivity({s: eff(-10, -5, -8, -2, -5) for s in S6})['label'], 'not_supported')
        g_t = {s: 10.0 for s in S6}
        self.assertEqual(K.transfer({s: 9.0 for s in S6}, g_t)['label'], 'supported')
        self.assertEqual(K.transfer({s: 5.0 for s in S6}, g_t)['label'], 'not_supported')

    def test_random_rule(self):
        scen = {f'{s}-{k}': s for s in S6 for k in (0, 1)}
        good = {i: {'G': -10.0, 'R': -6.0, 'R0': 0.5, 'R1': -1.0} for i in scen}
        self.assertEqual(K.random_rule(good, scen)['label'], 'stable_exceed')
        close = {i: {'G': -10.0, 'R': -1.0, 'R0': 1.0, 'R1': -0.5} for i in scen}      # 1.0 not > 1.0 + 0.1
        self.assertEqual(K.random_rule(close, scen)['label'], 'rule_not_met')
        wrong_dir = {i: {'G': -10.0, 'R': 6.0, 'R0': 0.1, 'R1': 0.1} for i in scen}     # large but wrong sign
        self.assertEqual(K.random_rule(wrong_dir, scen)['label'], 'rule_not_met')
        small = {i: {'G': 0.5, 'R': 0.4, 'R0': 0.0, 'R1': 0.0} for i in scen}
        self.assertEqual(K.random_rule(small, scen)['label'], 'insufficient_evaluable')


def synth_records(v_eff=-8.0, q_eff=-0.5, rnd_eff=0.2):
    """Records with only the fields cf_analysis reads; cz_a = base + S + Q + V contributions (+ entry for N)."""
    recs = []
    for s in S6:
        for k in (0, 1):
            cells = {}

            def put(cid, S, Q, V, entry, extra=0.0):
                cz_a = 5 + (-2 if S == 'T' else 0) + (q_eff if Q == 'T' else 0) + (v_eff if V == 'T' else 0) + (-1 if entry == 'T' else 0) + extra
                cz_s = -cz_a
                D = -20 - cz_a * 2
                cells[cid] = {'readout': {'primary': {'cz_a': cz_a, 'cz_s46': cz_s},
                                          'derived': {'s46_minus_a': cz_s - cz_a, 'think_minus_a': -cz_a, 's44_minus_a': -cz_a,
                                                      's46_minus_think': cz_s, 'D': D}, 'eos': False}}
            for S in 'CT':
                for Q in 'CT':
                    for V in 'CT':
                        put(f'M:{S}{Q}{V}', S, Q, V, 'C')
            for Q in 'CT':
                for V in 'CT':
                    put(f'N:{Q}{V}', 'T', Q, V, 'T')
            put('C', 'C', 'C', 'C', 'C', extra=3.0)
            put('D_step', 'C', 'C', 'C', 'T', extra=3.0)
            for p in 'QV':
                for j in (0, 1):
                    put(f'M:R{p}{j}', 'T', 'T', 'T', 'C', extra=rnd_eff * (1 if j else -1))
                    put(f'N:R{p}{j}', 'T', 'T', 'T', 'T', extra=rnd_eff * (1 if j else -1))
            recs.append({'item': {'id': f'{s}-f{k}', 'base_id': s}, 'cells': cells})
    return recs


class AnalysisConsumer(unittest.TestCase):
    def test_v_dominant_world(self):
        res = A.analyse(synth_records())
        h = res['hypotheses']['cz_a']
        self.assertEqual(h['M_T']['H_V']['label'], 'supported')
        self.assertEqual(h['N']['H_Q']['label'], 'not_supported')
        self.assertEqual(h['M_C']['H_add']['label'], 'supported')
        self.assertEqual(res['random']['M_T|V|cz_a']['label'], 'stable_exceed')
        self.assertEqual(res['hypotheses']['H_transfer_D']['label'], 'supported')
        self.assertFalse(res['random_stop']['all_eight_fail'])

    def test_random_world_triggers_stop(self):
        res = A.analyse(synth_records(v_eff=-0.6, q_eff=-0.6, rnd_eff=1.5))
        self.assertTrue(res['random_stop']['all_eight_fail'])
        self.assertEqual(res['hypotheses']['cz_a']['M_T']['H_V']['label'], 'not_supported')


class Wiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import conv_factor as CF
        cls.CF = CF

    def test_plan_and_design(self):
        d = self.CF.design()
        self.assertEqual(len(d['cells']), 22)
        pre = self.CF.plan('preflight', 0, 1)
        self.assertEqual([u['item_id'] for u in pre], d['preflight_inputs'])
        w0, w1 = self.CF.plan('formal', 0, 2), self.CF.plan('formal', 1, 2)
        self.assertEqual(sorted(u['item_id'] for u in w0 + w1), sorted(d['inputs']))
        self.assertFalse({u['base_id'] for u in w0} & {u['base_id'] for u in w1})
        self.assertEqual(self.CF.LIMITS['formal']['scores'], 12 * 22)
        self.assertEqual(self.CF.LIMITS['preflight']['scores'], 2 * (22 + 4))

    def test_counter_wrapper(self):
        c = self.CF.Counter(None, (13, 14))
        core = torch.zeros(1, 1, 2, 2)
        inner = c._wrap_r(lambda *a, **k: (core, None))
        c.key, c.current = 'x', 13
        out = inner(torch.zeros(1, 1, 2, 2))
        self.assertIs(out[0], core)
        c.current = 14
        inner(torch.zeros(1, 1, 2, 2))
        self.assertEqual(c.hits['x'], {13: 1, 14: 1})
        chunk = c._wrap_c(lambda *a, **k: 1)
        chunk()
        self.assertEqual(c.chunk['x'], 1)
        with self.assertRaises(AssertionError):
            inner(torch.zeros(1, 2, 2, 2))


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun,
                       'failures': len(res.failures), 'errors': len(res.errors), 'skipped': len(res.skipped),
                       'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
