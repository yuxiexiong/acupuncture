"""CPU-only checks for lossless blinding and the absence of semantic scoring."""
import json
import unittest
import delivery


class DeliveryTests(unittest.TestCase):
    def sources(self):
        return [{'record': {'item_id':'q', 'condition':{'id':f'AB_d{i}', 'dose':i},
                    'output':{'answer_text':'  <script>alert(1)</script>\n', 'raw_text':'\n\x00\ufffd<|im_end|>'}},
                 'source_path':f'/private/AB_d{i}.json', 'source_sha256':str(i)} for i in range(8)]

    def test_blinding_is_stable_and_does_not_reveal_condition(self):
        items = {'q':{'prompt':'题目\n'}}
        blind, key = delivery.anonymize(self.sources(), items)
        self.assertEqual((blind,key), delivery.anonymize(list(reversed(self.sources())), items))
        self.assertEqual(len({r['id'] for r in blind}),8)
        self.assertNotEqual([r['condition']['id'] for r in key], [f'AB_d{i}' for i in range(8)])
        for row in blind:
            self.assertEqual(set(row),{'id','prompt','answer_text','raw_text'})
            self.assertNotIn('AB_d', json.dumps(row))
            self.assertEqual(row['answer_text'],'  <script>alert(1)</script>\n')
            self.assertEqual(row['raw_text'],'\n\x00\ufffd<|im_end|>')
        with self.assertRaises(ValueError):
            delivery.anonymize(self.sources()+self.sources()[:1], items)

    def test_html_escapes_and_preserves_blank_answers(self):
        rows = [{'id':'id', 'prompt':'<img src=x onerror=bad()>', 'answer_text':'',
                 'raw_text':'\n<script>bad()</script>\n  &'}]
        rendered = delivery.render(rows)
        self.assertNotIn('<img', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;',rendered)
        self.assertIn('<pre><span></span></pre>',rendered)
        self.assertIn('<pre><span>\n&lt;script&gt;',rendered)
        self.assertIn('\n  &amp;',rendered)

    def test_reading_template_never_assesses_content(self):
        rows = delivery.reading_template([{'id':'a'}])
        self.assertEqual(rows[0]['status'],'unread')
        self.assertTrue(all(v is None for k,v in rows[0].items() if k not in ('id','status')))

    def test_quantitative_is_candidate_only_and_retains_ties(self):
        items = {'q':{'id':'q','base_id':'b','panel':'diagnostic','family':'reading','demand':'required',
                      'fact_version':0,'choices':['甲','乙'],'target_index':1}}
        source = self.sources()[0]
        source['record']['output'].update(generated_token_count=1,end_reason='eos_token')
        source['record']['choice_details']=[{'loglikelihood':-2.0},{'loglikelihood':-2.0}]
        result = delivery.quantitative([source],items)
        readout = result['records'][0]['candidate_readout']
        self.assertTrue(readout['tied'])
        self.assertEqual(readout['prediction_index'],0)
        self.assertFalse(readout['correct'])
        self.assertEqual(readout['target_margin'],0)
        self.assertFalse(result['semantic_assessment_complete'])
        self.assertNotIn('content',result['records'][0])
        self.assertNotIn('style',result['records'][0])


if __name__ == '__main__':
    unittest.main()
