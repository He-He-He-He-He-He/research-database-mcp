"""Regression for CBS no-match, false numeric claims, and evidence separation."""
import _bootstrap
import json,os,subprocess,tempfile,unittest
from unittest import mock
from pathlib import Path
import onboarding
import research_cli as cli
from result_contracts import assess
import result_store

class ResultContractChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='contract-check-');self.env=mock.patch.dict(os.environ,{'RESEARCH_MCP_STATE_DIR':self.temp.name});self.env.start();onboarding.select('general')
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def test_reported_cbs_empty_catalog_is_not_data(self):
        body={'@odata.context':'https://datasets.cbs.nl/odata/v1/CBS/$metadata#Datasets','value':[]}
        p=subprocess.CompletedProcess([],0,json.dumps(body),'')
        with mock.patch.object(cli.subprocess,'run',return_value=p):r=cli.query('cbs-datasets',['--query','population','--top','2'])
        self.assertTrue(r['ok']);self.assertTrue(r['execution_ok']);self.assertFalse(r['has_data']);self.assertFalse(r['data_verified'])
        self.assertEqual(r['record_count'],0);self.assertEqual(r['result_status'],'empty_result');self.assertEqual(r['empty_reason'],'no_match')
    def test_cbs_filter_and_language_suggestions_do_not_change_query(self):
        import sys,importlib
        sys.path.insert(0,str(cli.ROOT/'engine'));m=importlib.import_module('netherlands_cbs_odata_adapter')
        with mock.patch.object(m,'_get',return_value={'value':[]}) as get:r=m.datasets('population',2)
        self.assertEqual(get.call_args.args[1]['$filter'],"contains(Title,'population')")
        self.assertNotIn('$search',get.call_args.args[1]);self.assertEqual(r['query_info']['actual_filter'],"contains(Title,'population')")
        self.assertEqual(r['suggested_queries'][0]['query'],'Bevolking')
    def test_cbs_observation_rows_missing_values_are_not_no_match(self):
        r=assess('cbs-observations','observations',{'value':[{'Id':9,'Value':None,'Perioden':'2024JJ00'}]})
        self.assertEqual(r['record_count'],1);self.assertEqual(r['numeric_observation_count'],0);self.assertEqual(r['result_status'],'missing_observations');self.assertFalse(r['has_data'])
        r=assess('cbs-observations','observations',{'value':[]});self.assertEqual(r['empty_reason'],'no_matching_observations')
    def test_ids_and_years_cannot_satisfy_numeric_contract(self):
        r=assess('cbs-observations','observations',{'value':[{'Id':1,'year':2024,'Value':None}]});self.assertFalse(r['data_verified'])
    def test_zero_is_a_real_value_but_null_nan_and_boolean_are_not(self):
        r=assess('cbs-observations','observations',{'value':[{'Value':v} for v in [0,None,'NaN',False]]})
        self.assertEqual(r['numeric_observation_count'],1);self.assertTrue(r['data_verified']);self.assertEqual(r['missing_measure_count'],3)
    def test_numeric_catalog_ids_are_not_observations(self):
        r=assess('cbs-datasets','catalog',{'value':[{'Identifier':123,'ObservationCount':2000}]});self.assertIsNone(r['numeric_observation_count']);self.assertFalse(r['data_verified'])
    def test_nbs_periods_without_values_are_missing_not_zero(self):
        r=assess('nbs-frequency-series','observations',{'data':[{'code':'202401MM','values':[]}]});self.assertFalse(r['has_data']);self.assertEqual(r['result_status'],'missing_observations')
    def test_metadata_and_unknown_types_do_not_claim_values(self):
        r=assess('unknown','unclassified',{'count':20,'year':2024});self.assertEqual(r['result_status'],'unclassified');self.assertIsNone(r['has_data']);self.assertFalse(r['data_verified'])
    def test_jsonstat_values_keep_flags_and_dimensions(self):
        body={'value':{'0':1.25,'1':None},'status':{'1':'c'},'dimension':{'unit':{'label':'persons'}}};r=assess('eurostat','observations',body)
        self.assertEqual(r['numeric_observation_count'],1);self.assertEqual(body['status']['1'],'c')
    def test_batch_counts_empty_separately_from_completed(self):
        from batch_query import batch
        a={'ok':True,'result_status':'empty_result','has_data':False,'data_verified':False}
        b={'ok':True,'result_status':'observations','has_data':True,'data_verified':True}
        with mock.patch('batch_query.query',side_effect=[a,b]):r=batch([{'command':'one','args':[]},{'command':'two','args':[]}],max_workers=1)
        self.assertEqual(r['passed'],2);self.assertEqual(r['data_summary']['empty_results'],1);self.assertEqual(r['data_summary']['numeric_results'],1)
    def test_compact_export_keeps_empty_status_visible(self):
        r={'ok':True,'result':{'value':[]},**assess('cbs-datasets','catalog',{'value':[]})}
        out=result_store.present(r,'compact');self.assertFalse(out['has_data']);self.assertEqual(out['result_status'],'empty_result')
    def test_unlisted_commands_are_explicitly_not_tested(self):
        from capabilities import status
        self.assertEqual(status('unknown-command')['level'],'not_tested')
    def test_page_html_requires_visible_text_and_snippets_stay_snippets(self):
        r=assess('dingxiu-institution-page','text_search',{'page_html':'<div> </div>'})
        self.assertFalse(r['has_content'])
        r=assess('dingxiu-institution-page','text_search',{'page_html':'<div>論語序</div>'})
        self.assertTrue(r['has_content']);self.assertEqual(r['text_characters'],3)
        r=assess('minguofy-institution-content-hits','text_search',{'items':[{'snippet_raw_html':'<b>命中</b>片段'}]})
        self.assertTrue(r['has_records']);self.assertFalse(r['has_content']);self.assertFalse(r['has_data']);self.assertEqual(r['content_level'],'snippet')
    def test_hbn_counts_only_the_selected_measure_not_dates_or_other_columns(self):
        body={'indicator_code':'42','columns':[{'field':'hbn-date'},{'field':'hbn_0_42'}],'rows':[{'hbn-date':2022,'hbn_0_42':None,'other':999}]}
        r=assess('hbn-institution-values','observations',body);self.assertEqual(r['numeric_observation_count'],0)
        body['rows'][0]['hbn_0_42']=0
        self.assertEqual(assess('hbn-institution-values','observations',body)['numeric_observation_count'],1)
    def test_infobank_exact_source_title_mismatch_is_rejected(self):
        import sys,importlib
        sys.path.insert(0,str(cli.ROOT/'engine'));m=importlib.import_module('infobank_institution_article_adapter')
        response=mock.Mock();response.content='<html>ZJDX<table class="tictab"><tr><td>目录&gt;&gt;原始題名</td></tr></table><div class="bmtitle"></div><div id="text"><p>正文</p></div></html>'.encode()
        session=mock.Mock();session.get.return_value=response
        r=m.article('123','KX','KX',session=session,expected_title='原始題名');self.assertTrue(r['title_verified'])
        with self.assertRaisesRegex(RuntimeError,'标题.*不一致'):m.article('123','KX','KX',session=session,expected_title='原始题名')
    def test_nonempty_catalog_batch_is_not_counted_as_body_or_numeric_data(self):
        from batch_query import batch
        r={'ok':True,'result_kind':'catalog',**assess('cbs-datasets','catalog',{'value':[{'Identifier':'03743'}]})}
        with mock.patch('batch_query.query',return_value=r):out=batch([{'command':'cbs-datasets','args':[]}])
        self.assertEqual(out['passed'],1);self.assertEqual(out['data_summary']['nonempty_results'],1)
        self.assertEqual(out['data_summary']['content_results'],0);self.assertEqual(out['data_summary']['numeric_results'],0)
    def test_nasa_counts_named_returned_variables_and_preserves_missing(self):
        body={'parameters':{'T2M':{'units':'C'}},'rows':[{'date':'2024-01-01','T2M':20},{'date':'2024-01-02','T2M':None}]}
        r=assess('nasa-power-daily','observations',body)
        self.assertEqual(r['numeric_observation_count'],1);self.assertEqual(r['missing_measure_count'],1)
    def test_drc_reference_parses_leaf_parent_and_preserves_title(self):
        import sys,importlib
        sys.path.insert(0,str(cli.ROOT/'engine'));m=importlib.import_module('drcnet_ip_catalog_adapter')
        item={'code':'A10_123','leafIds':'16023','chnidPath':'3590_3628_4120_16023','title':'合併黃離草'}
        r=m.detail_reference(item)
        self.assertEqual(r,{'doc_id':'123','leaf_id':'16023','channel_id':'4120','expected_title':'合併黃離草'})
        self.assertEqual(m.detail_reference({**item,'chnidPath':'bad|3590_3628_4120_16023'})['channel_id'],'4120')
        self.assertIsNone(m.detail_reference({**item,'leafIds':'999'}))
    def test_nmr_display_counter_is_not_a_chemical_locant(self):
        import sys,importlib
        sys.path.insert(0,str(cli.ROOT/'engine'));m=importlib.import_module('nmrdata_institution_catalog_adapter')
        self.assertEqual(m.compound_name('1 . ethanol'),'ethanol')
        for name in ['1,2-dichloroethane','1.2-substance','13C ethanol','ethanol']:self.assertEqual(m.compound_name(name),name)
    def test_htcases_catalog_and_detail_share_the_same_strict_identity_guard(self):
        import sys,importlib
        sys.path.insert(0,str(cli.ROOT/'engine'));a=importlib.import_module('htcases_institution_catalog_adapter');b=importlib.import_module('htcases_institution_detail_adapter')
        self.assertIs(a._require_institution,b._require_institution)
        with mock.patch.object(a,'_post',return_value={'body':{'name':'其他学校'}}):
            with self.assertRaises(RuntimeError):a._require_institution(mock.Mock(),('app','key'))
    def test_minguo_body_does_not_count_image_placeholders(self):
        r=assess('minguofy-institution-document','text_search',{'paragraphs':[{'type_raw':'图片','text':None}]})
        self.assertFalse(r['has_content'])

    def test_setup_verification_does_not_accept_a_completed_but_empty_request(self):
        import research_mcp as mcp
        with mock.patch.object(mcp,'query',return_value={'ok':True,'result_status':'empty_result','has_records':False,'has_content':False,'data_verified':False}),mock.patch.object(onboarding,'record_test') as record:
            result=mcp.call('research_verify',{'source':'eia'})
        self.assertFalse(result['verification_accepted']);self.assertFalse(record.call_args.args[1])

if __name__=='__main__':unittest.main()
