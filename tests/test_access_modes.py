"""Access boundaries, legacy migrations, and actual-failure-based network skipping."""
import sys
import _bootstrap
sys.dont_write_bytecode=True
import json,os,platform,subprocess,tempfile,unittest
from unittest import mock
from pathlib import Path
import access_policy as policy
import network_health as network
import onboarding as setup
import release_runtime as rt
import research_cli as cli
import research_mcp as mcp


class AccessChecks(unittest.TestCase):
    def setUp(self):
        # Windows platform.system() can spawn cmd.exe on first use. Resolve it
        # before tests mock the shared subprocess.run function for query calls.
        platform.system()
        self.temp=tempfile.TemporaryDirectory(prefix='access-check-')
        self.env=mock.patch.dict(os.environ,{'RESEARCH_MCP_STATE_DIR':self.temp.name})
        self.env.start();setup.select('general')
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def entry(self,name):return next(x for x in cli.catalog() if x['command']==name)
    def success(self):return subprocess.CompletedProcess([],0,'{"ok":true,"items":[]}','')
    def failure(self,kind='dns_error',status=None):
        details={'kind':kind,'endpoint':'https://example.org/api'}
        if status:details['http_status']=status
        return subprocess.CompletedProcess([],1,'',json.dumps({'error':'test-only transport failure','diagnostics':details}))
    def test_all_general_commands_ignore_starter_gate(self):
        public=[x for x in cli.catalog() if x['access']=='general']
        self.assertGreater(len(public),42)
        self.assertTrue(all(policy.allowed('general',x) for x in public))
        with mock.patch.object(cli.subprocess,'run',return_value=self.success()):
            self.assertTrue(cli.query('pmi-list',[])['ok'])
    def test_reachable_function_analysis_fixes_transitive_false_login_flags(self):
        for command in ('household-spending','nbs-income','journalism-crossref','pmi-list',
                        'nhc-health-institutions','ror-search','us-federal-register-search',
                        'nsidc-seaice-monthly','japan-diet-speech-search','qingti-local-status','funder-search'):
            with self.subTest(command=command):self.assertEqual(self.entry(command)['access'],'general')
    def test_public_pagination_tokens_are_not_login_tokens(self):
        for command in ('copernicus-oai-next','rijksmuseum-search','trials-search-advanced','persee-records'):
            self.assertEqual(self.entry(command)['access'],'general')
    def test_credentials_and_institution_are_separate(self):
        institution=self.entry('incopat-institution-search');key=self.entry('eia-v2-browse')
        self.assertFalse(policy.allowed('general',institution));self.assertTrue(policy.allowed('zju',institution))
        self.assertFalse(policy.allowed('zju',key));self.assertTrue(policy.allowed('login',key))
        with mock.patch.object(cli.subprocess,'run',side_effect=AssertionError('no execution')):
            r=cli.query(key['command'],['electricity']);self.assertEqual(r['required_mode'],'login')
        setup.select('zju')
        with mock.patch.object(cli.subprocess,'run',return_value=self.success()):self.assertTrue(cli.query(institution['command'],['test'])['ok'])
        setup.select('login')
        missing=subprocess.CompletedProcess([],1,'',json.dumps({'error':'无法读取本机 EIA 密钥','diagnostics':{'exception_type':'RuntimeError'}}))
        with mock.patch.object(cli.subprocess,'run',side_effect=[self.success(),missing]):
            r=cli.query('eia-v2-browse',['electricity']);self.assertEqual(r['error'],'credential_required');self.assertNotIn('skipped',r)
    def test_no_credentials_read_in_general_or_zju(self):
        for mode in ('general','zju'):
            setup.select(mode)
            with mock.patch.object(rt.subprocess,'run',side_effect=AssertionError('keychain forbidden')):
                self.assertIsNone(rt.credential('eia'))
                self.assertIsNone(rt.getenv('TEST_API_KEY'))
                with self.assertRaises(ValueError):rt.save_credential('eia','test-only-key')
    def test_old_state_migrates_without_losing_progress_or_pause(self):
        path=Path(self.temp.name)/'progress.json'
        for old,new in [('partial','general'),('full','login')]:
            path.write_text(json.dumps({'schema':1,'mode':old,'paused':True,'active_source':'wto','progress':{'wto':{'done':['read_terms']}}}),encoding='utf-8')
            state=rt.load_state();self.assertEqual(state['mode'],new);self.assertEqual(state['schema'],2)
            self.assertTrue(state['paused']);self.assertEqual(state['active_source'],'wto')
            self.assertEqual(state['progress']['wto']['done'],['read_terms'])
    def test_mode_switch_preserves_paused_configuration(self):
        setup.select('login');setup.next_step('wto');setup.mark('wto','read_terms');setup.pause()
        setup.select('general');setup.select('zju');setup.select('login')
        self.assertTrue(setup.status()['paused']);self.assertEqual(setup.pause(False)['source'],'wto')
    def test_missing_proxy_does_not_block_overseas_sources(self):
        with mock.patch.dict(os.environ,{},clear=True),mock.patch.object(rt,'state_root',return_value=Path(self.temp.name)),mock.patch.object(cli.subprocess,'run',return_value=self.success()):
            self.assertTrue(cli.query('arxiv',['energy'])['ok'])
        self.assertFalse(network.status()['unavailable'])
    def test_actual_network_failure_skips_and_persists_without_secrets(self):
        with mock.patch.object(cli.subprocess,'run',side_effect=[self.success(),self.failure()]):r=cli.query('arxiv',['energy'])
        self.assertTrue(r['skipped']);self.assertEqual(r['skip_reason'],'network_unavailable')
        code='import network_health,json;print(json.dumps(network_health.status()))'
        p=subprocess.run([sys.executable,'-B','-c',code],env=rt.subprocess_environment(),capture_output=True,text=True,check=True)
        self.assertIn('command:arxiv',json.loads(p.stdout)['unavailable'])
        saved=(Path(self.temp.name)/'network-health.json').read_text()
        self.assertNotIn('energy',saved);self.assertNotIn('/api',saved)
    def test_repeat_skip_runs_only_syntax_validation_not_upstream(self):
        network.record(self.entry('arxiv'),{'error':'network_dns_error'})
        with mock.patch.object(cli.subprocess,'run',return_value=self.success()) as run:r=cli.query('arxiv',['energy'])
        self.assertTrue(r['skipped']);self.assertEqual(run.call_count,1)
        self.assertEqual(run.call_args.kwargs['env']['RESEARCH_MCP_VALIDATE_ONLY'],'1')
    def test_wrong_parameters_win_over_network_cooldown(self):
        network.record(self.entry('arxiv'),{'error':'network_dns_error'})
        r=cli.query('arxiv',['energy','--rows','2'])
        self.assertEqual(r['error'],'invalid_arguments');self.assertNotIn('skipped',r)
    def test_failure_does_not_block_other_sources(self):
        network.record(self.entry('arxiv'),{'error':'network_dns_error'})
        with mock.patch.object(cli.subprocess,'run',return_value=self.success()):self.assertTrue(cli.query('crossref',['energy'])['ok'])
    def test_http_access_denial_and_rate_limit_are_not_network_outages(self):
        for status in (401,403,404,429,503):
            with mock.patch.object(cli.subprocess,'run',side_effect=[self.success(),self.failure('http_status',status)]):r=cli.query('arxiv',['energy'])
            self.assertEqual(r['error'],'upstream_http_error');self.assertNotIn('skipped',r)
        self.assertFalse(network.status()['unavailable'])
    def test_cache_expiry_and_manual_reset(self):
        with mock.patch.object(network.time,'time',return_value=1000):network.record(self.entry('arxiv'),{'error':'network_dns_error'})
        with mock.patch.object(network.time,'time',return_value=1061):self.assertIsNone(network.blocked(self.entry('arxiv')))
        network.record(self.entry('arxiv'),{'error':'upstream_timeout'})
        self.assertFalse(mcp.call('research_setup',{'action':'network_reset'})['unavailable'])
    def test_discovery_filters_by_mode_and_recent_network_failure(self):
        r=mcp.discover('eia',available_only=True);self.assertNotIn('eia-v2-browse',[x['command'] for x in r['commands']])
        r=mcp.discover('eia',available_only=False);self.assertIn('eia-v2-browse',[x['command'] for x in r['commands']])
        network.record(self.entry('arxiv'),{'error':'network_dns_error'})
        r=mcp.discover('arxiv');self.assertNotIn('arxiv',[x['command'] for x in r['commands']]);self.assertGreater(r['excluded']['network'],0)
    def test_skips_do_not_destroy_onboarding_progress(self):
        setup.select('login');setup.mark('wto','read_terms');setup.pause()
        network.record(self.entry('arxiv'),{'error':'network_dns_error'})
        network.reset();state=setup.status();self.assertTrue(state['paused']);self.assertIn('read_terms',state['progress']['wto']['done'])
    def test_installer_emits_canonical_mode_and_preserves_old_state(self):
        import install
        setup.select('full');setup.mark('wto','read_terms');setup.pause()
        with mock.patch.object(install,'verify',return_value=({'ok':True},{})):
            upgraded=install.install(cli.ROOT.parent,Path(self.temp.name)/'runtime',None,config_only=True)
            self.assertEqual(upgraded['mode'],'login');self.assertTrue(setup.status()['paused'])
            r=install.install(cli.ROOT.parent,Path(self.temp.name)/'runtime','partial',config_only=True)
        self.assertEqual(r['mode'],'general');self.assertTrue(setup.status()['paused'])
        self.assertEqual(setup.status()['progress']['wto']['done'],['read_terms'])
    def test_schema_exposes_three_modes_and_legacy_aliases(self):
        spec=next(x for x in mcp.TOOLS if x['name']=='research_setup')
        self.assertEqual(set(spec['inputSchema']['properties']['mode']['enum']),{'general','zju','login','partial','full'})
    def test_catalog_is_complete_and_explicitly_classified(self):
        rows=cli.catalog();self.assertEqual(len(rows),3753)
        self.assertTrue(all(x.get('access') in policy.MODES and x.get('access_evidence') for x in rows))
        self.assertEqual(sum(x.get('starter',False) for x in rows),42)
    def test_legacy_curl_wrappers_retain_actual_network_failure_evidence(self):
        from diagnostics import error_payload
        with mock.patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],6,b'',b'')):
            rt.run(['curl','https://example.org/api?api_key=test-only-secret'])
        result=error_payload(RuntimeError('旧适配器请求失败'))
        self.assertEqual(result['diagnostics']['kind'],'dns_error')
        self.assertEqual(result['diagnostics']['evidence'],'actual-curl-return-code')
        self.assertNotIn('test-only-secret',json.dumps(result))
    def test_successful_transport_clears_failure_and_arguments_remain_arguments(self):
        from diagnostics import error_payload
        with mock.patch.object(rt.subprocess,'run',side_effect=[subprocess.CompletedProcess([],28,b'',b''),subprocess.CompletedProcess([],0,b'{}',b'')]):
            rt.run(['curl','https://example.org/']);rt.run(['curl','https://example.org/'])
        self.assertIsNone(rt.transport_error())
        self.assertEqual(error_payload(ValueError('test-only-bad-input'))['diagnostics']['exception_type'],'ValueError')


if __name__=='__main__':unittest.main()
