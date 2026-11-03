"""Crossref metadata for six Microbiology Society journals listed by ZJU library."""
import release_runtime
import json, subprocess
from urllib.parse import urlencode
JOURNALS = {'microbiology': ('Microbiology', '1465-2080'), 'virology': ('Journal of General Virology', '1465-2099'), 'medical': ('Journal of Medical Microbiology', '1473-5644'), 'taxonomy': ('International Journal of Systematic and Evolutionary Microbiology', '1466-5034'), 'genomics': ('Microbial Genomics', '2057-5858'), 'access': ('Access Microbiology', '2516-8290')}

def catalog():
    return [{'code': k, 'title': v[0], 'issn': v[1]} for k, v in JOURNALS.items()]

def search(keyword, journal='microbiology', page=1, rows=5):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为1至200字符')
    if journal not in JOURNALS:
        raise ValueError('未知期刊')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000) or isinstance(rows, bool) or (not isinstance(rows, int)) or (not 1 <= rows <= 20):
        raise ValueError('页码或数量无效')
    title, issn = JOURNALS[journal]
    if page * rows > 10000:
        raise ValueError('Crossref offset 与 rows 的范围不可超过10000；此入口未实现 cursor 深分页')
    url = 'https://api.crossref.org/journals/' + issn + '/works?' + urlencode({'query.bibliographic': keyword, 'rows': rows, 'offset': (page - 1) * rows})
    p = release_runtime.run(['/usr/bin/curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-filesize', '8000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Crossref request failed: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > 8000000:
        raise RuntimeError('response exceeds 8 MB')
    d = json.loads(p.stdout)
    m = d.get('message', {})
    if d.get('status') != 'ok' or not isinstance(m.get('items'), list):
        raise RuntimeError('Crossref response invalid')
    items = []
    for x in m['items']:
        items.append({'title': (x.get('title') or [''])[0], 'doi': x.get('DOI'), 'url': x.get('URL'), 'type': x.get('type'), 'published': x.get('published'), 'authors': [{'given': a.get('given'), 'family': a.get('family')} for a in x.get('author', [])], 'container_title': x.get('container-title', []), 'issn': x.get('ISSN', [])})
    return {'source': 'Crossref official public metadata', 'source_info': 'https://libdb.zju.edu.cn/s/lib/libtb/show/2019', 'journal': title, 'issn': issn, 'query': keyword, 'page': page, 'rows': rows, 'total_reported': m.get('total-results'), 'items': items, 'note': 'Crossref 按刊物 ISSN 的相关性检索，不是出版社直接接口或浙大全文权限证明；总量为查询元数据结果，可能含更正、其他条目及相关度不高结果，不代表全部相关文献。'}
