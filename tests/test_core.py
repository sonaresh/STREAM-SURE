import os, tempfile, unittest, time, json
from streamsure.models import *
from streamsure.engine import CertificationEngine
from streamsure.service import StreamSureService
from streamsure.ssac import seal, verify
from streamsure.scenarios import catalog
from streamsure.domains import apply_domain_invariant
from streamsure.baselines import baseline_ready


def mk_state(e=None, domain='inventory', value=None, dc=DecisionClass.D2):
    now=time.time(); e=e or Evidence(details={'provisional_max_class':0}); value=value or {'committed_inventory':50,'verified_available_inventory':100}
    st=DecisionBearingState('s',1,domain,value,e,now-1,now,['a'],{'a':0.1},{'a':True},{'x':'1'},{'a':'1'},'1','lineage://x',{})
    req=DecisionRequest('d',dc,'test')
    return st,req

class CoreTests(unittest.TestCase):
    def test_certified_all_pass(self):
        st,r=mk_state(); c=CertificationEngine().certify(st,r); self.assertEqual(c.outcome,Outcome.CERTIFIED)
    def test_reject_on_fail(self):
        st,r=mk_state(Evidence(contract=TriState.FAIL)); c=CertificationEngine().certify(st,r); self.assertEqual(c.outcome,Outcome.REJECT)
    def test_d0_can_certify_with_nonrequired_freshness_unknown(self):
        st,r=mk_state(Evidence(freshness=TriState.UNKNOWN),dc=DecisionClass.D0); c=CertificationEngine().certify(st,r); self.assertEqual(c.outcome,Outcome.CERTIFIED)
    def test_required_unknown_waits_by_default(self):
        st,r=mk_state(Evidence(freshness=TriState.UNKNOWN),dc=DecisionClass.D3); c=CertificationEngine().certify(st,r); self.assertEqual(c.outcome,Outcome.WAIT); self.assertIsNone(c.max_permitted_decision_class)
    def test_provisional_requires_explicit_fallback(self):
        st,r=mk_state(Evidence(freshness=TriState.UNKNOWN),dc=DecisionClass.D3)
        r.allow_provisional_fallback=True; r.max_provisional_class=1
        c=CertificationEngine().certify(st,r); self.assertEqual(c.outcome,Outcome.PROVISIONAL); self.assertEqual(c.max_permitted_decision_class,1)
    def test_correct_repair_signal(self):
        st,r=mk_state(); c=CertificationEngine().certify(st,r,True,'old'); self.assertEqual(c.outcome,Outcome.CORRECT); self.assertEqual(c.supersedes_certificate,'old')
    def test_ssac_digest(self):
        st,r=mk_state(); c=seal(CertificationEngine().certify(st,r)); self.assertTrue(verify(c)); c.reason_codes.append('tamper'); self.assertFalse(verify(c))
    def test_inventory_invariant(self):
        st,r=mk_state(value={'committed_inventory':100,'verified_available_inventory':50}); apply_domain_invariant(st.domain,st.value,st.evidence); self.assertEqual(st.evidence.invariant,TriState.FAIL)
    def test_finance_invariant(self):
        st,r=mk_state(domain='finance',value={'refund_amount':20,'settled_amount':10}); apply_domain_invariant(st.domain,st.value,st.evidence); self.assertEqual(st.evidence.invariant,TriState.FAIL)
    def test_security_invariant(self):
        st,r=mk_state(domain='security',value={'revoked_identity':True,'privileged_session':True}); apply_domain_invariant(st.domain,st.value,st.evidence); self.assertEqual(st.evidence.invariant,TriState.FAIL)
    def test_persistence_and_consumers(self):
        with tempfile.TemporaryDirectory() as td:
            with StreamSureService(os.path.join(td,'x.db')) as svc:
                st,r=mk_state(); c=svc.certify(st,r); self.assertEqual(svc.store.get_certificate(c.certificate_id).outcome,Outcome.CERTIFIED)
                svc.store.register_consumer(c.certificate_id,'decision-2'); self.assertEqual(svc.store.consumers(c.certificate_id),['decision-2'])
    def test_repair_affected_consumers(self):
        with tempfile.TemporaryDirectory() as td:
            with StreamSureService(os.path.join(td,'x.db')) as svc:
                st,r=mk_state(); c=svc.certify(st,r); svc.store.register_consumer(c.certificate_id,'D7')
                st2,r2=mk_state(Evidence(contract=TriState.FAIL)); st2.state_id=st.state_id; st2.state_version=2
                corr,aff=svc.repair(c.certificate_id,st2,r2); self.assertEqual(corr.outcome,Outcome.CORRECT); self.assertEqual(aff,['D7'])

class ScenarioTests(unittest.TestCase):

    def test_flagship_same_state_different_decision(self):
        e=Evidence(freshness=TriState.UNKNOWN)
        st,low=mk_state(e,dc=DecisionClass.D0)
        high=DecisionRequest('high',DecisionClass.D3,'high consequence')
        eng=CertificationEngine()
        self.assertEqual(eng.certify(st,low).outcome,Outcome.CERTIFIED)
        self.assertEqual(eng.certify(st,high).outcome,Outcome.WAIT)

    def test_b5_matches_frozen_scenario_ground_truth(self):
        for sc in catalog():
            st,r=sc.build(); apply_domain_invariant(st.domain,st.value,st.evidence)
            self.assertEqual(baseline_ready('B5',st,r),sc.expected_valid,sc.scenario_id)
    def test_catalog_has_16(self):
        c=catalog(); self.assertEqual(len(c),16); self.assertEqual([s.scenario_id for s in c],[f'E{i}' for i in range(1,17)])
    def test_e10_invariant_failure(self):
        sc=[s for s in catalog() if s.scenario_id=='E10'][0]; st,r=sc.build(); apply_domain_invariant(st.domain,st.value,st.evidence); self.assertEqual(st.evidence.invariant,TriState.FAIL)
    def test_e15_baseline_difference(self):
        sc=[s for s in catalog() if s.scenario_id=='E15'][0]; st,r=sc.build(); apply_domain_invariant(st.domain,st.value,st.evidence)
        self.assertTrue(baseline_ready('B1',st,r)); self.assertFalse(baseline_ready('B5',st,r))
    def test_expected_valid_partition(self):
        c=catalog(); self.assertTrue(any(s.expected_valid for s in c)); self.assertTrue(any(not s.expected_valid for s in c))

if __name__=='__main__': unittest.main()
