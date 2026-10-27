import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import survey


class DesignChecks(unittest.TestCase):
    def test_all_shards_are_disjoint_and_complete(self):
        contract, questions, samples = survey.load_design()
        total = 0
        for model in contract["models"]:
            ids = []
            for shard in range(2):
                jobs = survey.schedule("survey", model, questions, samples[model["id"]], shard, 2)
                ids.extend((c, q["id"]) for c, _, q, _ in jobs)
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(len(ids), model["layers"] * 10 * 8 + 8)
            total += len(ids)
            preview = survey.schedule("preflight", model, questions, samples[model["id"]], 0, 1)
            self.assertEqual(len(preview), 22)
            self.assertEqual(sum(d == 1 for _, _, _, d in preview), 8)
            self.assertEqual({c['layer'] for _, c, _, d in preview if d == 1}, {0, model['layers']//2, model['layers']-1})
        self.assertEqual(total, 7064)

    def test_preflight_is_not_formal_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'auth.json'
            path.write_text(json.dumps(dict(experiment=survey.HERE.name, freeze_sha256='frozen',
                status='authorized', purpose='preflight', models=['2b'], gpus=[0], user_instruction='test', recorded_utc='test')))
            with patch.object(survey, 'check_freeze', return_value='frozen'):
                survey.check_authorization(path, 'preflight', '2b', 0, True)
                with self.assertRaises(AssertionError):
                    survey.check_authorization(path, 'survey', '2b', 0, True)
                with self.assertRaises(AssertionError):
                    survey.check_authorization(path, 'preflight', '2b', 0, False)
            with self.assertRaises(AssertionError):
                survey.schedule('preflight', {'layers':24}, [], [], 1, 2)

    def test_frozen_change_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / 'a').write_text('original')
            (base / 'freeze.json').write_text(json.dumps({'experiment': base.name, 'files': {'a': survey.io.sha(base/'a')}}))
            with patch.object(survey, 'HERE', base), patch.object(survey, 'REPO', base):
                survey.check_freeze()
                (base/'a').write_text('changed')
                with self.assertRaises(AssertionError):
                    survey.check_freeze()

    def test_decoder_keeps_terminator_and_full_cap(self):
        from survey_engine import transfer
        finish = transfer._v2.finish_generation
        decode = lambda tokens, skip_special_tokens: str(tokens)
        eos = finish([8, 9, 0, 0], [9], 0, 128, None, [], decode)
        self.assertEqual(eos['token_ids'], [8, 9])
        self.assertEqual(eos['end_reason'], 'eos_token')
        cap = finish([8]*128, [9], 0, 128, None, [], decode)
        self.assertEqual(cap['generated_token_count'], 128)
        self.assertEqual(cap['end_reason'], 'length_limit')


@unittest.skipUnless(importlib.util.find_spec('torch'), 'Torch unavailable locally; required in remote CPU acceptance')
class HookChecks(unittest.TestCase):
    def test_only_one_channel_mask_decode_and_exception_cleanup(self):
        import torch
        from survey_engine import SurveyEngine
        engine = SurveyEngine.__new__(SurveyEngine)
        engine.torch = torch
        engine.modules = {0: torch.nn.Linear(4, 3, bias=False, dtype=torch.bfloat16),
                          1: torch.nn.Linear(4, 3, bias=False, dtype=torch.bfloat16)}
        engine.column_norms = {'0': torch.ones(4), '1': torch.ones(4)}
        cal = [{'residual_scales': {'0': 2., '1': 3.}}]
        mask = torch.tensor([[0, 1, 1]])
        x = torch.ones(1, 3, 4, dtype=torch.bfloat16)
        observed = []
        try:
            with engine._intervention((1, 2, 1.0), cal, mask):
                self.assertFalse(engine.modules[0]._forward_pre_hooks)
                self.assertEqual(len(engine.modules[1]._forward_pre_hooks), 1)
                handle = engine.modules[1].register_forward_pre_hook(lambda m, args: observed.append(args[0].clone()))
                try:
                    engine.modules[1](x)
                    engine.modules[1](x[:, :1])
                finally:
                    handle.remove()
                raise RuntimeError('intentional exception')
        except RuntimeError:
            pass
        expected = x.clone()
        expected[0, 1:, 2] += 3
        self.assertTrue(torch.equal(observed[0], expected))
        decoded = x[:, :1].clone()
        decoded[..., 2] += 3
        self.assertTrue(torch.equal(observed[1], decoded))
        self.assertTrue(torch.equal(x, torch.ones_like(x)))
        self.assertTrue(all(not m._forward_pre_hooks for m in engine.modules.values()))
        self.assertEqual(engine.last_hook['calls'], 2)


if __name__ == '__main__':
    unittest.main()
