"""Crossref 公布的牛津 OSO DOI 模式书目，不证明学校订购。"""
import release_runtime
import re
import requests
from crossref_catalog_validation import validate_crossref_page
BASE = 'https://api.crossref.org/members/286/works'
_PATTERN = re.compile('^10\\.1093/(?:acprof:)?oso/[^/]+\\.001\\.0001$', re.I)

def oxford_oso_metadata(query, work_type='monograph', page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if work_type not in ('monograph', 'edited-book', 'book'):
        raise ValueError('作品类型限 monograph、edited-book、book')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    params = {'query': query.strip(), 'filter': 'type:' + work_type + ',from-pub-date:1963-01-01,until-pub-date:2025-12-31', 'rows': page_size, 'offset': (page - 1) * page_size}
    r = requests.get(BASE, params=params, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('message', {})
    items = d.get('items')
    total = d.get('total-results')
    validate_crossref_page(d, page_size)
    rows = []
    for x in items:
        doi = x.get('DOI', '')
        title = x.get('title', [])
        if not _PATTERN.fullmatch(doi) or not title:
            continue
        rows.append({'doi': doi, 'title': title[0], 'publisher': x.get('publisher'), 'type': x.get('type'), 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')})
    return {'source': 'Crossref 牛津成员 286 公开元数据，以 OSO 书籍 DOI 模式筛选', 'source_url': BASE, 'library_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1241', 'query': query.strip(), 'type': work_type, 'page': page, 'upstream_total': total, 'items': rows, 'note': '限定 Crossref 出版日期 1963–2025，仅按 OSO 书籍 DOI 格式筛选，可能漏掉其他格式，且在上游分页后过滤，可能空页；上游总数不是筛选后的书数。馆方订购 15 个学科包的部分专著，公开元数据不能判断哪些书被订购、对应学科或全文权限。'}
