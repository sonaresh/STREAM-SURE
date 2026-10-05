import json, os, tempfile, threading, unittest, urllib.request
from streamsure.api import Handler
from streamsure.service import StreamSureService
from http.server import ThreadingHTTPServer


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        Handler.service = StreamSureService(os.path.join(cls.td.name, 'api.db'))
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.port = cls.server.server_address[1]
        cls.th = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.th.start()

    @classmethod
    def tearDownClass(cls):
        # Order matters on Windows: stop request handling, close the database
        # connection, then remove the TemporaryDirectory.
        cls.server.shutdown()
        cls.server.server_close()
        cls.th.join(timeout=2)
        if Handler.service is not None:
            Handler.service.close()
            Handler.service = None
        cls.td.cleanup()

    def test_health(self):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.port}/health') as r:
            d = json.load(r)
            self.assertEqual(d['status'], 'ok')

    def test_certify(self):
        payload = {
            'state': {
                'state_id': 'api-s',
                'domain': 'inventory',
                'value': {'committed_inventory': 10, 'verified_available_inventory': 20},
                'evidence': {},
                'required_sources': ['a'],
                'source_freshness': {'a': 0.1},
                'source_completeness': {'a': True},
            },
            'decision': {'decision_id': 'api-d', 'decision_class': 2, 'purpose': 'test'},
        }
        req = urllib.request.Request(
            f'http://127.0.0.1:{self.port}/certify',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req) as r:
            d = json.load(r)
            self.assertEqual(d['outcome'], 'CERTIFIED')
            self.assertTrue(d['digest'])
    def test_certify_batch(self):
        item = {
            'state': {
                'state_id': 'api-batch', 'domain': 'inventory',
                'value': {'committed_inventory': 10, 'verified_available_inventory': 20},
                'evidence': {}, 'required_sources': ['a'],
                'source_freshness': {'a': 0.1}, 'source_completeness': {'a': True},
            },
            'decision': {'decision_id': 'api-batch-d', 'decision_class': 2, 'purpose': 'test'},
        }
        req = urllib.request.Request(
            f'http://127.0.0.1:{self.port}/certify-batch',
            data=json.dumps({'items':[item,item]}).encode(),
            headers={'Content-Type':'application/json'}, method='POST')
        with urllib.request.urlopen(req) as r:
            d=json.load(r); self.assertEqual(len(d['certificates']),2); self.assertTrue(all(x['outcome']=='CERTIFIED' for x in d['certificates']))

