"""Release diagnostics must not mix index size, data previews or availability."""
import _bootstrap
import unittest,json
from unittest import mock
from capabilities import summarize
from doctor import query_diagnosis
import onboarding

class ReleaseReadiness(unittest.TestCase):
    def test_doctor_never_includes_query_previews_exports_or_static_sample_args(self):
        marker='private-fixture-not-research-data'
        result={'ok':True,'command':'example','result':{'text':marker},'preview':{'text':marker},'artifacts':[{'uri':marker}],'result_id':marker,'catalog_verification':{'samples':[{'args':[marker]}]},'result_status':'content','has_content':True,'text_characters':30}
        out=query_diagnosis(result)
        self.assertNotIn(marker,json.dumps(out));self.assertEqual(out['result_status'],'content');self.assertTrue(out['has_content'])
    def test_coverage_does_not_count_empty_failed_unknown_or_stale_entries_as_verified(self):
        commands=[{'command':'one','content_level_hint':'catalog','followup_template':{}},{'command':'two','content_level_hint':'observations'},{'command':'three','content_level_hint':'unclassified'},{'command':'four','content_level_hint':'catalog'}]
        samples={'one':{'level':'sample_verified'},'two':{'level':'sample_empty_only'},'four':{'level':'sample_failed'},'not-indexed':{'level':'sample_verified'}}
        c=summarize(commands,samples)
        self.assertEqual(c['indexed_commands'],4);self.assertEqual(c['sample_verified_commands'],1);self.assertEqual(c['commands_with_sample_evidence'],3);self.assertEqual(c['commands_without_sample_evidence'],1);self.assertEqual(c['unclassified_content_commands'],1);self.assertEqual(c['followup_templates'],1)
    def test_setup_exposes_scope_as_historical_evidence_not_live_authorization(self):
        coverage={'indexed_commands':99,'sample_verified_commands':2,'basis':'historical fixture'}
        with mock.patch('capabilities.coverage',return_value=coverage),mock.patch.object(onboarding.rt,'load_state',return_value={'mode':'general','progress':{}}),mock.patch('network_health.status',return_value={}):
            r=onboarding.status()
        self.assertEqual(r['coverage']['sample_verified_commands'],2);self.assertIn('不会授予',r['notice'])
if __name__=='__main__':unittest.main()
