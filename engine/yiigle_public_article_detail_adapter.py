"""中华医学期刊文章公开网页元数据；不读取正文。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://rs.yiigle.com/cmaid/'
FIELDS = ('citation_title', 'citation_author', 'citation_doi', 'citation_journal_title', 'citation_publication_date', 'citation_volume', 'citation_issue', 'citation_firstpage', 'citation_lastpage', 'citation_keyword', 'citation_abstract', 'citation_language')

def detail(article_id, expected_title, expected_doi, session=None):
    ident = str(article_id)
    if not re.fullmatch('[1-9][0-9]{0,11}', ident):
        raise ValueError('文献编号须为正整数')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 500 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供搜索返回的完整题名')
    if not isinstance(expected_doi, str) or not re.fullmatch('10\\.\\d{4,9}/[A-Za-z0-9._-]+', expected_doi, re.I):
        raise ValueError('须提供搜索返回的 DOI')
    try:
        r = (session or requests.Session()).get(BASE + ident, timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('详情不可用或未返回文章页面')
        p = BeautifulSoup(r.content, 'html.parser')
        found = {k: [] for k in FIELDS}
        omitted = []
        for meta in p.select('meta[name][content]'):
            key = meta.get('name', '').lower()
            if key not in found:
                continue
            value = meta.get('content', '').strip()
            if not value:
                continue
            if len(value) > 20000 or re.search('https?://|(?:token|session|cookie|authorization)\\s*[:=]|[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]', value, re.I):
                if key not in omitted:
                    omitted.append(key)
                continue
            found[key].append(value)
        if expected_title.strip() not in found['citation_title'] or not any((x.lower() == expected_doi.lower() for x in found['citation_doi'])):
            raise RuntimeError('详情题名或 DOI 与检索结果不一致')
        return {'source': '中华医学期刊官方文章公开元数据', 'article_id': int(ident), 'titles_raw': found['citation_title'], 'authors_raw': found['citation_author'], 'doi_raw': found['citation_doi'], 'journal_raw': found['citation_journal_title'], 'publication_date_raw': found['citation_publication_date'], 'volume_raw': found['citation_volume'], 'issue_raw': found['citation_issue'], 'firstpage_raw': found['citation_firstpage'], 'lastpage_raw': found['citation_lastpage'], 'keywords_raw': found['citation_keyword'], 'abstracts_raw': found['citation_abstract'], 'language_raw': found['citation_language'], 'source_fields_omitted': omitted, 'note': '公开网页元数据；多语言题名、关键词和摘要按站方顺序保留，语言对应关系未经逐项确认。未确认学校机构身份或全文权限，未读取正文；空列表仅表示未返回或安全过滤。'}
    except requests.RequestException:
        raise RuntimeError('中华医学期刊详情连接失败') from None
