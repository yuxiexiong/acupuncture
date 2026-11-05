"""CPU-only acceptance of the actual v9 counter, cache, report and freeze gates."""
import json
import tempfile
import unittest
from pathlib import Path
from continue50 import transition, archive_boundary
from test_offline import OfflineTests, contract, NAMES


class ContinueTests(unittest.TestCase):
    def test_v9_continuation_requires_boundary_and_stops_at_50(self):
        fixture = OfflineTests(); fixture.setUp()
        try:
            limits = contract()
            limits.update(repair_rounds=30, targeted=True, wall_seconds=None,
                          forwards=1000, samples=1000, target_tokens=10000000,
                          researcher_tokens=50000000)
            service = fixture.service(limits=limits)
            with self.assertRaises(ValueError):
                transition(service.state, limits)
            for n in range(1, 31):
                x = fixture.source.load(NAMES[0]); x[0, 0] = n
                m = fixture.candidates.commit(fixture.candidates.base_id, {NAMES[0]: x}, str(n))
                service.evaluate({'candidate': m['id']})
            self.assertTrue(service.state['round_budget_reached'])
            self.assertFalse(service.state['research_done'])
            with self.assertRaises(ValueError):
                transition(service.state, limits)
            report = {'report': {'candidate': service.state['best']}}
            (service.root/'mechanism-report.json').write_text(json.dumps(report))
            service.operation({'op': 'freeze'}, service.root)
            original = json.loads(json.dumps(service.state))
            service.state, service.contract = transition(service.state, limits)
            self.assertTrue(original['research_done'])
            self.assertFalse(service.state['round_budget_reached'])
            self.assertEqual(service.contract['researcher_tokens'], 83333334)
            for key in set(limits)-{'repair_rounds','forwards','samples','target_tokens','researcher_tokens'}:
                self.assertEqual(service.contract[key], limits[key])
            before = service.backend.calls
            service.evaluate({'candidate': m['id']})
            self.assertEqual(service.backend.calls, before)
            self.assertEqual(service.state['repair_rounds_completed'], 30)
            for n in range(31, 51):
                x = fixture.source.load(NAMES[0]); x[0, 0] = n
                m = fixture.candidates.commit(fixture.candidates.base_id, {NAMES[0]: x}, str(n))
                service.evaluate({'candidate': m['id']})
                self.assertEqual(service.state['round_budget_reached'], n == 50)
                self.assertFalse(service.state['research_done'])
            x[0, 0] = 51
            extra = fixture.candidates.commit(fixture.candidates.base_id, {NAMES[0]: x}, 'over cap')
            before = service.backend.calls
            with self.assertRaises(ValueError):
                service.evaluate({'candidate': extra['id']})
            self.assertEqual(service.backend.calls, before)
            (service.root/'mechanism-report.json').unlink()
            with self.assertRaises(ValueError):
                service.operation({'op': 'freeze'}, service.root)
            report['report']['candidate'] = service.state['best']
            (service.root/'mechanism-report.json').write_text(json.dumps(report))
            service.operation({'op': 'freeze'}, service.root)
            self.assertTrue(service.state['research_done'])
            self.assertEqual(service.state['repair_rounds_completed'], 50)
        finally:
            fixture.tearDown()

    def test_checkpoint_preserves_bytes_and_removes_stale_active_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            names = ('state.json','identity.json','config.json','frozen-candidate.json','mechanism-report.json')
            for name in names:
                (root/name).write_text(name)
            archive_boundary(root)
            for name in names:
                self.assertEqual((root/'checkpoint-round30'/name).read_text(), name)
            self.assertFalse((root/'mechanism-report.json').exists())
            self.assertFalse((root/'frozen-candidate.json').exists())


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromTestCase(ContinueTests)


if __name__ == '__main__':
    unittest.main()
