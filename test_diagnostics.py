"""Regression tests for actual caller failures, incomplete results and resume."""
import sys
sys.dont_write_bytecode=True
import json,os,subprocess,tempfile,unittest,importlib
from pathlib import Path
from unittest import mock
import onboarding as setup
import release_runtime as rt
import research_cli as cli
import research_mcp as mcp
from diagnostics import SourceError,request_error,environment_summary
sys.path.insert(0,str(cli.ROOT/'engine'))

class DiagnosticChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='diagnostic-check-')
        self.env=mock.patch.dict(os.environ,{'RESEARCH_MCP_STATE_DIR':self.temp.name});self.env.start();setup.select('partial')
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def test_original_wrong_rows_calls_are_short_and_actionable(self):
        for command,keyword,flag in [('arxiv','digital economy','--size'),('pubmed-search','digital economy','--size'),('ons-dataset-discover','population','--limit')]:
            with self.subTest(command=command):
                r=cli.query(command,[keyword,'--rows','2'])
                self.assertEqual(r['error'],'invalid_arguments');self.assertLess(len(r['message']),200)
                self.assertIn(command,r['usage']);self.assertIn(flag,r['supported_options']);self.assertIn(flag,r['hint'])
                self.assertNotIn('mongolia',json.dumps(r));self.assertNotIn('公开文件',r['hint'])
    def test_bad_integer_is_argument_error(self):
        r=cli.query('crossref',['energy','--rows','invalid']);self.assertEqual(r['error'],'invalid_arguments')
    def test_missing_positionals_are_argument_error(self):
        r=cli.query('usgs-earthquakes',[]);self.assertEqual(r['error'],'invalid_arguments');self.assertIn('start',r['message'])
    def test_optional_branch_is_not_network_or_mandatory_registration(self):
        r=cli.query('pmi-list',[]);self.assertEqual(r['error'],'optional_setup_required');self.assertEqual(r['required_mode'],'full');self.assertIn('本身不要求',r['hint'])
    def test_cas_parser_uses_the_same_error_contract(self):
        setup.select('full');r=cli.query('cas-common-search',[]);self.assertEqual(r['error'],'invalid_arguments')
    def test_public_nbs_is_allowed_before_network(self):
        r=cli.query('nbs-annual-series',['invalid','invalid','invalid','2020','2023'])
        self.assertNotEqual(r.get('error'),'optional_setup_required');self.assertFalse(r['ok'])
    def test_gdp_observation_discovery_exposes_nbs(self):
        r=mcp.discover('中国宏观 GDP',limit=5,starter_only=True,kind='observations')
        self.assertIn('nbs-annual-series',[x['command'] for x in r['commands']]);self.assertTrue(all(x['result_kind']=='observations' for x in r['commands']))
    def test_first_ons_page_failure_cannot_look_successful(self):
        module=importlib.import_module('ons_datasets_general_adapter')
        with mock.patch.object(module,'catalogue',side_effect=SourceError('http_status','test HTTP failure',status=503)):
            with self.assertRaises(SourceError):module.discover('population')
    def test_partial_ons_scan_is_reported(self):
        data={'pages':1,'scanned':1,'items':[{'id':'test'}],'failed_pages':[{'error':'test-only failure'}]}
        completed=subprocess.CompletedProcess([],0,json.dumps(data),'')
        with mock.patch.object(cli.subprocess,'run',return_value=completed):r=cli.query('ons-dataset-discover',['population'])
        self.assertTrue(r['ok']);self.assertTrue(r['partial']);self.assertTrue(r['warnings'])
    def test_fully_failed_legacy_scan_is_error(self):
        data={'pages':0,'scanned':0,'items':[],'failed_pages':[{'error':'test-only failure'}]}
        with mock.patch.object(cli.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(data),'')):r=cli.query('ons-dataset-discover',['population'])
        self.assertFalse(r['ok']);self.assertEqual(r['error'],'upstream_scan_failed')
    def test_http_failure_is_distinct_from_bad_arguments(self):
        error={'error':'HTTP failure','diagnostics':{'kind':'http_status','http_status':403,'endpoint':'https://example.org/api'}}
        with mock.patch.object(cli.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'',json.dumps(error))):r=cli.query('arxiv',['energy'])
        self.assertEqual(r['error'],'upstream_http_error');self.assertEqual(r['diagnostics']['http_status'],403)
    def test_network_diagnostics_never_include_query_credentials(self):
        import requests
        response=requests.Response();response.status_code=403
        error=request_error(requests.HTTPError(response=response),'https://example.org/api?api_key=test-only-private-value')
        self.assertNotIn('test-only-private-value',json.dumps(error.as_dict()))
    def test_doctor_does_not_dump_proxy_or_ca_values(self):
        with mock.patch.dict(os.environ,{'HTTPS_PROXY':'test-only-private-proxy','CURL_CA_BUNDLE':'test-only-private-path'}):text=json.dumps(environment_summary())
        self.assertNotIn('test-only-private',text)
    def test_resume_remembers_selected_source_across_processes(self):
        setup.select('full');setup.next_step('wto');setup.mark('wto','read_terms');setup.pause()
        code='import onboarding,json; print(json.dumps(onboarding.pause(False)))'
        p=subprocess.run([sys.executable,'-B','-c',code],capture_output=True,text=True,encoding='utf-8',env=rt.subprocess_environment(),check=True)
        r=json.loads(p.stdout);self.assertEqual(r['source'],'wto');self.assertEqual(r['step'],'account_ready')
    def test_upgrade_preserves_pause_and_active_source(self):
        import install
        setup.select('full');setup.next_step('wto');setup.mark('wto','read_terms');setup.pause()
        with mock.patch.object(install,'verify',return_value=({'ok':True},{})):
            install.install(cli.ROOT,Path(self.temp.name)/'runtime','full',config_only=True)
        s=setup.status();self.assertTrue(s['paused']);self.assertEqual(s['active_source'],'wto')
    def test_all_public_command_help_uses_valid_entrypoints(self):
        for row in cli.catalog():
            if row.get('starter'):
                with self.subTest(command=row['command']):self.assertTrue(cli.query(row['command'],help_only=True)['ok'])

if __name__=='__main__':unittest.main()
