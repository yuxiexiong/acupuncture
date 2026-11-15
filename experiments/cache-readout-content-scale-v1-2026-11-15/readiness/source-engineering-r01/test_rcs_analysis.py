"""Synthetic pure-Python checks only: python -m unittest -v test_rcs_analysis.py"""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rcs_analysis as R


def trajectory(item, row=0, logits=None, text=None, termination='stop', reached=True):
    if text is None:
        text = item['listed_codes'][row] + '<|im_end|>'
    nr = {'ids': [52, 17, 248046] if reached else [248046], 'text': text,
          'termination': termination, 'reached_t2': reached}
    answer = {'x': nr['ids'][0], 'N': nr, 'row': R.A.row_out(nr, item),
              'classification': R.A.NK.FK.classify(text, termination, item['target'],
                   [x for x in item['listed_codes'] if x != item['target']], item.get('question'))}
    return {'answer': answer, 't2': {'prefix_ids': [answer['x']], 'prefix_text': 'U',
        'candidate_token_ids': [17, 18, 19], 'mapping_valid': True, 'reason': '',
        'candidate_logits': logits or [2., 1., 0.], 'stop_logits': {'248044': -2., '248046': -3.}}}


def world():
    """12 synthetic receivers, six scenes; all tables have needed non-conflict controls."""
    items, tables, records = {}, {}, {}
    for s in range(6):
        for i in range(2):
            r = f's{s}-r{i}'
            item = {'id': r, 'scenario': f's{s}', 'listed_codes': ['U25', 'U35', 'U45'],
                    'target': 'U25', 'first_listed': 'U25', 'question': 'Q?'}
            table = [{'id': 'AL', 'type': 'AL', 'row': 1, 'key': 1},
                     {'id': 'BD', 'type': 'BD', 'row': 2, 'key': 1},
                     {'id': 'RS', 'type': 'RS', 'row': 0, 'key': 2}]
            items[r], tables[r] = item, table
            pairs = {}
            for d in table:
                pairs[d['id']] = {a: trajectory(item, d['row'] if a in ('H01', 'H11') else 0,
                    logits=([0., 3., 3.] if a in ('H01', 'H11') else [2., 1., 0.])) for a in R.ARMS}
            records[r] = {'bases': {b: trajectory(item) for b in ('C', 'H')}, 'pairs': pairs}
    return records, items, tables


def write_receipt(root, stage='formal', status='completed', exitcode=0):
    files = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (root/'records').glob('*/*.json')}
    (root/'receipt.json').write_text(json.dumps({'status': status, 'stage': stage, 'files': files}))
    (root/'exit.json').write_text(json.dumps({'returncode': exitcode}))


class AnalysisTests(unittest.TestCase):
    def test_frozen_scores_and_joint_families(self):
        records, items, tables = world()
        out = R.analyse(records, items, tables, n_boot=40)
        self.assertEqual(len(R.COEF), 11)
        self.assertEqual(out['full_D_tr']['cells']['H11'], 1.)
        self.assertEqual(out['full_D_tr']['cells']['C11'], 0.)
        self.assertEqual(out['full_D_tr']['intervals']['H_S0']['mean'], 1.)
        self.assertEqual(out['full_D_tr']['intervals']['H_S1']['mean'], 1.)
        self.assertEqual(out['full_D_tr']['intervals']['H_C0']['mean'], 0.)
        self.assertEqual(out['full_D_tr']['intervals']['H_C1']['mean'], 0.)
        self.assertEqual(len(out['continuous']['Q_family']['intervals']), 6)
        self.assertEqual(len(out['continuous']['L_family']['intervals']), 3)
        self.assertEqual(out['continuous']['conflict_pairs'], 24)
        self.assertTrue(out['delivery']['passed'])
        self.assertTrue(out['strong_background_beyond_fixed_margin']['holds'])
        self.assertTrue(out['conditional_use_advantage']['H']['denominator_advantage'])
        self.assertFalse(out['conditional_use_advantage']['H']['numerator_advantage'])
        for r in items:
            for a in R.ARMS:
                old = R.W.S.d_transfer(tables[r], {d: t[a]['answer']['row'] for d, t in records[r]['pairs'].items()})
                self.assertEqual(out['full_D_tr']['cells_per_receiver'][r][a], old)
        self.assertEqual(out['conflict_counts']['H11']['donor'], 24)
        self.assertEqual(out['conflict_counts']['H11']['later_stop'], 0)
        json.dumps(out, allow_nan=False)

    def test_exact_invalid_fill_bounds_against_enumeration(self):
        _, _, tables = world()
        table = tables['s0-r0']
        outputs = {a: {d['id']: 0 for d in table} for a in R.ARMS}
        outputs['H11']['AL'] = 'stop'
        outputs['H11']['RS'] = 'other'
        outputs['C11']['AL'] = 'other'
        coef = R.COEF['B']
        low, high = R.fill_bounds(table, outputs, coef)
        values = []
        for x, y, z in itertools.product(range(3), repeat=3):
            o = copy.deepcopy(outputs)
            o['H11']['AL'], o['H11']['RS'], o['C11']['AL'] = x, y, z
            values.append(R.W.S.d_transfer(table, o['H11'])-R.W.S.d_transfer(table, o['C11']))
        self.assertEqual((low, high), (min(values), max(values)))
        weights = R.W.weights(table)
        for rows in itertools.product(range(3), repeat=3):
            o = {d['id']: v for d, v in zip(table, rows)}
            self.assertEqual(sum(weights[d][v] for d, v in o.items()), R.W.S.d_transfer(table, o))

    def test_common_set_drops_whole_receiver_not_control_donor(self):
        records, items, tables = world()
        records['s0-r0']['pairs']['RS']['C10']['t2']['mapping_valid'] = False
        records['s0-r0']['pairs']['RS']['C10']['t2']['reason'] = 'synthetic mapping failure'
        out = R.analyse(records, items, tables, n_boot=30)
        self.assertEqual(out['Rstar']['receiver_coverage'], 11/12)
        self.assertEqual(out['Rstar']['pair_coverage'], 33/36)
        self.assertEqual(out['Rstar_D_tr']['receivers'], 11)
        self.assertEqual(out['continuous']['receivers'], 11)
        self.assertEqual(out['continuous']['conflict_pairs'], 22)
        self.assertEqual(set(out['continuous']['L_family']['per_receiver']), set(out['Rstar']['receivers']))
        self.assertEqual(set(out['continuous']['Q_family']['per_receiver']), set(out['Rstar']['receivers']))
        self.assertEqual(out['Rstar_D_tr']['cells']['H11'], 1.)
        self.assertEqual(out['full_D_tr']['receivers'], 12)
        self.assertEqual(len(out['Rstar']['excluded']['s0-r0']), 1)

    def test_eligibility_ignores_effect_and_rejects_missing_measurement(self):
        records, items, tables = world()
        before = R.eligibility(records, items, tables)['receivers']
        records['s0-r0']['pairs']['AL']['H11']['t2']['candidate_logits'] = [-1e6, 1e6, 0.]
        self.assertEqual(R.eligibility(records, items, tables)['receivers'], before)
        records['s0-r0']['pairs']['AL']['H11']['t2']['candidate_logits'] = None
        with self.assertRaisesRegex(ValueError, 'missing finite'):
            R.analyse(records, items, tables, n_boot=2)

    def test_prefix_and_candidate_mapping_must_match_baseline_and_every_pair(self):
        records, items, tables = world()
        records['s1-r0']['bases']['H']['t2']['candidate_token_ids'] = [17, 19, 18]
        records['s2-r0']['pairs']['BD']['C11']['t2']['prefix_text'] = 'V'
        out = R.eligibility(records, items, tables)
        self.assertEqual(set(out['excluded']), {'s1-r0', 's2-r0'})
        self.assertFalse(out['coverage_passed'])

    def test_receiver_equal_not_scene_equal_and_common_width(self):
        rows = {'a': {'x': 0., 'y': 0.}, 'b': {'x': 0., 'y': 0.}, 'c': {'x': 3., 'y': 6.}}
        scenes = {'a': 's0', 'b': 's0', 'c': 's1'}
        draws = list(itertools.product(('s0', 's1'), repeat=2))
        result = R.family(rows, scenes, draws, ('x', 'y'))
        self.assertEqual(result['intervals']['x']['mean'], 1.)
        self.assertEqual(result['intervals']['y']['mean'], 2.)
        self.assertEqual(result['common_width'], 4.)
        self.assertEqual(result['intervals']['x']['hi']-1., result['intervals']['y']['hi']-2.)
        empty = R.family({'a': rows['a']}, scenes, draws, ('x', 'y'))
        self.assertEqual(empty['status'], 'empty_cluster_draw')
        self.assertEqual(empty['empty_draws'], 1)
        self.assertIsNone(empty['intervals']['x']['lo'])

    def test_full_answer_parser_guard_and_invalid_retention(self):
        records, items, tables = world()
        for r, item in items.items():
            records[r]['pairs']['AL']['H01'] = trajectory(item, text='<|im_end|>', reached=False)
            records[r]['pairs']['BD']['H10'] = trajectory(item, text='<|im_end|>', reached=True)
            records[r]['pairs']['RS']['C00'] = trajectory(item, text='U25', termination='budget')
        out = R.analyse(records, items, tables, n_boot=10)
        self.assertEqual(out['pairs'], 36)
        self.assertFalse(out['delivery']['passed'])
        self.assertFalse(out['strong_background_beyond_fixed_margin']['holds'])
        self.assertEqual(out['conflict_counts']['H01']['first_stop'], 12)
        self.assertEqual(out['conflict_counts']['H10']['later_stop'], 12)
        self.assertEqual(out['full_D_tr']['receivers'], 12)
        self.assertGreater(out['full_D_tr']['intervals']['H_S0']['sensitivity_hi'],
                           out['full_D_tr']['intervals']['H_S0']['sensitivity_lo'])
        records, items, tables = world()
        records['s0-r0']['pairs']['AL']['C00']['answer']['row'] = 2
        with self.assertRaisesRegex(ValueError, 'saved row'):
            R.analyse(records, items, tables, n_boot=2)

    def test_missing_table_fails_instead_of_silent_subset(self):
        records, items, tables = world()
        del records['s0-r0']['pairs']['RS']
        with self.assertRaisesRegex(ValueError, 'donor table mismatch'):
            R.analyse(records, items, tables, n_boot=2)

    def test_loader_matches_runner_layout_and_preserves_hashes(self):
        records, items, tables = world()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for r, record in records.items():
                folder = root/'records'/r
                folder.mkdir(parents=True)
                (folder/'bases.json').write_text(json.dumps({'bases': record['bases'], 'formation_hashes': {}}))
                for d, pairs in record['pairs'].items():
                    (folder/(d+'.json')).write_text(json.dumps({**pairs, 'meta': {}}))
            write_receipt(root)
            with patch.object(R.W, 'panel', return_value=(items, tables)), patch.object(R, 'full_items', side_effect=lambda x: x):
                loaded, it, tb, hashes = R.load(root)
                self.assertEqual(len(hashes), 50)
                self.assertEqual(R.analyse(loaded, it, tb, n_boot=5)['pairs'], 36)
                # Engineering is one fixed receiver per original scene, not WSB's old single-scene pilot.
                import shutil
                for r in items:
                    if r.endswith('r1'):
                        shutil.rmtree(root/'records'/r)
                write_receipt(root, stage='engineering')
                engineering, eng_items, eng_tables, _ = R.load(root, 'engineering')
                self.assertEqual(len(engineering), 6)
                self.assertEqual(sum(map(len, eng_tables.values())), 18)
                self.assertEqual(len({x['scenario'] for x in eng_items.values()}), 6)

    def test_frozen_question_survives_panel_projection_and_echo_classification(self):
        _, items, _ = world()
        item = {**items['s0-r0'], 'base_id': 's0',
                'binding': {'A': ['box', 'U25'], 'B': ['bag', 'U35'], 'C': ['cup', 'U45']}}
        item.pop('scenario')
        panel = {'s0-r0': {k: v for k, v in items['s0-r0'].items() if k not in ('question', 'first_listed')}}
        panel['s0-r0']['binding'] = {k: v[1] for k, v in item['binding'].items()}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root/'experiments/cache-local-v-k-v1-2026-11-03'
            ledger = base/'data/heldout-tokens-r01.json'
            heldout = root/'experiments/cache-local-v-k-design-v1-2026-11-03/heldout-inputs-r01.json'
            ledger.parent.mkdir(parents=True)
            heldout.parent.mkdir(parents=True)
            heldout.write_text(json.dumps({'items': [item]}))
            ledger.write_text(json.dumps({'status': 'passed', 'heldout_sha256': hashlib.sha256(heldout.read_bytes()).hexdigest(),
                                         'items': {'s0-r0': {'item': item}}}))
            (base/'freeze-r01.json').write_text(json.dumps({'files': {
                str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (heldout, ledger)}}))
            recovered = R.full_items(panel, root)['s0-r0']
            self.assertEqual(recovered['question'], 'Q?')
            self.assertEqual(recovered['first_listed'], 'U25')
            echo = trajectory(recovered, text='Q? U25<|im_end|>')
            self.assertTrue(R.classify(echo, recovered)['classification']['tags']['contains_question'])
            with self.assertRaisesRegex(ValueError, 'saved classification'):
                R.classify(echo, panel['s0-r0'])
            ledger.write_text(ledger.read_text()+' ')
            with self.assertRaisesRegex(ValueError, 'source hash mismatch'):
                R.full_items(panel, root)

    def test_loader_requires_completed_receipt_exit_and_record_hashes(self):
        records, items, tables = world()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for r, record in records.items():
                folder = root/'records'/r
                folder.mkdir(parents=True)
                (folder/'bases.json').write_text(json.dumps({'bases': record['bases'], 'item': items[r]}))
                for d, pair in record['pairs'].items():
                    (folder/(d+'.json')).write_text(json.dumps(pair))
            with patch.object(R.W, 'panel', return_value=(items, tables)), patch.object(R, 'full_items', side_effect=lambda x: x):
                for status in ('running', 'failed'):
                    write_receipt(root, status=status)
                    with self.assertRaisesRegex(ValueError, 'completed run receipt'):
                        R.load(root)
                write_receipt(root, exitcode=1)
                with self.assertRaisesRegex(ValueError, 'zero worker exit'):
                    R.load(root)
                write_receipt(root, stage='engineering')
                with self.assertRaisesRegex(ValueError, 'stage mismatch'):
                    R.load(root)
                write_receipt(root)
                R.load(root)
                path = root/'records/s0-r0/AL.json'
                path.write_text(path.read_text()+' ')
                with self.assertRaisesRegex(ValueError, 'record hash missing or mismatched'):
                    R.load(root)
                write_receipt(root)
                baseline = root/'records/s0-r0/bases.json'
                value = json.loads(baseline.read_text())
                value['item']['question'] = 'different question'
                baseline.write_text(json.dumps(value))
                write_receipt(root)
                with self.assertRaisesRegex(ValueError, 'saved full item disagrees'):
                    R.load(root)

    def test_sensitivity_gate_and_continuous_boundary_are_not_replaced_by_point_means(self):
        interval = {'mean': .3, 'lo': .2, 'hi': .4, 'sensitivity_lo': .09, 'sensitivity_hi': .5}
        self.assertFalse(R.positive(interval))
        self.assertEqual(R.effect_label(interval), 'indeterminate')
        interval = {'mean': 0., 'lo': -.01, 'hi': .01, 'sensitivity_lo': -.06, 'sensitivity_hi': .01}
        self.assertFalse(R.near_zero(interval))
        records, items, tables = world()
        # A denominator withdrawal in the raw output is not sufficient for the bound-to-S1 continuous claim.
        for record in records.values():
            for pair in record['pairs'].values():
                pair['H10']['t2']['candidate_logits'] = pair['H11']['t2']['candidate_logits'][:]
        out = R.analyse(records, items, tables, n_boot=20)
        self.assertTrue(R.positive(out['full_D_tr']['intervals']['delta_S1']))
        self.assertFalse(out['strong_background_beyond_fixed_margin']['checks']['delta_L_S1'])
        self.assertFalse(out['strong_background_beyond_fixed_margin']['holds'])


if __name__ == '__main__':
    unittest.main()
