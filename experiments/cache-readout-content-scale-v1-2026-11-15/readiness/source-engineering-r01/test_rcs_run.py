"""Budget, panel, qualification and failure-gate checks; no model or GPU."""
import tempfile
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import time
import rcs_run as R


class Tests(unittest.TestCase):
    def test_fixed_panel_counts_and_frozen_supplier_table(self):
        all_items, all_tables = R.panel('formal')
        items, tables = R.panel('engineering')
        self.assertEqual((len(all_items), sum(map(len, all_tables.values()))), (48, 348))
        self.assertEqual((len(items), sum(map(len, tables.values()))), (6, 42))
        for r in items:
            self.assertEqual(tables[r], all_tables[r])
            self.assertEqual(r, min(k for k in all_items if all_items[k]['scenario'] == items[r]['scenario']))
        f, e = R.limits('formal'), R.limits('engineering')
        self.assertEqual((f['trajectories'], e['trajectories']), (2880, 348))
        self.assertEqual(f['trajectories']+2*e['trajectories'], 3576)
        self.assertEqual(f['t1']+2*e['t1'], 1104)
        self.assertEqual(f['t2_shadow']+2*e['t2_shadow'], 48384)
        self.assertEqual(R.SOURCE_BYTES/2**30, 19.03125)

    def test_caps_reject_extra_work_and_incomplete_finish(self):
        lim = R.limits('engineering')
        rc = {'counts': {k: 0 for k in ('t1', 'trajectories', 'formations', 'prefix_prefills')},
              'arm_counts': {k: 0 for k in ('baseline', 'zero', 'pair_t1', 'continuation')}}
        R.check_counts(rc, 'engineering')
        with self.assertRaises(AssertionError): R.check_counts(rc, 'engineering', complete=True)
        for d in rc.values():
            for k in d: d[k] = lim[k]
        R.check_counts(rc, 'engineering', complete=True)
        rc['counts']['t1'] += 1
        with self.assertRaises(AssertionError): R.check_counts(rc, 'engineering')

    def test_qualification_does_not_use_answer_or_margin(self):
        tok = SimpleNamespace(decode=lambda ids, **kw: str(ids))
        info = {'item': {'listed_codes': ['A', 'B', 'C']}, 'code_tokens': {'A': 1, 'B': 2, 'C': 3}, 'q_shared': 57}
        self.assertTrue(R.frozen_mapping(tok, 57, info)['mapping_valid'])
        self.assertFalse(R.frozen_mapping(tok, 56, info)['mapping_valid'])
        bad = {**info, 'code_tokens': {'A': 1, 'B': 1, 'C': 3}}
        self.assertFalse(R.frozen_mapping(tok, 57, bad)['mapping_valid'])

    def test_no_default_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'denied.json'
            p.write_text('{"gpu_authorized": false}')
            with self.assertRaises(AssertionError): R.authorize(p, 'engineering')

    def test_projected_budget_requires_every_measured_phase(self):
        with self.assertRaises(AssertionError): R.project_seconds({}, R.W.runtime())
        maxima = {k: 1. for k in ('load', 'setup', 'formation_overhead', 'receiver_overhead',
            'pair_overhead', 'prefix_token', 'formation_token', 'baseline_t1', 'zero_t1',
            'pair_t1', 't2', 'decode', 'integrity', 'readout_integrity', 'finalize_per_pair')}
        self.assertGreater(R.project_seconds(maxima, R.W.runtime()), 31*2880)

    def test_killed_worker_is_charged_from_supervisor(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'receipt.json'
            R.W.write(p, {'stage': 'engineering', 'status': 'running'})
            R.W.write(p.parent/'exit.json', {'returncode': -15, 'supervisor_wall_seconds': 91.})
            self.assertEqual(R.prior_usage(p), 91.)

    def test_authorization_is_single_output_and_cannot_hide_prior_attempt(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(R, 'HERE', Path(tmp).resolve()):
            root = Path(tmp).resolve()
            fr = dict(environment_checked=True, revision=R.K.REVISION, files={}, external_sources={},
                      torch_version='test', source_package_bytes=0)
            cpu = dict(status='passed', model_forwards=0, upstream_kernel_tested=True,
                       source_hashes={}, external_sources={}, torch_version='test')
            R.W.write(root/'freeze.json', fr); R.W.write(root/'cpu.json', cpu)
            auth = dict(gpu_authorized=True, experiment=root.name, allowed_stages=['engineering'],
                        maximum_workers=1, user_instruction='test fixture only', expires_unix=time.time()+60,
                        output='runs/next', freeze_path='freeze.json', freeze_sha256=R.W.sha(root/'freeze.json'),
                        cpu_receipt_path='cpu.json', cpu_receipt_sha256=R.W.sha(root/'cpu.json'))
            R.W.write(root/'auth.json', auth)
            R.authorize(root/'auth.json', 'engineering', root/'runs/next')
            with self.assertRaisesRegex(AssertionError, 'bound to one'):
                R.authorize(root/'auth.json', 'engineering', root/'runs/replayed')
            old = root/'runs/failed/receipt.json'
            R.W.write(old, {'stage': 'engineering', 'status': 'running'})
            R.W.write(old.parent/'exit.json', {'returncode': -15, 'supervisor_wall_seconds': 91.})
            with self.assertRaisesRegex(AssertionError, 'every existing attempt'):
                R.authorize(root/'auth.json', 'engineering', root/'runs/next')
            auth['prior_runs'] = {'runs/failed/receipt.json': R.W.sha(old)}
            R.W.write(root/'auth.json', auth)
            R.authorize(root/'auth.json', 'engineering', root/'runs/next')


if __name__ == '__main__':
    unittest.main()
