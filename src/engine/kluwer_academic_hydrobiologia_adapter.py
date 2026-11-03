"""Crossref records for a fixed historical Hydrobiologia journal window."""
import release_runtime
import json, subprocess
from crossref_catalog_validation import validate_crossref_page
from urllib.parse import urlencode
ISSN = '0018-8158'
PUBLISHER_SOURCE = 'https://link.springer.com/content/pdf/10.1023/A%3A1017235928288.pdf'
LIBRARY_SOURCE = 'https://libdb.zju.edu.cn/s/lib/libtb/show/538'

def search(keyword, page=1, rows=5):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为1—200字符')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000) or isinstance(rows, bool) or (not isinstance(rows, int)) or (not 1 <= rows <= 20):
        raise ValueError('页数或条数超限')
    if page * rows > 10000:
        raise ValueError('Crossref offset 与 rows 的范围不可超过10000；此入口未实现 cursor 深分页')
    url = 'https://api.crossref.org/journals/' + ISSN + '/works?' + urlencode({'query.bibliographic': keyword.strip(), 'filter': 'from-pub-date:1997-01-01,until-pub-date:2000-12-31', 'rows': rows, 'offset': (page - 1) * rows})
    p = release_runtime.run(['/usr/bin/curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-filesize', '8000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Crossref 查询失败: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > 8000000:
        raise RuntimeError('响应超过8MB')
    d = json.loads(p.stdout)
    m = d.get('message', {})
    if d.get('status') != 'ok':
        raise RuntimeError('Crossref 返回格式异常')
    validate_crossref_page(m, rows)
    items = [{'title': (x.get('title') or [''])[0], 'doi': x.get('DOI'), 'url': x.get('URL'), 'type': x.get('type'), 'published': x.get('published'), 'publisher': x.get('publisher'), 'authors': [{'given': a.get('given'), 'family': a.get('family')} for a in x.get('author', [])], 'issn': x.get('ISSN', [])} for x in m['items']]
    return {'source': 'Crossref public metadata', 'api_url': url, 'publisher_evidence': PUBLISHER_SOURCE, 'library_source': LIBRARY_SOURCE, 'journal': 'Hydrobiologia', 'issn': ISSN, 'publication_date_filter': '1997-01-01/2000-12-31', 'query': keyword.strip(), 'total_reported': m.get('total-results'), 'page': page, 'items': items, 'note': '期刊是馆方所述 Kluwer Academic 现并入 SpringerLink 资源的一种历史示例；按 Crossref 现有元数据筛选出版日期，非馆方订购全文或出版社官方API；相关性搜索可能返回其他条目，日期和出版者字段以返回值为准。'}
