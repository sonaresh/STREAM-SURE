import json
import tempfile
import unittest
from pathlib import Path
from streamsure.phase6b import percentile, iqr, bootstrap_ci_median, safe_median, load_runs

class Phase6BTests(unittest.TestCase):
    def test_percentile_and_iqr(self):
        self.assertEqual(percentile([1,2,3],.5),2)
        q1,q3=iqr([1,2,3,4]); self.assertLess(q1,q3)

    def test_bootstrap_ci_contains_median_for_constant_data(self):
        lo,hi=bootstrap_ci_median([7.0]*10,100)
        self.assertEqual((lo,hi),(7.0,7.0))

    def test_safe_median_empty_is_none(self):
        self.assertIsNone(safe_median([]))

    def test_zero_certificate_run_is_loadable(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=root/'target_2500'/'run_30'
            p.mkdir(parents=True)
            doc={'runs':[{
                'run_id':'e16-2500-zero','target_input_events_per_sec':2500,
                'completion_ratio':0.0,'certificates_received':0,'decisions_target':18750,
                'actual_input_events_per_sec':2499.9,'certificate_throughput_per_sec':0.0,
                'latency_p50_ms':None,'latency_p95_ms':None,'latency_p99_ms':None,
                'latency_max_ms':None,'delivery_errors':0,'consumer_errors':0,'sustained':False
            }]}
            (p/'summary.json').write_text(json.dumps(doc),encoding='utf-8')
            rows=load_runs(root)
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['certificates_received'],0)
            self.assertIsNone(rows[0]['latency_p95_ms'])

if __name__=='__main__': unittest.main()
