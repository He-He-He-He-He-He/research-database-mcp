"""Do not mistake a CHANT zero-result page or empty institution body for access."""
import _bootstrap
import sys,json,unittest,tempfile,os,subprocess
from pathlib import Path
from unittest import mock
import research_cli as cli
import onboarding
from diagnostics import SourceError,error_payload
sys.path.insert(0,str(cli.ROOT/'engine'))
import chant_ip_search_adapter as chant
import htcases_institution_catalog_adapter as ht

BOOK='cdfdf940-40b4-11e9-b2f3-65894529c26e';CHAPTER='572a6650-416b-11e9-bea6-099b3d962b85'
def page(word='诗经',body='',identity=True):
    return '<html><title>漢達文庫 - 檢索結果 - '+word+'</title><body>'+('[Zhejiang University]' if identity else '')+body+'</body></html>'
def url(word='诗经'):return chant.BASE+'/result/FastSearch/'+word+'?Target='+word
EMPTY='<script>ShowErrorMessage("沒有結果", \'info\');</script>'
HITS='結果總數： <span>1</span> 共 <span>1</span> 書目<h5>1：《<a href="/text/book/'+BOOK+'">史記</a>．<a href="/text/book/'+BOOK+'/'+CHAPTER+'">儒林列傳第六十一</a>》</h5>'
class InstitutionResponses(unittest.TestCase):
    def test_explicit_no_results_without_h3_is_empty_not_auth_failure(self):
        total,books,items,count,empty=chant.parse_result(page(body=EMPTY),'诗经',url())
        self.assertEqual((total,books,items,count,empty),(0,0,[],0,True))
    def test_title_without_result_evidence_does_not_become_empty_success(self):
        with self.assertRaises(SourceError) as caught:chant.parse_result(page(),'诗经',url())
        self.assertEqual(caught.exception.as_dict()['kind'],'source_schema_changed')
    def test_no_h3_nonempty_result_requires_exact_query_and_real_linked_ids(self):
        r=chant.parse_result(page('詩經',HITS),'詩經',url('詩經'),1)
        self.assertEqual(r[0],1);self.assertEqual(r[2][0]['book_id'],BOOK);self.assertEqual(r[2][0]['chapter_id'],CHAPTER)
        self.assertEqual(r[2][0]['book_title'],'史記');self.assertEqual(r[2][0]['chapter_title'],'儒林列傳第六十一')
    def test_result_title_or_heading_mismatch_is_rejected(self):
        for html in [page('詩經',HITS),page(body='<h3>【论语】</h3>'+HITS)]:
            with self.assertRaises(SourceError):chant.parse_result(html,'诗经',url())
    def test_zero_result_does_not_bypass_institution_identity(self):
        with self.assertRaises(SourceError) as caught:chant.parse_result(page(body=EMPTY,identity=False),'诗经',url())
        self.assertEqual(caught.exception.as_dict()['kind'],'institution_identity_unconfirmed')
    def test_inconsistent_no_match_or_cross_book_link_is_rejected(self):
        for body in [HITS.replace('<span>1</span>','<span>0</span>'),HITS+EMPTY,HITS.replace('/'+BOOK+'/'+CHAPTER,'/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/'+CHAPTER)]:
            with self.assertRaises(SourceError):chant.parse_result(page(body=body),'诗经',url())
    def test_ht_empty_identity_retries_once_then_stops_without_querying_records(self):
        with mock.patch.object(ht,'_post',return_value={'body':''}) as post:
            with self.assertRaises(SourceError) as caught:ht._require_institution(mock.Mock(),('app','key'))
        self.assertEqual(post.call_count,2);self.assertEqual(caught.exception.as_dict()['reason'],'empty_identity_response')
        self.assertTrue(all(c.args[1]=='client/org/getByIp' for c in post.call_args_list))
    def test_ht_other_institution_does_not_retry_or_allow(self):
        with mock.patch.object(ht,'_post',return_value={'body':{'name':'其他学校'}}) as post:
            with self.assertRaises(SourceError) as caught:ht._require_institution(mock.Mock(),('app','key'))
        self.assertEqual(post.call_count,1);self.assertEqual(caught.exception.as_dict()['reason'],'institution_name_mismatch')
    def test_ht_transient_empty_then_explicit_identity_can_continue(self):
        with mock.patch.object(ht,'_post',side_effect=[{'body':None},{'body':{'name':'浙江大学'}}]) as post:
            self.assertEqual(ht._require_institution(mock.Mock(),('app','key'))['name'],'浙江大学')
        self.assertEqual(post.call_count,2)
    def test_cli_empty_identity_error_is_not_network_error(self):
        error=SourceError('institution_identity_unconfirmed','机构认证请求完成但返回空机构信息');error.details['reason']='empty_identity_response'
        process=subprocess.CompletedProcess([],1,'',json.dumps(error_payload(error)))
        with tempfile.TemporaryDirectory() as state,mock.patch.dict(os.environ,{'RESEARCH_MCP_STATE_DIR':state}):
            onboarding.select('zju')
            with mock.patch.object(cli.subprocess,'run',return_value=process):r=cli.query('htcases-institution-catalog',['管理'])
        self.assertFalse(r['ok']);self.assertEqual(r['error'],'institution_identity_unconfirmed');self.assertEqual(r['diagnostics']['reason'],'empty_identity_response')
if __name__=='__main__':unittest.main()
