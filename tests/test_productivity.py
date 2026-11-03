"""Meaningful batch, export, SDK, installer and native World Bank regressions."""
import sys
import _bootstrap
sys.dont_write_bytecode=True
import csv,io,json,os,subprocess,tempfile,threading,time,unittest
from pathlib import Path
from unittest import mock
import release_runtime as rt
import onboarding
import result_store as store
import research_mcp as mcp
import research_cli as cli
from batch_query import batch
from research_sdk import ResearchClient,WorldBank
from client_connect import merge
import install_network

class ProductivityChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='productivity-check-')
        self.env=mock.patch.dict(os.environ,{'RESEARCH_MCP_STATE_DIR':self.temp.name});self.env.start();onboarding.select('general')
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def example(self):return {'ok':True,'command':'test','result':[{'value':None,'unit':'元','text':'=1+1'},{'value':1.25,'unit':'元','text':'safe'}]}
    def test_small_results_keep_original_shape_without_export(self):
        r=self.example();self.assertIs(store.present(r),r);self.assertFalse((Path(self.temp.name)/'results').exists())
    def test_large_auto_result_is_bounded_and_exact_original_is_preserved(self):
        r={'ok':True,'result':[{'name':'一'*2000,'value':i} for i in range(100)]}
        view=store.present(r);self.assertFalse(view['inline_complete']);self.assertLess(len(json.dumps(view,ensure_ascii=False)),store.INLINE_LIMIT)
        self.assertEqual(json.loads(store.read(view['result_id'])),r)
    def test_csv_preserves_json_and_escapes_spreadsheet_formulas(self):
        r=self.example();saved=store.present(r,'file','csv')
        self.assertEqual(len(saved['artifacts']),2);self.assertEqual(json.loads(store.read(saved['result_id'])),r)
        rows=list(csv.DictReader(io.StringIO(store.read(saved['result_id'],'csv').lstrip('\ufeff'))))
        self.assertEqual(rows[0]['text'],"'=1+1");self.assertEqual(rows[1]['value'],'1.25')
    def test_export_and_lookup_reject_paths_and_symlinks(self):
        for ident in ('../../private','a'*31,'/etc/passwd'):
            with self.assertRaises(ValueError):store.read(ident)
        saved=store.save(self.example());folder=Path(self.temp.name)/'results'/saved['result_id'];path=folder/'result.json'
        # Windows CI may not permit symlink creation; path traversal is always checked.
        try:
            path.unlink();path.symlink_to(Path(self.temp.name)/'progress.json')
        except OSError:return
        with self.assertRaises(ValueError):store.read(saved['result_id'])
    def test_result_paging_and_json_pointer_keep_units_and_nulls(self):
        saved=store.save(self.example());a=store.fetch(saved['result_id'],offset=0,limit=1)
        self.assertEqual(a['next_offset'],1);self.assertIsNone(a['items'][0]['value']);self.assertEqual(a['items'][0]['unit'],'元')
        b=store.fetch(saved['result_id'],pointer='/result/1/value');self.assertEqual(b['value'],1.25)
    def test_oversized_row_is_not_returned_as_empty_data(self):
        saved=store.save({'ok':True,'result':[{'text':'x'*30000}]});r=store.fetch(saved['result_id'])
        self.assertTrue(r['row_too_large']);self.assertEqual(r['total_rows_stored'],1);self.assertEqual(r['next_offset'],0)
    def test_export_file_is_not_shareable_source(self):
        from distribution import permitted
        saved=store.save(self.example());self.assertTrue(all(not permitted('results/'+saved['result_id']+'/'+name) for name in ('result.json','result.csv')))
    def test_resource_read_is_scoped_and_protocol_preserves_old_clients(self):
        saved=store.save(self.example());response=mcp.handle({'jsonrpc':'2.0','id':1,'method':'resources/read','params':{'uri':saved['artifacts'][0]['uri']}})
        self.assertEqual(json.loads(response['result']['contents'][0]['text']),self.example())
        bad=mcp.handle({'jsonrpc':'2.0','id':2,'method':'resources/read','params':{'uri':'file:///etc/passwd'}});self.assertIn('error',bad)
        for version,structured in [('2024-11-05',False),('2025-06-18',True)]:
            mcp.handle({'jsonrpc':'2.0','id':3,'method':'initialize','params':{'protocolVersion':version}})
            r=mcp.handle({'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'research_setup','arguments':{'action':'status'}}})
            self.assertEqual('structuredContent' in r['result'],structured)
    def test_mixed_batch_preserves_errors_and_order(self):
        r=batch([{'id':'first','command':'eia-v2-browse','args':['electricity']},{'id':'second','command':'arxiv','args':['energy','--rows','1']}],output='full')
        self.assertEqual([x['id'] for x in r['result']],['first','second']);self.assertEqual(r['failed'],2)
        self.assertEqual(r['result'][0]['error'],'mode_required');self.assertEqual(r['result'][1]['error'],'invalid_arguments')
    def test_batch_isolates_failure_and_keeps_partial_success(self):
        def run(command,args,**kw):
            if command=='bad':raise ValueError('test-only-bad-argument')
            return self.example()
        with mock.patch('batch_query.query',side_effect=run):r=batch([{'command':'ok','args':[]},{'command':'bad','args':[]}],output='full')
        self.assertTrue(r['partial']);self.assertEqual(r['passed'],1);self.assertEqual(r['failed'],1)
    def test_same_family_never_runs_concurrently(self):
        active=peak=0;lock=threading.Lock()
        def run(*args,**kw):
            nonlocal active,peak
            with lock:active+=1;peak=max(peak,active)
            time.sleep(.02)
            with lock:active-=1
            return self.example()
        with mock.patch('batch_query.query',side_effect=run):batch([{'command':'crossref-a','args':[]},{'command':'crossref-b','args':[]}],output='full')
        self.assertEqual(peak,1)
    def test_batch_workers_keep_sdk_state_not_global_environment(self):
        state=Path(self.temp.name)/'separate';client=ResearchClient(state);client.setup('general')
        with mock.patch('batch_query.query',side_effect=lambda *a,**k:{'ok':True,'state':str(rt.state_root())}):r=client.batch([{'command':'x','args':[]}])
        self.assertEqual(r['result'][0]['state'],str(state.resolve()));self.assertEqual(rt.state_root(),Path(self.temp.name).resolve())
    def test_batch_bounds_are_enforced(self):
        for rows,workers in [([],3),([{'command':'x','args':[]}]*13,3),([{'command':'x','args':[]}],5)]:
            with self.assertRaises(ValueError):batch(rows,max_workers=workers)
    def test_sdk_uses_existing_mode_and_rejects_credentials_in_args(self):
        client=ResearchClient();self.assertEqual(client.setup()['mode'],'general')
        with self.assertRaises(ValueError):client.query('crossref',['--api-key','test-only-not-a-secret'])
    def test_worldbank_sdk_uses_native_multi_entity_query(self):
        client=mock.Mock();WorldBank.get_series(['CHN','USA'],['SP.POP.TOTL','NY.GDP.MKTP.CD'],2020,2023,client=client)
        self.assertEqual(client.query.call_args.args[1][:2],['CHN,USA','SP.POP.TOTL,NY.GDP.MKTP.CD'])
    def wb(self):
        import importlib
        sys.path.insert(0,str(cli.ROOT/'engine'));return importlib.import_module('worldbank_adapters')
    def test_worldbank_bulk_one_native_request(self):
        wb=self.wb()
        with mock.patch.object(wb,'_get',return_value=[{'page':1,'pages':1,'total':1},[{'value':None}]]) as fetch:r=wb.series('CHN,USA','SP.POP.TOTL,NY.GDP.MKTP.CD',2020,2023)
        self.assertEqual(fetch.call_count,1);self.assertIn('CHN;USA',fetch.call_args.args[0]);self.assertEqual(fetch.call_args.args[1]['source'],'2');self.assertIsNone(r[1][0]['value'])
    def test_worldbank_bounded_pagination_is_explicitly_incomplete(self):
        wb=self.wb()
        with mock.patch.object(wb,'_get',return_value=[{'page':1,'pages':3,'total':3000},[{'value':1}]]):r=wb.series('CHN','SP.POP.TOTL',2000,2020,max_pages=1)
        self.assertFalse(r[0]['complete']);self.assertEqual(r[0]['next_page'],2)
    def test_worldbank_later_page_failure_keeps_first_rows(self):
        wb=self.wb()
        with mock.patch.object(wb,'_get',side_effect=[[{'page':1,'pages':2,'total':2},[{'value':1}]],RuntimeError('test-only-failure')]):r=wb.series('CHN','SP.POP.TOTL',2020,2023)
        self.assertEqual(len(r[1]),1);self.assertFalse(r[0]['complete']);self.assertEqual(r[0]['failed_pages'][0]['page'],2)
    def test_client_merge_preserves_other_connectors_and_private_backup(self):
        p=Path(self.temp.name)/'client/config.json';p.parent.mkdir();old={'other':{'keep':1},'mcpServers':{'other-service':{'env':{'SECRET':'test-only-private'}}}};p.write_text(json.dumps(old))
        entry={'command':'python','args':['server.py'],'env':{'RESEARCH_MCP_STATE_DIR':self.temp.name}}
        result=merge(entry,path=p);new=json.loads(p.read_text());self.assertEqual(new['mcpServers']['other-service'],old['mcpServers']['other-service']);self.assertEqual(new['other'],old['other'])
        self.assertNotIn('test-only-private',json.dumps(result));self.assertTrue(Path(result['backup_file']).is_relative_to(Path(self.temp.name).resolve()/'client-backups'));self.assertFalse(result['connected'])
        self.assertTrue(merge(entry,path=p)['unchanged'])
    def test_conflicting_client_is_not_overwritten(self):
        p=Path(self.temp.name)/'client.json';raw=json.dumps({'mcpServers':{'research-databases':{'command':'other'}}});p.write_text(raw)
        with self.assertRaises(ValueError):merge({'command':'python','env':{}},path=p)
        self.assertEqual(p.read_text(),raw)
    def test_jsonc_config_is_preserved(self):
        p=Path(self.temp.name)/'client.json';raw='{// private comment\n}';p.write_text(raw)
        with self.assertRaises(ValueError):merge({'command':'python'},path=p)
        self.assertEqual(p.read_text(),raw)
    def test_vscode_has_correct_server_root(self):
        p=Path(self.temp.name)/'mcp.json';merge({'command':'python','args':[]},client='vscode',path=p)
        d=json.loads(p.read_text());self.assertIn('servers',d);self.assertEqual(d['servers']['research-databases']['type'],'stdio')
    def test_pip_mirror_keeps_tls_and_only_retries_network_errors(self):
        fail=subprocess.CompletedProcess([],1,'','ReadTimeoutError');ok=subprocess.CompletedProcess([],0,'','')
        with mock.patch.object(install_network.subprocess,'run',side_effect=[fail,ok]) as run:
            r=install_network.dependencies('python','req.txt',fallback_index_url='https://example.org/simple/')
        self.assertEqual(len(r['attempted_sources']),2);self.assertNotIn('--trusted-host',run.call_args.args[0]);self.assertIn('--index-url',run.call_args.args[0])
    def test_pip_does_not_hide_dependency_or_certificate_errors(self):
        for error in ('No matching distribution found','SSLError CERTIFICATE_VERIFY_FAILED'):
            with mock.patch.object(install_network.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'',error)) as run:
                with self.assertRaises(RuntimeError):install_network.dependencies('python','req.txt',fallback_index_url='https://example.org/simple/')
            self.assertEqual(run.call_count,1)
    def test_pip_rejects_insecure_and_credential_urls(self):
        for url in ('http://example.org/simple','https://user:password@example.org/simple','https://example.org/simple?token=test'):
            with self.assertRaises(ValueError):install_network.validate_index(url)
    def test_export_invalid_pointer_and_negative_offsets(self):
        saved=store.save(self.example())
        for kwargs in ({'offset':-1},{'pointer':'/missing'},{'pointer':'/result/-1'}):
            with self.assertRaises(ValueError):store.fetch(saved['result_id'],**kwargs)

if __name__=='__main__':unittest.main()
