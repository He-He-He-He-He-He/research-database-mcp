"""通过 Crossref 官方公开元数据 API 检索 ACS 登记的期刊文章，不使用机构凭据。"""
import release_runtime
import re
import requests
from crossref_catalog_validation import validate_crossref_page
from urllib.parse import urlencode
from bs4 import BeautifulSoup
BASE = 'https://api.crossref.org/members/316/works'

def search_acs(query, rows=10, offset=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('query 必须为 1 至 200 字')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 50):
        raise ValueError('rows 必须为 1 至 50 的整数')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000):
        raise ValueError('offset 必须为 0 至 10000 的整数')
    if offset + rows > 10000:
        raise ValueError('Crossref works 的 offset + rows 不得超过 10000；此入口未实现 cursor 深分页')
    r = requests.get(BASE, params={'query': query.strip(), 'rows': rows, 'offset': offset, 'filter': 'type:journal-article'}, timeout=25)
    r.raise_for_status()
    data = r.json()
    if data.get('status') != 'ok' or not isinstance(data.get('message'), dict):
        raise RuntimeError('Crossref 返回异常')
    message = data['message']
    validate_crossref_page(message, rows)
    items = []
    for x in message['items']:
        title = BeautifulSoup((x.get('title') or [''])[0], 'html.parser').get_text(' ', strip=True)
        names = [' '.join(filter(None, (a.get('given'), a.get('family')))) for a in x.get('author', [])]
        published = x.get('published', {}).get('date-parts', [[]])[0]
        doi = x.get('DOI')
        items.append({'title': title, 'authors': names, 'doi': doi, 'url': 'https://doi.org/' + doi if doi else None, 'publication_date': published, 'type': x.get('type')})
    return {'source': 'Crossref 公开元数据，限定 American Chemical Society 会员 316 登记的期刊文章', 'source_url': BASE + '?' + urlencode({'query': query.strip(), 'rows': rows, 'offset': offset, 'filter': 'type:journal-article'}), 'query': query.strip(), 'total': message['total-results'], 'offset': offset, 'items': items, 'scope': 'Crossref 收录及相关性检索，仅 DOI 登记者会员 316 的期刊文章，可能包括更正或新闻；不代表 ACS 全部内容、浙大订购范围或全文权限；相关性排序跨请求可能变化，分页可能重叠或遗漏，offset + rows 最多10000，未实现深分页。', 'library_entry': 'https://libdb.zju.edu.cn/s/lib/libtb/show/390'}
