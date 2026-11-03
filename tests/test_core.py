"""Offline release checks. Uses temporary state and mocks, never real credentials."""
import sys
import _bootstrap
sys.dont_write_bytecode=True
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
import onboarding as setup
import release_runtime as rt
import research_mcp as mcp
import research_cli as cli

class ReleaseChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='research-mcp-self-check-')
        self.env=mock.patch.dict(os.environ,{'RESEARCH_MCP_STATE_DIR':self.tmp.name})
        self.env.start()
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def test_first_choice(self):self.assertEqual(setup.next_step()['action'],'ask_mode')
    def test_partial_needs_no_credentials(self):
        with mock.patch.object(rt,'credential',side_effect=AssertionError('must not read')):
            setup.select('partial');self.assertEqual(setup.next_step()['action'],'ready')
    def test_pause_resume(self):
        setup.select('full');setup.mark('eia','read_terms');setup.pause()
        self.assertEqual(setup.next_step()['action'],'paused')
        self.assertEqual(setup.pause(False)['step'],'account_ready')
    def test_restart_preserves_progress(self):
        setup.select('full');setup.mark('eia','read_terms')
        child=subprocess.run([sys.executable,'-B',str(cli.ROOT/'onboarding.py'),'status'],env=rt.subprocess_environment(),capture_output=True,text=True,check=True)
        self.assertIn('read_terms',json.loads(child.stdout)['progress']['eia']['done'])
    def test_switch_preserves_progress(self):
        setup.select('full');setup.mark('eia','account_ready');setup.select('partial');setup.select('full')
        self.assertIn('account_ready',setup.status()['progress']['eia']['done'])
    def test_skip_and_return(self):
        setup.select('full');setup.mark('eia',skip=True)
        self.assertEqual(setup.next_step()['source'],'cinii');self.assertEqual(setup.next_step('eia')['source'],'eia')
    def test_no_fake_test_confirmation(self):
        with self.assertRaises(ValueError):setup.mark('eia','tested')
    def test_old_env_is_invisible(self):
        setup.select('full')
        with mock.patch.dict(os.environ,{'API_TOKEN':'test-only-old-env','RESEARCH_MCP_EXTERNAL_API_TOKEN':'test-only-new-env'}):
            self.assertEqual(rt.getenv('API_TOKEN'),'test-only-new-env')
        with mock.patch.dict(os.environ,{'API_TOKEN':'test-only-old-env'}):self.assertIsNone(rt.getenv('API_TOKEN'))
    def test_credential_namespace(self):
        setup.select('full')
        with mock.patch.object(rt.sys,'platform','darwin'),mock.patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'test-only-key','')) as fake:
            result=rt.run(['/usr/bin/security','find-generic-password','-s','research-toolkit-wto-standard','-a','legacy-user','-w'],text=True)
            self.assertEqual(result.stdout.strip(),'test-only-key')
            args=fake.call_args.args[0];self.assertIn('research-mcp-publisher/wto',args);self.assertNotIn('legacy-user',args)
    def test_no_keychain_in_partial(self):
        setup.select('partial')
        with mock.patch.object(rt.subprocess,'run',side_effect=AssertionError('real keychain forbidden')):
            result=rt.run(['/usr/bin/security','find-generic-password','-s','research-toolkit-eia','-w'],text=True)
            self.assertEqual(result.returncode,44)
    def test_old_writes_rejected(self):
        with self.assertRaises(RuntimeError):rt.run(['/usr/bin/security','add-generic-password'])
    def test_clean_subprocess_environment(self):
        with mock.patch.dict(os.environ,{'OLD_SECRET':'test-only-old','RESEARCH_MCP_EIA_KEY':'test-only-explicit'}):
            env=rt.subprocess_environment();self.assertNotIn('OLD_SECRET',env);self.assertIn('RESEARCH_MCP_EIA_KEY',env)
            self.assertEqual(env['PYTHONPATH'],str(cli.ROOT)+os.pathsep+str(cli.ROOT/'engine'))
    def test_curlrc_disabled(self):
        with mock.patch.object(rt.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'',b'')) as fake:
            rt.run(['curl','https://example.org']);self.assertEqual(fake.call_args.args[0][1],'-q')
    def test_argv_validation(self):
        with self.assertRaises(ValueError):cli.query('not-a-command',[])
        with self.assertRaises(ValueError):cli.query('crossref',['--api-key','test-only-value'])
    def test_partial_gates_optional(self):
        setup.select('partial');self.assertEqual(cli.query('eia-v2-browse',['electricity'])['error'],'mode_required')
    def test_stdio_protocol(self):
        req=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list'}]
        p=subprocess.run([sys.executable,'-B',str(cli.ROOT/'research_mcp.py')],input=''.join(json.dumps(x)+'\n' for x in req),capture_output=True,text=True,env=rt.subprocess_environment(),check=True)
        rows=[json.loads(x) for x in p.stdout.splitlines()];self.assertEqual(len(rows),2);self.assertEqual(len(rows[1]['result']['tools']),7)
    def test_engine_help(self):self.assertTrue(cli.query('wb-series',help_only=True)['ok'])
    def test_python_syntax(self):
        for p in cli.ROOT.parent.rglob('*.py'):
            if '.venv' not in p.parts:compile(p.read_text(encoding='utf-8'),p.name,'exec')

if __name__=='__main__':
    sys.dont_write_bytecode=True
    unittest.main(verbosity=1)
