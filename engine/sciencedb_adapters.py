"""ScienceDB 科学数据集公开索引：搜索和按 DOI 查元数据。"""
import release_runtime
import re
import requests
from html.parser import HTMLParser
BASE = 'https://www.scidb.cn/api/sdb-query-service/query'

class _Text(HTMLParser):

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, s):
        self.parts.append(s)

def _plain(x):
    p = _Text()
    p.feed(x or '')
    return ''.join(p.parts).strip()

def _query(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('请输入不超过 200 字的检索词')
    r = requests.post(BASE, params={'queryCode': '', 'q': keyword}, json={}, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    x = r.json()
    if x.get('code') != 20000 or not isinstance(x.get('data'), dict):
        raise ValueError('未获得 ScienceDB 索引结果')
    return x['data']

def _record(x):
    return {'id': x.get('dataSetId'), 'doi': x.get('doi'), 'title_zh': _plain(x.get('titleZh')), 'title_en': _plain(x.get('titleEn')), 'abstract_zh': _plain(x.get('introductionZh')), 'abstract_en': _plain(x.get('introductionEn')), 'keywords_zh': x.get('keywordZh'), 'keywords_en': x.get('keywordEn'), 'authors': x.get('author'), 'license': x.get('copyRight'), 'access': x.get('shareStatus'), 'published': x.get('dataSetPublishDate'), 'source': 'ScienceDB 公开索引'}

def sciencedb_search(keyword):
    data = _query(keyword)
    return {'items': [_record(x) for x in data.get('data', [])], 'total': data.get('total'), 'note': 'ScienceDB 上游检索首页；字段和总数由上游提供，访问条件以数据集页面为准。'}

def sciencedb_metadata_by_doi(doi):
    if not isinstance(doi, str) or not re.fullmatch('10\\.\\d{4,9}/[A-Za-z0-9._;()/:+-]{1,180}', doi):
        raise ValueError('请输入 DOI')
    matches = [x for x in _query(doi).get('data', []) if str(x.get('doi', '')).lower() == doi.lower()]
    if not matches:
        raise ValueError('搜索首页未找到精确 DOI；不代表数据集不存在')
    return _record(matches[0])
