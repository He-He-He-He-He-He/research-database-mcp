"""CABI 注册于 Crossref 的公开书籍、章节题录，不访问 Ovid。"""
import release_runtime
import requests
from crossref_catalog_validation import validate_crossref_page
BASE = 'https://api.crossref.org/members/242/works'
TYPES = ('book', 'edited-book', 'monograph', 'book-chapter', 'reference-book')

def cabi_books_metadata(query, work_type='book-chapter', page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if work_type not in TYPES:
        raise ValueError('请选择 TYPES 中的一种出版类型')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    r = requests.get(BASE, params={'query': query.strip(), 'filter': 'type:' + work_type, 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('message', {})
    items = d.get('items')
    total = d.get('total-results')
    validate_crossref_page(d, page_size)
    rows = []
    for x in items:
        if not x.get('title'):
            continue
        rows.append({'doi': x.get('DOI'), 'title': x['title'][0], 'publisher': x.get('publisher'), 'type': x.get('type'), 'container_title': x.get('container-title', []), 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')})
    return {'source': 'Crossref 成员 242 CABI Publishing 登记公开题录', 'source_url': BASE, 'library_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1005', 'query': query.strip(), 'type': work_type, 'page': page, 'upstream_total': total, 'items': rows, 'note': '按 Crossref 登记成员和作品类型查询，不等于全部 CABI 书籍或浙大 Ovid 订购子集；可能包含该成员登记的其他出版物。未验证原站机构访问、正文或全文权限。'}
