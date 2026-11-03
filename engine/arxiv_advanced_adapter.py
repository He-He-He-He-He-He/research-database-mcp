"""arXiv Atom API structured discovery and exact preprint metadata."""
import release_runtime
import datetime, re, requests, xml.etree.ElementTree as ET
from urllib.parse import urlsplit
URL = 'https://export.arxiv.org/api/query'
A = '{http://www.w3.org/2005/Atom}'
AR = '{http://arxiv.org/schemas/atom}'
OS = '{http://a9.com/-/spec/opensearch/1.1/}'
ID = '(?:\\d{4}\\.\\d{4,5}|[a-z-]+(?:\\.[A-Za-z-]+)?/\\d{7})(?:v\\d+)?'

def _fetch(params):
    with requests.get(URL, params=params, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        source = r.url
        body = bytearray()
        for b in r.iter_content(65536):
            body.extend(b)
            if len(body) > 10000000:
                raise ValueError('arXiv response exceeds 10 MB')
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        raise RuntimeError('arXiv did not return valid Atom XML') from None
    if root.tag != A + 'feed':
        raise RuntimeError('unexpected arXiv response root')
    items = []
    for e in root.findall(A + 'entry'):
        url = e.findtext(A + 'id', '')
        p = urlsplit(url)
        identifier = p.path.removeprefix('/abs/')
        if p.hostname not in ('arxiv.org', 'www.arxiv.org') or not p.path.startswith('/abs/') or (not re.fullmatch(ID, identifier)):
            raise RuntimeError('unexpected arXiv article ID')
        clean = lambda v: ' '.join((v or '').split())
        items.append({'id': identifier, 'source_url': url, 'title': clean(e.findtext(A + 'title')), 'abstract': clean(e.findtext(A + 'summary')), 'published': e.findtext(A + 'published'), 'updated': e.findtext(A + 'updated'), 'authors': [clean(x.findtext(A + 'name')) for x in e.findall(A + 'author')], 'categories': [x.get('term') for x in e.findall(A + 'category')], 'doi': e.findtext(AR + 'doi'), 'journal_ref': e.findtext(AR + 'journal_ref'), 'comment': e.findtext(AR + 'comment'), 'links': [{'href': x.get('href'), 'type': x.get('type'), 'title': x.get('title')} for x in e.findall(A + 'link')]})
    return (source, root, items)

def _date(x):
    if not isinstance(x, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', x):
        raise ValueError('dates must be YYYY-MM-DD')
    try:
        datetime.date.fromisoformat(x)
    except ValueError:
        raise ValueError('invalid date') from None
    return x

def search(keyword, field='all', category='', start_date=None, end_date=None, sort='submittedDate', size=10, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 300 or any((c in keyword for c in ['"', '\n', '\r'])):
        raise ValueError('invalid keyword')
    if field not in ('all', 'ti', 'au', 'abs'):
        raise ValueError('invalid field')
    if not isinstance(category, str) or (category and (not re.fullmatch('[A-Za-z0-9.-]{1,40}', category))):
        raise ValueError('invalid category')
    if (start_date is None) != (end_date is None):
        raise ValueError('provide both dates')
    q = field + ':"' + keyword.strip() + '"'
    if category:
        q += ' AND cat:' + category
    if start_date:
        start_date = _date(start_date)
        end_date = _date(end_date)
        if start_date > end_date:
            raise ValueError('date range reversed')
        q += ' AND submittedDate:[' + start_date.replace('-', '') + '0000 TO ' + end_date.replace('-', '') + '2359]'
    if sort not in ('relevance', 'lastUpdatedDate', 'submittedDate') or type(size) is not int or (not 1 <= size <= 25) or (type(offset) is not int) or (offset < 0) or (offset + size > 10000):
        raise ValueError('invalid sorting or pagination')
    params = {'search_query': q, 'start': offset, 'max_results': size, 'sortBy': sort, 'sortOrder': 'descending'}
    source, root, items = _fetch(params)
    total = root.findtext(OS + 'totalResults')
    if not isinstance(total, str) or not total.isdigit() or len(items) > size:
        raise RuntimeError('unexpected arXiv search count')
    return {'source_url': source, 'query': q, 'total': int(total), 'offset': offset, 'items': items, 'note': 'arXiv 预印本可能未同行评审；日期为来源 submittedDate 检索条件，发表与更新字段应分别核验。摘要/元数据不代表论文结果可靠；跨请求排序可能变化。'}

def detail(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(ID, identifier):
        raise ValueError('invalid arXiv identifier')
    source, root, items = _fetch({'id_list': identifier})
    if len(items) != 1:
        raise ValueError('article not found or ambiguous')
    expected = identifier
    actual = items[0]['id'] if re.search('v\\d+$', identifier) else re.sub('v\\d+$', '', items[0]['id'])
    if actual != expected:
        raise RuntimeError('arXiv returned a different identifier')
    return {'source_url': source, 'item': items[0], 'note': '元数据及摘要；预印本版本可能更新，同行评审状态与许可需核原始论文。'}
