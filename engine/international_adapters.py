"""只读学术文献与科研数据检索：Europe PMC、DataCite、IEEE、Springer Nature。"""
import release_runtime
import argparse, json, os, re, subprocess, sys, xml.etree.ElementTree as ET
from urllib.parse import urlencode, quote

def _curl(url):
    if '\n' in url or '\r' in url:
        raise ValueError('请求不得含换行')
    config = 'url = "' + url.replace('\\', '\\\\').replace('"', '\\"') + '"\n'
    result = release_runtime.run(['/usr/bin/curl', '--silent', '--show-error', '--fail', '--max-time', '25', '--config', '-'], input=config, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError('请求失败（curl 状态 %s）；请检查网络、上游状态与授权' % result.returncode)
    return result.stdout

def _json(url):
    try:
        return json.loads(_curl(url))
    except json.JSONDecodeError:
        raise RuntimeError('上游返回非 JSON；可能需要授权或接口已变更')

def epmc_search(query, size=5, cursor='*'):
    if not query.strip() or not 1 <= size <= 25 or len(cursor) > 1000:
        raise ValueError('关键词必填，每页 1–25 条')
    params = {'query': query, 'format': 'json', 'pageSize': size, 'resultType': 'core', 'cursorMark': cursor}
    return _json('https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urlencode(params))

def epmc_fulltext(pmcid):
    if not re.fullmatch('PMC[0-9]+', pmcid):
        raise ValueError('请输入 PMC 编号，例如 PMC7096777')
    xml = _curl('https://www.ebi.ac.uk/europepmc/webservices/rest/' + pmcid + '/fullTextXML')
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise RuntimeError('上游未返回完整的 JATS XML') from e
    local = lambda tag: tag.rsplit('}', 1)[-1] if isinstance(tag, str) else ''
    if local(root.tag) != 'article':
        raise RuntimeError('上游 XML 根节点不是文章')
    front = next((x for x in root if local(x.tag) == 'front'), None)
    meta = next((x for x in front if local(x.tag) == 'article-meta'), None) if front is not None else None
    ids = [(x.text or '').strip() for x in meta if local(x.tag) == 'article-id' and x.get('pub-id-type', '').lower() in ('pmcid', 'pmc')] if meta is not None else []
    normalized = [v if v.upper().startswith('PMC') else 'PMC' + v for v in ids if v]
    if normalized and any((v.upper() != pmcid for v in normalized)):
        raise RuntimeError('正文中的 PMC 编号与请求不匹配')
    return {'source': 'Europe PMC', 'id': pmcid, 'format': 'JATS XML', 'pmcid_verified': bool(normalized), 'content': xml, 'note': '仅获取上游允许获取的开放全文；如正文未提供 PMC 编号则无法从文内核验身份，后续使用请核查具体许可。'}

def datacite_search(query, size=5, page=1):
    if not query.strip() or not 1 <= size <= 25 or (not 1 <= page <= 100):
        raise ValueError('关键词必填，每页 1–25 条，页码 1–100')
    data = _json('https://api.datacite.org/dois?' + urlencode({'query': query, 'page[size]': size, 'page[number]': page}))
    if not isinstance(data, dict) or not isinstance(data.get('data'), list):
        raise RuntimeError('DataCite 返回异常或数据结构变化')
    return {**data, 'toolkit_note': 'DataCite 跨请求排序可能变化，分页可能重复或遗漏，不保证穷尽；数据集或作品元数据不代表全文权限。'}

def datacite_doi(doi):
    if not re.fullmatch('10\\.\\d{4,9}/\\S+', doi, re.I) or len(doi) > 500:
        raise ValueError('请输入有效 DOI，例如 10.15468/s9sehb')
    return _json('https://api.datacite.org/dois/' + quote(doi, safe=''))

def ieee_search(query, size=5):
    key = release_runtime.environment.get('IEEE_API_KEY', '')
    if not key:
        raise ValueError('需要在环境变量 IEEE_API_KEY 中设置 IEEE API 密钥')
    if not query.strip() or not 1 <= size <= 25:
        raise ValueError('关键词必填，每页 1–25 条')
    params = {'querytext': query, 'max_records': size, 'apikey': key, 'format': 'json'}
    return _json('https://ieeexploreapi.ieee.org/api/v1/search/articles?' + urlencode(params))

def springer_search(query, size=5):
    key = release_runtime.environment.get('SPRINGER_API_KEY', '')
    if not key:
        raise ValueError('需要在环境变量 SPRINGER_API_KEY 中设置 Springer Nature API 密钥')
    if not query.strip() or not 1 <= size <= 25:
        raise ValueError('关键词必填，每页 1–25 条')
    return _json('https://api.springernature.com/meta/v2/json?' + urlencode({'q': query, 'p': size, 's': 1, 'api_key': key}))

def openalex_search(query, entity='works', size=5, page=1):
    if not query.strip() or entity not in ('works', 'authors', 'institutions') or (not 1 <= size <= 25) or (not 1 <= page <= 100):
        raise ValueError('关键词必填，类型须为 works/authors/institutions，每页 1–25 条，页码 1–100')
    params = {'search': query, 'per-page': size, 'page': page}
    key = release_runtime.environment.get('OPENALEX_API_KEY', '')
    if key:
        params['api_key'] = key
    data = _json('https://api.openalex.org/' + entity + '?' + urlencode(params))
    if 'results' not in data:
        raise RuntimeError('OpenAlex 返回异常或配额不足')
    return data

def arxiv_search(query, size=5, start=0):
    if not query.strip() or type(size) is not int or (not 1 <= size <= 25) or (type(start) is not int) or (start < 0) or (start + size > 10000):
        raise ValueError('关键词必填，每页 1–25 条，start 非负且 start + size 不超过 10000（源站当前实测边界）')
    params = {'search_query': 'all:' + query, 'start': start, 'max_results': size}
    xml = _curl('https://export.arxiv.org/api/query?' + urlencode(params))
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        raise RuntimeError('arXiv 返回非预期 XML')
    ns = {'a': 'http://www.w3.org/2005/Atom', 'o': 'http://a9.com/-/spec/opensearch/1.1/'}
    total = root.findtext('o:totalResults', namespaces=ns)
    items = []
    for e in root.findall('a:entry', ns):
        items.append({'id': e.findtext('a:id', namespaces=ns), 'title': ' '.join(e.findtext('a:title', default='', namespaces=ns).split()), 'abstract': ' '.join(e.findtext('a:summary', default='', namespaces=ns).split()), 'published': e.findtext('a:published', namespaces=ns), 'updated': e.findtext('a:updated', namespaces=ns), 'authors': [x.findtext('a:name', namespaces=ns) for x in e.findall('a:author', ns)], 'categories': [x.get('term') for x in e.findall('a:category', ns)], 'links': [{'href': x.get('href'), 'type': x.get('type'), 'title': x.get('title')} for x in e.findall('a:link', ns)]})
    if total is None:
        raise RuntimeError('arXiv 未返回搜索结果字段')
    return {'source': 'https://export.arxiv.org/api/query', 'query': query, 'start': start, 'total': int(total), 'items': items, 'note': '预印本不一定经过同行评审；内容使用请核对许可。当前源站实测 start + size 不超过 10000，跨请求结果可能变化。'}

def doaj_search(query, entity='articles', size=5, page=1):
    if not query.strip() or entity not in ('articles', 'journals') or (not 1 <= size <= 25) or (not 1 <= page <= 100):
        raise ValueError('关键词必填，类型须为 articles/journals，每页 1–25 条，页码 1–100')
    url = 'https://doaj.org/api/v4/search/' + entity + '/' + quote(query, safe='') + '?' + urlencode({'page': page, 'pageSize': size})
    data = _json(url)
    if 'results' not in data:
        raise RuntimeError('DOAJ 返回异常或数据结构变化')
    return data

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    for name in ('epmc', 'datacite', 'ieee', 'springer'):
        q = sub.add_parser(name)
        q.add_argument('query')
        q.add_argument('--size', type=int, default=5)
        if name == 'epmc':
            q.add_argument('--cursor', default='*')
        if name == 'datacite':
            q.add_argument('--page', type=int, default=1)
    q = sub.add_parser('epmc-fulltext')
    q.add_argument('pmcid')
    q = sub.add_parser('datacite-doi')
    q.add_argument('doi')
    q = sub.add_parser('openalex')
    q.add_argument('query')
    q.add_argument('--entity', choices=['works', 'authors', 'institutions'], default='works')
    q.add_argument('--size', type=int, default=5)
    q.add_argument('--page', type=int, default=1)
    q = sub.add_parser('arxiv')
    q.add_argument('query')
    q.add_argument('--size', type=int, default=5)
    q.add_argument('--start', type=int, default=0)
    q = sub.add_parser('doaj')
    q.add_argument('query')
    q.add_argument('--entity', choices=['articles', 'journals'], default='articles')
    q.add_argument('--size', type=int, default=5)
    q.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    if a.cmd == 'epmc':
        result = epmc_search(a.query, a.size, a.cursor)
    elif a.cmd == 'epmc-fulltext':
        result = epmc_fulltext(a.pmcid)
    elif a.cmd == 'datacite':
        result = datacite_search(a.query, a.size, a.page)
    elif a.cmd == 'datacite-doi':
        result = datacite_doi(a.doi)
    elif a.cmd == 'openalex':
        result = openalex_search(a.query, a.entity, a.size, a.page)
    elif a.cmd == 'arxiv':
        result = arxiv_search(a.query, a.size, a.start)
    elif a.cmd == 'doaj':
        result = doaj_search(a.query, a.entity, a.size, a.page)
    elif a.cmd == 'ieee':
        result = ieee_search(a.query, a.size)
    else:
        result = springer_search(a.query, a.size)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
