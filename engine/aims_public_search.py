"""AIMS 网站公开文章检索，返回题录而非机构授权证明。"""
import release_runtime
import argparse, html, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://www.aimsciences.org/search-data'
FIELDS = 'titleEn;authors.authorNameEn;keywords.keywordEn;abstractinfoEn;doi'
AGGS = 'year;authors.authorNameEn;keywords.keywordEn;classifyinfoEn;journalMeta.titleEn;publishDate'

def plain(s):
    return html.unescape(re.sub('<[^>]*>', '', str(s or ''))).strip()

def search(keyword, page=1):
    if not keyword.strip() or not 1 <= int(page) <= 1000:
        raise ValueError('请输入关键词及 1–1000 的页码')
    params = {'publisherId': '', 'searchField': FIELDS, 'q': keyword, 'searchType': '0', 'language': 'en', 'pn': str(page), 'limit': '10', 'filters': '[]', 'sorts': '[]', 'highlightFields': FIELDS.rsplit(';', 1)[0], 'aggreFields': AGGS}
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', '-X', 'POST', BASE + '?' + urlencode(params)], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('AIMS 检索请求失败: ' + p.stderr.strip())
    try:
        d = json.loads(p.stdout)
    except ValueError as e:
        raise RuntimeError('AIMS 响应不是 JSON') from e
    if not isinstance(d.get('resultlist'), list) or not isinstance(d.get('totalCount'), int):
        raise RuntimeError('AIMS 响应结构异常')
    items = []
    for x in d['resultlist']:
        j = x.get('journalMeta') or {}
        doi = x.get('doi') or ''
        items.append({'id': x.get('id'), 'title': plain(x.get('titleEn')), 'authors': [plain(a.get('authorNameEn')) for a in x.get('authors', []) if a.get('authorNameEn')], 'journal': plain(j.get('titleEn')), 'year': x.get('year'), 'volume': x.get('volume'), 'issue': x.get('issue'), 'doi': doi, 'url': 'https://doi.org/' + doi if doi else None})
    return {'source': 'AIMS 公开文章检索', 'scope': '平台公开文章题录；非浙大订购子集，不证明机构认证或全文授权', 'keyword': keyword, 'page': int(page), 'total': d['totalCount'], 'items': items}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page), ensure_ascii=False, indent=2))
