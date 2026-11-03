"""联合国西亚经社会阿拉伯发展门户数据集元数据及有界分页。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlsplit, parse_qs, urlencode
from bs4 import BeautifulSoup
PORTAL = 'https://jordan.unescwa.org'
API = 'https://api.arabdevelopmentportal.org/api/data/'
MAX_BYTES = 8000000

def _fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('UNESCWA 门户请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小限制')
    return p.stdout

def categories():
    url = PORTAL + '/datacatalog'
    soup = BeautifulSoup(_fetch(url), 'html.parser')
    items = []
    seen = set()
    for a in soup.find_all('a', href=True):
        h = a['href']
        if re.fullmatch('/datacatalog/[a-z-]+', h, re.I) and h not in seen:
            seen.add(h)
            items.append({'path': h, 'text': a.get_text(' ', strip=True), 'url': PORTAL + h})
    if not items:
        raise ValueError('未识别门户分类')
    return {'source': url, 'items': items, 'note': '门户分类导航，不是全部数据集目录；分类列表可能动态加载。'}

def _args(category, ident):
    if category not in ('un-agencies', 'national-data', 'other-institutions'):
        raise ValueError('不支持该门户分类')
    if not isinstance(ident, str) or not re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', ident):
        raise ValueError('数据集 UUID 无效')
    return PORTAL + '/datacatalog/' + category + '/' + ident

def metadata(category, ident):
    url = _args(category, ident)
    soup = BeautifulSoup(_fetch(url), 'html.parser')
    node = soup.find('input', id='API')
    if not node or not node.get('value'):
        raise ValueError('数据页面未提供可识别的 API')
    parsed = urlsplit(node['value'])
    values = parse_qs(parsed.query)
    if parsed.scheme != 'https' or parsed.netloc != 'api.arabdevelopmentportal.org' or parsed.path != '/api/data/' or (values.get('name') != [ident]) or (len(values.get('organization', [])) != 1) or (len(values.get('source', [])) != 1):
        raise ValueError('数据页面 API 地址不符合安全约束')
    organization = values['organization'][0]
    source = values['source'][0]
    if any((not re.fullmatch('[a-zA-Z0-9_-]{1,80}', v) for v in (organization, source))):
        raise ValueError('数据来源参数无效')
    for e in soup(['script', 'style', 'noscript']):
        e.decompose()
    title = soup.find('h1')
    text = soup.get_text(' ', strip=True)
    return {'source': url, 'title': title.get_text(' ', strip=True) if title else '', 'organization': organization, 'api_source': source, 'page_text': text[:20000], 'note': '页面标题与描述可能由 AI 自动生成，不等于原始统计标题；须逐项核对数据字段、来源和方法。文本可能含导航及截断。'}

def records(category, ident, page=1):
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 10000):
        raise ValueError('页号须在 1–10000')
    meta = metadata(category, ident)
    query = {'name': ident, 'organization': meta['organization'], 'source': meta['api_source'], 'ReturnFull': 'true', 'Page': page}
    url = API + '?' + urlencode(query)
    v = json.loads(_fetch(url))
    d = v.get('data', {})
    if not isinstance(d, dict) or not isinstance(d.get('data'), list) or (not isinstance(d.get('total'), int)):
        raise ValueError('数据 API 响应异常')
    return {'source': url, 'dataset_page': meta['source'], 'page': page, 'total': d['total'], 'returned': len(d['data']), 'schema': d.get('schema'), 'records': d['data'], 'note': '返回上游指定页；各表字段和数值口径不同，须核对数据源、单位、年度、估计和缺失。目录由多机构供数，不是全由 ESCWA 采集。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('categories')
    q = s.add_parser('metadata')
    q.add_argument('category')
    q.add_argument('id')
    q = s.add_parser('records')
    q.add_argument('category')
    q.add_argument('id')
    q.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    v = categories() if a.cmd == 'categories' else metadata(a.category, a.id) if a.cmd == 'metadata' else records(a.category, a.id, a.page)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
