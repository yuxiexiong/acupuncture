"""CPU-only source pairing and export-fidelity check."""
import unittest

import export_survey
import serve


class SurveyExportTest(unittest.TestCase):
    def test_every_response_matches_its_source(self):
        data, manifest = export_survey.build()
        saved = export_survey.read_json(export_survey.ROOT / "survey-evidence.json")
        self.assertEqual(data["models"], saved["models"])
        self.assertEqual(data["questions"], saved["questions"])
        self.assertEqual(len(manifest["record_paths"]), 9880)
        saved_manifest = export_survey.read_json(export_survey.ROOT / "survey-manifest.json")
        self.assertEqual(saved_manifest["record_paths"], manifest["record_paths"])
        self.assertEqual(saved_manifest["export_sha256"], export_survey.sha(export_survey.ROOT / "survey-evidence.json"))
        allowed = serve.allowed_paths()
        self.assertTrue(all(export_survey.REPO / p in allowed for p in manifest["record_paths"]))
        self.assertNotIn(export_survey.REPO / "README.md", allowed)
        model = next(m for m in data["models"] if m["id"] == "4b")
        point = next(p for p in model["points"] if p["layer"] == 6 and p["channel"] == 7840)
        self.assertIn("SLC24A1", point["doses"]["0.5"]["Q04"]["text"])
        self.assertNotIn("SLC24A1", point["doses"]["0.25"]["Q04"]["text"])


if __name__ == "__main__":
    unittest.main()
