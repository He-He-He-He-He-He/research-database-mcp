"""AIMS Sciences 出版社公开文章元数据，不读取正文。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.aimsciences.org/article/doi/'
FIELDS = ('citation_title', 'citation_doi', 'citation_author', 'citation_journal_title', 'citation_publisher', 'citation_date', 'citation_online_date', 'citation_volume', 'citation_issue', 'citation_firstpage', 'citation_lastpage', 'citation_issn', 'dc.description')
BAD = re.compile('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=|<\\s*(?:script|iframe|object|embed|style)\\b|\\bon\\w+\\s*=|[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]', re.I)

def detail(doi, expected_title, session=None):
    if not isinstance(doi, str) or not re.fullmatch('10\\.3934/[A-Za-z0-9._-]+', doi, re.I):
        raise ValueError('须提供 AIMS 搜索返回的 DOI')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 1000 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供完整题名')
    try:
        r = (session or requests.Session()).get(BASE + doi, timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('AIMS 详情不可用或重定向')
        p = BeautifulSoup(r.content, 'html.parser')
        m = {k: [] for k in FIELDS}
        omitted = []
        for e in p.select('meta[name][content]'):
            k = e.get('name', '').lower()
            if k not in m:
                continue
            v = e.get('content', '').strip()
            if not v:
                continue
            if len(v) > 30000 or BAD.search(v):
                if k not in omitted:
                    omitted.append(k)
                continue
            m[k].append(v)
        norm = lambda s: re.sub('\\s+', ' ', s).strip()
        if not any((norm(x) == norm(expected_title) for x in m['citation_title'])) or not any((x.lower() == doi.lower() for x in m['citation_doi'])):
            raise RuntimeError('详情题名或 DOI 与检索结果不一致')
        return {'source': 'AIMS Sciences 出版社公开文章详情', 'doi': doi, 'title_raw': m['citation_title'], 'authors_raw': m['citation_author'], 'journal_raw': m['citation_journal_title'], 'publisher_raw': m['citation_publisher'], 'publication_date_raw': m['citation_date'], 'online_date_raw': m['citation_online_date'], 'volume_raw': m['citation_volume'], 'issue_raw': m['citation_issue'], 'firstpage_raw': m['citation_firstpage'], 'lastpage_raw': m['citation_lastpage'], 'issn_raw': m['citation_issn'], 'abstract_raw': m['dc.description'], 'source_fields_omitted': omitted, 'note': '原站公开网页元数据；摘要保留来源字段，不读取正文。学校订购范围、机构身份及逐篇全文权限未验证；字段缺失或安全过滤不代表不存在。'}
    except requests.RequestException:
        raise RuntimeError('AIMS 详情连接失败') from None
