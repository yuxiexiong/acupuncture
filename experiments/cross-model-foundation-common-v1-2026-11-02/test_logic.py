"""CPU tests: panel, parser, needles, layer picks, real-tokenizer spans.  No model weights."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models as M  # noqa: E402
import panel as P  # noqa: E402


class PanelTests(unittest.TestCase):
    def test_counts_and_ids(self):
        scs = P.scenarios()
        self.assertEqual(len(scs), 36)
        self.assertEqual(len({s["id"] for s in scs}), 36)
        for split in P.SPLITS:
            for fam in P.FAMILIES:
                self.assertEqual(sum(1 for s in scs if s["split"] == split and s["family"] == fam), 4)

    def test_deterministic(self):
        self.assertEqual(P.panel_sha256(), P.panel_sha256())

    def test_fact_swap(self):
        for sc in P.scenarios():
            a0, a1 = P.render_item(sc, 0, "A"), P.render_item(sc, 1, "A")
            self.assertEqual(a0["correct"], a1["other"])
            self.assertEqual(a0["other"], a1["correct"])
            self.assertEqual(a0["candidates_in_order"], a1["candidates_in_order"])  # order fixed per scenario
            for it in (a0, a1):
                self.assertIn(it["correct"], it["column_values"])
                self.assertIn(it["other"], it["column_values"])
                self.assertEqual(len(set(it["column_values"])), len(it["column_values"]))
                rs, re_ = it["record_char_span"]
                self.assertIn(it["correct"], it["user"][rs:re_])

    def test_candidate_order_balanced(self):
        firsts = [P.render_item(sc, 0, "A")["candidates_in_order"][0] == P.render_item(sc, 0, "A")["correct"]
                  for sc in P.scenarios()]
        self.assertEqual(sum(firsts), 18)

    def test_lock_wording_differs(self):
        sc = {s["split"]: s for s in P.scenarios() if s["family"] == "ea"}
        self.assertNotEqual(P.render_item(sc["lock"], 0, "A")["user"].split("\n")[0],
                            P.render_item(sc["dev"], 0, "A")["user"].split("\n")[0])

    def test_num_columns_do_not_collide(self):
        for sc in P.scenarios():
            if sc["family"] != "num":
                continue
            it = P.render_item(sc, 0, "B")
            trucks = {r["trucks"] for r in sc["rows"]}
            self.assertFalse(trucks & set(it["column_values"]))


class ParserTests(unittest.TestCase):
    def setUp(self):
        sc = [s for s in P.scenarios() if s["id"] == "DEV-id-00"][0]
        self.it = P.render_item(sc, 0, "B")

    def test_cases(self):
        it = self.it
        tid, v = it["target_row_id"], it["correct"]
        wrong = [x for x in it["column_values"] if x != v][0]
        self.assertEqual(P.parse_b(it, f"{tid}: {v}"), ("correct", True))
        self.assertEqual(P.parse_b(it, f"{v}")[0], "value_right_id_missing")
        other_id = [r for r in it["row_ids"] if r != tid][0]
        self.assertEqual(P.parse_b(it, f"{other_id}: {v}")[0], "value_right_id_wrong")
        self.assertEqual(P.parse_b(it, f"{tid}: {wrong}"), ("wrong_value", False))
        self.assertEqual(P.parse_b(it, f"{tid}: {v} or {wrong}"), ("conflict", None))
        self.assertEqual(P.parse_b(it, ""), ("no_answer", False))
        self.assertEqual(P.parse_b(it, "I cannot tell."), ("no_answer", False))

    def test_number_boundaries(self):
        sc = [s for s in P.scenarios() if s["family"] == "num"][0]
        it = P.render_item(sc, 0, "B")
        v = it["correct"]
        self.assertEqual(P.parse_b(it, f"{it['target_row_id']}: 1{v}")[0], "no_answer")


class NeedleAndLayerTests(unittest.TestCase):
    def test_picks(self):
        self.assertEqual(M.pick_layers(32), [3, 15, 26])
        self.assertEqual(M.pick_layers(36), [3, 17, 29])
        self.assertEqual(M.pick_layers(28), [2, 13, 22])

    def test_needles(self):
        import engine as E
        a = E.needle_set("qwen3_4b", 17, 9728, 2560)
        b = E.needle_set("qwen3_4b", 17, 9728, 2560)
        self.assertEqual([x["name"] for x in a], [x["name"] for x in b])
        self.assertEqual(len({x["channel"] for x in a if x["kind"] == "native"}), 4)
        dirs = [x for x in a if x["kind"] == "direction"]
        self.assertEqual(len(dirs), 2)
        for d, d2 in zip(dirs, [x for x in b if x["kind"] == "direction"]):
            self.assertAlmostEqual(float(d["vector"].norm()), 1.0, places=12)
            self.assertEqual(d["vector_sha256"], d2["vector_sha256"])
        c = E.needle_set("qwen3_4b", 3, 9728, 2560)
        self.assertNotEqual([x["name"] for x in a], [x["name"] for x in c])


@unittest.skipUnless(all(os.path.exists(s["path"]) for s in M.MODELS.values()), "model files not present")
class TokenizerTests(unittest.TestCase):
    def test_spans(self):
        from transformers import AutoTokenizer
        import tokspan as T
        for key, spec in M.MODELS.items():
            tok = AutoTokenizer.from_pretrained(spec["path"], local_files_only=True)
            for task in ("A", "B"):
                for it in P.items(task)[:6]:
                    e = T.encode_item(tok, key, it)
                    text = tok.decode([e["ids"][i] for i in e["record_positions"]])
                    rs, re_ = it["record_char_span"]
                    self.assertEqual(text.strip(), it["user"][rs:re_].strip(), (key, it["item_id"]))
                    self.assertEqual(e["q"], e["n_tokens"] - 1)
                    if task == "A":
                        for c in it["candidates_in_order"]:
                            ids = T.continuation_ids(tok, key, it, c)
                            self.assertTrue(ids)
                            self.assertEqual(tok.decode(ids), c)


if __name__ == "__main__":
    unittest.main(verbosity=1)
