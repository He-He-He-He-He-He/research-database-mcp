"""Crossref bibliographic subset under the registered JSTOR DOI prefix."""
import release_runtime
import json, subprocess
from urllib.parse import urlencode
ENDPOINT = 'https://api.crossref.org/prefixes/10.2307/works'
PREFIX_INFO = 'https://api.crossref.org/prefixes/10.2307'
CROSSREF_INFO = 'https://www.crossref.org/documentation/retrieve-metadata/rest-api/'
LIBRARY_INFO = 'https://libdb.zju.edu.cn/s/lib/libtb/show/413'

def search(query, page=1, rows=5):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为1—200字符')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000) or isinstance(rows, bool) or (not isinstance(rows, int)) or (not 1 <= rows <= 20):
        raise ValueError('页码或数量超限')
    if page * rows > 10000:
        raise ValueError('Crossref offset 与 rows 的范围不可超过10000；此入口未实现 cursor 深分页')
    q = query.strip()
    url = ENDPOINT + '?' + urlencode({'query.bibliographic': q, 'rows': rows, 'offset': (page - 1) * rows})
    p = release_runtime.run(['/usr/bin/curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-filesize', '8000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Crossref 查询失败: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > 8000000:
        raise RuntimeError('Crossref 响应超过8MB')
    d = json.loads(p.stdout)
    m = d.get('message', {})
    if d.get('status') != 'ok' or not isinstance(m.get('items'), list) or len(m['items']) > rows:
        raise RuntimeError('Crossref 返回格式或数量异常')
    items = []
    for x in m['items']:
        if not isinstance(x, dict):
            raise RuntimeError('Crossref 题录格式异常')
        titles = x.get('title', [])
        authors = x.get('author', [])
        if not isinstance(titles, list) or any((not isinstance(t, str) for t in titles)) or (not isinstance(authors, list)) or any((not isinstance(a, dict) for a in authors)):
            raise RuntimeError('Crossref 标题或作者格式异常')
        doi = x.get('DOI')
        if not isinstance(doi, str) or not doi.lower().startswith('10.2307/'):
            raise RuntimeError('Crossref 返回非 JSTOR 登记前缀结果')
        items.append({'title': titles[0] if titles else '', 'doi': doi, 'doi_url': x.get('URL'), 'type': x.get('type'), 'publisher': x.get('publisher'), 'published': x.get('published'), 'authors': [{'given': a.get('given'), 'family': a.get('family')} for a in authors], 'container_title': x.get('container-title', []), 'issn': x.get('ISSN', [])})
    return {'source': 'Crossref public bibliographic metadata', 'source_url': url, 'prefix_registration': PREFIX_INFO, 'source_documentation': CROSSREF_INFO, 'library_info': LIBRARY_INFO, 'query': q, 'total_reported': m.get('total-results'), 'page': page, 'rows': rows, 'items': items, 'note': '仅查询 Crossref 收录且 DOI 前缀 10.2307 登记为 JSTOR 的元数据子集，不是 JSTOR 站内搜索、全部 JSTOR 内容或浙大全文权限；相关性结果不保证包含关键词，仅返回书目字段，不输出摘要或全文。'}
