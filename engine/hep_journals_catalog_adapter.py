"""高等教育出版社 HEP Journals 官方跨期刊公开题录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://journal.hep.com.cn/hep/EN/search/keyword'

def search(keyword, page=1, limit=5):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–100 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('每页须为 1–20 条')
    q = keyword.strip()
    r = requests.get(URL, params={'searchResult': '', 'keyword': q, 'pageNum': page, 'pageSize': limit}, timeout=30)
    r.raise_for_status()
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('HEP 未返回 JSON') from None
    if not isinstance(d, dict) or type(d.get('total')) is not int or d['total'] < 0 or (not isinstance(d.get('list'), list)) or (len(d['list']) > limit):
        raise RuntimeError('HEP 搜索结果结构异常')
    items = []
    for x in d['list']:
        if not isinstance(x, dict) or x.get('id') is None or (not isinstance(x.get('ext'), dict)):
            raise RuntimeError('题录缺少编号或扩展字段')
        ext = x['ext'].get('EN') or x['ext'].get('CN') or {}
        issue = x.get('issue') or {}
        if not isinstance(ext, dict) or not isinstance(issue, dict) or (not isinstance(ext.get('title'), str)):
            raise RuntimeError('题录标题或期次缺失')
        items.append({'id': str(x['id']), 'title': BeautifulSoup(ext['title'], 'html.parser').get_text(' ', strip=True), 'journal_raw': ext.get('journalTitle'), 'authors_raw': x.get('authorsStrEn') or x.get('authorsStrCn'), 'doi': x.get('doi'), 'article_url_raw': ext.get('idUrl'), 'doi_url_raw': ext.get('doiUrl'), 'abstract_html_raw': ext.get('articleAbstract'), 'language_raw': ext.get('language'), 'year_raw': issue.get('year'), 'volume_raw': issue.get('volume'), 'issue_raw': issue.get('issue'), 'first_page_raw': x.get('startPage'), 'last_page_raw': x.get('endPage'), 'publish_time_raw': x.get('pubDate')})
    return {'source': '高等教育出版社 HEP Journals 公开文章题录', 'query': q, 'page_requested': page, 'page_size': limit, 'total': d['total'], 'items': items, 'note': '站方跨期刊搜索覆盖标题、作者、摘要、关键词等；上游响应未回显页码或关键词。摘要为原始 HTML，链接与时间戳按上游原值保留，缺失为 null；学校机构身份、具体期刊订购和全文权限未核验。'}
