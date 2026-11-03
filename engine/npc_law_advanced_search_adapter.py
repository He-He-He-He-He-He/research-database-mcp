"""Bounded official NPC law search with verified date filtering semantics."""
import release_runtime
import datetime, html, re, requests
URL = 'https://flk.npc.gov.cn/law-search/search/list'

def _range(v, name):
    if v is None:
        return []
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        raise ValueError(name + ' requires start and end')
    for x in v:
        if not isinstance(x, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', x):
            raise ValueError(name + ' dates must be YYYY-MM-DD')
        try:
            datetime.date.fromisoformat(x)
        except ValueError:
            raise ValueError('invalid ' + name + ' date') from None
    if v[0] > v[1]:
        raise ValueError(name + ' dates out of order')
    return list(v)

def search(keyword, published=None, effective=None, statuses=None, title_contains='', search_range=1, category=None, agency=None, start_page=1, end_page=1, page_size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200 or (not isinstance(title_contains, str)) or (len(title_contains) > 100):
        raise ValueError('invalid keyword')
    pub = _range(published, 'published')
    eff = _range(effective, 'effective')
    statuses = [] if statuses is None else statuses
    if not isinstance(statuses, list) or any((type(s) is not int or s not in (1, 2, 3, 4) for s in statuses)) or len(set(statuses)) != len(statuses):
        raise ValueError('invalid statuses')
    if type(search_range) is not int or search_range not in (1, 2):
        raise ValueError('search range must be 1 title or 2 content')
    if any((type(x) is not int for x in (start_page, end_page, page_size))) or not 1 <= start_page <= end_page <= 10000 or end_page - start_page >= 10 or (not 1 <= page_size <= 50):
        raise ValueError('up to 10 pages, page size 1–50')
    for v in (category, agency):
        if v is not None and (type(v) is not int or not 0 <= v <= 9999):
            raise ValueError('invalid category or agency')
    rows = []
    seen = set()
    duplicates = []
    unknown = []
    totals = []
    for page in range(start_page, end_page + 1):
        body = {'searchRange': search_range, 'sxrq': [], 'gbrq': pub, 'searchType': 2, 'sxx': statuses, 'gbrqYear': [], 'flfgCodeId': [] if category is None else [category], 'zdjgCodeId': [] if agency is None else [agency], 'searchContent': keyword, 'orderByParam': {'order': '-1', 'sort': ''}, 'pageNum': page, 'pageSize': page_size}
        r = requests.post(URL, json=body, headers={'Referer': 'https://flk.npc.gov.cn/'}, timeout=(8, 20), allow_redirects=False)
        r.raise_for_status()
        j = r.json()
        items = j.get('rows') if isinstance(j, dict) else None
        if not isinstance(j, dict) or j.get('code') != 200 or type(j.get('total')) is not int or (not isinstance(items, list)) or (len(items) > page_size):
            raise RuntimeError('unexpected NPC search response')
        totals.append(j['total'])
        for x in items:
            if not isinstance(x, dict):
                raise RuntimeError('invalid search row')
            if statuses and x.get('sxx') not in statuses:
                raise RuntimeError('source returned unexpected status')
            if pub:
                date = x.get('gbrq')
                if not isinstance(date, str) or not pub[0] <= date <= pub[1]:
                    raise RuntimeError('source returned out-of-range publication date')
            identifier = x.get('bbbs')
            if identifier in seen:
                duplicates.append(identifier)
            else:
                seen.add(identifier)
            title = html.unescape(re.sub('<[^>]*>', '', str(x.get('title', ''))))
            if title_contains and title_contains not in title:
                continue
            if eff:
                date = x.get('sxrq')
                if not isinstance(date, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', date):
                    unknown.append(identifier)
                    continue
                if not eff[0] <= date <= eff[1]:
                    continue
            rows.append({'source_page': page, 'title_plain': title, 'source_record': x})
    return {'source_url': URL, 'keyword': keyword, 'source_search_range': search_range, 'published_filter': pub, 'effective_filter_local': eff, 'statuses': statuses, 'start_page': start_page, 'end_page': end_page, 'page_size': page_size, 'source_totals_unverified': totals, 'matching_rows': len(rows), 'rows': rows, 'duplicate_ids': duplicates, 'excluded_missing_effective_date_ids': unknown, 'note': '公布日期和效力筛选由来源执行并核验返回行；生效日期及标题包含条件仅对所请求的页本地过滤。实测源 sxrq 参数被忽略，故不传；筛后空结果不代表全库无结果。来源相关度排序和总量不稳定，跨页可能漏重，当前效力以官网及后续修订为准。'}
