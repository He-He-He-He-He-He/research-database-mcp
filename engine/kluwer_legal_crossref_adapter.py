"""Crossref public bibliographic records for three Kluwer Law journals."""
import release_runtime
import json, subprocess
from crossref_catalog_validation import validate_crossref_page
from urllib.parse import urlencode
JOURNALS = {'common_market': {'title': 'Common Market Law Review', 'issn': '0165-0750', 'publisher_page': 'https://kluwerlawonline.com/journals/common%2Bmarket%2Blaw%2Breview/2'}, 'arbitration': {'title': 'Journal of International Arbitration', 'issn': '0255-8106', 'publisher_page': 'https://kluwerlawonline.com/Journals/Journal%2Bof%2BInternational%2BArbitration/4'}, 'business': {'title': 'European Business Law Review', 'issn': '0959-6941', 'publisher_page': 'https://kluwerlawonline.com/Journals/European%2BBusiness%2BLaw%2BReview/383'}}

def catalog():
    return {'source': 'Publisher journal descriptions', 'items': [{'code': k, **v} for k, v in JOURNALS.items()], 'note': '仅列3种经出版社页面核对的期刊，不代表全馆藏或全部Kluwer法学期刊。'}

def search(keyword, journal='arbitration', page=1, rows=5):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词需为1–200字符')
    if journal not in JOURNALS:
        raise ValueError('期刊代码不存在')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000) or isinstance(rows, bool) or (not isinstance(rows, int)) or (not 1 <= rows <= 20):
        raise ValueError('页码或条数超限')
    if page * rows > 10000:
        raise ValueError('Crossref offset 与 rows 的范围不可超过10000；此入口未实现 cursor 深分页')
    item = JOURNALS[journal]
    url = 'https://api.crossref.org/journals/' + item['issn'] + '/works?' + urlencode({'query.bibliographic': keyword.strip(), 'rows': rows, 'offset': (page - 1) * rows})
    p = release_runtime.run(['/usr/bin/curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-filesize', '8000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Crossref request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 8000000:
        raise RuntimeError('Crossref 返回过大')
    payload = json.loads(p.stdout)
    m = payload.get('message', {})
    if payload.get('status') != 'ok':
        raise RuntimeError('Crossref 返回格式异常')
    validate_crossref_page(m, rows)
    results = []
    for x in m['items']:
        results.append({'title': (x.get('title') or [''])[0], 'doi': x.get('DOI'), 'url': x.get('URL'), 'type': x.get('type'), 'publisher': x.get('publisher'), 'published': x.get('published'), 'authors': [{'given': a.get('given'), 'family': a.get('family')} for a in x.get('author', [])], 'container_title': x.get('container-title', []), 'issn': x.get('ISSN', [])})
    return {'source': 'Crossref public metadata', 'source_url': url, 'publisher_journal_page': item['publisher_page'], 'journal': item['title'], 'issn': item['issn'], 'query': keyword.strip(), 'page': page, 'rows': rows, 'total_reported': m.get('total-results'), 'items': results, 'note': 'Crossref按ISSN检索的相关性结果，可能含相关度低的文献、更正及其他文献类型；不是出版社接口、全部馆藏或学校全文权限的证明。'}
