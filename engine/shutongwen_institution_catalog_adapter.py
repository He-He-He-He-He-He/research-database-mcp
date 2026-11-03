"""Institution-session Shh Tong Wen search-path catalog, no text excerpts."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://gujiku.unihan.com.cn/'
PRODUCTS = {'qing_records': 'QSL', 'qing_institutions': 'QHD', 'stone_inscriptions': 'LDSK'}

def search(product, keyword, page=1, limit=10, session=None, include_snippet=False, second_keyword='', logic='And'):
    if not isinstance(second_keyword, str) or len(second_keyword) > 100 or any((ord(c) < 32 for c in second_keyword)):
        raise ValueError('第二关键词须为不超过100字的单行文本')
    if logic not in ('And', 'Or', 'Not') or (not second_keyword.strip() and logic != 'And'):
        raise ValueError('检索逻辑或第二关键词无效')
    if product not in PRODUCTS:
        raise ValueError('不支持的子库')
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    if type(include_snippet) is not bool:
        raise ValueError('片段开关须为布尔值')
    q = keyword.strip()
    app = PRODUCTS[product]
    s = session or requests.Session()
    r = s.get(BASE + 'Products/Search/' + app, timeout=20)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    if not re.search('\\bzjdx\\b', p.get_text(' ', strip=True), re.I):
        raise RuntimeError('未识别学校账户标识')
    v = p.select_one('input[name=catalogVersion]')
    if not v or not v.get('value'):
        raise RuntimeError('未识别目录版本')
    body = {'version': '', 'catalogVersion': v['value'], 'sl_0': 'And', 'sv_0': q, 'gl': True, 'page': page, 'count': 10, 'sort': 0, 'start': (page - 1) * 10, 'appId': app, 'clauses': [{'searchLogic': 'And', 'searchTerm': q}]}
    if second_keyword.strip():
        body.update({'sl_1': logic, 'sv_1': second_keyword.strip()})
        body['clauses'].append({'searchLogic': logic, 'searchTerm': second_keyword.strip()})
    r = s.post(BASE + 'Products/SearchApi/' + app, json=body, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    root = p.select_one('.search-results')
    if not root or root.get('data-appid') != app:
        raise RuntimeError('未识别对应子库搜索结果')
    text = root.get_text(' ', strip=True)
    m = re.search('共匹配到\\s*([\\d,]+)\\s*页\\s*([\\d,]+)\\s*命中', text)
    if not m:
        if '无检索结果' in text:
            matched = hits = 0 if page == 1 else None
        else:
            raise RuntimeError('未识别结果数量')
    else:
        matched, hits = (int(x.replace(',', '')) for x in m.groups())
    items = []
    for a in root.select('a.list-group-item[data-pageid]'):
        h = a.select_one('h4')
        ident = a.get('data-pageid')
        title = h.get_text('', strip=True) if h else ''
        if not ident or not ident.isdigit() or (not title):
            raise RuntimeError('命中路径缺失')
        item = {'page_id': ident, 'path': title}
        if include_snippet:
            snippet = a.select_one('p.list-group-item-text')
            raw = snippet.decode_contents().strip() if snippet else None
            if raw is not None and re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', raw, re.I):
                item['snippet_raw_html'] = None
                item['snippet_omitted'] = True
            else:
                item['snippet_raw_html'] = raw
        items.append(item)
    if len(items) > 10 or (matched and page == 1 and (not items)):
        raise RuntimeError('检索结果异常')
    result = {'source': '书同文古籍数据库', 'account_marker': 'zjdx', 'product': product, 'query': q, 'page': page, 'matched_document_pages': matched, 'hit_count': hits, 'source_page_items': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'note': '当前页面显示学校账户标识；关联简繁异体字，站方命中片段保留原始 HTML，可能截断，非完整正文；匹配页数与命中次数不同，未验证全文权限；limit只截取原站当前页，若truncated为true，翻到下一站方页会遗漏本页其余结果，请用limit=10取整页。' if include_snippet else '当前页面显示学校账户标识；关联简繁异体字，返回命中路径不含正文；匹配页数与命中次数不同，未验证全文权限；limit只截取原站当前页，若truncated为true，翻到下一站方页会遗漏本页其余结果，请用limit=10取整页。'}
    if matched is None:
        result['note'] += ' 当前请求页无结果，站方未提供总匹配页数或命中次数；不能认定整个检索无命中。'
    if include_snippet:
        result['note'] += ' 片段含链接或疑似凭据标记时省略并标记。'
    if second_keyword.strip():
        result['second_keyword'] = second_keyword.strip()
        result['logic_requested'] = logic
        result['note'] += ' 站方未回显完整检索条件，匹配页数与命中次数分别保留。'
    return result
